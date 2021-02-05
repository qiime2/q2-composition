# ----------------------------------------------------------------------------
# Copyright (c) 2016-2021, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin import (Str, Int, Choices, Citations,
                           MetadataColumn, Categorical, Plugin)
from q2_types.feature_table import FeatureTable, Frequency, Composition

import q2_composition


plugin = Plugin(
    name='composition',
    version=q2_composition.__version__,
    website='https://github.com/qiime2/q2-composition',
    package='q2_composition',
    description=('This QIIME 2 plugin supports methods for '
                 'compositional data analysis.'),
    short_description='Plugin for compositional data analysis.',
    citations=Citations.load('citations.bib', package='q2_composition')
)

plugin.methods.register_function(
    function=q2_composition.add_pseudocount,
    inputs={'table': FeatureTable[Frequency]},
    parameters={'pseudocount': Int},
    outputs=[('composition_table', FeatureTable[Composition])],
    input_descriptions={
        'table': 'The feature table to which pseudocounts should be added.'
    },
    parameter_descriptions={
        'pseudocount': 'The value to add to all counts in the feature table.'
    },
    output_descriptions={
        'composition_table': 'The resulting feature table.'
    },
    name='Add pseudocount to table',
    description="Increment all counts in table by pseudocount."
)

_transform_functions = q2_composition._ancom.transform_functions()
_difference_functions = q2_composition._ancom.difference_functions()

plugin.visualizers.register_function(
    function=q2_composition.ancom,
    inputs={'table': FeatureTable[Composition]},
    parameters={
        'metadata': MetadataColumn[Categorical],
        'transform_function': Str % Choices(_transform_functions),
        'difference_function': Str % Choices(_difference_functions)
    },
    input_descriptions={
        'table': 'The feature table to be used for ANCOM computation.'
    },
    parameter_descriptions={
            'metadata': ('The categorical sample metadata column to test for '
                         'differential abundance across.'),
            'transform_function': ('The method applied to transform feature '
                                   'values before generating volcano plots.'),
            'difference_function': 'The method applied to visualize fold '
                                   'difference in feature abundances across '
                                   'groups for volcano plots.'},
    name='Apply ANCOM to identify features that differ in abundance.',
    description=("Apply Analysis of Composition of Microbiomes (ANCOM) to "
                 "identify features that are differentially abundant across "
                 "groups.")
)
