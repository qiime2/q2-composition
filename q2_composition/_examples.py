# ----------------------------------------------------------------------------
# Copyright (c) 2022-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import importlib.resources

import qiime2


def _get_data_from_tests(path):
    return (
        importlib.resources.files('q2_composition') / 'tests' / 'data' / path
    )


def ancombc_md_factory():
    return qiime2.Metadata.load(
        _get_data_from_tests('sample-md-ancombc.tsv'))


def ancombc_table_factory():
    return qiime2.Artifact.load(
        _get_data_from_tests('table-ancombc.qza'))


def ancombc_dataloaf_factory():
    return qiime2.Artifact.load(
        _get_data_from_tests('dataloaf.qza'))


def ancombc_single_formula(use):
    table = use.init_artifact('table', ancombc_table_factory)
    metadata = use.init_metadata('metadata', ancombc_md_factory)

    dataloaf, = use.action(
        use.UsageAction('composition', 'ancombc'),
        use.UsageInputs(
            table=table,
            metadata=metadata,
            formula='bodysite'
        ),
        use.UsageOutputNames(
            differentials='dataloaf'
        )
    )

    dataloaf.assert_output_type('FeatureData[DifferentialAbundance]')


def ancombc_multi_formula_with_reference_levels(use):
    table = use.init_artifact('table', ancombc_table_factory)
    metadata = use.init_metadata('metadata', ancombc_md_factory)

    dataloaf, = use.action(
        use.UsageAction('composition', 'ancombc'),
        use.UsageInputs(
            table=table,
            metadata=metadata,
            formula='bodysite + animal',
            reference_levels=["bodysite::tongue", "animal::dog"]
        ),
        use.UsageOutputNames(
            differentials='dataloaf'
        )
    )

    dataloaf.assert_output_type('FeatureData[DifferentialAbundance]')


def ancombc_tabulate(use):
    data = use.init_artifact('dataloaf', ancombc_dataloaf_factory)

    viz, = use.action(
        use.UsageAction('composition', 'tabulate'),
        use.UsageInputs(
            data=data
        ),
        use.UsageOutputNames(
            visualization='visualization'
        )
    )

    viz.assert_output_type('Visualization')


def ancombc2_single_formula(use):
    table = use.init_artifact('table', ancombc_table_factory)
    metadata = use.init_metadata('metadata', ancombc_md_factory)

    abc2_output, = use.action(
        use.UsageAction('composition', 'ancombc2'),
        use.UsageInputs(
            table=table,
            metadata=metadata,
            fixed_effects_formula='bodysite'
        ),
        use.UsageOutputNames(ancombc2_output='abc2_output')
    )

    abc2_output.assert_output_type('FeatureData[ANCOMBC2Output]')


def ancombc2_multi_formula_with_reference_levels(use):
    table = use.init_artifact('table', ancombc_table_factory)
    metadata = use.init_metadata('metadata', ancombc_md_factory)

    abc2_output, = use.action(
        use.UsageAction('composition', 'ancombc2'),
        use.UsageInputs(
            table=table,
            metadata=metadata,
            fixed_effects_formula='bodysite + animal',
            reference_levels=["bodysite::tongue", "animal::dog"]
        ),
        use.UsageOutputNames(ancombc2_output='abc2_output')
    )

    abc2_output.assert_output_type('FeatureData[ANCOMBC2Output]')
