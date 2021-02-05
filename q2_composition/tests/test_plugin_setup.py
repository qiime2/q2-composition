# ----------------------------------------------------------------------------
# Copyright (c) 2016-2021, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import unittest

from q2_composition.plugin_setup import plugin as composition_plugin


class PluginSetupTests(unittest.TestCase):

    def test_plugin_setup(self):
        self.assertEqual(composition_plugin.name, 'composition')
