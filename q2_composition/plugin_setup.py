# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import importlib

import numpy as np

from qiime2.plugin import (Int, Float, Bool, Str, List,
                           Choices, Citations, Plugin, Metadata,
                           MetadataColumn, Categorical, Range)
from q2_types.feature_table import FeatureTable, Frequency, Composition
from q2_types.feature_data import FeatureData

import q2_composition
from q2_composition._type import DifferentialAbundance
from q2_composition._format import (FrictionlessCSVFileFormat,
                                    DataPackageSchemaFileFormat,
                                    DataLoafPackageDirFmt)
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

plugin.register_formats(FrictionlessCSVFileFormat, DataPackageSchemaFileFormat,
                        DataLoafPackageDirFmt)

plugin.register_semantic_type_to_format(FeatureData[DifferentialAbundance],
                                        DataLoafPackageDirFmt)

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
        'neg_lb': Bool,
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
        'neg_lb': 'Whether to classify a taxon as a structural zero using its'
                  ' asymptotic lower bound.',
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

plugin.visualizers.register_function(
    function=q2_composition.tabulate,
    inputs={'data': FeatureData[DifferentialAbundance]},
    parameters={},
    input_descriptions={'data': 'The ANCOM-BC output to be tabulated.'},
    name=' View tabular output from ANCOM-BC.',
    description='Generate tabular view of ANCOM-BC output, which includes'
                ' per-page views for the log-fold change (lfc), standard error'
                ' (se), P values, Q values, and W scores.',
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
        'label_limit': ("Set labelLimit for y-axis labels")},
    name='Differential abundance bar plots',
    description=('Generate bar plot views of ANCOM-BC output. One plot will '
                 'be present per column in the ANCOM-BC output. The '
                 '`significance_threshold`, `effect_size_threshold` '
                 'and `feature_ids` filter results are intersected, '
                 'such that only features that remain after all three '
                 'filters have been applied will be present in the output.'),
)
importlib.import_module('q2_composition._transformer')
