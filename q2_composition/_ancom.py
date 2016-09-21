import os
import qiime
import pandas as pd
from typing import Callable
from skbio.stats.composition import ancom as _ancom_
from skbio.stats.composition import clr

from bokeh.plotting import figure, output_file, show, ColumnDataSource, save
from bokeh.models import HoverTool


def ancom(table: pd.DataFrame,
          metadata: qiime.MetadataCategory,
          significance_test: Callable[[pd.Series],
                                      pd.Series]=None) -> pd.DataFrame:
    _metadata = metadata.to_series()
    ancom_results, _ = _ancom_(table, _metadata,
                               significance_test=significance_test)

    # pack together these objects to minimize bookkeeping
    # for visualizing results
    results = (table, metadata, ancom_results)

    return results


def volcanoplot(output_dir : str,
                ancom_results : (pd.DataFrame,
                                 qiime.MetadataCategory,
                                 pd.DataFrame),
                transform_function : Callable[[pd.Series],
                                              pd.Series]=clr,
                difference_function: Callable[[pd.Series],
                                              pd.Series]=None):

    # unpack the ancom_results
    table, metadata, ancom_results = ancom_results

    output_file(os.path.join(output_dir, 'index.html'))

    metadata = metadata.to_series()
    cats = list(set(metadata))

    transformed_table = table.apply(transform_function, axis=1)

    # set default for difference_function
    if difference_function is None:
        if len(cats) == 2:
            difference_function = \
                lambda x: x[metadata==cats[0]].mean() - x[metadata==cats[1]].mean()
        else:  # len(categories) > 2
            difference_function = f_oneway(*[x[metadata==c] for c in cats])

    fold_change = transformed_table.apply(difference_function, axis=0)
    transform_function_name = transform_function.__name__
    volcano_results = pd.DataFrame({transform_function_name: fold_change,
                                    'W' : ancom_results.W})
    source = ColumnDataSource(volcano_results)

    hover = HoverTool(
            tooltips=[
                ("index", "@index"),
                ("(%s fold change, W)" % transform_function_name,
                 "(@" + transform_function_name + ", @W)")
            ]
        )

    colors =

    p = figure(plot_width=600, plot_height=600, tools=[hover],
           title="ANCOM Volcano Plot")

    p.circle(transform_function_name, 'W',
             size=10, source=source)
    p.xaxis.axis_label = transform_function_name
    p.yaxis.axis_label = 'W'
    save(p)
