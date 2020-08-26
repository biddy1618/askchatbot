# Lessons Learned

## Sentence embedding

- We are using the [**large** universal sentence encoder](https://tfhub.dev/google/universal-sentence-encoder-large/5), but this might be overkill
  - The medium size might be good enough. I did not do a thorough test on this.
  - Using the large version slows down the ingestion, because the embedding takes long. Right now, this is OK, because we only ingest ~3,300 documents.



- ...

## Deployment

- The memory of the EC2 is a bit low:

  - One bot deployment uses ~40 %

  - The bot needs to be stopped before you can run the elasticsearch ingestion script

    

- Deploying 2 Rasa chat-bots on the same EC2 using docker-compose does not work

  - The postgres containers interfere.
  - A temporary solution was to deploy the QA version with docker-compose, and the DEV version with microk8s
  - Going forward, it is recommended to set up a separate EC2 instance for the DEV version



- ...