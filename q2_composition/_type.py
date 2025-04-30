# ----------------------------------------------------------------------------
# Copyright (c) 2022-2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin import SemanticType
from q2_types.feature_data import FeatureData


DifferentialAbundance = SemanticType(
    'DifferentialAbundance', variant_of=FeatureData.field['type']
)

ANCOMBC2Output = SemanticType(
    'ANCOMBC2Output', variant_of=FeatureData.field['type']
)
