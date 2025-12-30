FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"

ARG PKGNAME

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    default-jre \
    ffmpeg \
    espeak


COPY . /home/llm

RUN pip install spacy && \
    python -m spacy download en_core_web_sm   

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install  --no-cache-dir -r /home/llm/requirements_kokoro.txt 


ENV PYTHONPATH=$PYTHONPATH:/home/llm

WORKDIR /home/llm
ENTRYPOINT ["python", "service.py"]




