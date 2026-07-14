# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import json
import os

import pandas as pd

from qiime2 import Metadata
from qiime2.sdk import ValidationError
from rachis.plugin.util import transform

from q2_composition.plugin_setup import plugin
from q2_composition._format import (
    ANCOMBC2OutputDirFmt,
    ANCOMBC2SliceMapping,
    FrictionlessCSVFileFormat,
    DataLoafPackageDirFmt,
    DataPackageSchemaFileFormat
)


@plugin.register_transformer
def _1(obj: FrictionlessCSVFileFormat) -> pd.DataFrame:
    path = obj.view(FrictionlessCSVFileFormat)
    df = pd.read_csv(str(path))

    return df


@plugin.register_transformer
def _12(format: DataLoafPackageDirFmt) -> ANCOMBC2SliceMapping:

    slice_md = format.nutrition_facts.view(DataPackageSchemaFileFormat)
    with open(str(slice_md)) as fh:
        intercepts = json.load(fh)['metadata']['intercept_groups']
        if type(intercepts) is str:
            intercepts = [intercepts]

    slices = ANCOMBC2SliceMapping()
    slices.intercepts = intercepts

    name_map = {
        'lfc': 'lfc',
        'se': 'se',
        'p_val': 'p',
        'q_val': 'q',
        'w': 'W',
    }
    for (slice_path, slice_df) in format.data_slices.iter_views(pd.DataFrame):
        slice_name = name_map[slice_path.name.split('_slice')[0]]
        slice_df = slice_df.rename(columns={'id': 'taxon'})
        slices[slice_name] = slice_df

    return slices


@plugin.register_transformer
def _2(slices: ANCOMBC2SliceMapping) -> ANCOMBC2OutputDirFmt:
    '''
    Transforms a dictionary of ANCOMBC2 model statistics into the ANCOMBC2
    output directory format.
    '''
    format = ANCOMBC2OutputDirFmt()
    for slice_name, slice_df in slices.items():
        format_slice = format.__getattribute__(slice_name)
        format_slice.write_data(slice_df, pd.DataFrame)

    extra_files = ['diff', 'passed_ss']
    if not any(file in slices.keys() for file in extra_files):
        header = {
            "doctype": {
                "name": "table.jsonl",
                "format": "application/x-json-lines",
                "version": "1.0"
            },
            "direction": "row",
            "style": "key:value",
            "fields": [
                {"name": "taxon", "type": "string", "missing": False},
                {"name": "(Intercept)", "type": "number", "missing": False}
            ],
            "index": [],
            "title": "",
            "description": "",
            "extra": {}
        }

        for file in extra_files:
            output_path = os.path.join(format.path, file + '.jsonl')
            with open(output_path, 'w') as f:
                f.write(json.dumps(header, separators=(',', ':')) + "\n")

    return format


@plugin.register_transformer
def _3(format: ANCOMBC2OutputDirFmt) -> ANCOMBC2SliceMapping:
    '''
    Transforms an ANCOMBC2 output directory format into a dictionary mapping
    slice names to dataframes containing the contents of that slice. See the
    `ACOMBC2OutputDirFmt` definition for an explanation of the slices. An
    additional entry for the structural zeros, with key `structural_zeros`,
    will be present if structurual zeros are present in the format.
    '''
    slices = ANCOMBC2SliceMapping()
    for slice_name in format.ALL_SLICES:
        format_slice = format.__getattribute__(slice_name)
        try:
            slice_df = format_slice.view(pd.DataFrame)
            slices[slice_name] = slice_df
        except ValidationError:
            # optional structurual_zeros bound file not present on disk
            pass

    intercepts = {}  # dict to preserve order instead of set()
    _first_slice = slices[format.REQUIRED_SLICES[0]]
    for column in _first_slice.columns:
        extra = _first_slice[column].attrs.get('extra', {})
        reference = extra.get('reference')
        variable = extra.get('variable')
        if reference and variable:
            intercepts[f'{variable}::{reference}'] = True

    slices.intercepts = list(intercepts)

    return slices


@plugin.register_transformer
def _5(format: DataLoafPackageDirFmt) -> ANCOMBC2OutputDirFmt:
    slice_format = transform(format, to_type=ANCOMBC2SliceMapping)
    ancombc2_format = transform(slice_format, to_type=ANCOMBC2OutputDirFmt)
    return ancombc2_format


@plugin.register_transformer
def _6(format: ANCOMBC2OutputDirFmt) -> Metadata:
    slices = transform(format, to_type=ANCOMBC2SliceMapping)

    merged = None
    for slice, df in slices.items():
        df = df.set_index(df['taxon'])
        df = df.drop(columns='taxon')
        df.index.name = 'feature-id'
        df.columns = str(slice) + '_' + df.columns
        if merged is None:
            merged = df
            continue
        merged = pd.merge(
            merged, df, left_index=True,  right_index=True, how='outer'
        )

    merged = merged.replace({True: 'True', False: 'False'})

    md = Metadata(merged)

    return md
