#!/bin/bash

echo "Starting DiagnoAI API Server..."

if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama server is not running on localhost:11434"
    echo "Please start Ollama first: ollama serve"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags | grep -q "mistral:7b-instruct"; then
    echo "Error: Mistral 7B model not found in Ollama"
    echo "Available models:"
    curl -s http://localhost:11434/api/tags | jq -r '.models[].name'
    echo ""
    echo "Please pull the model: ollama pull mistral:7b-instruct"
    exit 1
fi

echo "Ollama server is running"
echo "Mistral 7B model found"

cd "$(dirname "$0")/.."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload