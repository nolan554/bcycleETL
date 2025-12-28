FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fsSLo /usr/local/bin/supercronic \
    https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
  && chmod +x /usr/local/bin/supercronic

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY etl.py /app/etl.py
COPY ml /app/ml
COPY crontab /app/crontab

CMD ["/usr/local/bin/supercronic", "/app/crontab"]
