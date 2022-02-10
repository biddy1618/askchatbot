'''
ETL for the scraped askextensiondata json, to prepare it for ingestion into
elastic search.

Data can be retrieved through this API `https://ask2.extension.org/api/knowledge/YYYY-MM-DD/YYYY-MM-DD`

The JSON files representing questions and answers from the Ask Extension system:
https://drive.google.com/drive/folders/12CyhdvCwNLgtdUHTcmWkAKR4oIWhGKHq
'''
import pandas as pd
import numpy as np

import json
from io import StringIO

import re
from string import punctuation as pn

import constants

import logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__file__)


def _clean(text):
    '''
    Fix encodings and remove escape and redundant whitespace characters from text.

    Examples with non-ascii characters - 110358, 147160
    Examples with redundant whitespace - 117069, 127760

    See: https://stackoverflow.com/a/53821967/5480536
    '''
    text = text.encode('ascii', 'ignore').decode()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _merge_json(source_files):
    '''
    Combines the data files into one and returns it.
    '''
    
    data = []
    for file in source_files:
    
        with open(file) as f:
            data.extend(json.load(f))
    
    return json.dumps(data)

def _transform_answer(answer_dict):
    '''
    Convert answer field from a dictionary to a list.
    '''
    answers = [{}] * len(answer_dict)
    
    for key, value in answer_dict.items():
        # clean the response up
        value['response'] = _clean(value['response'])
        answers[int(key) - 1] = value
    
    return answers

def _transform_title(title):
    '''
    Remove question ID from title, and append '.' in the end
    if no punctuation was detected.

    Example with '#' - 437259
    Example with '...' - 437264
    '''
    title = "".join(title.split('#')[:-1]).strip().strip('...')
    
    # add a '.' if it does not yet end with a punctuation
    title = title if (title and title[-1] in pn) else title + '.'
    
    return title

def _merge_title_question(df):
    '''
    Create new column from questions and title,
    but only if it is not already exactly in the question.
    '''
    titles      = df["title"].tolist()
    questions   = df["question"].tolist()
    
    tqs = [
        question
        if (title and question.startswith(title[:-1]))
        else title + " " + question
        for (title, question) in zip(titles, questions)
    ]

    return tqs

def _transform_save(data, path_save, min_word_count = 2, max_str_len = None, state_filters = ['California']):
    '''
    Read json string data, transform and save.
    '''
    # Read all data
    logger.info('Reading data into DataFrame')
    df = pd.read_json(StringIO(data)).set_index("faq-id")
    
    # Leave tickets from California state
    logger.info(f'Filtering states - {state_filters}')
    df = df[df['state'] == 'California']

    # Add the URL and leave blank URL for questions with no ID
    logger.info('Adding URL')
    df['url'] = [
        f"{constants.ASKEXTENSION_QUESTION_URL}{ticket_no}" if len(ticket_no) == 6 else ""
        for ticket_no in df['title'].str.split('#').str[-1]
    ]

    # Add the ticket number from title and leave blank for questions without
    logger.info('Adding ticket number from title')
    df['ticket-no'] = [
        int(ticket_no) if len(ticket_no) == 6 else 0
        for ticket_no in df['title'].str.split('#').str[-1]
    ]

    # Transform answer for consistency with IPM data
    logger.info('Transforming answers')
    df['answer'] = df['answer'].apply(_transform_answer)

    # Strip all spaces and remove non-ascii characters
    logger.info(f'Cleaning long text fields')
    for column in ['state', 'title', 'question']:
        df[column] = df[column].apply(_clean)

    # Clean ID and '...' from title, and append punctuation if not present
    logger.info('Transforming titles')
    df['title'] = df['title'].apply(_transform_title)

    # Create new column from `title` and `question`, or only question
    # if title is exactly the question 
    logger.info('Creating new field out of title and question')
    df['title-question'] = _merge_title_question(df)
    
    # Remove questions with less than 2 words in title-question
    # shape = df.shape
    logger.info(f'Filtering out questions wiht less than {min_word_count} words')
    df = df[df['title-question'].str.split().str.len() > min_word_count]
    
    
    # Trim extremely long questions or responses, if constraint given:
    if max_str_len:
        logger.info(f'Trimming questions and responses to {max_str_len} characters')  
        df['question']          = df['question'].str[:max_str_len]
        df['title-question']    = df['title-question'].str[:max_str_len]
        
        df = df['answer'].apply(lambda answer: [
            r['response'][:max_str_len] for r in answer
            ])
    
    logger.info(f'Saving data as JSON at {path_save}')  
    df = df.reset_index()
    df = df.loc[
        :,
        [
            'faq-id',
            'ticket-no',
            'url',
            'created',
            'updated',
            'state',
            'county',
            'title',
            'question',
            'title-question',
            'answer',
        ],
    ]

    with open(path_save, "w") as f:
        f.write(df.reset_index().to_json(orient="records", indent=2))
    
    return df

if __name__ == "__main__":

    logger.info('Merging source files into one')
    tmp_json = _merge_json(constants.ASKEXTENSION_FILE_NAMES)

    logger.info('Start transforming data')
    _transform_save(tmp_json, constants.ASKEXTENSION_FILE_RESULT)