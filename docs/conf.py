# -*- coding: utf-8 -*-
"""
Lambada documentation build configuration file
"""
# pylint: disable=invalid-name,wrong-import-position

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import sphinx_rtd_theme  # pylint: disable=import-error

from lambada import __version__

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinxcontrib.napoleon',
]

templates_path = ['_templates']

source_suffix = ['.rst', '.md']

# The master toctree document.
master_doc = 'index'

autoclass_content = 'both'

# General information about the project.
project = u'Lambada'
copyright = u'2016, Superpedestrian, Inc.'  # pylint: disable=redefined-builtin
author = u'Superpedestrian, Inc.'

suppress_warnings = ['image.nonlocal_uri']

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = __version__
# The full version, including alpha/beta/rc tags.
release = __version__

language = None

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
todo_include_todos = False
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# html_logo = None
# html_favicon = None
html_static_path = ['_static']
html_use_smartypants = True


latex_elements = {
}

latex_documents = [
    (master_doc, 'Lambada.tex', u'Lambada Documentation',
     u'Superpedestrian, Inc.', 'manual'),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'lambada', u'Lambada Documentation',
     [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (master_doc, 'Lambada', u'Lambada Documentation',
     author, 'Lambada', 'One line description of project.',
     'Miscellaneous'),
]
