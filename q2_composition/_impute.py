# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import biom
import numpy as np
from skbio.stats.composition import multiplicative_replacement, closure


def add_pseudocount(table: biom.Table,
                    pseudocount: float=1,
                    multiplicative: bool=False) -> biom.Table:
    # This is ugly, and it requires a sparse and dense representation to
    # be in memory at the same time, but biom.Table.transform only operates
    # on non-zero values, so it isn't useful here (as we need to operate on
    # all values).
    if multiplicative:
        data = [closure(multiplicative_replacement(v, delta=pseudocount))
                for v in table.iter_data(dense=True,
                                         axis='sample')]
        data = np.array(data).T
    else:
        data = np.array([v + pseudocount
                         for v in table.iter_data(dense=True,
                                                  axis='observation')])

    result = biom.Table(data, table.ids(axis='observation'), table.ids())
    return result
