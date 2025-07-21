#!/bin/bash
# Start Celery workers and beat scheduler for IOAgent

set -e

echo "Starting Celery services for IOAgent"
echo "===================================="

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please run setup_dev.sh first."
        exit 1
    fi
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew services start redis  (macOS)"
    echo "   sudo systemctl start redis (Linux)"
    echo "   docker run -d -p 6379:6379 redis:7-alpine (Docker)"
    exit 1
fi
echo "✅ Redis is running"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Celery services..."
    pkill -f "celery.*ioagent" || true
    echo "✅ Celery services stopped"
}

trap cleanup EXIT

# Start Celery worker
echo ""
echo "🚀 Starting Celery worker..."
celery -A src.celery_app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=threads \
    -n worker1@%h \
    --queues=default,documents,ai,files,notifications &

WORKER_PID=$!
echo "✅ Celery worker started (PID: $WORKER_PID)"

# Start Celery beat (scheduler)
echo ""
echo "⏰ Starting Celery beat scheduler..."
celery -A src.celery_app.celery_app beat \
    --loglevel=info &

BEAT_PID=$!
echo "✅ Celery beat started (PID: $BEAT_PID)"

# Optional: Start Flower monitoring
read -p "Would you like to start Flower monitoring? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌸 Starting Flower monitoring..."
    celery -A src.celery_app.celery_app flower \
        --port=5555 \
        --url_prefix=flower &
    
    FLOWER_PID=$!
    echo "✅ Flower started at http://localhost:5555 (PID: $FLOWER_PID)"
fi

echo ""
echo "✅ All Celery services are running!"
echo ""
echo "Monitoring logs. Press Ctrl+C to stop all services."
echo ""

# Keep script running and show logs
tail -f celery*.log 2>/dev/null || wait