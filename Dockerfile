# syntax=docker/dockerfile:1
FROM python:3.8
ENV PYTHONUNBUFFERED=1
# RUN apk update && \
#     apk add --virtual build-deps gcc python3-dev musl-dev && \
#     apk add postgresql-dev
RUN apt update
WORKDIR /code
COPY ./src/requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/