# ----------------------------------------------------------------------------
# Copyright (c) 2016-2021, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import unittest
import numpy as np
from q2_composition import add_pseudocount
from biom import Table


class TestAdd_Pseudocount(unittest.TestCase):

    def test_add_pseudocount(self):
        t = Table(np.array([[0, 1, 3], [1, 1, 2]]),
                  ['O1', 'O2'],
                  ['S1', 'S2', 'S3'])
        obs = add_pseudocount(t)
        exp = Table(np.array([[1, 2, 4], [2, 2, 3]]),
                    ['O1', 'O2'],
                    ['S1', 'S2', 'S3'])
        self.assertEqual(obs, exp)

    def test_add_pseudocount2(self):
        t = Table(np.array([[0, 1, 3], [1, 1, 2]]),
                  ['O1', 'O2'],
                  ['S1', 'S2', 'S3'])
        obs = add_pseudocount(t, 2)
        exp = Table(np.array([[2, 3, 5], [3, 3, 4]]),
                    ['O1', 'O2'],
                    ['S1', 'S2', 'S3'])
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    unittest.main()
