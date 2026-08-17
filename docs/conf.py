"""Sphinx configuration."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project `src` directory to path so autodoc can import the package when building docs
# This works with the `src/` layout used by the project template.
sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "src").resolve()))

# -- Project information -----------------------------------------------------
project = "bluesky-nexus"
author = "Eva Lott"
copyright = f"{datetime.now(tz=UTC).year}, {author}"  # noqa: A001

# The version info from the project
try:
    from bluesky_nexus import __version__

    release = __version__
    version = ".".join(__version__.split(".")[:2])
except ImportError:
    release = "unknown"
    version = "unknown"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
}

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Extension configuration for todo
todo_include_todos = True

# Autosummary (generate API stubs) — useful for `src` layout projects
autosummary_generate = True

# If your docs build in an environment without all optional deps installed,
# you can list them here to avoid import errors during documentation build.
autodoc_mock_imports = []

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
]
