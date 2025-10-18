#!/bin/bash
echo "🚀 Starting DiagnoAI in Production Mode..."

# Wait for vector store to be ready (if needed)
if [ -d "/app/data/vector_store" ]; then
    echo "✅ Vector store found"
else
    echo "⚠️  Vector store not found, app will initialize it"
fi

# Start the application
echo "🔧 Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000