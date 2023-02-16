# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import tempfile
import os.path
from pathlib import Path

import pandas as pd

from qiime2.plugin.testing import TestPluginBase
from qiime2 import Metadata, Artifact

from q2_composition import (ancombc, da_barplot, DataLoafPackageDirFmt)


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()

        # self.md = Metadata.load(self.get_data_path('sample-md-ancombc.tsv'))
        # table = Artifact.load(self.get_data_path('table-ancombc.qza'))
        # self.table = table.view(pd.DataFrame)

        self.dataloaf1 = Artifact.load(self.get_data_path('dataloaf.qza'))


class TestDABarplot(TestBase):

    def test_basic(self):
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon')
            self.assertTrue((output_dir / 'index.html').exists())

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            self.assertTrue(tongue_path.exists())

            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            self.assertTrue(right_palm_path.exists())

            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'
            self.assertTrue(left_palm_path.exists())

            # file shouldn't exist for reference column
            gut_path = \
                output_dir / 'bodysitegut-ancombc-barplot.html'
            self.assertFalse(gut_path.exists())

            # spot check for a feature id
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

    def test_filter_on_significance(self):
        # confirm feature presence when not filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon',
                             significance_threshold=1.0)

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'

            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

        # confirm feature absence when filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon',
                             significance_threshold=1e-3)

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'

            # this feature is significant at this
            # threshold only in tongue and left palm
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

    def test_filter_on_effect_size(self):
        # confirm feature presence when not filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon',
                             effect_size_threshold=0)

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'

            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

        # confirm feature absence when filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon',
                             effect_size_threshold=3.5)

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'

            # this feature's effect size is greater
            # than the threshold only in tongue and left palm
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

    def test_filter_on_feature_ids(self):
        ids_to_keep = ['bfbed36e63b69fec4627424163d20118',
                       '4b5eeb300368260019c1fbc7a3c718fc']

        # confirm feature presence when no filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon',
                             feature_ids=None)

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'

            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertTrue(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

        # confirm feature absence when filtering
        with tempfile.TemporaryDirectory() as output_dir:
            output_dir = Path(output_dir)
            viz = da_barplot(output_dir,
                             self.dataloaf1.view(DataLoafPackageDirFmt),
                             feature_id_column='taxon',
                             feature_ids=ids_to_keep)

            tongue_path = output_dir / 'bodysitetongue-ancombc-barplot.html'
            right_palm_path = \
                output_dir / 'bodysiteright-palm-ancombc-barplot.html'
            left_palm_path = \
                output_dir / 'bodysiteleft-palm-ancombc-barplot.html'

            # feature ids expected to be absent are absent
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(tongue_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(right_palm_path).read())
            self.assertFalse(
                'd29fe3c70564fc0f69f2c03e0d1e5561' in
                open(left_palm_path).read())

            # feature ids expected to be present are present
            self.assertTrue(
                'bfbed36e63b69fec4627424163d20118' in
                open(tongue_path).read())
            self.assertTrue(
                'bfbed36e63b69fec4627424163d20118' in
                open(right_palm_path).read())
            self.assertTrue(
                'bfbed36e63b69fec4627424163d20118' in
                open(left_palm_path).read())

            self.assertTrue(
                '4b5eeb300368260019c1fbc7a3c718fc' in
                open(tongue_path).read())
            self.assertTrue(
                '4b5eeb300368260019c1fbc7a3c718fc' in
                open(right_palm_path).read())
            self.assertTrue(
                '4b5eeb300368260019c1fbc7a3c718fc' in
                open(left_palm_path).read())

    def test_error_on_bad_column_names(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(KeyError, "Column .* id .* not prese"):
                da_barplot(output_dir,
                           self.dataloaf1.view(DataLoafPackageDirFmt))

    ## Add tests using q2_composition/tests/data/dataloaf-hmp1-body-habitat.qza