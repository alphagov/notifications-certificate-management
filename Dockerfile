FROM python:3.8.7-alpine3.12

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY config.py main.py run.sh ./app/
WORKDIR /app

ENTRYPOINT ["./run.sh"]
