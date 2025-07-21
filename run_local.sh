#!/bin/bash

# IOAgent Local Development Startup Script

echo "🚀 Starting IOAgent Local Development Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found! Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your Anthropic API key"
fi

# Create required directories
mkdir -p projects/uploads projects/generated

# Initialize database if needed
if [ ! -f "src/database/app.db" ]; then
    echo "🗄️  Initializing database..."
    python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting server on http://localhost:5001"
echo "📱 Also available on local network at http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask development server
python app.py