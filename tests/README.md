# IOAgent Test Suite

This directory contains the comprehensive test suite for the IOAgent application.

## Test Structure

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_models.py       # Database model unit tests
├── test_auth.py         # Authentication tests
├── test_api.py          # API endpoint tests
├── test_utils.py        # Utility function tests
├── test_config.py       # Configuration tests
└── test_integration.py  # Integration tests
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run specific test class or function
```bash
pytest tests/test_auth.py::TestAuthEndpoints::test_login_success
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### Run tests in parallel (requires pytest-xdist)
```bash
pip install pytest-xdist
pytest -n auto
```

## Test Categories

### Unit Tests
- **test_models.py**: Tests for SQLAlchemy models
- **test_utils.py**: Tests for utility functions
- **test_config.py**: Tests for configuration classes

### API Tests
- **test_auth.py**: Authentication endpoint tests
- **test_api.py**: CRUD operation tests for all resources

### Integration Tests
- **test_integration.py**: End-to-end workflow tests

## Key Fixtures

### Authentication
- `auth_headers`: Headers with valid JWT token for regular user
- `admin_headers`: Headers with valid JWT token for admin user

### Database Models
- `test_user`: A test user instance
- `admin_user`: An admin user instance
- `test_project`: A test project instance
- `test_evidence`: A test evidence instance
- `test_timeline_entry`: A test timeline entry
- `test_causal_factor`: A test causal factor

### Utilities
- `mock_anthropic`: Mock for Anthropic API calls
- `sample_pdf_file`: In-memory PDF file for upload tests
- `sample_docx_file`: In-memory DOCX file for upload tests

## Coverage Requirements

The test suite is configured to require a minimum of 70% code coverage. Coverage reports are generated in:
- Terminal output (with missing lines)
- HTML report in `htmlcov/` directory
- XML report in `coverage.xml`

## Writing New Tests

1. Create test functions starting with `test_`
2. Use appropriate fixtures from `conftest.py`
3. Group related tests in classes starting with `Test`
4. Use descriptive test names that explain what is being tested
5. Add appropriate markers (@pytest.mark.unit, @pytest.mark.integration, etc.)

### Example Test Structure
```python
import pytest

class TestFeatureName:
    """Test suite for feature name."""
    
    def test_happy_path(self, client, auth_headers):
        """Test successful operation."""
        response = client.get('/api/endpoint', headers=auth_headers)
        assert response.status_code == 200
        
    def test_error_handling(self, client, auth_headers):
        """Test error scenarios."""
        response = client.get('/api/invalid', headers=auth_headers)
        assert response.status_code == 404
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines. Key features:
- Fast unit tests run first
- Integration tests can be run separately
- Coverage reports for quality gates
- Configurable timeouts for long-running tests

## Troubleshooting

### Common Issues

1. **Database errors**: Ensure test database is using SQLite in-memory
2. **Import errors**: Check PYTHONPATH includes project root
3. **Fixture errors**: Verify fixture dependencies are correct
4. **Timeout errors**: Increase timeout in pytest.ini or mark test as slow

### Debugging Tests

Run with more verbose output:
```bash
pytest -vv -s tests/test_file.py::test_function
```

Use pytest debugger:
```bash
pytest --pdb tests/test_file.py::test_function
```