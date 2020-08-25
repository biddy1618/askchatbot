"""
Create training data for a ResponseSelector from the scraped AskExtension data:
https://dev.osticket.eduworks.com/kb/faq.php?id=faq_id   
https://dev.osticket.eduworks.com/kb/faq.php?id=221      (example for Potatoes)

Retrieval Actions & Response Selectors, with training data format are described here:
https://rasa.com/docs/rasa/core/retrieval-actions/

The JSON files representing questions and answers from the Ask Extension system:
https://drive.google.com/drive/folders/12CyhdvCwNLgtdUHTcmWkAKR4oIWhGKHq 
"""
import logging
import sys
import string
from pathlib import Path
import spacy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from actions import actions_config as ac
from actions.actions_parquet import file_size, persist_df, read_df
from actions.actions_spacy import (
    pd_tokens_from_spacy,
    pd_sentences_from_spacy,
)

pd.set_option("display.max_columns", 100)
pd.set_option("display.min_rows", 25)
pd.set_option("display.max_rows", 25)
pd.set_option("display.width", 1000)
# pd.set_option('display.max_colwidth', None)

nlp = spacy.load("en")

# log to stdout instead of default stderr
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def plot_word_counts(df_plot):
    """Plot histograms of the word counts"""
    # Histogram of word-count in responses
    s = pd.Series([len(x) for x in df_plot["response"].tolist()])
    ax = s.hist(bins=50)
    ax.set_xlabel("Word count in responses")
    ax.set_ylabel("Response counts")
    plt.show()
    #
    # Histogram of word-count in questions
    s = pd.Series([len(x) for x in df_plot["title-question"].tolist()])
    ax = s.hist(bins=50)
    ax.set_xlabel("Word count in questions")
    ax.set_ylabel("Question counts")
    plt.show()


def remove_encodings_and_escapes(sentences):
    """See: https://stackoverflow.com/a/53821967/5480536"""
    return [
        s.encode("ascii", "ignore").decode().replace("\n", " ").replace('"', '"')
        for s in sentences
    ]


def etl(path_data, path_guide, max_word_count=None, verbose=1, plot=True):
    """ETL for the extracted ask extension data.
    Returns a pandas dataframe for processing by spacy"""
    df_data = pd.read_json(path_data).set_index("faq-id")

    df_guide = pd.read_csv(path_guide).set_index("faq-id")
    assert (
        df_guide["include"].dtypes == np.bool
    ), "df_guide 'include' column did not come in as boolean. Using spaces (?)"

    if verbose:
        print("-----------------------------------------------------------------------")
        print("ETL:")
        print(f"File: {path_data} ({file_size(path_data)})")
        print(f"df_data: {df_data.shape}")
        print(f"File: {path_guide} ({file_size(path_guide)})")
        print(f"df_guide: {df_guide.shape}")

    # remove rows as indicated in guide
    df = df_data.copy()
    df["include"] = df_guide["include"]
    df["include"] = df["include"].fillna(True)
    df = df.drop(df_data[~df["include"]].index)
    df = df.drop("include", 1)

    # response is the 1st answer
    df["response"] = [answer["1"]["response"] for answer in df["answer"]]

    # we only use a few columns
    df = df.loc[:, ["state", "title", "question", "response", "answer"]]

    # strip all spaces
    for column in ["state", "title", "question", "response"]:
        df[column] = df[column].str.strip()

    # intent-id
    df["intent-id"] = [
        str(faq_id) + "_" + state.replace(" ", "")
        for (faq_id, state) in zip(df.index.tolist(), df["state"].tolist())
    ]
    df = df.drop("state", 1)

    #
    # title-question:
    #
    titles = df["title"].tolist()
    questions = df["question"].tolist()
    # strip ' #number' from title
    # strip '...' from titles like https://dev.osticket.eduworks.com/kb/faq.php?id=7826
    titles = ["".join(title.split("#")[:-1]).strip().strip("...") for title in titles]
    # add a '.' if it does not yet end with a punctuation
    titles = [
        title if (title and title[-1] in string.punctuation) else title + "."
        for title in titles
    ]
    # Add title to tqs, but only if it is not already exactly in the question
    tqs = [
        question
        if (title and question.startswith(title[:-1]))
        else title + " " + question
        for (title, question) in zip(titles, questions)
    ]
    tqs = remove_encodings_and_escapes(tqs)
    df["title-question"] = tqs

    #
    # cleanup
    #
    #
    # Remove questions with less than 2 words in title-question
    shape = df.shape
    mask = [len(x.split()) > 2 for x in df["title-question"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} title-question with less than 2 words")
    #
    # remove long responses:
    #
    shape = df.shape
    df["response"] = remove_encodings_and_escapes(df["response"].tolist())
    #
    if plot:
        plot_word_counts(df)
    #
    if max_word_count:
        # drop rows with excessive word count in response or question
        mask = [
            (len(q) <= max_word_count and len(r) <= max_word_count)
            for (q, r) in zip(df["title-question"].tolist(), df["response"].tolist())
        ]
        df = df[mask]
        print(f"Removed {shape[0] - df.shape[0]} with more than {max_word_count} words")
        if plot:
            plot_word_counts(df)
    #
    # Remove responses with less than 4 words
    shape = df.shape
    mask = [len(x.split()) > 4 for x in df["response"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} responses with less than 4 words")
    #
    # Remove responses with 'font-'
    shape = df.shape
    mask = ["font-" not in x for x in df["response"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} responses with font-")
    #
    # Questions with 'font-' data
    shape = df.shape
    mask = ["font-" not in x for x in df["title-question"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} questions with font-")

    if verbose:
        print("ETL completed:")
        print(f"df: {df.shape}")
        print(" ")

    return df


def write_training_data(
    df, path_nlu, path_responses, response_selector_name, verbose=1
):
    """Write the training files"""

    with open(path_nlu, "w") as f:
        f.write("<!-- This file is auto-generated from scraped JSON. -->\n")
        f.write("\n")

        for (intent_id, short_question) in zip(
            df["intent-id"].tolist(), df["short-question"].tolist(),
        ):
            f.write(f"## intent: {response_selector_name}/{intent_id}\n")
            f.write(f"- {short_question}\n\n")

    with open(path_responses, "w") as f:
        f.write("<!-- This file is auto-generated from scraped JSON. -->\n")
        f.write("\n")

        for (intent_id, short_response) in zip(
            df["intent-id"].tolist(), df["short-response"].tolist(),
        ):
            f.write(f"## {intent_id}\n")
            f.write(f"* {response_selector_name}/{intent_id}\n")
            f.write(f"  - {short_response}\n\n")

    if verbose:
        print("-----------------------------------------------------------------------")
        print(f"{path_nlu} ({file_size(path_nlu)})")
        print(f"{path_responses} ({file_size(path_responses)})")


def make_it_short(title, text, do_title=True, do_questions=True, do_nouns=True):
    """Create a representative short version"""

    titles = []
    if do_title:
        titles = [title]

    # sentences that are questions
    questions = []
    if do_questions:
        df_sentences = pd_sentences_from_spacy(nlp, text)
        mask = df_sentences["is_question"]
        questions = df_sentences.loc[mask, "sentence"].tolist()
        # cutoff those long rambling questions at 100 characters
        questions = [text[:100] for text in questions]

    # nouns.
    nouns = []
    if do_nouns:
        df_tokens = pd_tokens_from_spacy(nlp, text)
        mask = df_tokens["pos_"] == "NOUN"
        # the top 10 most occuring nouns
        nouns = df_tokens.loc[mask, "text"].value_counts().index.tolist()[:10]

    # join it all into one string
    short_text = " ".join(titles + questions + nouns)

    # remove some unwelcome words
    banned = ["%"]
    short_text = " ".join([word for word in short_text.split() if word not in banned])

    banned_starts_with = ["http"]
    for bsw in banned_starts_with:
        short_text = " ".join(
            [word for word in short_text.split() if not word.startswith(bsw)]
        )

    return short_text


def etl_spacy(df, verbose=1):
    """Extract representive 'short strings' for each title & question, using spacy.
    Returns a pandas dataframe for writing NLU training data"""
    if verbose:
        print("ETL with spacy to create shorter strings for questions & responses")

    df = df.copy()

    faq_ids = df.index.tolist()
    titles = df["title"].tolist()
    questions = df["question"].tolist()
    responses = df["response"].tolist()

    titles = remove_encodings_and_escapes(titles)
    questions = remove_encodings_and_escapes(questions)
    responses = remove_encodings_and_escapes(responses)

    #
    # titles:
    #
    # strip ' #number' from title
    # strip '...' from titles like https://dev.osticket.eduworks.com/kb/faq.php?id=7826
    titles = ["".join(title.split("#")[:-1]).strip().strip("...") for title in titles]
    # add a '.' if it does not yet end with a punctuation
    titles = [
        title if (title and title[-1] in string.punctuation) else title + "."
        for title in titles
    ]
    # In short_question, use title only if it is not already exactly in the question
    titles_for_questions = [
        "" if (title and question.startswith(title[:-1])) else title
        for (title, question) in zip(titles, questions)
    ]

    short_questions = []
    short_responses = faq_ids
    for title, title_for_question, question, response in zip(
        tqdm(titles, desc="Create short strings"),
        titles_for_questions,
        questions,
        responses,
    ):
        # build short question
        short_question = make_it_short(
            title_for_question,
            question,
            do_title=True,
            do_questions=True,
            do_nouns=True,
        )
        short_questions.append(short_question)

        # for response, just use the faq_id. Seems to work best
    ##        # build short response
    ##        short_response = make_it_short(
    ##            title, response, do_title=True, do_questions=False, do_nouns=True
    ##        )
    ##        question_nouns_string = make_it_short(
    ##            title, question, do_title=False, do_questions=False, do_nouns=True
    ##        )
    ##        short_response = f"{short_response} {question_nouns_string}"

    df["short-question"] = short_questions
    df["short-response"] = short_responses
    return df


def main():
    """Main function"""

    data_name = "askextensiondata"
    max_word_count = None

    do_etl = True

    if do_etl:

        df = etl(
            f"{Path(__file__).parents[6]}/data/{data_name}/{data_name}-california.json",
            f"{Path(__file__).parents[6]}/data/{data_name}/{data_name}-guide.csv",
            max_word_count,
            verbose=1,
            plot=False,
        )

        df = etl_spacy(df, verbose=2)

        # save the ETL result, also used by the custom action
        persist_df(
            df,
            local_dir=f"{Path(__file__).parents[3]}/actions",
            fname=ac.askextension_parquet,
        )
    else:
        df = read_df(
            local_dir=f"{Path(__file__).parents[3]}/actions",
            fname=ac.askextension_parquet,
        )

    write_training_data(
        df,
        f"{Path(__file__).parents[3]}/data/nlu/nlu-{data_name}-california.md",
        f"{Path(__file__).parents[3]}/data/nlu/responses-{data_name}-california.md",
        "askextension_california",
    )


if __name__ == "__main__":
    main()
