# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import unittest
from _composition import
import numpy as np


class CompositionTypesTest(unittest.TestCase):

    def test_feature_table_to_pandas_composition(self):
        t = Table(np.array([[0, 1, 3], [1, 1, 2]]),
                  ['O1', 'O2'],
                  ['S1', 'S2', 'S3'])

        # ?? What am I testing here?


if __name__ == '__main__':
    unittest.main()
