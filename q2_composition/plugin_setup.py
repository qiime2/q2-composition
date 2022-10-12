# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin import (Int, Float, Bool, Str, List,
                           Choices, Citations, Plugin, Metadata)
from q2_types.feature_table import FeatureTable, Frequency, Composition
from q2_types.feature_data import FeatureData
from q2_stats import DifferentialAbundance

import q2_composition
from q2_composition._ancombc import ancombc
import q2_composition._examples as ex

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

plugin.methods.register_function(
    function=ancombc,
    inputs={'table': FeatureTable[Frequency]},
    parameters={
        'metadata': Metadata,
        'formula': Str,
        'p_adj_method': Str % Choices(['holm', 'hochberg', 'hommel',
                                       'bonferroni', 'BH', 'BY',
                                       'fdr', 'none']),
        'prv_cut': Float,
        'lib_cut': Int,
        'level_ordering': List[Str],
        'neg_lb': Bool,
        'tol': Float,
        'max_iter': Int,
        'conserve': Bool,
        'alpha': Float,
    },
    outputs=[('differentials', FeatureData[DifferentialAbundance])],
    input_descriptions={
        'table': 'The feature table to be used for ANCOM computation.'
    },
    parameter_descriptions={
        'metadata': 'The sample metadata.',
        'formula': 'How the microbial absolute abundances for each taxon'
                   ' depend on the variables within the `metadata`.',
        'p_adj_method': 'Method to adjust p-values. Default is "holm".',
        'prv_cut': 'A numerical fraction between 0-1. Taxa with prevalences'
                   ' less than this value will be excluded from the analysis.'
                   ' Default is 0.10.',
        'lib_cut': 'A numerical threshold for filtering samples based on'
                   ' library sizes. Samples with library sizes less than this'
                   ' value will be excluded from the analysis. Default is 0.',
        'level_ordering': ' The preferred order (if any) for the values in the'
                          ' `formula` column, if provided.',
        'neg_lb': 'Whether to classify a taxon as a structural zero using its'
                  ' asymptotic lower bound. Default is FALSE.',
        'tol': 'The iteration convergence tolerance for the E-M algorithm.'
               ' Default is 1e-05.',
        'max_iter': 'The maximum number of iterations for the E-M algorithm.'
                    ' Default is 100.',
        'conserve': 'Whether to use a conservative variance estimator for the'
                    ' test statistic. It is recommended if the sample size is'
                    ' small and/or the number of differentially abundant taxa'
                    ' is believed to be large. Default is FALSE.',
        'alpha': 'Level of significance. Default is FALSE.',
    },
    output_descriptions={
        'differentials': 'The calculated per-feature differentials.',
    },
    name=('Analysis of Composition of Microbiomes with Bias Correction'),
    description=('ANCOM-BC description goes here.'),
    examples={
        'ancombc_single_formula': ex.ancombc_single_formula,
        'ancombc_multi_formula_with_level_ordering': (
            ex.ancombc_multi_formula_with_level_ordering)
    }
)
