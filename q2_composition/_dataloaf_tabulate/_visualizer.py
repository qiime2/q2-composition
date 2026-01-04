# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import importlib.resources
import os

import q2templates

from q2_composition._format import ANCOMBC2SliceMapping


def tabulate(output_dir: str, data: ANCOMBC2SliceMapping):
    # setup for the index.html page
    ASSETS = importlib.resources.files('q2_composition') / '_dataloaf_tabulate'
    index = os.path.join(ASSETS, 'assets', 'index.html')

    # restructuring input data
    slice_names = []
    slice_contents = []

    for slice_name, slice_df in data.items():
        idx = str(slice_df.columns[0])
        slice_df = slice_df.set_index(idx)
        slice_html = q2templates.df_to_html(slice_df)

        slice_names.append(slice_name)
        slice_contents.append(slice_html)

    slice_tables = zip(slice_names, slice_contents)

    # Filling in the table that will appear on index.html
    if len(data.intercepts) == 1:
        context = {
            'intercept_single': data.intercepts[0],
            'tables': slice_tables
        }
    else:
        context = {
            'intercept_multi': data.intercepts,
            'tables': slice_tables
        }
    # Render the results using q2templates
    q2templates.render(index, output_dir, context=context)
