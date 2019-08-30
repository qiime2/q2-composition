# ----------------------------------------------------------------------------
# Copyright (c) 2016-2019, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin import (Str, Int, Choices, Citations, Metadata, Range,
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

          main_variable: str,
          adjusted_formula: str = 'NULL',
          random_formula: str = None,
          alpha: float = 0.05,
          max_sparsity: float = 0.9,
          p_adjust_method: str = 'BH') -> None:

plugin.visualizers.register_function(
    function=q2_composition.ancom,
    inputs={'table': FeatureTable[Composition]},
    parameters={
        'metadata': Metadata,
        'main_variable': Str,
        'adjusted_formula': Str,
        'random_formula': Str,
        'alpha': Float % Range(0.0, 1.0),
        'max_sparsity': Float % Range(0.0, 1.0),
        'p_adjust_method': Str % Choices(["holm", "hochberg", "hommel",
                                          "bonferroni", "BH", "BY", "fdr",
                                          "none"])
    },
    input_descriptions={
        'table': 'The feature table to be used for ANCOM computation.'
    },
    parameter_descriptions={
        'metadata': ('The categorical sample metadata column to test for '
                     'differential abundance across.'),
        'main_variable': 'Main variable of interest for differential '
                         'abundance testing.',
        'adjusted_formula': 'Covariate formula used to adjust ANCOM test. If '
                            'the metadata contains cross-sectional data, '
                            'an ANOVA test will be used as the distance '
                            'function. If the metadata contain repeated '
                            'measurements for individual sites/subjects, as '
                            'specified by the "random_formula" parameter, a '
                            'linear mixed effects model will be used as the '
                            'distance function.',
        'random_formula': 'Mixed effects model random effects formula. See '
                          'R package nlme for more details. Examples:\n'
                          'Set a random intercept for each subject according '
                          'to metadata column "studyid": "~ 1 | studyid"\n'
                          'nSet a random intercept and slope for each subject '
                          'according to metadata columns "studyid" and '
                          '"month": "~ month | studyid"',
        'alpha': 'Level of significance.',
        'max_sparsity': 'Features with a proportion of zero values greater '
                        'than max_sparsity will be filtered prior to running '
                        'the ANCOM test.',
        'p_adjust_method': 'Method to use for adjusing p-values for multiple '
                           'comparisons. See p.adjust for more details.'},
    name='Apply ANCOM 2.0 to identify features that differ in abundance.',
    description=("Apply Analysis of Composition of Microbiomes (ANCOM) to "
                 "identify features that are differentially abundant across "
                 "groups distinguished by 'main_variable'. Four different "
                 "difference functions may be used by this test, depending "
                 "on the nature of the input data and parameters used:\n"
                 "adjusted_formula  random_formula   Test\n"
                 "      False           False        Wilcoxon\n"
                 "      True            False        ANOVA\n"
                 "      False           True         Mixed-Effects model\n"
                 "      True            True         Mixed-Effects + ANOVA")
)

plugin.visualizers.register_function(
    function=q2_composition.ancom1,
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
