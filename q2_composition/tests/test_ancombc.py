# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin.testing import TestPluginBase
from qiime2 import Metadata, Artifact

# from q2_composition._ancombc import ancombc


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        super().setUp()

        self.md = Metadata.load(self.get_data_path('sample-md-ancom.tsv'))
        self.table = Artifact.load(self.get_data_path('table-ancom.qza'))


class TestANCOMBC(TestBase):
    def test_examples(self):
        self.execute_examples()

    # error handling for required fields
    def test_required_fields_table(self):
        pass

    def test_required_fields_metadata(self):
        pass

    def test_required_fields_formula(self):
        pass

    # error handling for column validation
    def test_missing_formula_column(self):
        pass

    def test_missing_group_column(self):
        pass

    def test_missing_level_ordering_column(self):
        pass

    # error handling for missing IDs in metadata
    def test_ids_in_table_not_in_metadata(self):
        pass

    # confirm level ordering behavior
    def test_level_ordering_behavior(self):
        pass
