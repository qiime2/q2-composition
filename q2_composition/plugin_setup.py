# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime.plugin import (SemanticType, Str, Int, Properties, Choices,
                          MetadataCategory, Plugin)
import qiime
import q2_composition
import q2_composition._ancom as ancom

from q2_types import (FeatureTable, Frequency, AlphaDiversity,
                      SampleData)

from q2_types.feature_table import BIOMV100DirFmt, BIOMV210DirFmt


Composition = SemanticType('Composition',
                           variant_of=FeatureTable.field['content'])

plugin = Plugin(
    name='composition',
    version="0.0.1",
    website='https://github.com/mortonjt/q2-composition',
    package='q2_composition'
)

plugin.register_semantic_type(Composition)

plugin.register_semantic_type_to_format(
    FeatureTable[Composition],
    artifact_format=BIOMV210DirFmt
)

plugin.register_semantic_type_to_format(
    FeatureTable[Composition],
    artifact_format=BIOMV100DirFmt
)

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
    inputs={'table': FeatureTable[Frequency]},
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

plugin.visualizers.register_function(
    function=q2_composition.volcanoplot,
    inputs={'ancom_results': SampleData[AlphaDiversity]},
    # Difference between parameters and input?
    parameters={
        'table' : FeatureTable[Composition],
        'metadata' : MetadataCategory,
        'transform_function' : Str % Choices(ancom.transform_functions()),
        'difference_function' : Str % Choices(ancom.difference_functions())},
    name='Volcano plot',
    description="Plots a Volcano plot of the ANCOM results"
)
