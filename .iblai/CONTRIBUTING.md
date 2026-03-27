# Contributing to ibl.ai CLI

Thank you for your interest in contributing to the ibl.ai CLI!

## Development Setup

1. **Install the package in development mode:**

```bash
cd packages/iblai-cli
pip install -e ".[dev]"
```

2. **Run tests:**

```bash
pytest
```

3. **Run tests with coverage:**

```bash
pytest --cov=iblai --cov-report=html
```

4. **Format code:**

```bash
black iblai tests
```

5. **Type checking:**

```bash
mypy iblai
```

## Project Structure

```
iblai-cli/
├── iblai/               # Source code
│   ├── cli.py               # Main CLI entry point
│   ├── commands/            # CLI commands
│   │   └── startapp.py      # startapp command
│   ├── generators/          # App generators
│   │   ├── base.py          # Base generator class
│   │   └── agent.py         # Agent app generator
│   └── templates/           # Jinja2 templates
│       └── agent/           # Agent app templates
├── tests/                   # Unit tests
│   ├── test_cli.py          # CLI tests
│   └── test_generators.py  # Generator tests
├── pyproject.toml           # Package configuration
└── README.md                # Documentation
```

## Adding a New Template

To add a new app template (e.g., `dashboard`):

1. **Create a generator class** in `iblai/generators/dashboard.py`:

```python
from iblai.generators.base import BaseGenerator

class DashboardAppGenerator(BaseGenerator):
    def generate(self) -> None:
        # Implement generation logic
        self._generate_package_json()
        # ... more generation methods
```

2. **Create template files** in `iblai/templates/dashboard/`:

```
templates/dashboard/
├── package.json.j2
├── app/
│   └── layout.tsx.j2
└── components/
    └── dashboard.tsx.j2
```

3. **Update the startapp command** in `iblai/commands/startapp.py`:

```python
@click.argument("template", type=click.Choice(["agent", "dashboard"], case_sensitive=False))
```

4. **Add generator logic**:

```python
if template.lower() == "dashboard":
    generator = DashboardAppGenerator(...)
    generator.generate()
```

5. **Write tests** in `tests/test_generators.py`:

```python
class TestDashboardAppGenerator:
    def test_generate_creates_dashboard_component(self, temp_dir):
        # ... test implementation
```

## Template Development

### Jinja2 Template Syntax

Templates use Jinja2 with the following context variables:

- `app_name`: Name of the generated app
- `platform_key`: Platform/tenant identifier
- `mentor_id`: Optional mentor/agent ID
- `has_mentor_id`: Boolean indicating if mentor_id is provided

**Example template:**

```jinja2
{
  "name": "{{ app_name }}",
  {% if has_mentor_id %}
  "mentor": "{{ mentor_id }}",
  {% endif %}
}
```

### Best Practices

1. **Keep templates minimal** - Only include essential code
2. **Use comments** - Explain complex template logic
3. **Reference packages** - Re-export from @iblai packages where possible
4. **Document components** - Add JSDoc comments to generated code
5. **Test thoroughly** - Write tests for all generation scenarios

## Testing

### Writing Tests

Use pytest fixtures for test setup:

```python
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path / "test-app"

def test_generator_creates_files(temp_dir):
    generator = AgentAppGenerator(
        app_name="test",
        platform_key="test",
        output_dir=str(temp_dir)
    )
    generator.generate()

    assert (temp_dir / "package.json").exists()
```

### Running Specific Tests

```bash
# Run specific test file
pytest tests/test_generators.py

# Run specific test class
pytest tests/test_generators.py::TestAgentAppGenerator

# Run specific test
pytest tests/test_generators.py::TestAgentAppGenerator::test_generate_creates_files
```

## Code Style

- Follow PEP 8 style guide
- Use type hints for function signatures
- Use docstrings for classes and functions
- Format code with Black (line length: 100)

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes with conventional commits
6. Push to your fork
7. Open a pull request

## Conventional Commits

Use conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Build/tooling changes

**Examples:**

```
feat(templates): add dashboard template
fix(generator): handle missing mentor_id correctly
docs(readme): update installation instructions
test(cli): add test for startapp command
```

## Questions?

If you have questions, please open an issue on GitHub or reach out to support@ibl.ai.
