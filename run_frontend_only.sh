#!/bin/bash

# IOAgent Frontend Only Development Script

echo "⚛️  Starting IOAgent React Frontend..."
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies (this may take a few minutes)..."
    npm install --legacy-peer-deps
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