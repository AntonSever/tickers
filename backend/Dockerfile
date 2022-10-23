FROM python:3.10-alpine
WORKDIR /backend
COPY backend/requirements.txt /
RUN apk add --no-cache build-base
RUN python3 -m pip install -r /requirements.txt
COPY backend /backend
