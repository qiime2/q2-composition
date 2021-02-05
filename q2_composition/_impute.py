# ----------------------------------------------------------------------------
# Copyright (c) 2016-2021, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import biom


def add_pseudocount(table: biom.Table,
                    pseudocount: int = 1) -> biom.Table:
    # This is ugly, and it requires a sparse and dense representation to
    # be in memory at the same time, but biom.Table.transform only operates
    # on non-zero values, so it isn't useful here (as we need to operate on
    # all values).
    result = biom.Table(
        [v + pseudocount
         for v in table.iter_data(dense=True, axis='observation')],
        table.ids(axis='observation'),
        table.ids())
    return result
