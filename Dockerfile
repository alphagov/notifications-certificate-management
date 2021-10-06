FROM python:3.10.0b2-alpine3.12 AS builder

RUN apk add --no-cache \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        openssl-dev \
        cargo

COPY requirements.txt /
RUN pip install --user -r /requirements.txt

FROM python:3.10.0b2-alpine3.12

COPY --from=builder /root/.local /root/.local
COPY config.py main.py run.sh ./app/
WORKDIR /app

ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["./run.sh"]
