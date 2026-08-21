# bluesky-nexus

Welcome to the documentation for **bluesky-nexus**!

```{include} ../README.md
:start-after: <!--- docs index include start -->
:end-before: <!--- docs index include end -->
```

## Features

- **Modern Python**: Built with Python 3.12+
- **Type Safe**: Full type hints with MyPy validation
- **Code Quality**: Ruff for fast linting and formatting
- **Security**: Bandit security scanning
- **Testing**: Comprehensive test suite with pytest
- **Fast Development**: UV package manager for rapid dependency installation
- **Professional Build System**: Hatch with VCS versioning

## Technology Stack

This project leverages modern Python tooling:

- **[UV](https://github.com/astral-sh/uv)**: Fast Python package installer and resolver
- **[Hatch](https://hatch.pypa.io/)**: Modern Python build system with VCS versioning
- **[Ruff](https://github.com/astral-sh/ruff)**: Extremely fast Python linter and formatter (replaces flake8, isort, black, pyupgrade)
- **[MyPy](https://mypy-lang.org/)**: Static type checker for Python
- **[Bandit](https://github.com/PyCQA/bandit)**: Security issue scanner
- **[Pytest](https://pytest.org/)**: Full-featured testing framework
- **[Sphinx](https://www.sphinx-doc.org/)**: Documentation generator with MyST markdown support

## Contents

```{toctree}
:caption: Installation
:maxdepth: 1

installation
```

```{toctree}
:caption: Nexus Structure 

nexus_structure
using_the_nexus_structure
```


```{toctree}
:caption: Device Nexus Structure

device_nexus_structure/index
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/modules
```

```{toctree}
:maxdepth: 2
:caption: Contributing

CONTRIBUTING
```

```{toctree}
:maxdepth: 2
:caption: Changelog

CHANGELOG
```
