# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd

from q2_composition.plugin_setup import plugin
from q2_composition._format import FrictionlessCSVFileFormat


@plugin.register_transformer
def _5(obj: FrictionlessCSVFileFormat) -> pd.DataFrame:
    path = obj.view(FrictionlessCSVFileFormat)
    df = pd.read_csv(str(path))

    return df
