FROM python:3.10-alpine
WORKDIR /updater
COPY updater/requirements.txt /
RUN apk add --no-cache build-base
RUN python3 -m pip install -r /requirements.txt
COPY updater /updater
