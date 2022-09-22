# ----------------------------------------------------------------------------
# Copyright (c) 2022-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import pkg_resources

import qiime2


def _get_data_from_tests(path):
    return pkg_resources.resource_filename('q2_composition.tests',
                                           os.path.join('data', path))


def ancom_md_factory():
    return qiime2.Metadata.load(
        _get_data_from_tests('sample-md-ancom.tsv'))


def ancom_table_factory():
    return qiime2.Artifact.load(
        _get_data_from_tests('table-ancom.qza'))


def ancombc_single_formula_no_group(use):
    table = use.init_artifact('table', ancom_table_factory)
    metadata = use.init_metadata('metadata', ancom_md_factory)

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

def ancombc_single_formula_group(use):
    table = use.init_artifact('table', ancom_table_factory)
    metadata = use.init_metadata('metadata', ancom_md_factory)

    dataloaf, = use.action(
        use.UsageAction('composition', 'ancombc'),
        use.UsageInputs(
            table=table,
            metadata=metadata,
            formula='bodysite',
            group='month',
        ),
        use.UsageOutputNames(
            differentials='dataloaf'
        )
    )

    dataloaf.assert_output_type('FeatureData[DifferentialAbundance]')

def ancombc_multi_formula_group_with_level_ordering(use):
    table = use.init_artifact('table', ancom_table_factory)
    metadata = use.init_metadata('metadata', ancom_md_factory)

    dataloaf, = use.action(
        use.UsageAction('composition', 'ancombc'),
        use.UsageInputs(
            table=table,
            metadata=metadata,
            formula='bodysite + month',
            group='bodysite',
            level_ordering=["bodysite::tongue"]
        ),
        use.UsageOutputNames(
            differentials='dataloaf'
        )
    )

    dataloaf.assert_output_type('FeatureData[DifferentialAbundance]')
