# Contributing to Nitter Twitter Scraper

Thank you for considering contributing to this project!

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Install Playwright: `playwright install chromium`
6. Copy `.env.example` to `.env` and configure

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and modular

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

## Adding New Features

### Adding a New Scraper

1. Create a new file in `src/scrapers/`
2. Inherit from `BaseScraper`
3. Implement scraping logic
4. Add to `src/scrapers/__init__.py`
5. Create a Celery task in `src/scheduler/tasks.py`
6. Add API endpoint in `src/api/routes/`

### Adding New Data Processing

1. Create a new module in `src/data_processing/`
2. Implement processing logic
3. Add to `src/data_processing/__init__.py`
4. Integrate into scraping pipeline

### Adding API Endpoints

1. Create or update route file in `src/api/routes/`
2. Add request/response models using Pydantic
3. Include router in `src/api/main.py`
4. Test endpoints

## Submitting Changes

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Write or update tests
4. Ensure all tests pass
5. Commit with clear messages
6. Push to your fork
7. Create a pull request

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Provide error messages and logs
- Specify your environment (OS, Python version, etc.)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help create a welcoming community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
