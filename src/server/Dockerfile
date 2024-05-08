# Use the official Python base image
FROM python:3.11-bullseye

# Set the working directory
WORKDIR /server

# Set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y gcc python3-dev musl-dev libmagic1 libffi-dev netcat-traditional \
    build-essential libpq-dev
RUN pip3 install poetry

COPY requirements.txt ./

# # Install dependencies
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

COPY ./ /server/
EXPOSE 8000