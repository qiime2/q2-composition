import qiime
import pandas as pd
from typing import Callable
from skbio.stats.composition import ancom as _ancom_


def ancom(table: pd.DataFrame,
          metadata: qiime.MetadataCategory,
          significance_test: Callable[[pd.Series],
                                      pd.Series]=None) -> pd.DataFrame:
    print('metadata type', type(metadata))
    metadata = metadata.to_series()
    results, _ = _ancom_(table, metadata, significance_test=significance_test)
    return results
