# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import unittest
import qiime2
import biom
import os
import tempfile
import pandas as pd

from pathlib import Path
from q2_composition._ancombc2 import da_barplot, ancombc2
from q2_composition._ancombc import ancombc
from q2_composition._format import ANCOMBC2OutputDirFmt
from qiime2.sdk import PluginManager
from qiime2 import Artifact


class TestDiffAbundancePlot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_data_fp = Path(__file__).parent / 'data' / 'ancombc2'

        table_fp = cls.test_data_fp / 'feature-table.biom'
        cls.biom_table = biom.load_table(table_fp)

        metadata_fp = cls.test_data_fp / 'metadata.tsv'
        cls.ancombc2_metadata = qiime2.Metadata.load(metadata_fp)

        ancombc_table_fp = Path(__file__).parent / 'data' / 'table-ancombc.qza'
        ancombc_table = qiime2.Artifact.load(ancombc_table_fp)
        cls.ancombc_table = ancombc_table.view(pd.DataFrame)

        metadata_fp = Path(__file__).parent / 'data' / 'sample-md-ancombc.tsv'
        cls.ancombc_metadata = qiime2.Metadata.load(metadata_fp)

        cls.abc2_output = ancombc2(
            table=cls.biom_table,
            metadata=cls.ancombc2_metadata,
            fixed_effects_formula='body-site + year',
            group='body-site',
            structural_zeros=True
        )

        # Use this for raw calls to da_barplot but use the original for when we
        # load it to an Artifact and invoke the action
        cls.abc2_output_DirFmt = qiime2.plugin.util.transform(
            data=cls.abc2_output, to_type=ANCOMBC2OutputDirFmt
        )

        cls.abc_output = ancombc(
            table=cls.ancombc_table,
            metadata=cls.ancombc_metadata,
            formula='bodysite'
        )

    def test_da_barplot(self):
        '''
        Tests that the visualizer runs successfully, which is essentially a
        test of whether or not the visualizer got built into the
        q2_composition/_da_barplot/dist/ folder successfully.
        '''
        with tempfile.TemporaryDirectory() as tempdir:
            da_barplot(tempdir, self.abc2_output_DirFmt)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))

        with tempfile.TemporaryDirectory() as tempdir:
            da_barplot(tempdir, self.abc_output)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))

    def test_da_barplot_non_overlapping_taxonomy(self):
        '''
        Tests that an error is raised when attempting to visualize ancombc2
        data with a taxonomy that contains none of the features present in the
        ancombc2 data.
        '''
        taxonomy_df = pd.DataFrame({
            'Feature ID': ['feat1', 'feat2'],
            'Taxon': ['taxon1', 'taxon2'],
            'Confidence': [0.9, 0.95]
        })

        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(
                ValueError, 'No features remained in your taxonomy'
            ):
                da_barplot(tempdir, self.abc2_output_DirFmt, taxonomy_df)

        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(
                ValueError, 'No features remained in your taxonomy'
            ):
                da_barplot(tempdir, self.abc_output, taxonomy_df)

    def test_da_barplot_accepts_ancombc2(self):
        '''
        Tests that da_barplot accepts ancombc2 outputs.
        '''
        with tempfile.TemporaryDirectory() as tempdir:
            da_barplot(tempdir, self.abc2_output_DirFmt)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))

    def test_da_barplot_accepts_ancombc(self):
        '''
        Tests that da_barplot accepts ancombc outputs.
        '''
        with tempfile.TemporaryDirectory() as tempdir:
            da_barplot(tempdir, self.abc_output)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))

    def test_da_barplot_action_ancombc2(self):
        pm = PluginManager()
        da_barplot = pm.plugins['composition'].actions['da_barplot']

        ancombc2_artifact = Artifact.import_data(
            type='FeatureData[ANCOMBC2Output]', view=self.abc2_output
        )

        viz = da_barplot(ancombc2_artifact)
        viz = viz.visualization

        with tempfile.TemporaryDirectory() as tempdir:
            viz.export_data(tempdir)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))

    def test_da_barplot_action_ancombc(self):
        pm = PluginManager()
        da_barplot = pm.plugins['composition'].actions['da_barplot']

        ancombc_artifact = Artifact.import_data(
            type='FeatureData[DifferentialAbundance]', view=self.abc_output
        )

        viz = da_barplot(ancombc_artifact)
        viz = viz.visualization

        with tempfile.TemporaryDirectory() as tempdir:
            viz.export_data(tempdir)
            assert os.path.exists(os.path.join(tempdir, 'index.html'))
