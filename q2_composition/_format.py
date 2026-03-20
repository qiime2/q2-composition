# ----------------------------------------------------------------------------
# Copyright (c) 2022-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import pandas as pd

from qiime2.plugin import model
from q2_types.tabular import TableJSONLFileFormat


class FrictionlessCSVFileFormat(model.TextFileFormat):
    """
    Format for frictionless CSV.

    More on this later.
    """
    def _validate_(self, level):
        pass


class DataPackageSchemaFileFormat(model.TextFileFormat):
    """Format for the associated metadata for each file in the DataLoaf.

    More on this later.
    """
    def _validate_(self, level):
        pass


class DataLoafPackageDirFmt(model.DirectoryFormat):
    data_slices = model.FileCollection(r'.+\.csv',
                                       format=FrictionlessCSVFileFormat)
    nutrition_facts = model.File('datapackage.json',
                                 format=DataPackageSchemaFileFormat)

    @data_slices.set_path_maker
    def _data_slices_path_maker(self, slice_name):
        return slice_name + '.csv'


class ANCOMBC2OutputDirFmt(model.DirectoryFormat):
    '''
    Stores the model statistics and optionally the structural zeros table
    output by the ANCOMBC2 method.

    The slices are:
        - lfc: log-fold change
        - se: standard error
        - W: lfc / se (the test statistic)
        - p: p-value
        - q: adjusted p-value
        - diff: differentially abundant boolean (i.e. q < alpha)
        - diff_robust: robust diff abun boolean (q < alpha AND passed_ss)
        - passed_ss: whether sensitivity analysis was passed
    '''
    REQUIRED_SLICES = (
        'lfc', 'se', 'W', 'p', 'q', 'diff', 'passed_ss'
    )
    ALL_SLICES = REQUIRED_SLICES + ('structural_zeros', 'diff_robust')

    # required slices
    lfc = model.File('lfc.jsonl', format=TableJSONLFileFormat)
    se = model.File('se.jsonl', format=TableJSONLFileFormat)
    W = model.File('W.jsonl', format=TableJSONLFileFormat)
    p = model.File('p.jsonl', format=TableJSONLFileFormat)
    q = model.File('q.jsonl', format=TableJSONLFileFormat)
    diff = model.File('diff.jsonl', format=TableJSONLFileFormat)
    passed_ss = model.File('passed_ss.jsonl', format=TableJSONLFileFormat)

    # optional slices
    diff_robust = model.File(
        'diff_robust.jsonl', format=TableJSONLFileFormat, optional=True
    )
    structural_zeros = model.File(
        'structural-zeros.jsonl', format=TableJSONLFileFormat, optional=True
    )

    def _validate_(self, level='min'):
        pass


class ANCOMBC2SliceMapping(dict):
    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError('Keys must be strings.')
        if not isinstance(value, pd.DataFrame):
            raise TypeError('Values must be pandas DataFrames.')

        super().__setitem__(key, value)
