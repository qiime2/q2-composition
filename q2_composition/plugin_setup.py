from qiime.plugin import SemanticType, FileFormat, DataLayout
from q2_types import FeatureTable
import q2_composition
from skbio.stats import composition as comp

Composition = SemanticType('Composition', variant_of=FeatureTable.field['content'])

plugin = Plugin(
    name='composition',
    version=q2_composition.__version__,
    website='https://github.com/qiime2/q2-composition',
    package='q2_composition'
)

plugin.register_semantic_type(Frequency)
plugin.register_type_to_data_layout(
    FeatureTable[Composition],
    'feature-table', 1)
