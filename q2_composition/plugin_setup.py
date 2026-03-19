# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import importlib

import numpy as np

from qiime2.plugin import (Int, Float, Bool, Str, List,
                           Choices, Citations, Plugin, Metadata,
                           MetadataColumn, Categorical, Range, Threads)
from q2_types.feature_table import FeatureTable, Frequency, Composition
from q2_types.feature_data import FeatureData, Taxonomy

import q2_composition
from q2_composition._type import DifferentialAbundance, ANCOMBC2Output
from q2_composition._format import (
    FrictionlessCSVFileFormat,
    DataPackageSchemaFileFormat,
    DataLoafPackageDirFmt,
    ANCOMBC2OutputDirFmt,
)
import q2_composition._examples as ex

citations = Citations.load('citations.bib', package='q2_composition')

plugin = Plugin(
    name='composition',
    version=q2_composition.__version__,
    website='https://github.com/qiime2/q2-composition',
    package='q2_composition',
    description=('This QIIME 2 plugin supports methods for '
                 'compositional data analysis.'),
    short_description='Plugin for compositional data analysis.'
)

plugin.register_formats(
    FrictionlessCSVFileFormat,
    DataPackageSchemaFileFormat,
    DataLoafPackageDirFmt,
    ANCOMBC2OutputDirFmt,
)

plugin.register_semantic_type_to_format(
    FeatureData[DifferentialAbundance], DataLoafPackageDirFmt
)

plugin.register_semantic_type_to_format(
    FeatureData[ANCOMBC2Output], ANCOMBC2OutputDirFmt
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
    name='Add pseudocount to table.',
    description='Increment all counts in table by pseudocount.'
)

_transform_functions = q2_composition._ancom.transform_functions()
_difference_functions = q2_composition._ancom.difference_functions()

plugin.visualizers.register_function(
    function=q2_composition.ancom,
    inputs={'table': FeatureTable[Composition]},
    parameters={
        'metadata': MetadataColumn[Categorical],
        'transform_function': Str % Choices(_transform_functions),
        'difference_function': Str % Choices(_difference_functions),
        'filter_missing': Bool,
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
                               'groups for volcano plots.',
        'filter_missing': 'If True, samples with missing metadata '
                          'values will be filtered from the table '
                          'prior to analysis. If False, an error '
                          'will be raised if there are any missing '
                          'metadata values.'},
    name='Apply ANCOM to identify features that differ in abundance.',
    description=('Apply Analysis of Composition of Microbiomes (ANCOM) to'
                 ' identify features that are differentially abundant across'
                 ' groups.'),
    citations=[citations['mandal2015ancom']]
)

plugin.methods.register_function(
    function=q2_composition.ancombc,
    inputs={'table': FeatureTable[Frequency]},
    parameters={
        'metadata': Metadata,
        'formula': Str,
        'p_adj_method': Str % Choices(['holm', 'hochberg', 'hommel',
                                       'bonferroni', 'BH', 'BY',
                                       'fdr', 'none']),
        'prv_cut': Float,
        'lib_cut': Int,
        'reference_levels': List[Str],
        'tol': Float,
        'max_iter': Int,
        'conserve': Bool,
        'alpha': Float,
    },
    outputs=[('differentials', FeatureData[DifferentialAbundance])],
    input_descriptions={
        'table': 'The feature table to be used for ANCOM-BC computation.'
    },
    parameter_descriptions={
        'metadata': 'The sample metadata.',
        'formula': 'How the microbial absolute abundances for each taxon'
                   ' depend on the variables within the `metadata`.',
        'p_adj_method': 'Method to adjust p-values.',
        'prv_cut': 'A numerical fraction between 0-1. Taxa with prevalences'
                   ' less than this value will be excluded from the analysis.',
        'lib_cut': 'A numerical threshold for filtering samples based on'
                   ' library sizes. Samples with library sizes less than this'
                   ' value will be excluded from the analysis.',
        'reference_levels': 'Define the reference level(s) to be used for'
                            ' categorical columns found in the `formula`.'
                            ' These categorical factors are dummy coded'
                            ' relative to the reference(s) provided.'
                            ' The syntax is as follows:'
                            ' "column_name::column_value"',
        'tol': 'The iteration convergence tolerance for the E-M algorithm.',
        'max_iter': 'The maximum number of iterations for the E-M algorithm.',
        'conserve': 'Whether to use a conservative variance estimator for the'
                    ' test statistic. It is recommended if the sample size is'
                    ' small and/or the number of differentially abundant taxa'
                    ' is believed to be large.',
        'alpha': 'Level of significance.',
    },
    output_descriptions={
        'differentials': 'The calculated per-feature differentials.',
    },
    name=('Analysis of Composition of Microbiomes with Bias Correction'),
    description=('Apply Analysis of Compositions of Microbiomes with Bias'
                 ' Correction (ANCOM-BC) to identify features that are'
                 ' differentially abundant across groups.'),
    citations=[citations['lin2020ancombc']],
    examples={
        'ancombc_single_formula': ex.ancombc_single_formula,
        'ancombc_multi_formula_with_reference_levels': (
            ex.ancombc_multi_formula_with_reference_levels)
    }
)

plugin.methods.register_function(
    function=q2_composition.ancombc2,
    inputs={
        'table': FeatureTable[Frequency],
    },
    parameters={
        'metadata': Metadata,
        'fixed_effects_formula': Str,
        'random_effects_formula': Str,
        'reference_levels': List[Str],
        'p_adjust_method': Str,
        'prevalence_cutoff': Float % Range(
            0.0, 1.0, inclusive_start=True, inclusive_end=True
        ),
        'group': Str,
        'structural_zeros': Bool,
        'asymptotic_cutoff': Bool,
        'alpha': Float % Range(
            0.0, 1.0, inclusive_start=False, inclusive_end=True
        ),
        'diff_robust': Bool,
        'num_processes': Threads,
    },
    outputs=[
        ('ancombc2_output', FeatureData[ANCOMBC2Output])
    ],
    input_descriptions={
        'table': 'The feature table to be used for ANCOM-BC2 computation.'
    },
    parameter_descriptions={
        'metadata': 'The per-sample metadata.',
        'fixed_effects_formula': (
            'A formula that expresses how the feature absolute abundances in '
            'the feature table depend on the fixed effects of variables '
            '(columns) in the metadata. Do not include the dependent '
            'variable. Reference the `formula` function in the `stats` R '
            'package for a specification of valid formulae.'
        ),
        'random_effects_formula': (
            'A formula that expresses how the feature absolute abundances in '
            'the feature table depend on the random effects of variables '
            '(columns) in the metadata. Do not include the dependent '
            'variable. For example, to specify `MyVariable` as a random '
            'intercept use the syntax `(1 | MyVariable)`. Reference the '
            '`lmerTest` R package for a specification of valid formulae.'
        ),
        'reference_levels': (
            'Specify reference levels for one or more categorical metadata '
            'variables (columns). The method of specification is '
            '"column_name::column_value". E.g. "sex::female" sets the '
            '"female" category of the "sex" variable to be the reference '
            'level. Separate multiple specifications by spaces.'
        ),
        'p_adjust_method': (
            'The method used to adjust p-values. Choose from "holm", '
            '"hochberg", "hommel", "bonferroni",  "BH", "BY", "fdr", "none". '
            'See the `p.adjust` method in the `stats` R package for '
            'explanations of each option.'
        ),
        'prevalence_cutoff': (
            'Features with prevalences less than this threshold will be '
            'excluded from the analysis.'
        ),
        'group': (
            'The name of the group variable in the metadata. The group '
            'variable must be categorical and is required to detect '
            'structural zeros.'
        ),
        'structural_zeros': (
            'Whether to detect structurual zeros based on the `group` '
            'variable. Refer to the ANCOM-BC2 paper for an expalanation of '
            'the use of structural zeros.'
        ),
        'asymptotic_cutoff': (
            'Whether to classify a taxon as a structural zero using its '
            'asymptotic lower bound. Generally, it is recommended to set '
            'this parameter when the sample size per group is relatively '
            'large (n > 30). When this parameter is not set, a feature is '
            'classified as a structural zero in a group if its frequency is '
            'zero in that group. See the ANCOM-BC2 publication for details.'
        ),
        'alpha': 'The significance level.',
        'diff_robust': (
            'Whether to include `diff_robust` columns in the output. The '
            '`diff_robust` values are true where q < alpha AND sensitivity '
            'analysis was passed, and false otherwise.'
        ),
        'num_processes': (
            'The number of processes to create that can be run in parallel.'
        ),
    },
    output_descriptions={
        'ancombc2_output': (
            'The estimated log fold changes and their standard errors for '
            'the variables included in the mixed effects model. Also includes '
            'the structural zero designations if the `structural_zeros` '
            'parameter is passed.'
        )
    },
    name=(
        'ANCOM-BC2: Analysis of Composition of Microbiomes with Bias '
        'Correction 2.'
    ),
    description=(
        'Calls the `ancombc2` function of the ANCOMBC software package. See '
        'the ANCOM-BC2 publication and source code for details.'
        '\n\nSensitivity Analysis for Pseudo-Count Addition: To assess '
        'robustness, a series of pseudo-counts (0.01 to 0.5, in 0.01 '
        'increments) is added to zero counts, and a linear model is fitted to '
        'the bias-corrected log-abundance data for each. A sensitivity score '
        'is calculated as the proportion of p-values above the specified '
        'alpha. Taxa with consistent significance across all pseudo-counts, '
        'and agreement with complete-data results, are flagged as robust '
        '(diff_robust = TRUE). Note: Results depend on the selected alpha '
        'value.'
    ),
    citations=[citations['lin2024multigroup']],
    examples={
        'single-variable': ex.ancombc2_single_formula,
        'multi-variable-reference':
            ex.ancombc2_multi_formula_with_reference_levels,
    }
)

plugin.visualizers.register_function(
    function=q2_composition.ancombc2_visualizer,
    inputs={
        'data': FeatureData[ANCOMBC2Output],
        'taxonomy': FeatureData[Taxonomy],
    },
    parameters={},
    input_descriptions={
        'data': 'The ANCOMBC2 output to visualize.',
        'taxonomy': (
            'The taxonomy associated with the features present in the '
            'ANCOMBC2 data.'
        )
    },
    name='Visualize ANCOMBC2 output.',
    description=(
        'Displays ANCOMBC2 Log-Fold Change values in a barplot and allows '
        'filtering based on p-value and standard error. If a taxonomy is '
        'provided, features can be filtered by taxonomy using an interactive '
        'tree.'
    ),
)

plugin.visualizers.register_function(
    function=q2_composition.tabulate,
    inputs={'data': FeatureData[DifferentialAbundance | ANCOMBC2Output]},
    parameters={},
    input_descriptions={
        'data': 'The ANCOM-BC or ANCOM-BC2 output to be tabulated.'
    },
    name=' View tabular output from ANCOM-BC or ANCOM-BC2.',
    description=(
        'Generate tabular view of ANCOM-BC or ANCOM-BC2 output, which includes'
        ' per-page views for the log-fold change (lfc), standard error'
        ' (se), P values, Q values, and W scores.'
    ),
)

plugin.visualizers.register_function(
    function=q2_composition.da_barplot,
    inputs={'data': FeatureData[DifferentialAbundance]},
    parameters={'effect_size_label': Str,
                'feature_id_label': Str,
                'error_label': Str,
                'significance_label': Str,
                'significance_threshold': Float % Range(0.0, 1.0,
                                                        inclusive_start=True,
                                                        inclusive_end=True),
                'effect_size_threshold': Float % Range(0.0, np.inf,
                                                       inclusive_start=True),
                'feature_ids': Metadata,
                'level_delimiter': Str,
                'label_limit': Int},
    input_descriptions={'data': 'The ANCOM-BC output to be plotted.'},
    parameter_descriptions={
        'effect_size_label': "Label for effect sizes in `data`.",
        'feature_id_label': "Label for feature ids in `data`.",
        'error_label': "Label for effect size errors in `data`.",
        'significance_label': ("Label for statistical significance "
                               "level in `data`."),
        'significance_threshold': ("Exclude features with statistical "
                                   "significance level greater (i.e., less "
                                   "significant) than this threshold."),
        'effect_size_threshold': ("Exclude features with an absolute value "
                                  "of effect size less than this threshold."),
        'feature_ids': ("Exclude features if their ids are not included in "
                        "this index."),
        'level_delimiter': ("If feature ids encode hierarchical information, "
                            "split the levels when generating feature labels "
                            "in the visualization using this delimiter."),
        'label_limit': ("Set the maximum length that will be viewable for "
                        "axis labels. You can set this parameter if your "
                        "axis labels are being cut off.")},
    name='Differential abundance bar plots',
    description=('Generate bar plot views of ANCOM-BC output. One plot will '
                 'be present per column in the ANCOM-BC output. The '
                 '`significance_threshold`, `effect_size_threshold` '
                 'and `feature_ids` filter results are intersected, '
                 'such that only features that remain after all three '
                 'filters have been applied will be present in the output.'),
)
importlib.import_module('q2_composition._transformer')
