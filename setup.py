# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from setuptools import setup, find_packages
import re
import ast

# version parsing from __init__ pulled from Flask's setup.py
# https://github.com/mitsuhiko/flask/blob/master/setup.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('q2_composition/__init__.py', 'rb') as f:
    hit = _version_re.search(f.read().decode('utf-8')).group(1)
    version = str(ast.literal_eval(hit))

setup(
    name="q2-composition",
    version=version,
    packages=find_packages(),
    install_requires=['qiime >= 2.0.5', 'q2-types >= 0.0.5', 'bokeh',
                      'biom-format >= 2.1.5, < 2.2.0', 'scipy',
                      'scikit-bio'],
    package_data={'q2_composition': ['workflows/*md']},
    author="Jamie Morton",
    author_email="jamietmorton@gmail.com",
    description="Compositional statistics plugin for QIIME2.",
    license='BSD-3-Clause',
    url="http://www.qiime.org",
    entry_points={
        'qiime.plugins':
        ['q2-composition=q2_composition.plugin_setup:plugin']
    }
)
