"""
Create training data for the ResponseSelector from the scraped AskExtension data.

Retrieval Actions & Response Selectors, with training data format are discribed here:
https://rasa.com/docs/rasa/core/retrieval-actions/

The JSON files representing questions and answers from the Ask Extension system:
https://drive.google.com/drive/folders/12CyhdvCwNLgtdUHTcmWkAKR4oIWhGKHq 

A reference conversation with multiple turns between asker & expert:
(This is not common, most have only 1 question & answer)
  {
    "faq-id": 1190,
    "title": "Ditch water for organic farming #118171",
    "created": "2013-03-20 19:08:34",
    "updated": "2013-03-29 21:26:34",
    "tags": [
      "irrigation and water management",
      "organic production"
    ],
    "state": "Colorado",
    "county": "Mesa County",
    "question": "I have been told that if I...",
    "answer": {
      "1": {
        "response": "That's ...",
        "author": "Susan Rose"
      },
      "2": {
        "response": "Thank you ...",
        "author": "The Question Asker"
      },
      "3": {
        "response": "Hello. I'm going ...",
        "author": "Cindy Salter"
      },
      "4": {
        "response": "Thank you for ...",
        "author": "The Question Asker"
      },
      "5": {
        "response": "Hello again,See ...",
        "author": "Cindy Salter"
      }
    }

The following files will be created, with text manipulation as described:

nlu-askextension-tomato.md
==========================
## intent: askextension_tomato/<faq_id>_<state>
- <title>. <question>

<title>. <question>
(-) separate out & mark up urls:
    (-) [name.pdf](http...../name.pdf)   [.pdf]
    (-) [name.php](http...../name.php)   [.php, .php/]
    (-) [name.html](http..../name.html)  [.html]

--
responses-askextension-tomato.md
================================
## <faq_id>_<state>
* askextension_tomato/<faq_id>_<state>
    - <response>

<response>    

(-) separate out & mark up urls (see above)

--
askextensiondata-guide.csv
======================
A table to instruct the generator

faq-id,include,comments

with:
(-) faq-id
(-) include  : [True/False] - include this one or not

"""
import os
import string
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)
# pd.set_option('display.max_colwidth', None)


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            break
        num /= 1024.0

    return f"{num:.1f} {x}"


def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

    return f"File does not exist: {file_path}"


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
    Returns a pandas dataframe that is ready for processing"""
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
    df = df.loc[:, ["state", "title", "question", "response"]]

    # strip all spaces
    for column in df.columns:
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
    # strip '#number' from title
    titles = ["".join(title.split("#")[:-1]).strip() for title in titles]
    # add a '.' if it does not yet end with a punctuation
    titles = [
        title if title[-1] in string.punctuation else title + "." for title in titles
    ]
    #
    tqs = [title + " " + question for (title, question) in zip(titles, questions)]
    tqs = remove_encodings_and_escapes(tqs)
    df["title-question"] = tqs
    df = df.drop("title", 1)
    df = df.drop("question", 1)

    #
    # cleanup
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
    mask = ['font-' not in x for x in df["response"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} responses with font-")
    #
    # Questions with 'font-' data
    shape = df.shape
    mask = ['font-' not in x for x in df["title-question"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} questions with font-")

    #
    #
    # Identical questions
    #
    # Identical responses

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

        for (intent_id, title_question) in zip(
            df["intent-id"].tolist(), df["title-question"].tolist(),
        ):
            f.write(f"## intent: {response_selector_name}/{intent_id}\n")
            f.write(f"- {title_question}\n\n")

    with open(path_responses, "w") as f:
        f.write("<!-- This file is auto-generated from scraped JSON. -->\n")
        f.write("\n")

        for (intent_id, response) in zip(
            df["intent-id"].tolist(), df["response"].tolist(),
        ):
            f.write(f"## {intent_id}\n")
            f.write(f"* {response_selector_name}/{intent_id}\n")
            f.write(f"  - {response}\n\n")

    if verbose:
        print("-----------------------------------------------------------------------")
        print(f"{path_nlu} ({file_size(path_nlu)})")
        print(f"{path_responses} ({file_size(path_responses)})")


def main():
    """Main function"""

    data_name = "askextensiondata"
    max_word_count = 2000

    df = etl(
        f"{Path(__file__).parents[6]}/data/{data_name}/{data_name}-tomato.json",
        f"{Path(__file__).parents[0]}/{data_name}-guide.csv",
        max_word_count,
        verbose=1,
        plot=False,
    )

    write_training_data(
        df,
        f"{Path(__file__).parents[3]}/data/nlu/nlu-{data_name}-tomato.md",
        f"{Path(__file__).parents[3]}/data/nlu/responses-{data_name}-tomato.md",
        "askextension_tomato",
    )


if __name__ == "__main__":
    main()
