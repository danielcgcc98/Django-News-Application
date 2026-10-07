"""Sphinx configuration for the Django News Application documentation."""

import os
import sys

import django

# -- Django setup ------------------------------------------------------------
# Make the project importable and load Django so autodoc can import models.
sys.path.insert(0, os.path.abspath(".."))
os.environ["DJANGO_SETTINGS_MODULE"] = "news_project.settings"
django.setup()

# -- Project information -----------------------------------------------------
project = "Django News Application"
author = "danielgc98"
release = "1.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"
html_static_path = []
