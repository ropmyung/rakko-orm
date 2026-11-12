# Modified for Rakko ORM: configure Rakko branding, ocean colors and documentation metadata.

"""Sphinx configuration for Rakko ORM."""

import sys
from datetime import datetime
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
sys.path[:0] = [str(ROOT), str(DOCS)]
from rakko import __version__

project = "Rakko ORM"
author = "ropmyung"
copyright = f'{datetime.now().year}, ropmyung; upstream credits retained'
version = release = __version__
extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_immaterial",
]
source_suffix = ".rst"
master_doc = root_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]
language = "en"
autodoc_typehints = "none"
autodoc_member_order = "bysource"
napoleon_google_docstring = False
napoleon_numpy_docstring = True
nitpicky = True
pygments_style = "sphinx"
html_theme = "sphinx_immaterial"
html_title = "Rakko ORM — typed, async Python"
html_short_title = "Rakko ORM"
html_logo = html_favicon = "_static/rakko-logo.png"
html_static_path = ["_static"]
html_css_files = ["rakko.css"]
html_show_sourcelink = True
htmlhelp_basename = "rakkodoc"
html_theme_options = {
    "font": False,
    "globaltoc_collapse": False,
    "globaltoc_includehidden": True,
    "toc_title_is_page_title": True,
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "blue",
            "accent": "light-blue",
            "toggle": {"icon": "material/weather-night", "name": "Switch to dark mode"},
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "blue",
            "accent": "light-blue",
            "toggle": {"icon": "material/weather-sunny", "name": "Switch to light mode"},
        },
    ],
    "features": ["navigation.sections", "navigation.top", "search.highlight"],
}
html_meta = {
    "google-site-verification": "NJpL79DXNacVskxcy_hbP-QweGwKg3NsyhZZIiBCqSU"
}
latex_documents = [(root_doc, "rakko.tex", "Rakko ORM", author, "manual")]
man_pages = [(root_doc, "rakko", "Rakko ORM documentation", [author], 1)]
