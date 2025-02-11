#!/usr/bin/env bash

if [[ -z "${DEPLOY_KEY}" ]]; then
  DEPLOY_KEY="$(cat ~/.ssh/id_rsa)"
else
  echo "deploy key has found."
fi

docker build \
  --build-arg DEPLOY_KEY="$DEPLOY_KEY" SERVER_DOMAIN="backend"\  # SERVER_DOMAIN服务器域名
  -t backend-dev .
