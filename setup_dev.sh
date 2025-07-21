#!/bin/bash
# Setup development environment for IOAgent

set -e  # Exit on error

echo "IOAgent Development Setup"
echo "========================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.txt

echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p static/uploads
mkdir -p static/projects
mkdir -p htmlcov
mkdir -p logs

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Security Keys (generate new ones for production!)
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production

# Database
DATABASE_URL=sqlite:///ioagent_dev.db

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Application Settings
PORT=5001
EOF
    echo "⚠️  Please update .env with your actual API keys!"
fi

# Create test environment file
if [ ! -f .env.test ]; then
    echo "📝 Creating .env.test file..."
    cat > .env.test << EOF
FLASK_ENV=testing
SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
DATABASE_URL=sqlite:///test_ioagent.db
ANTHROPIC_API_KEY=test-api-key
EOF
fi

# Initialize database
echo "🗄️  Initializing database..."
python manage.py init_db

# Create admin user (optional)
echo ""
read -p "Would you like to create an admin user? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py create_admin
fi

# Install pre-commit hooks (optional)
echo ""
read -p "Would you like to install pre-commit hooks? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
fi

# Run initial tests
echo ""
echo "🧪 Running initial tests..."
pytest tests/test_models.py -v || {
    echo "⚠️  Some tests failed. This is normal for initial setup."
}

# Final instructions
echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your Anthropic API key"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run tests: ./run_tests.sh"
echo "4. Start development server: python manage.py run_server"
echo "   or: ./run_local.sh"
echo ""
echo "Useful commands:"
echo "  python manage.py --help        # Show all management commands"
echo "  python manage.py check_config  # Check configuration"
echo "  ./run_tests.sh --help         # Test runner options"