# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from qiime2.plugin.testing import TestPluginBase


class UsageExampleTests(TestPluginBase):
    package = 'q2_composition.tests'

    def test_examples(self):
        self.execute_examples()
