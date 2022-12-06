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
import qiime2

# from q2_stats import DataLoafPackageDirFmt, FrictionlessCSVFileFormat


def hello_world(output_dir: str, input_var: qiime2.Metadata):

    ASSETS = pkg_resources.resource_filename('q2_composition', '_dummy_viz')
    index = os.path.join(ASSETS, 'assets', 'index.html')

    input_df = input_var.to_dataframe()
    html_table = q2templates.df_to_html(input_df)
    print(html_table)

    context = {
        'dataframe': html_table
    }

    q2templates.render(index, output_dir, context=context)
