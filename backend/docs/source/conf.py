# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Получаем путь к каталогу, находящемуся на два уровня выше conf.py, затем переходим в backend
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "backend")
    ),
)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "information-store"
copyright = "2025, Andrey Rotanov"
author = "Andrey Rotanov"
release = "-"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    # "numpydoc",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "venv",
    "backend/app/api",
    # "backend/app/consumer",
    # "backend/app/core",
    # "backend/app/crud",
    # "backend/app/db",
    # "backend/app/deps",
    # "backend/app/schemas",
    # "backend/app/utils",
]

language = "ru"

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "inherited-members": False,  # Исключить унаследованные методы
    "show-inheritance": False,
    "exclude-members": "__weakref__, model_construct, model_copy, model_dump, model_dump_json, model_json_schema, model_parametrized_name, model_post_init, model_rebuild, model_validate, model_validate_json, model_validate_strings, copy",
}
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
# autodoc_default_options = {
#     "members": True,
#     "member-order": "bysource",
#     "special-members": "__init__",
#     "undoc-members": True,
#     "exclude-members": "_execute_in_transaction, __weakref__",
# }
# autodoc_mock_imports = [
#     "elasticsearch",
#     "fastapi_pagination",
#     "sqlmodel",
#     "sqlalchemy",
#     "pydantic",
#     # "pydantic_settings"
# ]
