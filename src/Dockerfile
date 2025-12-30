FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG PKGNAME

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    ffmpeg \
    espeak

COPY content_core/ /home/llm/content_core/
COPY podcast_creator/ /home/llm/podcast_creator/
COPY resources/ /home/llm/resources/
COPY server/ /home/llm/server/
COPY requirements.txt /home/llm/


RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install  --no-cache-dir -r /home/llm/requirements.txt 

ENV PYTHONPATH=$PYTHONPATH:/home/llm

WORKDIR /home/llm
ENTRYPOINT ["streamlit", "run", "server/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
