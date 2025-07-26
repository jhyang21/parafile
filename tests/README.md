# Parafile Testing Framework

This directory contains the comprehensive testing framework for Parafile, implementing the senior developer's recommended multi-layered testing approach.

## Testing Architecture

### 1. Unit Tests (`tests/`)
Fast, isolated tests that verify individual functions without external dependencies:

- **`test_ai_processor.py`**: Tests pure logic functions like `parse_naming_pattern()` and mocked AI functions
- **`test_config_manager.py`**: Tests configuration loading, saving, and transformation logic  
- **`test_organizer.py`**: Tests file organization logic with mocked AI calls

Run unit tests:
```bash
python -m pytest tests/ -v
```

### 2. Integration/End-to-End Tests (`src/`)
Comprehensive tests that verify the entire AI-powered workflow:

- **`test_data_generator.py`**: Generates realistic test documents with known expected outcomes
- **`run_and_verify.py`**: Verifies that the application produces exactly the expected results

Run integration tests:
```bash
# Generate test data
python -m src.test_data_generator

# Run verification
python -m src.run_and_verify
```

## Key Testing Features

### Config-Driven Test Data Generation
The test generator uses the enhanced config structure with variable types:
```json
{
  "name": "company_name",
  "description": "The legal name of your company",
  "type": "company"
}
```

This allows for realistic, varied test data generation using the `Faker` library.

### Deterministic Testing
The end-to-end tests work backwards from expected results:

1. Generate realistic values for each variable type
2. Construct the expected filename using the naming pattern
3. Prompt AI to create document text containing those specific values
4. Verify the application produces the exact expected filename

### Comprehensive Verification
The verification script checks:
- ✅ Files moved to correct category folders
- ✅ Files renamed with exact expected names
- ✅ No files left unprocessed
- ✅ No unexpected files created

## CI/CD Pipeline

The GitHub Actions workflow provides multi-stage validation:

### Stage 1: Code Quality & Linting
- Black code formatting
- Import sorting with isort
- flake8 linting
- mypy type checking

### Stage 2: Unit Tests
- Fast isolated tests with mocking
- Test coverage reporting
- Dependency caching for speed

### Stage 3: Integration Tests (AI-Powered)
- Full end-to-end validation
- Real AI API calls (requires `OPENAI_API_KEY` secret)
- Artifact upload for debugging

### Stage 4: Security Scanning
- Vulnerability scanning with Safety
- Security linting with Bandit

### Stage 5: Build Summary
- Aggregated results from all stages
- Clear pass/fail status

## Running Tests Locally

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
# Unit tests only (fast)
python -m pytest tests/ -v

# Integration tests (requires OpenAI API key)
export OPENAI_API_KEY="your-key-here"
python -m src.test_data_generator
python -m src.run_and_verify

# Code quality checks
black --check src/ tests/
flake8 src/ tests/
isort --check-only src/ tests/
```

### Development Workflow
1. Write/modify code
2. Run unit tests for fast feedback
3. Run code quality checks
4. Run integration tests before committing
5. Push to trigger full CI pipeline

## Benefits of This Architecture

### For Development
- **Fast Feedback**: Unit tests run in seconds
- **Isolation**: Test individual components without dependencies
- **Debugging**: Clear failure messages and test artifacts

### For Confidence
- **Deterministic**: Same input always produces same expected output
- **Comprehensive**: Tests categorization, organization, and naming
- **Real-World**: Uses actual AI models in integration tests

### for Maintenance
- **Config-Driven**: Test data generation adapts to config changes
- **Modular**: Each test type serves a specific purpose
- **Documented**: Clear structure and purpose for each component

This testing framework ensures Parafile's AI-powered functionality works reliably across different configurations and edge cases. 