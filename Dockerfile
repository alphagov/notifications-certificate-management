FROM python:3.8.7-alpine3.12

RUN apk add --no-cache \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        openssl-dev

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY config.py main.py run.sh ./app/
WORKDIR /app

ENTRYPOINT ["./run.sh"]
