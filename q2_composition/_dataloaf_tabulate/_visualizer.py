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

from q2_composition._format import (DataLoafPackageDirFmt,
                                    FrictionlessCSVFileFormat)


def tabulate(output_dir: str, data: DataLoafPackageDirFmt):
    # setup for the index.html page
    ASSETS = pkg_resources.resource_filename('q2_composition',
                                             '_dataloaf_tabulate')
    index = os.path.join(ASSETS, 'assets', 'index.html')

    # restructuring input data
    slices = data.data_slices.iter_views(FrictionlessCSVFileFormat)

    slice_names = []
    slice_contents = []

    for slice in slices:
        slice_name = str(slice[0]).split('_slice')[0]
        slice_df = slice[1].view(pd.DataFrame)
        idx = str(slice_df.columns[0])
        slice_df = slice_df.set_index(idx)
        slice_html = q2templates.df_to_html(slice_df)

        slice_names.append(slice_name)
        slice_contents.append(slice_html)

    slice_tables = zip(slice_names, slice_contents)

    # Filling in the table that will appear on index.html
    context = {
        'tables': slice_tables
    }

    # Render the results using q2templates
    q2templates.render(index, output_dir, context=context)
