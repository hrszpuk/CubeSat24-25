#!/usr/bin/env bash

set -e

if [ ! -d venv ]; then
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

git fetch origin main

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

cd Vector

if [ "$LOCAL" != "$REMOTE" ]; then
  git pull origin main
  if git diff --name-only HEAD@{1} HEAD | grep -q '^requirements.txt$'; then
    pip install -r requirements.txt
  fi
fi

exec python3 startup.py
