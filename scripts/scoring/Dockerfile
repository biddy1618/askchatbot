FROM python:3.9-slim-bullseye
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
WORKDIR /app

COPY "data/transformed/result.pkl" /app/
COPY "run_scoring.py" /app/
CMD ["python", "run_scoring.py"]