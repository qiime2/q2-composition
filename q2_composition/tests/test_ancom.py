# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import qiime2
from q2_composition import ancom
import unittest
import pandas.util.testing as pdt
import numpy as np
import pandas as pd
import os
import shutil


class AncomTests(unittest.TestCase):

    def setUp(self):
        self.results = "results"
        os.mkdir(self.results)

    def tearDown(self):
        shutil.rmtree(self.results)

    def test_ancom(self):
        t = pd.DataFrame([[9, 9, 9, 19, 19, 19],
                          [10, 11, 10, 20, 20, 20],
                          [9, 10, 9, 9, 10, 9],
                          [9, 10, 9, 9, 9, 8],
                          [9, 10, 9, 9, 9, 9],
                          [9, 10, 9, 9, 9, 10],
                          [9, 12, 9, 9, 9, 11]],
                         index=['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],
                         columns=['S1', 'S2', 'S3', 'S4', 'S5', 'S6']).T
        c = qiime2.MetadataCategory(
                pd.Series([0, 0, 0, 1, 1, 1],
                          index=['S1', 'S2', 'S3',
                                 'S4', 'S5', 'S6']))
        ancom(self.results, t+1, c)

        res = pd.read_csv(os.path.join(self.results, 'ancom.csv'),
                          index_col=0)
        exp = pd.DataFrame(
            {'W': np.array([5, 5, 2, 2, 2, 2, 2]),
             'Reject null hypothesis': np.array([True, True, False, False,
                                                 False, False, False],
                                                dtype=bool)},
            index=['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],)
        pdt.assert_frame_equal(res, exp)

        index_fp = os.path.join(self.results, 'index.html')
        self.assertTrue(os.path.exists(index_fp))
        self.assertTrue(os.path.getsize(index_fp) > 0)

        csv_fp = os.path.join(self.results, 'percent-abundances.csv')
        self.assertTrue(os.path.exists(csv_fp))
        self.assertTrue(os.path.getsize(csv_fp) > 0)

        with open(index_fp, 'r') as fh:
            html = fh.read()
            self.assertIn('<th>Percentile</th>', html)
            self.assertIn('<th>Group</th>', html)
            self.assertIn('<th>O1</th>', html)

    def test_ancom_3class_anova(self):
        t = pd.DataFrame([[9, 9, 19, 19, 29, 29],
                          [10, 11, 20, 20, 29, 28],
                          [9, 10, 9, 9, 10, 9],
                          [9, 10, 9, 9, 9, 8],
                          [9, 10, 9, 9, 9, 9],
                          [9, 10, 9, 9, 9, 10],
                          [9, 12, 9, 9, 9, 11]],
                         index=['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],
                         columns=['S1', 'S2', 'S3', 'S4', 'S5', 'S6']).T
        c = qiime2.MetadataCategory(
                pd.Series([0, 0, 1, 1, 2, 2],
                          index=['S1', 'S2', 'S3',
                                 'S4', 'S5', 'S6']))
        ancom(self.results, t+1, c)

        res = pd.read_csv(os.path.join(self.results, 'ancom.csv'),
                          index_col=0)
        exp = pd.DataFrame(
            {'W': np.array([5, 5, 3, 3, 2, 2, 2]),
             'Reject null hypothesis': np.array([True, True, False, False,
                                                 False, False, False],
                                                dtype=bool)},
            index=['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],)
        pdt.assert_frame_equal(res, exp)

    def test_ancom_integer_indices(self):
        # The idea behind this test is to use integer indices to confirm
        # that the metadata category mapping is joining on labels, not on
        # indices. If it was joining on the index, the metadata would map in
        # the opposite direction, resulting in no significant results being
        # rendered to the output HTML table.
        t = pd.DataFrame([[9, 9, 9, 19, 19, 19],
                          [10, 11, 10, 20, 20, 20],
                          [9, 10, 9, 9, 10, 9],
                          [9, 10, 9, 9, 9, 8],
                          [9, 10, 9, 9, 9, 9],
                          [9, 10, 9, 9, 9, 10],
                          [9, 12, 9, 9, 9, 11]],
                         index=['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],
                         columns=['1', '2', '3', '4', '5', '6']).T
        c = qiime2.MetadataCategory(pd.Series([1, 0, 0, 0, 1, 0],
                                    index=['6', '5', '4', '3', '2', '1']))
        ancom(self.results, t+1, c)

        index_fp = os.path.join(self.results, 'index.html')
        with open(index_fp, 'r') as fh:
            html = fh.read()
            self.assertIn('<th>O7</th>', html)


if __name__ == "__main__":
    unittest.main()
