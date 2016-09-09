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

def impute(table: biom.Table,
           imputation_method: Callable[[pd.Series],
                                        pd.Series]=None) -> pd.DataFrame:
    if imputation_method is None:
        imputation_method = lambda x: x + 1
    df = pd.DataFrame(np.array(table.matrix_data.todense()).T,
                      index=table.ids(axis='sample'),
                      columns=table.ids(axis='observation'))
    return df.apply(imputation_method, axis=1)
