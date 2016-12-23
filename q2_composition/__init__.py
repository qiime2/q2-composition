# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pkg_resources

from ._impute import add_pseudocount
from ._ancom import ancom


__version__ = pkg_resources.get_distribution('q2-composition').version

__all__ = ['add_pseudocount', 'ancom']
