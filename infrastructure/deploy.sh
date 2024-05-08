#!/bin/bash

git pull
docker compose -f infrastructure/prod/docker-compose.yaml up -d --build
