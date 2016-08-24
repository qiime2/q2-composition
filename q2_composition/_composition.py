# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd
import qiime
from qiime.plugin import SemanticType, FileFormat, DataLayout
from .plugin_setup import plugin


Composition = SemanticType('Composition', variant_of=FeatureTable.field['content'])

plugin.register_semantic_type(Composition)

def feature_table_to_pandas_composition(view, data_dir,
                                        imputation_method=None):
    if imputation_method is None:
        imputation_method = lambda x: x + 1

    with open(os.path.join(data_dir, 'feature-table.biom'), 'r') as fh:
        table = biom.Table.from_json(json.load(fh))
        array = table.matrix_data.toarray().T
        sample_ids = table.ids(axis='sample')
        feature_ids = table.ids(axis='observation')
        df = pd.DataFrame(array, index=sample_ids, columns=feature_ids)
        return df.apply(mr, axis=1)

plugin.register_semantic_type(Frequency)
plugin.register_type_to_data_layout(
    FeatureTable[Composition],
    'feature-table', 1)
