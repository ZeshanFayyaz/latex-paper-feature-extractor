#!/bin/bash
read -p "Enter your question about the paper: " ticket

if [ -z "$ticket" ]; then
  echo "No input given. Please enter a question."
  exit 1
fi

# Build safe JSON payload using jq (never breaks)
payload=$(jq -n --arg ticket_text "$ticket" '{ticket_text: $ticket_text}')

# Send to API
curl -s -X POST "http://127.0.0.1:8000/ask-paper" \
  -H "Content-Type: application/json" \
  -d "$payload" | jq .
