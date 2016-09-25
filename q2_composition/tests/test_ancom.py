import qiime
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
        c = qiime.MetadataCategory(
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
        c = qiime.MetadataCategory(
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

if __name__ == "__main__":
    unittest.main()
