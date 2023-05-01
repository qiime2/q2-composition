# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import pandas as pd
import tempfile

from qiime2.plugin.testing import TestPluginBase
from qiime2 import Artifact, Metadata

from q2_composition._ancombc import ancombc
from q2_composition._dataloaf_tabulate._visualizer import tabulate


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()
        self.md = Metadata.load(self.get_data_path('sample-md-ancombc.tsv'))

        table = Artifact.load(self.get_data_path('table-ancombc.qza'))
        self.table = table.view(pd.DataFrame)


class TestTabulate(TestBase):
    def test_intercept_cols_single_formula_no_ref_levels(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite')

        with tempfile.TemporaryDirectory() as output_dir:
            tabulate(data=dataloaf, output_dir=output_dir)
            viz_index_fp = os.path.join(output_dir, 'index.html')

            with open(viz_index_fp) as fh:
                viz_contents = fh.read()

                self.assertTrue('bodysite::gut'
                                ' (and any numerical metadata columns)'
                                in viz_contents)

    def test_intercept_cols_single_formula_single_ref_level(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite',
                           reference_levels='bodysite::tongue')

        with tempfile.TemporaryDirectory() as output_dir:
            tabulate(data=dataloaf, output_dir=output_dir)
            viz_index_fp = os.path.join(output_dir, 'index.html')

            with open(viz_index_fp) as fh:
                viz_contents = fh.read()

                self.assertTrue('bodysite::tongue'
                                ' (and any numerical metadata columns)'
                                in viz_contents)

    def test_intercept_cols_multi_formula_no_ref_levels(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + animal')

        with tempfile.TemporaryDirectory() as output_dir:
            tabulate(data=dataloaf, output_dir=output_dir)
            viz_index_fp = os.path.join(output_dir, 'index.html')

            with open(viz_index_fp) as fh:
                viz_contents = fh.read()

                self.assertTrue('bodysite::gut, animal::bird'
                                ' (and any numerical metadata columns)'
                                in viz_contents)

    def test_intercept_cols_multi_formula_single_ref_level(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + animal',
                           reference_levels='bodysite::tongue')

        with tempfile.TemporaryDirectory() as output_dir:
            tabulate(data=dataloaf, output_dir=output_dir)
            viz_index_fp = os.path.join(output_dir, 'index.html')

            with open(viz_index_fp) as fh:
                viz_contents = fh.read()

                self.assertTrue('bodysite::tongue, animal::bird'
                                ' (and any numerical metadata columns)'
                                in viz_contents)

    def test_intercept_cols_multi_formula_multi_ref_levels(self):
        dataloaf = ancombc(table=self.table, metadata=self.md,
                           formula='bodysite + animal',
                           reference_levels=['bodysite::tongue',
                                             'animal::dog'])

        with tempfile.TemporaryDirectory() as output_dir:
            tabulate(data=dataloaf, output_dir=output_dir)
            viz_index_fp = os.path.join(output_dir, 'index.html')

            with open(viz_index_fp) as fh:
                viz_contents = fh.read()

                self.assertTrue('bodysite::tongue, animal::dog'
                                ' (and any numerical metadata columns)'
                                in viz_contents)
