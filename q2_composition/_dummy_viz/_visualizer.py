# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import jinja2
import pkg_resources
import os
import q2templates


def hello_world(output_dir: str, input_var: str=None):
    # J_ENV = jinja2.Environment(
    #     loader=jinja2.PackageLoader('q2_composition._dummy_viz', 'assets')
    # )

    # index = J_ENV.get_template('index.html')

    ASSETS = pkg_resources.resource_filename('q2_composition', '_dummy_viz')
    index = os.path.join(ASSETS, 'assets', 'index.html')

    q2templates.render(index, output_dir)

    with open(os.path.join(output_dir, "index.html"), "w") as fh:
        fh.write('')
