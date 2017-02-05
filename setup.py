# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from setuptools import setup, find_packages


setup(
    name="q2-composition",
    version="2017.2.0",
    packages=find_packages(),
    install_requires=['qiime2 == 2017.2.*', 'q2-types == 2017.2.*', 'bokeh',
                      'biom-format >= 2.1.5, < 2.2.0', 'scipy', 'scikit-bio'],
    author="Jamie Morton",
    author_email="jamietmorton@gmail.com",
    description="Compositional statistics plugin for QIIME2.",
    license='BSD-3-Clause',
    url="https://qiime2.org",
    entry_points={
        'qiime2.plugins':
        ['q2-composition=q2_composition.plugin_setup:plugin']
    }
)
