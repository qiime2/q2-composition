# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin.testing import TestPluginBase

from q2_composition._ancombc import ancombc


class TestBase(TestPluginBase):
    package = 'q2_composition.tests'

    def setUp(self):
        return super().setUp()


class TestANCOMBC(TestBase):
    def test_pass(self):
        pass
