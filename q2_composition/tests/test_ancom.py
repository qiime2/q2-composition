# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import unittest
import os

import pandas.testing as pdt
import numpy as np
import pandas as pd

import qiime2
from qiime2.plugin.testing import TestPluginBase
from q2_composition import ancom


class AncomTests(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()
        self.example_obs = ['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7']
        self.example_samples = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
        self.otu_table = pd.DataFrame([[9, 9, 9, 19, 19, 19],
                                       [10, 11, 10, 20, 20, 20],
                                       [9, 10, 9, 9, 10, 9],
                                       [9, 10, 9, 9, 9, 8],
                                       [9, 10, 9, 9, 9, 9],
                                       [9, 10, 9, 9, 9, 10],
                                       [9, 12, 9, 9, 9, 11]],
                                      index=self.example_obs,
                                      columns=self.example_samples).T

        self.otu_table_3class = pd.DataFrame([[9, 9, 19, 19, 29, 29],
                                              [10, 11, 20, 20, 29, 28],
                                              [9, 10, 9, 9, 10, 9],
                                              [9, 10, 9, 9, 9, 8],
                                              [9, 10, 9, 9, 9, 9],
                                              [9, 10, 9, 9, 9, 10],
                                              [9, 12, 9, 9, 9, 11]],
                                             index=self.example_obs,
                                             columns=self.example_samples).T

        self.index_fp = os.path.join(self.temp_dir.name, 'index.html')

    def test_ancom(self):
        t = self.otu_table
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['a', 'a', 'a', '1', '1', '1'], name='n',
                      index=pd.Index(self.example_samples, name='id'))
        )
        ancom(output_dir=self.temp_dir.name,
              table=self.otu_table + 1, metadata=c)

        res = pd.read_csv(os.path.join(self.temp_dir.name, 'ancom.tsv'),
                          index_col=0, sep='\t')
        exp = pd.DataFrame(
            {'W': np.array([5, 5, 2, 2, 2, 2, 2]),
             'Reject null hypothesis': np.array([True, True, False, False,
                                                 False, False, False],
                                                dtype=bool)},
            index=self.example_obs,)
        pdt.assert_frame_equal(res, exp)

        self.assertTrue(os.path.exists(self.index_fp))
        self.assertTrue(os.path.getsize(self.index_fp) > 0)

        data_fp = os.path.join(self.temp_dir.name, 'data.tsv')
        self.assertTrue(os.path.exists(data_fp))
        self.assertTrue(os.path.getsize(data_fp) > 0)

        tsv_fp = os.path.join(self.temp_dir.name, 'percent-abundances.tsv')
        self.assertTrue(os.path.exists(tsv_fp))
        self.assertTrue(os.path.getsize(tsv_fp) > 0)

        with open(self.index_fp, 'r') as fh:
            html = fh.read()
            self.assertIn('<th>Percentile</th>', html)
            self.assertIn('<th>Group</th>', html)
            self.assertIn('<th>O1</th>', html)

    def test_ancom_3class_anova(self):
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['0', '0', '1', '1', '2', '2'], name='n',
                      index=pd.Index(self.example_samples, name='id'))
        )
        ancom(output_dir=self.temp_dir.name,
              table=self.otu_table_3class + 1, metadata=c)

        res = pd.read_csv(os.path.join(self.temp_dir.name, 'ancom.tsv'),
                          index_col=0, sep='\t')
        exp = pd.DataFrame(
            {'W': np.array([5, 5, 3, 3, 2, 2, 2]),
             'Reject null hypothesis': np.array([True, True, False, False,
                                                 False, False, False],
                                                dtype=bool)},
            index=self.example_obs)
        pdt.assert_frame_equal(res, exp)

    def test_ancom_integer_indices(self):
        # The idea behind this test is to use integer indices to confirm
        # that the metadata column mapping is joining on labels, not on
        # indices. If it was joining on the index, the metadata would map in
        # the opposite direction, resulting in no significant results being
        # rendered to the output HTML table.
        t = self.otu_table
        t.index = [str(n) for n in range(1, 7)]
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['1', '0', '0', '0', '1', '0'], name='n',
                      index=pd.Index(['6', '5', '4', '3', '2', '1'],
                                     name='id'))
        )
        ancom(output_dir=self.temp_dir.name, table=t + 1, metadata=c)

        with open(self.index_fp, 'r') as fh:
            html = fh.read()
            self.assertIn('<th>O7</th>', html)

    def test_ancom_no_volcano_plot(self):
        short_index = self.example_samples[:4]
        t = pd.DataFrame([[1, 1], [1, 1], [1, 1], [1, 1]],
                         index=short_index, columns=self.example_obs[:2])
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['0', '0', '1', '2'], name='n',
                      index=pd.Index(short_index, name='id'))
        )
        ancom(output_dir=self.temp_dir.name, table=t+1, metadata=c)

        self.assertTrue(os.path.exists(self.index_fp))
        self.assertTrue(os.path.getsize(self.index_fp) > 0)
        with open(self.index_fp) as fh:
            f = fh.read()
            self.assertTrue('Unable to generate volcano plot' in f)

        data_fp = os.path.join(self.temp_dir.name, 'data.tsv')
        self.assertFalse(os.path.exists(data_fp))

    def test_ancom_no_tables(self):
        short_index = self.example_samples[:3]
        t = pd.DataFrame([[2, 1, 2], [2, 2, 2], [2, 2, 2]],
                         index=short_index, columns=self.example_obs[:3])
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['0', '0', '1'], name='n',
                      index=pd.Index(short_index, name='id'))
        )
        ancom(output_dir=self.temp_dir.name, table=t+1, metadata=c)

        self.assertTrue(os.path.exists(self.index_fp))
        self.assertTrue(os.path.getsize(self.index_fp) > 0)
        with open(self.index_fp) as fh:
            f = fh.read()
            self.assertTrue('No significant features found' in f)

    def test_ancom_zero_division(self):
        t = pd.DataFrame([[10, 0], [11, 0], [12, 0], [13, 0],
                          [1000, 10], [1000, 10]],
                         index=self.example_samples,
                         columns=['O1', 'O2'])
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['0', '0', '1', '1', '2', '2'], name='n',
                      index=pd.Index(self.example_samples,
                                     name='id'))
        )

        ancom(output_dir=self.temp_dir.name, table=t+1, metadata=c,
              transform_function='log')

        with open(os.path.join(self.temp_dir.name, 'index.html')) as fh:
            f = fh.read()
            self.assertFalse('Infinity' in f)
            self.assertTrue(
                'non-numeric results:\n    <strong>O2</strong>' in f)

    def test_ancom_filter_nan_values_metadata(self):
        # Testing if test produces an output and info when
        # metadata contains empty values & filter_missing_samples=True
        t = pd.DataFrame(self.otu_table,
                         index=self.example_samples,
                         columns=self.example_obs)
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['0', '0', '1', '1', np.nan, np.nan], name='n',
                      index=pd.Index(self.example_samples,
                                     name='id'))
        )

        ancom(output_dir=self.temp_dir.name, table=t +
              1, metadata=c, filter_missing=True)

        with open(self.index_fp, 'r') as fh:
            html = fh.read()
            self.assertNotIn('<th>S5</th>', html)
            self.assertNotIn('<th>S6</th>', html)

    def test_ancom_error_nan_values_metadata(self):
        # Testing if ANCOM produces raises an error when
        # metadata contains empty values & filter_missing_samples=False
        t = pd.DataFrame(self.otu_table,
                         index=self.example_samples,
                         columns=self.example_obs)
        c = qiime2.CategoricalMetadataColumn(
            pd.Series(['0', '0', '1', '1', np.nan, np.nan], name='n',
                      index=pd.Index(self.example_samples,
                                     name='id')))

        with self.assertRaisesRegex(ValueError, 'S5, S6'):
            ancom(output_dir=self.temp_dir.name, table=t +
                  1, metadata=c, filter_missing=False)


if __name__ == "__main__":
    unittest.main()
