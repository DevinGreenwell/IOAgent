#!/bin/bash

# IOAgent Frontend Development Script

echo "⚛️  Starting IOAgent React Frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js is not installed. Please install Node.js first:"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
else
    echo "✓ Frontend dependencies already installed"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating frontend .env file..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=ws://localhost:5001
EOF
fi

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "🌐 Starting React development server..."
echo "   - Frontend will be available at: http://localhost:3000"
echo "   - Make sure backend is running on: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start React development server
npm start