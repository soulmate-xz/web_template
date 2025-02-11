#!/usr/bin/env bash

docker-compose up -d
docker-compose run --rm dagou pytest --cov
