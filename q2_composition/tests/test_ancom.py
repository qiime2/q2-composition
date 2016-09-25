import qiime
from q2_composition import add_pseudocount, ancom
import unittest
import pandas.util.testing as pdt
from biom import Table
import numpy as np
import pandas as pd
import os


class AncomTests(unittest.TestCase):

    def setUp(self):
        self.results = "results"

    def tearDown(self):
        os.rmdir(self.results)

    def test_ancom(self):
        t = Table(np.array([[9, 9, 9, 19, 19, 19],
                           [10, 11, 10, 20, 20, 20],
                           [9, 10, 9, 9, 10, 9],
                           [9, 10, 9, 9, 9, 8],
                           [9, 10, 9, 9, 9, 9],
                           [9, 10, 9, 9, 9, 10],
                           [9, 12, 9, 9, 9, 11]]),
                  ['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],
                  ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'])
        c = qiime.MetadataCategory(
                pd.Series([0, 0, 0, 1, 1, 1],
                          index=['S1', 'S2', 'S3',
                                 'S4', 'S5', 'S6']))
        it = add_pseudocount(t)
        ancom(self.results, it, c)

        res = pd.read_table(os.path.join(self.results, 'ancom.csv'),
                            index_col=0)
        exp = pd.DataFrame(
            {'W': np.array([5, 5, 2, 2, 2, 2, 2]),
             'Reject null hypothesis': np.array([True, True, False, False,
                                                 False, False, False],
                                                dtype=bool)},
            index=['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7'],)
        pdt.assert_frame_equal(res, exp)

if __name__ == "__main__":
    unittest.main()
