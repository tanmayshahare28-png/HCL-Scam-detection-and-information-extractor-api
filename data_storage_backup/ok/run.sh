#!/bin/bash
# Run the Agentic Honey-Pot API

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Create logs directory
mkdir -p logs

# Check if Ollama is running
echo "Checking Ollama status..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Run the application
echo ""
echo "=========================================="
echo "  Agentic Honey-Pot API Starting..."
echo "=========================================="
echo ""
echo "  API:      http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Frontend: http://localhost:8000"
echo ""
echo "=========================================="
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
