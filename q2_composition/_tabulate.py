# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------


import os
import pkg_resources
import shutil

import pandas as pd

import qiime2
import q2templates


TEMPLATES = pkg_resources.resource_filename('q2_composition', 'templates')


def tabulate(output_dir: str, input: qiime2.Metadata,
             page_size: int = 100) -> None:
    if page_size < 1:
        raise ValueError('Cannot render less than one record per page.')

    df = input.to_dataframe()
    df_columns = pd.MultiIndex.from_tuples(
        [(n, t.type) for n, t in input.columns.items()],
        names=['column header', 'type'])
    df.columns = df_columns
    df.reset_index(inplace=True)
    table = df.to_json(orient='split')
    index = os.path.join(TEMPLATES, 'tabulate', 'index.html')
    q2templates.render(index, output_dir,
                       context={'table': table, 'page_size': page_size})

    input.save(os.path.join(output_dir, 'metadata.tsv'))

    js = os.path.join(TEMPLATES, 'tabulate', 'datatables.min.js')
    os.mkdir(os.path.join(output_dir, 'js'))
    shutil.copy(js, os.path.join(output_dir, 'js', 'datatables.min.js'))

    css = os.path.join(TEMPLATES, 'tabulate', 'datatables.min.css')
    os.mkdir(os.path.join(output_dir, 'css'))
    shutil.copy(css, os.path.join(output_dir, 'css', 'datatables.min.css'))
