# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime.plugin import SemanticType, FileFormat, DataLayout, Plugin
import q2_composition
import q2_composition._ancom as ancom

from q2_types import (FeatureTable, Frequency, AlphaDiversity,
                      SampleData)

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
    function=q2_composition.add_pseudocount,
    # TODO use more restrictive primitive type for `depth`
    inputs={'table': FeatureTable[Frequency]},
    parameters={'pseudocount': Int},
    outputs=[('composition_table',
              FeatureTable[Composition] % Properties('imputed-table'))],
    name='Add pseudocount to table',
    description="Replaces all of the zeros in the table with a pseudocount"
)

plugin.methods.register_function(
    function=q2_composition.ancom,
    inputs={'table': FeatureTable[Frequency], 'metadata': qiime.Metadata},
    parameters={'metadata' : MetadataCategory,
                'statistical_test' : Str % Choices(ancom.statistical_tests())},
    outputs=[('ancom_results',
              # Not sure what should replace `AlphaDiversity` ...
              # we just want to have a data frame that stores the main
              # ANCOM results.
              SampleData[AlphaDiversity] % Properties('ANCOM statistics'))],
    name='ANCOM',
    description="Reruns the ANCOM test on all features."
)

plugin.methods.register_function(
    function=q2_composition.volcanoplot,
    inputs={'ancom_results': SampleData[AlphaDiversity]},
    # Difference between parameters and input?
    parameters={
        'table' : FeatureTable[Composition],
        'metadata' : MetadataCategory,
        'volcano_transform_function' : Str % Choices(ancom.transform_functions()),
        'volcano_difference_function' : Str % Choices(ancom.difference_functions())},
    name='Plots a Volcano plot of the ANCOM results',
    description="Replaces all of the zeros in the table with a pseudocount"
)
