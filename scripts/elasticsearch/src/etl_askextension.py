"""ETL for the scraped askextensiondata json, to prepare it for ingestion into
elastic search.

The scraped AskExtension data:
https://dev.osticket.eduworks.com/kb/faq.php?id=faq_id
https://dev.osticket.eduworks.com/kb/faq.php?id=221      (example for Potatoes)

The JSON files representing questions and answers from the Ask Extension system:
https://drive.google.com/drive/folders/12CyhdvCwNLgtdUHTcmWkAKR4oIWhGKHq
"""

import json
import string
from pathlib import Path
import pandas as pd
import numpy as np
from actions.actions_parquet import file_size

# Define the index
data_name = "askextensiondata"  # pylint: disable=invalid-name

DATA_FILE = f"{Path(__file__).parents[6]}/data/{data_name}/{data_name}.json"

DATA_FILE_GUIDE = f"{Path(__file__).parents[6]}/data/{data_name}/{data_name}-guide.csv"

SCRAPED_DATA_FILES = [
    f"{Path(__file__).parents[6]}/data/{data_name}/2012-2014.json",
    f"{Path(__file__).parents[6]}/data/{data_name}/2014-2016.json",
    f"{Path(__file__).parents[6]}/data/{data_name}/2016-2018.json",
    f"{Path(__file__).parents[6]}/data/{data_name}/2018-2020.json",
]

DATA_FILE_CALIFORNIA = (
    f"{Path(__file__).parents[1]}/data/ipmdata/{data_name}-california.json"
)

pd.set_option("display.max_columns", 100)
pd.set_option("display.min_rows", 25)
pd.set_option("display.max_rows", 25)
pd.set_option("display.width", 1000)
# pd.set_option('display.max_colwidth', None)


def remove_encodings_and_escapes(text):
    """See: https://stackoverflow.com/a/53821967/5480536"""
    return text.encode("ascii", "ignore").decode().replace("\n", " ").replace('"', '"')


def merge_scraped_data_files(scraped_data_files, data_file):
    """Combines the exported data files into one. Writes it out in readable format"""
    data = []
    for exported_data_file in scraped_data_files:
        with open(exported_data_file) as f:
            data.extend(json.load(f))

    print(f"Writing merged file: {data_file}")
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)


def make_answer_a_list_and_clean_response(answer_dict):
    """convert it from a dictionary into a list"""
    answers = [{}] * len(answer_dict)
    for key, value in answer_dict.items():
        # clean the response up
        value["response"] = remove_encodings_and_escapes(value["response"].strip())
        answers[int(key) - 1] = value
    return answers


def etl(path_data, path_guide, data_file_california, max_word_count=None, verbose=1):
    """ETL"""

    # Read all faqs
    df = pd.read_json(path_data).set_index("faq-id")
    if verbose:
        print(f"All faqs: {df.shape[0]}")

    # From california only
    mask = df["state"] == "California"
    df = df[mask]
    if verbose:
        print(f"California faqs: {df.shape[0]}")

    df_guide = pd.read_csv(path_guide).set_index("faq-id")
    assert (
        df_guide["include"].dtypes == np.bool
    ), "df_guide 'include' column did not come in as boolean. Using spaces (?)"

    # remove rows as indicated in guide
    df["include"] = df_guide["include"]
    df["include"] = df["include"].fillna(True)
    df = df.drop(df[~df["include"]].index)
    df = df.drop("include", 1)

    # for consistency with the ipmdata json files, transform it into a list
    df["answer"] = [
        make_answer_a_list_and_clean_response(answer_dict)
        for answer_dict in df["answer"]
    ]

    # add the url
    df["url"] = [
        f"https://dev.osticket.eduworks.com/kb/faq.php?id={faq_id}"
        for faq_id in df.index.tolist()
    ]

    # strip all spaces
    for column in ["state", "title", "question"]:
        df[column] = df[column].str.strip()

    #
    # clean titles
    #
    # strip ' #number' from title
    # strip '...' from titles like https://dev.osticket.eduworks.com/kb/faq.php?id=7826
    #
    titles = df["title"].tolist()
    titles = ["".join(title.split("#")[:-1]).strip().strip("...") for title in titles]
    # add a '.' if it does not yet end with a punctuation
    titles = [
        title if (title and title[-1] in string.punctuation) else title + "."
        for title in titles
    ]
    df["title"] = titles

    #
    # title-question:
    #
    # Add title to tqs, but only if it is not already exactly in the question
    questions = df["question"].tolist()
    tqs = [
        question
        if (title and question.startswith(title[:-1]))
        else title + " " + question
        for (title, question) in zip(titles, questions)
    ]
    tqs = [remove_encodings_and_escapes(tq) for tq in tqs]
    df["title-question"] = tqs

    #
    # Remove questions with less than 2 words in title-question
    shape = df.shape
    mask = [len(x.split()) > 2 for x in df["title-question"].tolist()]
    df = df[mask]
    print(f"Removed {shape[0] - df.shape[0]} title-question with less than 2 words")
    #
    # remove extremely long questions or responses:
    #
    if max_word_count:
        # drop rows with excessive word count in response or question
        mask = [
            (len(q) <= max_word_count and len(r) <= max_word_count)
            for (q, r) in zip(df["title-question"].tolist(), df["response"].tolist())
        ]
        df = df[mask]
        print(f"Removed {shape[0] - df.shape[0]} with more than {max_word_count} words")

    #
    # replace NaN with [] for attachments
    df["attachments"] = [[] if x is np.nan else x for x in df["attachments"]]

    # Write it to disk, for ingestion into elastic search
    # The writing is a little weird, as a list, to make it the consistent with others
    # we only use a few columns
    df = df.reset_index()
    df = df.loc[
        :,
        [
            "faq-id",
            "url",
            "title",
            "title-question",
            "created",
            "updated",
            "state",
            "county",
            "question",
            "answer",
            "attachments",
        ],
    ]
    with open(data_file_california, "w") as f:
        f.write(df.reset_index().to_json(orient="records", indent=2))

    print("ETL completed:")
    print(f"df of california faqs: {df.shape}")
    print(" ")
    print(f"File: {data_file_california} ({file_size(data_file_california)})")

    return df


if __name__ == "__main__":

    MERGE_IT = True
    if MERGE_IT:
        merge_scraped_data_files(SCRAPED_DATA_FILES, DATA_FILE)
    else:
        print("Not merging json files, just reading the full one")

    df_california = etl(
        DATA_FILE, DATA_FILE_GUIDE, DATA_FILE_CALIFORNIA, max_word_count=None, verbose=1
    )

    print("All done.")
