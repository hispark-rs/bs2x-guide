# Configuration file for the Sphinx documentation builder.
# -- BS21 / BS2X 系列 SoC 用户指南

import os
import sys

# -- Project information -----------------------------------------------------
project = 'BS21 / BS2X 系列 SoC 用户指南'
copyright = '2024, HiSilicon'
author = 'HiSilicon'
version = '01'
release = '01'

# -- General configuration ---------------------------------------------------
extensions = [
    'myst_parser',
    'sphinx.ext.ifconfig',
    'sphinx.ext.todo',
    'sphinxcontrib.mermaid',
]

# MyST Parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_image",
    "replacements",
    "smartquotes",
    "substitution",
    "dollarmath",
]

myst_number_code_blocks = ["json"]
myst_heading_anchors = 4
myst_title_to_header = True

# Suppress warnings for unknown mime types
myst_fence_as_directive = ["mermaid", "list-table", "figure", "table", "danger", "warning", "caution", "important", "note", "tip"]

# Source settings
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

root_doc = 'index'

# Templates path
templates_path = ['_templates']

# Exclude patterns
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_language = 'zh_CN'
html_permalinks_icon = '#'

html_theme_options = {
    'repository_url': 'https://github.com/sanchuanhehe/ws63-guide',
    'repository_branch': 'main',
    'path_to_docs': 'source',
    'use_edit_page_button': True,
    'use_issues_button': True,
    'use_repository_button': True,
    'use_download_button': False,
    'home_page_in_toc': True,
    'show_navbar_depth': 1,
    'max_navbar_depth': 3,
    'show_toc_level': 2,
    'toc_title': '本页内容',
}

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'fontpkg': r'''
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}
''',
    'preamble': r'''
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{tabularx}
\usepackage{array}
\usepackage{colortbl}
\usepackage{multirow}
\usepackage{hyperref}

% CJK support via fontspec (xeCJK requires ctexhook which is not available)
\usepackage{xeCJK}
\setCJKmainfont{Droid Sans Fallback}
\setCJKsansfont{Droid Sans Fallback}
\setCJKmonofont{Droid Sans Fallback}

% Custom colors
\definecolor{headerblue}{RGB}{51, 102, 153}
\definecolor{lightgray}{RGB}{240, 240, 240}

% Table header style
\newcommand{\tableheader}{\rowcolor{headerblue}\textcolor{white}}

% Set default figure placement
\makeatletter
\def\fps@figure{htbp}
\makeatother

% Better table support
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.2}
''',
    'sphinxsetup': r'''
hmargin={2cm,2cm},
vmargin={2.5cm,2.5cm},
''',
    'tableofcontents': r'''
\pagenumbering{Roman}
\sphinxtableofcontents
\clearpage
\pagenumbering{arabic}
''',
    'maketitle': r'''
\begin{titlepage}
\centering
\vspace*{5cm}
{\Huge \textbf{BS2X 系列 SoC \\ Wi-Fi、BLE 和 SLE Combo 芯片}}\\[1cm]
{\LARGE \textbf{用户指南}}\\[2cm]
{\Large 文档版本 01}\\[0.5cm]
{\Large 发布日期 2024-04-10}\\[3cm]
\end{titlepage}
''',
}

# Latex documents
latex_documents = [
    (root_doc, 'ws63_user_guide.tex', 'BS21 / BS2X 系列 SoC 用户指南', 'HiSilicon', 'manual'),
]

# -- Options for manual page output ------------------------------------------
man_pages = [
    (root_doc, 'ws63-user-guide', 'BS21 / BS2X 系列 SoC 用户指南', [author], 1),
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (root_doc, 'BS2XUserGuide', 'BS21 / BS2X 系列 SoC 用户指南',
     author, 'BS2XUserGuide', 'BS2X 系列 SoC Wi-Fi、BLE 和 SLE Combo 芯片用户指南',
     'Miscellaneous'),
]

# -- Figure numbering --------------------------------------------------------
numfig = True
numfig_secnum_depth = 3
numfig_format = {
    'figure': '图 %s',
    'table': '表 %s',
    'code-block': '代码 %s',
    'section': '第 %s 节',
}

# -- Smart quotes ------------------------------------------------------------
smartquotes = False

# -- Internationalization ----------------------------------------------------
language = 'zh_CN'
locale_dirs = ['locale/']
gettext_compact = False

# -- MyST specific -----------------------------------------------------------
myst_url_schemes = ("http", "https", "mailto")

# -- Copy Markdown source alongside HTML for AI/crawler access ---------------
def setup(app):
    from pathlib import Path
    import shutil

    def copy_md_sources(app, exception):
        if exception or app.builder.name != 'html':
            return
        outdir = Path(app.outdir)
        srcdir = Path(app.srcdir)
        for md_file in srcdir.rglob('*.md'):
            rel = md_file.relative_to(srcdir)
            dest = outdir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, dest)

    app.connect('build-finished', copy_md_sources)
