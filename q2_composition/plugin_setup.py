# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime.plugin import SemanticType, FileFormat, DataLayout, Plugin
from q2_types import FeatureTable
import q2_composition


Composition = SemanticType('Composition',
                           variant_of=FeatureTable.field['content'])

plugin = Plugin(
    name='composition',
    version="0.0.1",
    website='https://github.com/mortonjt/q2-composition',
    package='q2_composition'
)


plugin.register_semantic_type(Composition)

plugin.register_semantic_type(Frequency)
plugin.register_type_to_data_layout(
    FeatureTable[Composition],
    'feature-table', 1)



plugin.methods.register_function(
    function=q2_composition.impute,
    # TODO use more restrictive primitive type for `depth`
    inputs={'table': FeatureTable[Frequency]},
    parameters={'counts_per_sample': Int},
    outputs=[('composition_table',
              FeatureTable[Composition] % Properties('imputed-table'))],
    name='Impute table',
    description="Replaces all of the zeros in the table with a pseudocount"
)

