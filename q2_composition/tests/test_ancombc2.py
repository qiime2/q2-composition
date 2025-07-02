# ----------------------------------------------------------------------------
# Copyright (c) 2016-2024, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import biom
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from pathlib import Path
import tempfile
import os
import unittest

import qiime2
from qiime2.metadata import NumericMetadataColumn, CategoricalMetadataColumn
from qiime2.plugin.util import transform

from q2_composition._ancombc2 import (
    r_base, ancombc2, _process_formula, _convert_metadata, _split_into_slices,
    _rename_variables_post, _is_categorical, _parse_variable_and_level,
    _deduce_reference_levels, _process_categorical_variables,
    _process_structural_zeros, ancombc2_visualizer
)
from q2_composition._format import ANCOMBC2SliceMapping


class TestANCOMBC2Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_data_fp = Path(__file__).parent / 'data' / 'ancombc2'

        table_fp = cls.test_data_fp / 'feature-table.biom'
        cls.biom_table = biom.load_table(table_fp)

        metadata_fp = cls.test_data_fp / 'metadata.tsv'
        cls.metadata = qiime2.Metadata.load(metadata_fp)


class TestANCOMBC2(TestANCOMBC2Base):
    def _slices_to_single_df(
        self, slices: ANCOMBC2SliceMapping
    ) -> pd.DataFrame:
        df = pd.DataFrame()
        for slice_name, slice_df in slices.items():
            if slice_name == 'structural_zeros':
                continue

            slice_df = slice_df.rename(
                lambda n: n if n == 'taxon' else f'{slice_name}_{n}',
                axis='columns'
            )

            if df.empty:
                df = slice_df
            else:
                df = pd.merge(df, slice_df, on='taxon', how='inner')

        return df

    def test_wrapped_ancombc2(self):
        '''
        Assert that ancombc2 called through qiime2 results in the same output
        as when it is called in R. The `r-model-statistics.tsv` and
        `r-structural-zeros.tsv` files were obtained by running ANCOMBC2 in R
        using the moving pictures tutorial data.

        Note: the `_rename_variables_post` and `_process_structural_zeros`
        functions are patched so that column names are shared between the R
        output and the wrapper's output. Note also that
        `_process_categorical_variables` does nothing in this case because
        columns have not been renamed and are thus not detected as categorical
        in the metadata. These methods are tested elsewhere.
        '''
        model_stats_fp = self.test_data_fp / 'r-model-statistics.tsv'
        ground_truth_model_stats = pd.read_csv(
            model_stats_fp, sep='\t', dtype={'taxon': 'string'}
        )
        structural_zeros_fp = self.test_data_fp / 'r-structural-zeros.tsv'
        ground_truth_struc_zeros = pd.read_csv(
            structural_zeros_fp, sep='\t', dtype={'taxon': 'string'}
        )

        with unittest.mock.patch(
            'q2_composition._ancombc2._rename_variables_post',
            side_effect=lambda slices, metadata: slices
        ), unittest.mock.patch(
            'q2_composition._ancombc2._process_structural_zeros',
            side_effect=lambda structural_zeros: structural_zeros
        ):
            output_format = ancombc2(
                table=self.biom_table,
                metadata=self.metadata,
                fixed_effects_formula='body-site + year',
                group='body-site',
                structural_zeros=True
            )

        slices = transform(data=output_format, to_type=ANCOMBC2SliceMapping)
        model_stats = self._slices_to_single_df(slices)

        struc_zeros = output_format.structural_zeros.view(pd.DataFrame)

        assert_frame_equal(ground_truth_model_stats, model_stats)
        assert_frame_equal(ground_truth_struc_zeros, struc_zeros)

    def test_group_enforced_if_structural_zeros(self):
        '''
        Detecting structural zeros is only possible if a group variable is
        provided, so ensure that we error if the structural zeros flag is set
        but no group variable is passed.
        '''
        with self.assertRaisesRegex(
            ValueError, 'structural zeros option was enabled but no group'
        ):
            ancombc2(
                table=self.biom_table,
                fixed_effects_formula='body-site',
                metadata=self.metadata,
                structural_zeros=True
            )

    def test_spaces_in_metadata_column(self):
        '''
        Tests that metadata columns that contain spaces are handled properly.
        '''
        output_format = ancombc2(
            table=self.biom_table,
            metadata=self.metadata,
            fixed_effects_formula='Variable with spaces',
        )

        slices = transform(data=output_format, to_type=ANCOMBC2SliceMapping)

        lfc_slice_columns = list(slices['lfc'].columns)
        variable_with_spaces_columns = [
            col for col in lfc_slice_columns if 'Variable with spaces::' in col
        ]

        # three levels, so one reference and other two in the output
        self.assertEqual(len(variable_with_spaces_columns), 2)

    def test_ancombc2_visualizer(self):
        '''
        Tests that the visualizer runs successfully, which is essentially a
        test of whether or not the visualizer got built into the
        q2_composition/_ancombc2_visualizer/dist/ folder successfully.
        '''
        abc2_output = ancombc2(
            table=self.biom_table,
            metadata=self.metadata,
            fixed_effects_formula='body-site + year',
            group='body-site',
            structural_zeros=True
        )

        with tempfile.TemporaryDirectory() as tempdir:
            ancombc2_visualizer(tempdir, abc2_output)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))

    def test_ancombc2_visualizer_non_overlapping_taxonomy(self):
        '''
        Tests that an error is raised when attempting to visualize ancombc2
        data with a taxonomy that contains none of the features present in the
        ancombc2 data.
        '''
        abc2_output = ancombc2(
            table=self.biom_table,
            metadata=self.metadata,
            fixed_effects_formula='body-site + year',
            group='body-site',
            structural_zeros=True
        )

        taxonomy_df = pd.DataFrame({
            'Feature ID': ['feat1', 'feat2'],
            'Taxon': ['taxon1', 'taxon2'],
            'Confidence': [0.9, 0.95]
        })

        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(
                ValueError, 'No features remained in your taxonomy'
            ):
                ancombc2_visualizer(tempdir, abc2_output, taxonomy_df)


class TestFormulaProcessing(TestANCOMBC2Base):
    def test_process_formula(self):
        '''
        Tests that invalid R identifiers in the formula are renamed to valid
        ones, that valid R identifiers are not changed, and that hyphens are
        replaced only if they are in a metadata variable.
        '''
        formula = 'year + month + day'
        processed_formula = _process_formula(formula, self.metadata)
        self.assertEqual(processed_formula, formula)

        formula = 'body-site'
        processed_formula = _process_formula(formula, self.metadata)
        self.assertEqual(processed_formula, 'body.site')

        formula = 'body-site + reported-antibiotic-usage'
        processed_formula = _process_formula(formula, self.metadata)
        self.assertEqual(
            processed_formula, 'body.site + reported.antibiotic.usage'
        )

        formula = 'year - month'
        processed_formula = _process_formula(formula, self.metadata)
        self.assertEqual(processed_formula, formula)

    def test_process_formula_errors(self):
        '''
        Tests various error conditions that should be raised when processing
        a formula. These include the presence of the dependent variable in the
        formula, variables that are not present in the metadata, and empty
        formulas.
        '''
        formula = 'abundance ~ body-site'
        with self.assertRaisesRegex(
            ValueError,
            'dependent variable should not be included in the formula'
        ):
            _process_formula(formula, self.metadata)

        formula = 'body-site + stonks'
        with self.assertRaisesRegex(
            ValueError, '"stonks" variable was not found in your metadata'
        ):
            _process_formula(formula, self.metadata)

        # NOTE: `does-not-exist` is tokenized into `[does, -, not, -, exist]`
        # and the error message will include only one of these identifiers
        # which is less than ideal, but there isn't much we can do about this
        formula = 'year + does-not-exist'
        with self.assertRaisesRegex(
            ValueError,
            r'"(does|not|exist)" variable was not found in your metadata'
        ):
            _process_formula(formula, self.metadata)

        formula = ''
        with self.assertRaisesRegex(
            ValueError, 'A formula was found to be empty'
        ):
            _process_formula(formula, self.metadata)


class TestMetadataConversion(TestANCOMBC2Base):
    def test_variable_releveling(self):
        '''
        Test the categorical variable reference levels are being enforced in
        the R metadata dataframe.
        '''
        reference_levels = ['body-site::tongue']
        releveled_metadata = _convert_metadata(self.metadata, reference_levels)
        levels = r_base.levels(releveled_metadata.rx2('body.site'))
        reference_level = levels[0]
        self.assertEqual(reference_level, 'tongue')

        reference_levels = [
            'body-site::left palm', 'reported-antibiotic-usage::Yes'
        ]
        releveled_metadata = _convert_metadata(self.metadata, reference_levels)

        body_site_levels = r_base.levels(releveled_metadata.rx2('body.site'))
        body_site_reference = body_site_levels[0]
        self.assertEqual(body_site_reference, 'left palm')

        antibiotic_levels = r_base.levels(
            releveled_metadata.rx2('reported.antibiotic.usage')
        )
        antibiotic_reference = antibiotic_levels[0]
        self.assertEqual(antibiotic_reference, 'Yes')

    def test_variable_releveling_errors(self):
        '''
        Test various error conditions that should be raised when converting
        the metadata into an R dataframe. These include reference level
        specifications of variables not found in the metadata, reference level
        specifications of numeric metadata variables, multiple reference level
        specifications for the same column, improperly formed reference
        level specifications, and nonexistent reference levels.
        '''
        reference_levels = ['body-site::tongue', 'fake::reference']
        with self.assertRaisesRegex(
            ValueError, 'The "fake" column.*was not found in the metadata'
        ):
            _convert_metadata(self.metadata, reference_levels)

        reference_levels = ['days-since-experiment-start::0']
        with self.assertRaisesRegex(
            ValueError,
            'Can not specify a reference level for the numeric metadata column'
        ):
            _convert_metadata(self.metadata, reference_levels)

        reference_levels = ['body-site::tongue', 'body-site::gut']
        with self.assertRaisesRegex(
            ValueError,
            'Only specify a reference level.*once'
        ):
            _convert_metadata(self.metadata, reference_levels)

        reference_levels = ['body-site::tongue::gut']
        with self.assertRaisesRegex(
            ValueError, 'More than one reference level were detected'
        ):
            _convert_metadata(self.metadata, reference_levels)

        reference_levels = ['body-site:gut']
        with self.assertRaisesRegex(
            ValueError, 'No reference level was detected'
        ):
            _convert_metadata(self.metadata, reference_levels)

        reference_levels = ['body-site']
        with self.assertRaisesRegex(
            ValueError, 'No reference level was detected'
        ):
            _convert_metadata(self.metadata, reference_levels)

        reference_levels = ['body-site::fake']
        with self.assertRaisesRegex(
            ValueError, 'reference level "fake" was not found'
        ):
            _convert_metadata(self.metadata, reference_levels)

    def test_variable_type_conversion(self):
        '''
        Tests that metadata variable types are properly converted to the
        corresponding types in R.
        '''
        converted_md = _convert_metadata(self.metadata)

        for column_name in self.metadata.columns:
            r_column_name = r_base.make_names(column_name)[0]
            column = self.metadata.get_column(column_name)

            if isinstance(column, CategoricalMetadataColumn):
                self.assertTrue(
                    r_base.is_factor(converted_md.rx2[r_column_name])[0]
                )
            elif isinstance(column, NumericMetadataColumn):
                self.assertTrue(
                    r_base.is_numeric(converted_md.rx2[r_column_name])[0]
                )


class TestANCOMBC2Helpers(TestANCOMBC2Base):
    def test_split_into_slices(self):
        '''
        Tests that a single model statistics table as returned by ANCOMBC2 is
        properly converted to per-statistics slices.
        '''
        # non-overlapping prefixes
        df = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'lfc_variable.1': [0.2, 0.9, 0.1],
            'lfc_variable.2': [-0.4, 0.0, -0.3],
            'se_variable.1': [0.4, 0.02, 0.1],
            'se_variable.2': [0.04, 0.0, 0.3],
        })

        exp = ANCOMBC2SliceMapping(
            lfc=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'variable.1': [0.2, 0.9, 0.1],
                'variable.2': [-0.4, 0.0, -0.3],
            }),
            se=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'variable.1': [0.4, 0.02, 0.1],
                'variable.2': [0.04, 0.0, 0.3],
            })
        )

        obs = _split_into_slices(df)

        assert_frame_equal(exp['lfc'], obs['lfc'])
        assert_frame_equal(exp['se'], obs['se'])

        # overlapping prefixes
        df = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'p_variable.1': [0.2, 0.9, 0.1],
            'p_variable.2': [-0.4, 0.0, -0.3],
            'passed_ss_variable.1': [0.4, 0.02, 0.1],
            'passed_ss_variable.2': [0.04, 0.0, 0.3],
        })

        exp = ANCOMBC2SliceMapping(
            p=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'variable.1': [0.2, 0.9, 0.1],
                'variable.2': [-0.4, 0.0, -0.3],
            }),
            passed_ss=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'variable.1': [0.4, 0.02, 0.1],
                'variable.2': [0.04, 0.0, 0.3],
            })
        )

        obs = _split_into_slices(df)

        assert_frame_equal(exp['p'], obs['p'])
        assert_frame_equal(exp['passed_ss'], obs['passed_ss'])

    def test_rename_variables_post(self):
        '''
        Tests that any metadata variables that were renamed to valid R-style
        identifiers are properly renamed to the original identifers.
        '''
        slices = ANCOMBC2SliceMapping(
            lfc=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body.sitegut.lower': [0.2, 0.9, 0.1],
                'body.sitegut.upper': [-0.4, 0.0, -0.3],
                'year': [0.33, 0.2, 0.8],
            }),
            se=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body.sitegut.lower': [0.4, 0.02, 0.1],
                'body.sitegut.upper': [0.04, 0.0, 0.3],
                'year': [0.33, 0.2, 0.8],
            })
        )

        obs = _rename_variables_post(slices, self.metadata)

        exp = ANCOMBC2SliceMapping(
            lfc=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body-sitegut.lower': [0.2, 0.9, 0.1],
                'body-sitegut.upper': [-0.4, 0.0, -0.3],
                'year': [0.33, 0.2, 0.8],
            }),
            se=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body-sitegut.lower': [0.4, 0.02, 0.1],
                'body-sitegut.upper': [0.04, 0.0, 0.3],
                'year': [0.33, 0.2, 0.8],
            })
        )

        assert_frame_equal(exp['lfc'], obs['lfc'])
        assert_frame_equal(exp['se'], obs['se'])

    def test_is_categorical(self):
        '''
        Tests that it can be determined whether column names return by ANCOBMC2
        in the model statistics refer to categorical variables.
        '''
        self.assertTrue(
            _is_categorical('body-sitegut', self.metadata)
        )
        self.assertTrue(
            _is_categorical('body-site::gut', self.metadata)
        )
        self.assertTrue(
            _is_categorical('body-site::gut::upper', self.metadata)
        )
        self.assertTrue(
            _is_categorical('body-site', self.metadata)
        )

        self.assertFalse(
            _is_categorical('year', self.metadata)
        )

        # robust when one column prefix of another
        prefix_df = pd.DataFrame({
            'sample-id': ['s1', 's2', 's3'],
            'body-site': ['gut', 'palm', 'tongue'],
            'body-site-count': [2, 3, 2],
        }).set_index('sample-id')
        prefix_md = qiime2.Metadata(prefix_df)

        self.assertTrue(
            _is_categorical('body-site', prefix_md)
        )
        self.assertFalse(
            _is_categorical('body-site-count', prefix_md)
        )

    def test_parse_variable_and_level(self):
        '''
        Tests that parsing the variable name and level name from a
        concatenation of the two as returned by ANCOMBC2 (and possibly
        reformated by _reformat_categorical_variables) works as expected.
        '''
        exp = ('body-site', 'level1')
        obs = _parse_variable_and_level('body-sitelevel1', self.metadata)
        self.assertEqual(exp, obs)

        exp = ('body-site', 'level1')
        obs = _parse_variable_and_level('body-site::level1', self.metadata)
        self.assertEqual(exp, obs)

        # robust to '::' present in variable name and level name
        namespace_symbol_df = pd.DataFrame({
            'sample-id': ['s1', 's2', 's3'],
            'body::site': ['gut', 'palm', 'tongue::left'],
        }).set_index('sample-id')
        namespace_symbol_md = qiime2.Metadata(namespace_symbol_df)

        exp = ('body::site', 'gut')
        obs = _parse_variable_and_level('body::sitegut', namespace_symbol_md)
        self.assertEqual(exp, obs)

        exp = ('body::site', 'gut')
        obs = _parse_variable_and_level('body::site::gut', namespace_symbol_md)
        self.assertEqual(exp, obs)

        exp = ('body::site', 'tongue::left')
        obs = _parse_variable_and_level(
            'body::sitetongue::left',  namespace_symbol_md
        )
        self.assertEqual(exp, obs)

        exp = ('body::site', 'tongue::left')
        obs = _parse_variable_and_level(
            'body::site::tongue::left', namespace_symbol_md
        )
        self.assertEqual(exp, obs)

    def test_deduce_reference_levels(self):
        '''
        Tests that reference levels of categorical variables can be detected
        post ANCOMBC2.
        '''
        slice_df = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'body-site::gut': [0.2, 0.9, 0.1],
            'body-site::left palm': [-0.4, 0.0, -0.3],
            'body-site::right palm': [-0.4, 0.0, -0.3],
            'year': [0.33, 0.2, 0.8],
        })

        exp = {
            'body-site': 'tongue'
        }

        obs = _deduce_reference_levels(
            slice_df, self.metadata, self.biom_table
        )

        self.assertEqual(exp, obs)

    def test_deduce_reference_levels_table_is_subset_of_metadata(self):
        '''
        Tests that reference levels of categorical variables can still be
        deduced even when the levels of the variable represented in the table
        are a subset of the levels in the metadata.
        '''
        slice_df = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'body-site::gut': [0.2, 0.9, 0.1],
            'body-site::left palm': [-0.4, 0.0, -0.3],
            'year': [0.33, 0.2, 0.8],
        })

        # the sample ids represent gut, tongue, left palm (no right palm,
        # which is present in the metadata)
        table = biom.Table(
            np.array([[1, 2, 3], [5, 5, 5], [0, 8, 0]]),
            sample_ids=['L1S8', 'L5S104', 'L2S240'],
            observation_ids=['feature1', 'feature2', 'feature3']
        )

        exp = {
            'body-site': 'tongue'
        }

        obs = _deduce_reference_levels(slice_df, self.metadata, table)

        self.assertEqual(exp, obs)

    def test_deduce_reference_levels_missing_data(self):
        '''
        Tests that missing levels for a categorical variable are ignored when
        deducing the reference level chosen by ANCOMBC2.
        '''
        slice_df = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'body-site::gut': [0.2, 0.9, 0.1],
        })

        table = biom.Table(
            np.array([[1, 2, 3], [5, 5, 5], [0, 8, 0]]),
            sample_ids=['S1', 'S2', 'S3'],
            observation_ids=['feature1', 'feature2', 'feature3']
        )

        metadata = pd.DataFrame({
            'sample-id': ['S1', 'S2', 'S3'],
            'body-site': ['gut', np.nan, 'tongue']
        })
        metadata.set_index('sample-id', inplace=True)
        metadata = qiime2.Metadata(metadata)

        exp = {
            'body-site': 'tongue'
        }

        obs = _deduce_reference_levels(slice_df, metadata, table)

        self.assertEqual(exp, obs)

    def test_process_categorical_variables(self):
        '''
        Tests that columns in the model statistics slices that refer to
        categorical variables have been properly renamed and annotated with
        their variable, level, and reference level.
        '''
        slices = ANCOMBC2SliceMapping(
            lfc=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body-sitegut': [0.2, 0.9, 0.1],
                'body-sitetongue': [-0.4, 0.0, -0.3],
                'body-siteright palm': [-0.4, 0.9, -0.1],
                'year': [0.33, 0.2, 0.8],
            }),
            se=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body-sitegut': [0.4, 0.02, 0.1],
                'body-sitetongue': [0.04, 0.0, 0.3],
                'body-siteright palm': [0.4, 0.4, 0.2],
                'year': [0.33, 0.2, 0.8],
            })
        )

        exp = ANCOMBC2SliceMapping(
            lfc=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body-site::gut': [0.2, 0.9, 0.1],
                'body-site::tongue': [-0.4, 0.0, -0.3],
                'body-site::right palm': [-0.4, 0.9, -0.1],
                'year': [0.33, 0.2, 0.8],
            }),
            se=pd.DataFrame({
                'taxon': ['feature1', 'feature2', 'feature3'],
                'body-site::gut': [0.4, 0.02, 0.1],
                'body-site::tongue': [0.04, 0.0, 0.3],
                'body-site::right palm': [0.4, 0.4, 0.2],
                'year': [0.33, 0.2, 0.8],
            })
        )
        for slice in ('lfc', 'se'):
            for level in ('gut', 'tongue', 'right palm'):
                column = f'body-site::{level}'
                exp[slice][column].attrs['variable'] = 'body-site'
                exp[slice][column].attrs['level'] = level
                exp[slice][column].attrs['reference'] = 'left palm'

        obs = _process_categorical_variables(
            slices, self.metadata, self.biom_table
        )

        # tests variable, level separation
        assert_frame_equal(exp['lfc'], obs['lfc'])
        assert_frame_equal(exp['se'], obs['se'])

        # tests reference annotation
        for slice in exp:
            for column in exp[slice].columns:
                self.assertEqual(
                    exp[slice][column].attrs, obs[slice][column].attrs
                )

    def test_process_structural_zeros(self):
        '''
        Tests that the structural zeros table returned by ANCOMBC2 has its
        column names properly reformatted.
        '''
        structural_zeros = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'structural_zero (body.site = gut)': ['TRUE', 'FALSE', 'FALSE'],
            'structural_zero (body.site = right palm)': [
                'TRUE', 'TRUE', 'TRUE'
            ],
            'structural_zero (reported.antibiotic.usage = Yes)': [
                'FALSE', 'TRUE', 'TRUE'
            ],
        })

        exp = pd.DataFrame({
            'taxon': ['feature1', 'feature2', 'feature3'],
            'body.sitegut': ['TRUE', 'FALSE', 'FALSE'],
            'body.siteright palm': ['TRUE', 'TRUE', 'TRUE'],
            'reported.antibiotic.usageYes': ['FALSE', 'TRUE', 'TRUE'],
        })

        obs = _process_structural_zeros(structural_zeros)

        assert_frame_equal(exp, obs)
