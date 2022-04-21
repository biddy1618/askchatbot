import requests
import random
import json
import re

import pandas as pd

import tqdm

DATA_URL    = './scripts/data/UCIPM_Chatbot_Core_Questions 2020_08_19.xlsx - Questions with correct link.csv'

URL     = 'http://localhost:5005/webhooks/rest/webhook'
SENDER  = random.randint(0, 9)
DATA    = {
    'message'   : '', 
    'sender'    : str(SENDER)
}

def _read_data():
    df = pd.read_csv(DATA_URL)

    df['request']   = df['Question'   ].apply(lambda x: x.split('\n')[0]              )
    df['answer' ]   = df['URL'        ].apply(lambda x: x.split('\n')                 )
    df['answer' ]   = df['answer'     ].apply(lambda x: [x1.split('?')[0] for x1 in x])

    df              = df[['request', 'answer']]

    messages        = df.values.tolist()

    return messages

def _get_results(messages):
    results = []

    print(f'Querying {len(messages)} questions against chatbot...')

    for m, _ in tqdm.tqdm(messages):
        DATA['message'] = m
        r = requests.post(URL, json = DATA)
        r = json.loads(r.text)
        
        assert isinstance(r, list)
        assert len(r) >= 3
        r = r[2]

        assert 'custom' in r
        r = r['custom']

        assert 'data' in r
        r = r['data']

        result = []
        for e in r:
            title   = re.findall("<em>(.*?)</em>"           , e['title'])[0]
            link    = re.findall("href=[\"\'](.*?)[\"\']"   , e['title'])[0]
            result.append((title, link))
        
        results.append(result)

        DATA['message'] = '/intent_affirm'
        r = requests.post(URL, json = DATA)
        r = json.loads(r.text)

        assert len(r) == 1
        r = r[0]

        assert 'text' in r
        r = r['text']

        assert 'Anything else I can help with?' == r

    return results

def _get_scores(messages, results):
    scores = []
    for i, r in enumerate(results):
        answers = messages[i][1]
        topn = [False, False, False]
        for _, r1 in enumerate(r):
            if r1[1].split('?')[0] in answers:
                if i == 0:
                    topn[0] = True
                if i < 3:
                    topn[1] = True
                topn[2] = True
        scores.append(topn)
    
    return scores

def print_metrics(scores):
    top1 = 0
    top3 = 0
    top5 = 0
    for topn in scores:
        if topn[0]: top1 += 1
        if topn[1]: top3 += 1
        if topn[2]: top5 += 1

    

    print(f'Out of {len(scores)} results, following correct:'  )
    print(f'Top 1: {top1:<3d} ({top1/len(scores) * 100:<.2f}%)')
    print(f'Top 3: {top3:<3d} ({top3/len(scores) * 100:<.2f}%)')
    print(f'Top 5: {top5:<3d} ({top5/len(scores) * 100:<.2f}%)')

def main():
    
    messages    = _read_data()
    results     = _get_results(messages)

    scores = _get_scores(messages, results)

    print_metrics(scores)


if __name__ == "__main__":
    main()
