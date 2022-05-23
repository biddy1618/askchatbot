from typing import List, Tuple

import requests
import logging
import random
import json
import sys
import re
import os

import pandas as pd
import mlflow

import argparse

parser = argparse.ArgumentParser(description = 'Script for getting stats for chatbot accuracy of valid queries and recall of NA queries.')
parser.add_argument('--save', action = 'store_true', help = 'If using in MLFlow environment to save stats.')

args = parser.parse_args()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_VALID  = os.getenv('DATA_VALID'    , 'scripts/scoring/data/transformed/valid_questions.pkl')
DATA_NA     = os.getenv('DATA_NA'       , 'scripts/scoring/data/transformed/na_questions.pkl'   )
RASA_URL    = os.getenv('RASA_URL'      , 'http://localhost:5005/webhooks/rest/webhook'         )
DESCRIPTION = os.getenv('DESCRIPTION'   , 'Experiment running locally'                          )

def _read_data(
    path: str, 
    urls: bool = False
    ) -> Tuple[List, List]:
    '''Read the data of questions for querying against the chatbot.

    Args:
        path    (str)           : Path to data to be read.
        urls    (bool, optional): If URLs as answers are in the data provided. Defaults to False.

    Returns:
        Tuple[List, List]: List of questions along with correct answers (URLs).
    '''
    df = pd.read_pickle(path)
    
    answers     = None
    questions   = df['Question' ].values.tolist()
    if urls:
        answers = df['URL'      ].values.tolist()

    return (questions, answers)


def _get_results(questions: List) -> List:
    '''Query the list of questions against the chatbot in development environment.

    Args:
        questions (List): List of questions.

    Returns:
        List: Returns the list of answers generated by the chatbot.
    '''

    SENDER  = random.randint(0, 1000000)
    DATA    = {
        'message'   : '', 
        'sender'    : str(SENDER)
    }

    results = []

    logger.info(f'Querying {len(questions)} questions against chatbot...')
    for i, q in enumerate(questions):

        DATA['message'] = q
        try:
            response = requests.post(RASA_URL, json = DATA)
            if response.status_code != 200:
                logger.error(f'Error: Service at {RASA_URL} is unavailable, exit.')
                exit()

        except Exception as e:
            logger.error(f'Error: Exception at posting question - "{q}", exit. {type(e).__name__}: "{e}".')
            exit()

        
        try:
            r = json.loads(response.text)
            success = False
            for link in r:
                if 'custom' in link:
                    success = True
                    r = link['custom']
                    break
        except Exception as e:
            logger.error(f'Error: Failed on parsing response on question - "{q}", exit. {type(e).__name__}: "{e}".')
            exit()

        
        result = []
        if success:
            try:
                r = r['data']
                if len(r) == 0:
                    raise Exception
            except Exception as e:
                logger.error(f'Error: Failed on parsing response on question - "{q}", exit. . {type(e).__name__}: "{e}".')

            for e in r:
                title   = re.findall("<em>(.*?)</em>"           , e['title'])[0]
                link    = re.findall("href=[\"\'](.*?)[\"\']"   , e['title'])[0]
                result.append((title, link))
            

            DATA['message'] = '/intent_affirm'
            try:
                response = requests.post(RASA_URL, json = DATA)
                if response.status_code != 200:
                    logger.error(f'Error: Service at {RASA_URL} is unavailable, exit.')
                    exit()
            except Exception as e:
                logger.error(f'Error: Exception at posting affirmative message on question - "{q}", exit. {type(e).__name__}: "{e}".')
                exit()
            
            try:
                r = json.loads(response.text)
                r = r[0]
                r = r['text']
                if 'Anything else I can help with?' != r:
                    raise Exception
            except Exception as e:
                logger.error(f'Error: Failed on parsing response of affirmative message on question - "{q}", exit. {type(e).__name__}: "{e}".')
                exit()
        else:
            logger.info(f'No results for question - "{q}".')
            
        if (i+1)%5 == 0:
            logger.info(f'Finished {i+1} questions...')
        
        results.append(result)
    
    logger.info(f'Finished querying all {len(questions)} questions for scoring.')
    return results


def _calc_stats_valid_queries() -> Tuple[int, dict]:
    '''Get stats for valid queries.

    Returns:
        Tuple[int, dict]: Tuple of integer and dictionary, where integer is number of questions and dict is statistics.
    '''

    def _get_scores(
        answers: List, 
        results: List
        ) -> List:
        '''Get scores for the messages - in top 1, 3, 5 and 10 results from the chatbot.

        Args:
            answers (List): Correct URLS to questions.
            results (List): Correspondong results from chatbot.

        Returns:
            List: List of scores in boolean quadruples (for top 1, 3, 5, and 10 hits correspondingly).
        '''
        scores = []
        for i, r in enumerate(results):
            answer = answers[i]
            topn = [False, False, False, False]
            for i1, r1 in enumerate(r):
                if r1[1].split('?')[0] in answer:
                    if i1 == 0:
                        topn[0] = True
                    if i1 < 3:
                        topn[1] = True
                    if i1 < 5:
                        topn[2] = True
                    topn[3] = True
            scores.append(topn)

        return scores

    def _get_stats(
        scores: List,
        ) -> dict:
        '''Get statistics for valid queries of the questions.

        Args:
            scores (List): List of scores in boolean quatruplets.

        Returns:
            dict: Dictinary of total hits for each rank (1, 3, 5, and 10). 
        '''

        topn = {
            '1' : 0,
            '3' : 0,
            '5' : 0,
            '10': 0
        }
        
        for score in scores:
            if score[0]: topn['1'   ] += 1
            if score[1]: topn['3'   ] += 1
            if score[2]: topn['5'   ] += 1
            if score[3]: topn['10'  ] += 1
        
        return topn
    
    questions, answers  = _read_data    (DATA_VALID, urls = True)
    results             = _get_results  (questions)
    scores              = _get_scores   (answers, results)
    topn                = _get_stats    (scores)
    total               = len           (questions)

    return (total, topn)
    

def _calc_stats_na_queries() -> Tuple[int, int]:
    '''Get stats for NA queries.
    
    Returns:
        Tuple[int, int]: Tuple of two integers, where first one is number of questions and another one is number of correctly categorized questions.
    '''
    
    def _get_stats(results: List) -> int:
        '''Get statistics for NA queries of the questions.

        Args:
            results (List): List of answers generated by chatbot.

        Returns:
            int: Number of NA queries that are correctly categorized as out of scope.
        '''
        no_results = 0
        for res in results:
            if len(res) == 0:
                no_results += 1
        
        return no_results

    questions, _    = _read_data    (DATA_NA, urls = False)
    results         = _get_results  (questions)
    no_results      = _get_stats    (results)
    total           = len           (results)

    return (total, no_results)


def main(save = False) -> None:
    '''Prints out the metrics.'''

    logger.info(f'---------------------------------------------------------------')
    logger.info(f'DESCRIPTION       : {DESCRIPTION}')
    logger.info(f'RASA CHATBOT URL  : {RASA_URL}'   )
    
    logger.info(f'Reading data for valid queries and getting stats.')
    total_valid , topn          = _calc_stats_valid_queries ()

    logger.info(f'Reading data for NA queries and getting stats.')
    total_na    , no_results    = _calc_stats_na_queries    ()

    logger.info(f'---------------------------------------------------------------')
    logger.info(f'Statistics for valid questions:')
    logger.info(f'Out of {total_valid} valid queries, following correct:'  )
    logger.info(f'Top 1 : {topn["1" ]:<3d} ({topn["1" ]/total_valid * 100:<.2f}%)')
    logger.info(f'Top 3 : {topn["3" ]:<3d} ({topn["3" ]/total_valid * 100:<.2f}%)')
    logger.info(f'Top 5 : {topn["5" ]:<3d} ({topn["5" ]/total_valid * 100:<.2f}%)')
    logger.info(f'Top 10: {topn["10"]:<3d} ({topn["10"]/total_valid * 100:<.2f}%)')


    logger.info(f'---------------------------------------------------------------')
    logger.info(f'Statistics for NA questions:')
    logger.info(f'Out of {total_na} NA questions {no_results} have correctly returned 0 results')
    logger.info(f'Recall: {no_results/total_na * 100:.2f}%')
    logger.info(f'---------------------------------------------------------------')
    
    if save:
        # Set MLflow experiment name (MLFLOW_EXPERIMENT_NAME is set in the workflow or docker-compose)
        mlflow.set_experiment(os.getenv('MLFLOW_EXPERIMENT_NAME'))
        # Start an MLflow run
        with mlflow.start_run() as run:
            # Log evaluation results to MLflow
            mlflow.log_metric("valid_total", total_valid)
            mlflow.log_metric("valid_top01", topn["1" ]/total_valid * 100)
            mlflow.log_metric("valid_top03", topn["3" ]/total_valid * 100)
            mlflow.log_metric("valid_top05", topn["5" ]/total_valid * 100)
            mlflow.log_metric("valid_top10", topn["10"]/total_valid * 100)
            
            mlflow.log_metric("na_total" , total_na)
            mlflow.log_metric("na_recall", no_results/total_na * 100)
            
            mlflow.log_param("description", DESCRIPTION) # Short description of is being evaluated


if __name__ == "__main__":
    main(save = args.save)
