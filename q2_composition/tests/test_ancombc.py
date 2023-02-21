# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd

from qiime2.plugin.testing import TestPluginBase
from qiime2 import Metadata, Artifact

from q2_composition._ancombc import ancombc


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()

        self.md = Metadata.load(self.get_data_path('sample-md-ancombc.tsv'))

        self.missing_md = Metadata.load(self.get_data_path(
            'sample-md-ancombc-missing.tsv'))

        table = Artifact.load(self.get_data_path('table-ancombc.qza'))
        self.table = table.view(pd.DataFrame)


class TestANCOMBC(TestBase):
    def test_examples(self):
        self.execute_examples()

    # error handling for column validation
    def test_missing_formula_column(self):
        with self.assertRaisesRegex(ValueError, 'formula.*parameter was not'
                                    ' found in any of the metadata columns'):
            ancombc(table=self.table, metadata=self.md, formula='foo')

    def test_missing_reference_levels_column(self):
        with self.assertRaisesRegex(ValueError, 'reference_levels.*parameter'
                                    ' was not found in any of the metadata'
                                    ' columns'):
            ancombc(table=self.table, metadata=self.md, formula='bodysite',
                    reference_levels=['foo::tongue'])

    # error handling for missing IDs in metadata
    def test_ids_in_table_not_in_metadata(self):
        with self.assertRaisesRegex(KeyError, 'Not all samples present within'
                                    ' the table were found in the associated'
                                    ' metadata file.*L6S68'):
            ancombc(table=self.table, metadata=self.missing_md,
                    formula='bodysite')

    # confirm level ordering behavior
    def test_reference_levels_behavior_A(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + AZcolumn',
                           reference_levels=['AZcolumn::A'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('AZcolumnA', col)

    def test_reference_levels_behavior_Z(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + AZcolumn',
                           reference_levels=['AZcolumn::Z'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('AZcolumnZ', col)

    def test_reference_level_value_in_md_not_table(self):
        with self.assertRaisesRegex(ValueError, '.*Value not associated with'
                                    ' any IDs in the table: "toe"'):
            ancombc(table=self.table, metadata=self.md, formula='bodysite',
                    reference_levels=['bodysite::toe'])
