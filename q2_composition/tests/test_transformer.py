# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import biom
import pandas as pd

from qiime2 import Metadata
from qiime2.plugin.testing import TestPluginBase
from q2_composition._format import (
    FrictionlessCSVFileFormat, ANCOMBC2OutputDirFmt
)
from q2_composition._ancombc2 import ancombc2
from rachis.plugin.util import transform


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()


class TestTransformers(TestBase):
    def test_frictionless_csv_to_dataframe(self):
        _, obs = self.transform_format(FrictionlessCSVFileFormat, pd.DataFrame,
                                       filename='data_slice.csv')

        exp = pd.DataFrame({
            'id': ['sample1'],
            'bodysiteleft palm': [-4.391278379],
            'bodysiteright palm': [-3.390748186],
            'bodysitetongue': [-4.326335562],
            'animalcat': [1.152330146],
            'animalcow': [1.45003133],
            'animalbird': [2.029340857]
        })

        pd.testing.assert_frame_equal(obs, exp)

    def test_ancombc2_to_metadata(self):
        biom_table_fp = self.get_data_path('ancombc2/feature-table.biom')
        metadata_fp = self.get_data_path('ancombc2/metadata.tsv')
        biom_table = biom.load_table(biom_table_fp)
        metadata = Metadata.load(metadata_fp)

        ancombc2_result = ancombc2(
            biom_table,
            metadata,
            fixed_effects_formula='body-site + year',
            group='body-site',
            structural_zeros=True
        )

        ancombc2_dir_fmt = transform(
            ancombc2_result, to_type=ANCOMBC2OutputDirFmt
        )
        ancombc2_md = transform(ancombc2_dir_fmt, to_type=Metadata)
        ancombc2_df = ancombc2_md.to_dataframe()

        for slice, df in ancombc2_result.items():
            df = df.drop(columns='taxon')
            df.columns = slice + '_' + df.columns
            obs_columns = list(df.columns)
            exp_columns = list(ancombc2_df.columns)
            self.assertTrue(column in exp_columns for column in obs_columns)
