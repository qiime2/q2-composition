from qiime.plugin import SemanticType, FileFormat, DataLayout
from q2_types import FeatureTable
import q2_composition


Composition = SemanticType('Composition',
                           variant_of=FeatureTable.field['content'])

plugin = Plugin(
    name='composition',
    version=q2_composition.__version__,
    website='https://github.com/qiime2/q2-composition',
    package='q2_composition'
)





