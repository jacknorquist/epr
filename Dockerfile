FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
