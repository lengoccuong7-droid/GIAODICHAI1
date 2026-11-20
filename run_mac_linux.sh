#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/streamlit ]; then
  echo "Chua cai moi truong. Chay: python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
. .venv/bin/activate
streamlit run app.py
