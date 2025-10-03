#!/bin/bash
read -p "Enter your question about the paper: " query

if [ -z "$query" ]; then
  echo "No input given. Please enter a question."
  exit 1
fi

curl -s -X POST "http://127.0.0.1:8000/ask-paper" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$query\"}" | jq .
