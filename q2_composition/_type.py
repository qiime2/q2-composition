from qiime.plugin import SemanticType
from q2_types.feature_table import FeatureTable


Composition = SemanticType('Composition',
                           variant_of=FeatureTable.field['content'])
