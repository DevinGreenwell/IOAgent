#!/bin/bash
# Run IOAgent test suite

set -e  # Exit on error

echo "IOAgent Test Runner"
echo "=================="

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please run setup_dev.sh first."
        exit 1
    fi
fi

# Install test dependencies if needed
echo "📦 Checking test dependencies..."
pip install -q -r requirements-dev.txt 2>/dev/null || {
    echo "Installing test dependencies..."
    pip install -r requirements-dev.txt
}

# Create test environment file if it doesn't exist
if [ ! -f .env.test ]; then
    echo "📝 Creating test environment file..."
    cat > .env.test << EOF
FLASK_ENV=testing
SECRET_KEY=test-secret-key-local
JWT_SECRET_KEY=test-jwt-secret-local
DATABASE_URL=sqlite:///test_ioagent.db
ANTHROPIC_API_KEY=test-api-key
EOF
fi

# Export test environment
export FLASK_ENV=testing
source .env.test

# Parse command line arguments
RUN_COVERAGE=true
RUN_LINTING=true
RUN_SECURITY=false
SPECIFIC_TEST=""
PYTEST_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            RUN_COVERAGE=false
            shift
            ;;
        --no-lint)
            RUN_LINTING=false
            shift
            ;;
        --security)
            RUN_SECURITY=true
            shift
            ;;
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
            shift
            ;;
        --unit)
            PYTEST_ARGS="$PYTEST_ARGS -m unit"
            shift
            ;;
        --integration)
            PYTEST_ARGS="$PYTEST_ARGS -m integration"
            shift
            ;;
        --parallel)
            PYTEST_ARGS="$PYTEST_ARGS -n auto"
            shift
            ;;
        *)
            SPECIFIC_TEST="$1"
            shift
            ;;
    esac
done

# Run linting
if [ "$RUN_LINTING" = true ]; then
    echo ""
    echo "🔍 Running code linting..."
    echo "------------------------"
    flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics || {
        echo "❌ Critical linting errors found!"
        exit 1
    }
    echo "✅ No critical linting errors"
fi

# Run security scan
if [ "$RUN_SECURITY" = true ]; then
    echo ""
    echo "🔒 Running security scan..."
    echo "-------------------------"
    bandit -r src -ll || {
        echo "⚠️  Security issues found (non-critical)"
    }
fi

# Run tests
echo ""
echo "🧪 Running tests..."
echo "-----------------"

if [ "$RUN_COVERAGE" = true ]; then
    if [ -n "$SPECIFIC_TEST" ]; then
        pytest --cov=src --cov-report=term-missing --cov-report=html $PYTEST_ARGS "$SPECIFIC_TEST"
    else
        pytest --cov=src --cov-report=term-missing --cov-report=html $PYTEST_ARGS
    fi
    echo ""
    echo "📊 Coverage report generated in htmlcov/index.html"
else
    if [ -n "$SPECIFIC_TEST" ]; then
        pytest $PYTEST_ARGS "$SPECIFIC_TEST"
    else
        pytest $PYTEST_ARGS
    fi
fi

# Summary
echo ""
echo "✅ Test run completed!"
echo ""
echo "Quick commands:"
echo "  ./run_tests.sh --fast           # Skip slow tests"
echo "  ./run_tests.sh --unit           # Run only unit tests"
echo "  ./run_tests.sh --integration    # Run only integration tests"
echo "  ./run_tests.sh --no-coverage    # Skip coverage report"
echo "  ./run_tests.sh --parallel       # Run tests in parallel"
echo "  ./run_tests.sh test_auth.py     # Run specific test file"