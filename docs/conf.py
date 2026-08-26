# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from __future__ import annotations

import sys
from pathlib import Path

# -- Path setup ---------------------------------------------------------------
# Make the "src" layout package importable so autodoc/autosummary can find it
# without requiring the project to be installed first.
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from pyiconeus.__about__ import __version__  # noqa: E402

# -- Project information -------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PyIconeus"
copyright = "2026, Iconeus"
author = "Iconeus"
version = __version__
release = __version__

# -- General configuration ------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Pull docstrings from the pyiconeus source code
    "sphinx.ext.autosummary",  # Auto-generate one reference page per module/class
    "sphinx.ext.viewcode",  # Add links to the highlighted source code
    "sphinx.ext.intersphinx",  # Link out to numpy/h5py/python documentation
    "sphinx_book_theme",
]


autosummary_generate = True
autosummary_imported_members = False

autosummary_ignore_module_all = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "h5py": ("https://docs.h5py.org/en/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"

# -- Options for HTML output ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
