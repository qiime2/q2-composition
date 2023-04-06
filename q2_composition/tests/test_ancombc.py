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
    def test_missing_formula_col(self):
        with self.assertRaisesRegex(ValueError, "'foo' is not a column in"
                                    " the metadata"):
            ancombc(table=self.table, metadata=self.md, formula='foo')

    def test_missing_ref_levels_col(self):
        with self.assertRaisesRegex(ValueError, "'foo' is not a column in"
                                    " the metadata"):
            ancombc(table=self.table, metadata=self.md, formula='bodysite',
                    reference_levels=['foo::tongue'])

    # error handling for missing IDs in metadata
    def test_ids_in_table_not_in_md(self):
        with self.assertRaisesRegex(KeyError, 'Not all samples present within'
                                    ' the table were found in the associated'
                                    ' metadata file.*L6S68'):
            ancombc(table=self.table, metadata=self.missing_md,
                    formula='bodysite')

    # confirm output columns based on formula inputs and ref levels
    def test_output_cols_single_formula_no_ref_level(self):
        # should see the alphabetical ref level group removed
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite')

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('bodysitegut', col)

    def test_output_cols_single_formula_single_ref_level(self):
        # should see the chosen ref level group removed
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite',
                           reference_levels=['bodysite::tongue'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('bodysitetongue', col)

    def test_output_cols_single_formula_multi_ref_levels(self):
        # should see the chosen ref level groups removed
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite',
                           reference_levels=['bodysite::tongue',
                                             'bodysite::left palm'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('bodysitetongue', col)
                self.assertNotIn('bodysiteleft palm', col)

    def test_output_cols_multi_formula_no_ref_level(self):
        # should see each formula term's alphabetical ref level groups removed
        # TODO: also check that column groups from both formula terms exist
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + animal')

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('bodysitegut', col)
                self.assertNotIn('animalbird', col)

    def test_output_cols_multi_formula_single_ref_level(self):
        # should see the chosen formula term's ref level group removed
        # as well as the alphabetical ref level group for any terms left out
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + animal',
                           reference_levels=['bodysite::tongue'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('bodysitetongue', col)
                self.assertNotIn('animalbird', col)

    def test_output_cols_multi_formula_multi_ref_levels(self):
        # should see the chosen formula terms ref level groups removed
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + animal',
                           reference_levels=['bodysite::tongue',
                                             'animal::dog'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('bodysitetongue', col)
                self.assertNotIn('animaldog', col)

    # confirm ref level behavior
    def test_ref_levels_behavior_A(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + AZcolumn',
                           reference_levels=['AZcolumn::A'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('AZcolumnA', col)

    def test_ref_levels_behavior_Z(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + AZcolumn',
                           reference_levels=['AZcolumn::Z'])

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)
        for _, slice in slices:
            for col in slice.columns:
                self.assertNotIn('AZcolumnZ', col)

    def test_multi_ref_levels(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + month',
                           reference_levels=['bodysite::tongue',
                                             'month::10'])

        exp_col_list = ['id', '(Intercept)', 'bodysitegut',
                        'bodysiteleft palm', 'bodysiteright palm',
                        'month1', 'month2', 'month3', 'month4']

        slices = dataloaf.data_slices.iter_views(pd.DataFrame)

        for _, slice in slices:
            col_list = []
            for col in slice.columns:
                col_list.append(col)
                self.assertIn(col, exp_col_list)

            self.assertNotIn('bodysitetongue', col_list)
            self.assertNotIn('month10', col_list)

    def test_numerical_md_col_ref_level_failure(self):
        with self.assertRaisesRegex(TypeError, 'Non-categorical column'
                                    ' selected:.*day'):
            ancombc(table=self.table, metadata=self.md, formula='bodysite',
                    reference_levels=['day::28'])

    def test_ref_level_col_not_in_formula_failure(self):
        with self.assertRaisesRegex(ValueError, 'column "animal" was not'
                                    ' found within the `formula` terms.'):
            ancombc(table=self.table, metadata=self.md,
                    formula='bodysite + month',
                    reference_levels=['bodysite::tongue', 'animal::dog'])

    def test_ref_level_value_in_md_not_table(self):
        with self.assertRaisesRegex(ValueError, '.*Value not associated with'
                                    ' any IDs in the table: "toe"'):
            ancombc(table=self.table, metadata=self.md, formula='bodysite',
                    reference_levels=['bodysite::toe'])
