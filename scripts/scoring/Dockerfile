FROM python:3.9-slim-bullseye
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
WORKDIR /app

COPY "data/transformed/na_questions.pkl" /app/
COPY "data/transformed/valid_questions.pkl" /app/
COPY "run_scoring.py" /app/
CMD ["python", "run_scoring.py"]