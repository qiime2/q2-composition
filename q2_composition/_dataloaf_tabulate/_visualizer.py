# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd
import pkg_resources
import os

import q2templates

from q2_stats import (DataLoafPackageDirFmt, FrictionlessCSVFileFormat)


def tabulate(output_dir: str, dataloaf: DataLoafPackageDirFmt):
    # setup for the index.html page
    ASSETS = pkg_resources.resource_filename('q2_composition',
                                             '_dataloaf_tabulate')
    index = os.path.join(ASSETS, 'assets', 'index.html')

    # restructuring input data
    slices = dataloaf.data_slices.iter_views(FrictionlessCSVFileFormat)

    for slice in slices:
        slice_df = slice[1].view(pd.DataFrame)

    html_table = q2templates.df_to_html(slice_df)

    # Filling in the table that will appear on index.html
    context = {
        'table': html_table
    }

    # Render the results using q2templates
    q2templates.render(index, output_dir, context=context)
