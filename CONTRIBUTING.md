# Contributing to Clinical FHIR Extractor

Thank you for your interest in contributing to this project!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clinical-fhir-extractor
   ```

2. **Set up development environment**
   ```bash
   # Using uv (recommended)
   uv sync --extra dev
   
   # Or using pip
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Run tests**
   ```bash
   uv run pytest
   # or
   pytest
   ```

## Code Style

This project follows PEP 8 style guidelines:

```bash
# Format code
black .
isort .

# Check code quality
flake8 app/ tests/
mypy app/
```

## Running the Application

```bash
# Development mode with auto-reload
uv run python main.py

# Or with uvicorn directly
uv run uvicorn app.main:app --reload
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_root_endpoint
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names
- Include docstrings explaining what each test validates
- Mock external API calls when appropriate

Example:

```python
def test_extract_fhir_endpoint():
    """Test that the extract-fhir endpoint processes files correctly"""
    # Test implementation
    pass
```

## Adding Features

### Adding New FHIR Resources

1. Update `app/prompts/fhir_prompt.txt` with the new resource structure
2. Modify the prompt instructions to extract the new resource
3. Update validation in `app/extractor.py` if needed
4. Add tests for the new resource type

### Improving Extraction Quality

1. Refine the prompt template in `app/prompts/fhir_prompt.txt`
2. Adjust chunk sizes in `app/extractor.py`
3. Experiment with different retrieval parameters
4. Consider using different OpenAI models

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Add or update tests as needed
4. Ensure all tests pass
5. Update documentation (README.md, docstrings)
6. Submit a pull request with a clear description

## Project Structure

```
clinical-fhir-extractor/
├── app/
│   ├── __init__.py        # Package initialization
│   ├── main.py            # FastAPI routes
│   ├── extractor.py       # Core extraction logic
│   └── prompts/
│       └── fhir_prompt.txt # LLM prompt template
├── tests/
│   ├── __init__.py
│   ├── test_api.py        # API tests
│   └── conftest.py        # Pytest fixtures
├── main.py                # Entry point
├── pyproject.toml         # Dependencies
└── README.md              # Documentation
```

## Areas for Contribution

- **Prompt Engineering**: Improve FHIR extraction accuracy
- **Error Handling**: Better error messages and recovery
- **Performance**: Optimize document processing speed
- **Testing**: Increase test coverage
- **Documentation**: Improve examples and guides
- **Security**: Add authentication and validation
- **FHIR Compliance**: Enhance FHIR resource validation

## Questions?

Feel free to open an issue for discussion before starting significant work.

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the project
- Show empathy towards others

Thank you for contributing! 🙏

