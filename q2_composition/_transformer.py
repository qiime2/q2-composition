# ----------------------------------------------------------------------------
# Copyright (c) 2016-2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import json

import pandas as pd

from qiime2.sdk import ValidationError

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

    for (slice_path, slice_df) in format.data_slices.iter_views(pd.DataFrame):
        slice_name = slice_path.name.split('_slice')[0]
        slices[slice_name] = slice_df

    return slices


@plugin.register_transformer
def _2(slices: ANCOMBC2SliceMapping) -> ANCOMBC2OutputDirFmt:
    '''
    Transforms a dataframe of ANCOMBC2 model statistics into the ANCOMBC2
    output directory format.
    '''
    format = ANCOMBC2OutputDirFmt()
    for slice_name, slice_df in slices.items():
        format_slice = format.__getattribute__(slice_name)
        format_slice.write_data(slice_df, pd.DataFrame)

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
