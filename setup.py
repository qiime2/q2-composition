# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from setuptools import setup, find_packages

import versioneer


setup(
    name="q2-composition",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    author="Jamie Morton",
    author_email="jamietmorton@gmail.com",
    description="Compositional statistics plugin for QIIME2.",
    scripts=['q2_composition/assets/run_ancombc.R'],
    license='BSD-3-Clause',
    url="https://qiime2.org",
    entry_points={
        'qiime2.plugins':
        ['q2-composition=q2_composition.plugin_setup:plugin']
    },
    package_data={
        'q2_composition': [
            'citations.bib',
            'assets/ancom/index.html',
            'assets/ancom/css/*',
            'assets/ancom/js/*',
            'assets/ancom/licenses/*',
        ],
        'q2_composition.tests': ['data/*'],
        'q2_composition._dataloaf_tabulate': ['assets/*']
    },
    zip_safe=False,
)
