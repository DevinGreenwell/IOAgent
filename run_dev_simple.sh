#!/bin/bash

# IOAgent Simple Development Startup Script (Backend + Frontend)

echo "🚀 Starting IOAgent Development Environment (Simple Mode)..."
echo ""

# Function to kill all background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js is not installed. Please install Node.js first:"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Setup Backend
echo "🔧 Setting up Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update backend dependencies
echo "   Installing backend dependencies..."
pip install -q -r requirements.txt

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
    python -c "from app import app, db; app.app_context().push(); db.create_all(); print('   Database initialized!')"
fi

# Start Flask backend
echo ""
echo "🐍 Starting Flask backend..."
python app.py &
BACKEND_PID=$!
sleep 3

# Setup Frontend
echo ""
echo "⚛️  Setting up Frontend..."

# Navigate to frontend directory
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies (this may take a few minutes)..."
    npm install
else
    echo "   Frontend dependencies already installed"
fi

# Create .env file for frontend if it doesn't exist
if [ ! -f ".env" ]; then
    echo "   Creating frontend .env file..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=ws://localhost:5001
EOF
fi

# Start React development server
echo ""
echo "🎨 Starting React frontend..."
npm start &
FRONTEND_PID=$!

# Wait for services to start
sleep 5

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:5001"
echo ""
echo "⚠️  Note: Running without Redis/Celery - async features disabled"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user to stop the script
wait