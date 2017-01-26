# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin import (Str, Int, Choices,
                           MetadataCategory, Plugin)
from q2_types.feature_table import (
    FeatureTable, Frequency, BIOMV100DirFmt, BIOMV210DirFmt)

import q2_composition
from q2_composition import Composition

_citation_text = ("Analysis of composition of microbiomes: a novel method for "
                  "studying microbial composition.\nMandal S, Van Treuren W, "
                  "White RA, Eggesbø M, Knight R, Peddada SD.\n"
                  "Microb Ecol Health Dis. 2015 May 29;26:27663. doi: "
                  "10.3402/mehd.v26.27663.")

plugin = Plugin(
    name='composition',
    version=q2_composition.__version__,
    website='https://github.com/qiime2/q2-composition',
    citation_text=_citation_text,
    package='q2_composition'
)

plugin.register_semantic_types(Composition)

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
    inputs={'table': FeatureTable[Frequency]},
    parameters={'pseudocount': Int},
    outputs=[('composition_table', FeatureTable[Composition])],
    name='Add pseudocount to table',
    description="Increment all counts in table by pseudocount."
)

_ancom_statistical_tests = q2_composition._ancom.statistical_tests()
_transform_functions = q2_composition._ancom.transform_functions()
_difference_functions = q2_composition._ancom.difference_functions()

plugin.visualizers.register_function(
    function=q2_composition.ancom,
    inputs={'table': FeatureTable[Composition]},
    parameters={
        'metadata': MetadataCategory,
        'statistical_test': Str % Choices(_ancom_statistical_tests),
        'transform_function': Str % Choices(_transform_functions),
        'difference_function': Str % Choices(_difference_functions)
    },
    name='Apply ANCOM to identify features that differ in abundance.',
    description=("Apply Analysis of Composition of Microbiomes (ANCOM) to "
                 "identify features that are differentially abundant across "
                 "groups.")
)
