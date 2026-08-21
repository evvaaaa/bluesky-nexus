# Contributing Guidelines

## Overview

This project uses modern Python development tools to ensure consistency, reproducibility, and code quality across the project:

- **uv**: A fast, reliable package manager that handles Python versions, virtual environments, and dependencies.
- **pre-commit**: Automated code checks that run before each commit to catch issues early.
- **Ruff**: A linter and code formatter for consistent style.
- **MyPy**: Static type checking to catch type-related bugs before runtime.
- **pytest**: Testing framework with coverage reporting.
- **Sphinx**: Documentation generation from docstrings and Markdown files.

## Requirements

Before starting, install the essential tools:

```bash
# Install uv (the package manager for this project)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pipx (needed to run Python CLI tools in isolation)
sudo apt install pipx

# Install copier (used to bootstrap new projects from the template)
pipx install copier
```

## For Project Owners (Initializing a New Project)

If you are creating a new project, follow these steps to set it up correctly.

### 1. Create Project Structure

The copier tool generates a complete project structure with sensible defaults. Choose one of the following approaches:

**Option A: From remote template**
```bash
copier copy --trust https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bessyii_python_template.git my-new-project
```

**Option B: From a specific branch or tag**
```bash
copier copy --trust --vcs-ref <branch-or-tag> https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bessyii_python_template.git my-new-project
```

**Option C: From a local template**
```bash
copier copy --trust bessyii_python_template my-new-project
```

The `--trust` flag skips confirmation prompts. Copier will ask you for project details (name, author, etc.) and generate the folder `my-new-project` with all necessary files.

Tip: Use Ctrl+Shift+V to paste in most terminals.

### 2. Initialize the Project Environment

After generation, the project needs a Python environment with all dependencies installed.

Open `pyproject.toml` and review the dependencies. The template provides sensible defaults, but you should add any project-specific packages you need. For example, if your project uses NumPy and Pandas, add them now or later using the commands in section 3.

Create the environment and install development tools:

```bash
uv sync --extra dev
```

This command:
- Downloads and installs the exact Python version specified in the project
- Creates a virtual environment in `.venv`
- Installs all core dependencies and optional dev tools (linters, type checkers, test frameworks)
- Generates `uv.lock` — a detailed lockfile with every resolved dependency

**What is `uv.lock`?**
The lockfile ensures that everyone working on the project uses the exact same package versions. This eliminates "works on my machine" issues. Always commit `uv.lock` to version control.

To install all optional dependency groups (not just dev), use `--all-extras`.

### 3. Add and Manage Dependencies

As development progresses, you may need additional packages. Use uv to add them:

**Add a package with version constraint:**
```bash
uv add "numpy>=1.26"
```
This pins NumPy to version 1.26.0 or higher but below 2.0.0.

**Add a package without specifying a version:**
```bash
uv add numpy
```
uv queries PyPI and installs the latest compatible release.

**Add to an optional dependency group (e.g., dev or docs):**
```bash
uv add --optional dev "pytest-cov>=4.0"
```
This adds pytest-cov to the dev group, useful for development-only tools.

**Remove a dependency:**
```bash
uv remove numpy
uv remove --optional dev pytest-cov
```

After any add/remove operation, uv automatically syncs your environment and updates both `pyproject.toml` and `uv.lock`.

### 4. Install Pre-commit Hooks

Pre-commit hooks are scripts that run automatically before each commit. They catch common issues (formatting, type errors, security problems) before code is committed.

Install the hooks into the local `.git` directory:

```bash
uv run pre-commit install
```

Once installed, every `git commit` will run the checks defined in `.pre-commit-config.yaml`. If any check fails, the commit is blocked and you must fix the issues first.

### 5. Push to Remote Repository

Commit all changes and push to your remote repository:

```bash
git add .
git commit -m "Initial project setup"
git push origin main
```

Always ensure `uv.lock` is committed alongside `pyproject.toml`. This is critical for reproducible environments.

## For Project Contributors (Joining an Existing Project)

If you are joining a project that already uses this template, follow these steps to set up your local environment.

### 1. Clone or Update the Repository

**Clone for the first time:**
```bash
git clone https://{url}/my_project.git
cd my_project
```

**Update an existing clone:**
```bash
git pull
```

### 2. Sync Your Environment

After cloning, sync your environment to match the project's exact specifications:

```bash
uv sync
```

This command:
- Downloads the Python version specified in the project (if not already present)
- Creates a virtual environment in `.venv`
- Installs all dependencies from `uv.lock` with exact pinned versions

Because versions are locked, you get an identical environment instantly, whether you are on Linux, macOS, or Windows (assuming compatible systems).

**Why not just pip?**
pip with a `requirements.txt` does not resolve transitive dependencies reliably. uv and `uv.lock` guarantee reproducibility across the entire dependency tree.

## Additional Operations

### Update Dependencies

Over time, you may need to update packages for bug fixes, security patches, or feature access.

**To update all packages within the constraints in `pyproject.toml`:**
```bash
uv lock --upgrade
uv sync
```

This resolves all dependencies to the newest versions allowed by your version constraints (e.g., `numpy>=1.26` will upgrade to 2.x if available). It may introduce breaking changes, so test thoroughly.

**To update a single package (safer):**
```bash
uv lock --upgrade-package numpy
uv sync
```

This updates only the specified package and its direct dependencies, minimizing risk. Use this when you need a specific bug fix or security patch without a full upgrade.

**Important notes:**
- `uv sync` alone does not upgrade packages; it restores the environment to match `uv.lock`.
- Always run tests after upgrading dependencies.
- Commit the updated `uv.lock` so other developers get the changes.

**Best practice:**
Perform full upgrades (`uv lock --upgrade`) periodically (e.g., monthly or at the start of a development cycle), not for every commit. Use targeted upgrades for urgent fixes.

### Run the Application

To execute your package as a module:

```bash
uv run python -m {package_name}
```

Or run the entry point directly:

```bash
uv run src/{package_name}/__main__.py
```

The `uv run` command automatically uses the project's managed virtual environment — you do not need to manually activate it.

## Quality Assurance

Maintaining code quality is essential. This project includes several tools to check and enforce standards.

### Running QA Tools

All QA tools are installed when you run `uv sync --extra dev`. Run them with uv:

**Linting and formatting:**
```bash
# Check for style issues and errors
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check --fix

# Format code to project style
uv run ruff format .
```

Always run `ruff check` first to review issues before auto-fixing. This helps you understand what changed.

**Static type checking:**
```bash
uv run mypy src
```

MyPy analyzes type hints (e.g., `def greet(name: str) -> str:`) and catches type mismatches before runtime. Type hints make code more readable and maintainable.

**Security scanning:**
```bash
uv run bandit -r src -c pyproject.toml
```

Bandit identifies common security vulnerabilities like hardcoded credentials or unsafe functions.

**Testing:**
```bash
uv run pytest
```

Run all tests. See the next section for coverage reports.

**Pre-commit checks:**
```bash
uv run pre-commit run --all-files
```

Runs all checks defined in `.pre-commit-config.yaml` (useful before opening a merge request).

### Test and Coverage Report

Testing is crucial for catching bugs early. Generate a coverage report to see which parts of your code are tested:

```bash
uv run pytest --cov={package_name} --cov-report=term --cov-report=html:htmlcov
```

This command:
- Runs all test files
- Measures code coverage (percentage of code executed by tests)
- Prints a summary to the terminal
- Generates an HTML report in `htmlcov/index.html`

Open the HTML report in your browser to explore which lines and branches are untested. Aim for high coverage (typically 80%+) but prioritize testing critical paths.

### Documentation

This project uses Sphinx to generate documentation from docstrings and Markdown files.

**Build the documentation:**
```bash
uv run sphinx-build -b html docs docs/_build/html
```

**Preview the documentation locally:**
```bash
uv run python -m http.server --directory docs/_build/html/ 8000
```

Visit `http://localhost:8000` in your browser. (Note: some JavaScript features require serving over HTTP, not opening files directly.)

**Docstring styles:**
The project is configured with the napoleon extension, supporting Google-style (recommended) or NumPy-style docstrings.

Google style (recommended):
```python
def calculate_speed(distance: float, time: float) -> float:
    """
    Calculate the speed based on distance and time.

    Args:
        distance: The distance traveled in meters.
        time: The time taken in seconds.

    Returns:
        The calculated speed in meters per second.

    Raises:
        ValueError: If time is zero or negative.
    """
    if time <= 0:
        raise ValueError("Time must be positive")
    return distance / time
```

NumPy style:
```python
def calculate_speed(distance: float, time: float) -> float:
    """
    Calculate the speed based on distance and time.

    Parameters
    ----------
    distance : float
        The distance traveled in meters.
    time : float
        The time taken in seconds.

    Returns
    -------
    float
        The calculated speed in meters per second.

    Raises
    ------
    ValueError
        If time is zero or negative.
    """
    if time <= 0:
        raise ValueError("Time must be positive")
    return distance / time
```

### Pre-commit Hooks

Pre-commit hooks automate QA checks and prevent common mistakes. This project includes hooks for:
- Ruff linting and formatting
- MyPy type checking
- Trailing whitespace removal
- YAML validation
- Other standard checks

The hooks are defined in `.pre-commit-config.yaml` and run automatically before each commit. If any hook fails, the commit is aborted. Fix the issues and commit again.

To test hooks without committing:
```bash
uv run pre-commit run --all-files
```

### Changelog Management

This project provides a template for maintaining a changelog in `CHANGELOG.md` using the "Keep a Changelog" format.

When preparing a new release, update `CHANGELOG.md` with:
- New features
- Bug fixes
- Breaking changes
- Other relevant changes

## Editor Integration

### VSCode

This project includes a `.vscode` folder with workspace configuration:

- **`extensions.json`**: Recommended extensions (ESLint, Prettier, Python, Pylance, etc.). VSCode will suggest these under Extensions > Recommended.
- **`settings.json`**: Workspace-specific settings that align with the project's standards.
- **`launch.json`**: Debug configurations:
  - Current File: Debug the active file
  - Main module: Debug the package entry point
  - PyTest: Debug tests with pytest
- **`tasks.json`**: Shortcuts for common commands (lint, test, pre-commit, docs). Access via Terminal > Run Task.

These configurations ensure consistency across your team.

## GitLab Integration

### CI/CD Pipeline

This project includes a CI/CD pipeline (`.gitlab-ci.yml`) that runs on every commit to the default branch:

1. **Ruff check**: Lint and format validation
2. **Tests and coverage**: Run pytest and generate a coverage report (visible in the pipeline UI and available as an artifact)
3. **Package build**: Build the project with uv
4. **Documentation build**: Compile Sphinx docs and publish to GitLab Pages

For version tags, the pipeline additionally publishes the package to the repository's package registry, making it available for installation by other projects.

### Documentation

GitLab automatically recognizes `README.md` and `CONTRIBUTING.md` in the repository root. Keep them up to date.

If the project uses Sphinx, the built documentation is published as GitLab Pages and linked from the repository homepage.

## Troubleshooting & Best Practices

### Common issues

**uv command not found:**
- Ensure uv is in your PATH.

**Pre-commit hooks not running:**
- Ensure you ran `uv run pre-commit install` in the project directory
- Check that `.pre-commit-config.yaml` exists and is valid

**MyPy or Ruff report "module not found":**
- Run `uv sync` to ensure all dependencies are installed
- Check that the module is listed in `pyproject.toml`

**Tests fail after updating dependencies:**
- This may indicate a breaking change in a dependency
- Review the changelog of the updated package
- Consider reverting to the previous version or updating code to match the new API

### Best practices

- **Commit both files together**: Always push `pyproject.toml` and `uv.lock` as a pair. Never commit one without the other.
- **Test locally first**: Run linters, type checkers, and tests before opening a merge request.
- **Use targeted upgrades**: Prefer `uv lock --upgrade-package` for bug fixes and security patches. Use full `--upgrade` only periodically.
- **Document your changes**: Keep docstrings updated with your code changes. Run Sphinx builds locally to check rendering.
- **Review pre-commit output**: If hooks modify files (e.g., ruff format), review the changes before committing.
- **Keep lock files committed**: The lockfile is what makes environments reproducible. Never `.gitignore` it.
