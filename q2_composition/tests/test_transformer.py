# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd

from qiime2.plugin.testing import TestPluginBase

from q2_composition._format import FrictionlessCSVFileFormat


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()


class TestTransformers(TestBase):
    def test_frictionless_csv_to_dataframe(self):
        _, obs = self.transform_format(FrictionlessCSVFileFormat, pd.DataFrame,
                                       filename='data_slice.csv')

        exp = pd.DataFrame({
            'feature_id': ['sample1'],
            'bodysiteleft palm': [-4.391278379],
            'bodysiteright palm': [-3.390748186],
            'bodysitetongue': [-4.326335562],
            'animalcat': [1.152330146],
            'animalcow': [1.45003133],
            'animalbird': [2.029340857]
        })

        pd.testing.assert_frame_equal(obs, exp)
