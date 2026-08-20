# Installation

## Requirements

- Python 3.12+
- Git (for development installation)
- UV package manager (recommended for development)

## Installation from PyPI

### Using pip

```bash
pip install bluesky_nexus
```

### Using UV

```bash
uv add bluesky_nexus
```

## Installation from Source

### Using UV

```bash
# Clone the repository
git clone <repository-url>
cd bluesky_nexus

# Create virtual environment and install dependencies
uv sync
```

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd bluesky_nexus

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .
```

## Development Installation

For development work, install with all optional dependencies.

### Using UV

```bash
# Clone and navigate to project
git clone <repository-url>
cd bluesky_nexus

# Install with all development dependencies
uv sync -all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Using pip

```bash
# Clone and navigate to project
git clone <repository-url>
cd bluesky_nexus

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with all development dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install
```

## Optional Dependency Groups

The project includes three optional dependency groups:

- **`dev`**: Development tools (ruff, mypy, bandit, pre-commit)
- **`test`**: Testing tools (pytest, pytest-cov, coverage)
- **`docs`**: Documentation tools (sphinx, sphinx-rtd-theme, myst-parser)
- **`zmq`**: For installing zmq requirements to allow the package to be ran as a zmq callback service.
- **`kafka`**: For installing zmq requirements to allow the package to be ran as a bluesky-kafka callback service.

Install specific groups as needed:

```bash
# With UV
uv sync --extra dev

# With pip
pip install -e ".[dev]"
```

## Setting up Pre-commit Hooks

Pre-commit hooks help maintain code quality by running checks before each commit.

```bash
# Using UV
uv run pre-commit install

# Using system pre-commit
pre-commit install
```

To run checks manually on all files:

```bash
# Using UV
uv run pre-commit run --all-files

# Using system pre-commit
pre-commit run --all-files
```

## Verifying Installation

Verify the installation by checking the version:

```python
import bluesky_nexus

print(bluesky_nexus.__version__)
```

Or run the test suite:

```bash
# Using UV
uv run pytest

# Using system pytest
pytest
```
