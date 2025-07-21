#!/bin/bash

# IOAgent Backend Only Development Script

echo "🐍 Starting IOAgent Backend..."
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Use virtual environment Python directly
PYTHON_BIN="./venv/bin/python"

# Check if venv exists
if [ ! -f "$PYTHON_BIN" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "   Creating .env from example..."
    cp .env.example .env
    echo "   ⚠️  Please edit .env and add your Anthropic API key"
fi

# Create required directories
mkdir -p projects/uploads projects/generated

# Initialize database if needed
if [ ! -f "src/database/app.db" ]; then
    echo "   Initializing database..."
    $PYTHON_BIN -c "from app import app, db; app.app_context().push(); db.create_all(); print('   Database initialized!')"
fi

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "🌐 Starting Flask server..."
echo "   - Backend API: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask with the virtual environment Python
$PYTHON_BIN app.py