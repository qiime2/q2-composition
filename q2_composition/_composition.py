# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import biom
import numpy as np
import pandas as pd
from typing import Callable


def add_pseudocount(table: biom.Table,
                    pseudocount: int=1) -> pd.DataFrame:
    imputation_method = lambda x: x + pseudocount

    df = pd.DataFrame(np.array(table.matrix_data.todense()).T,
                      index=table.ids(axis='sample'),
                      columns=table.ids(axis='observation'))
    return df.apply(imputation_method, axis=1)
