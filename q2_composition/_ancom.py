import os
import qiime
import pandas as pd
from skbio.stats.composition import ancom as _ancom_
from skbio.stats.composition import clr

from bokeh.plotting import figure, output_file, show, ColumnDataSource, save
from bokeh.models import HoverTool

from numpy import log, sqrt
from scipy.stats import (f_oneway, kruskal, mannwhitneyu,
                         wilcoxon, ttest_ind, ttest_rel, kstest, chisquare,
                         friedmanchisquare)

_sig_tests={'f_oneway': f_oneway,
            'kruskal': kruskal,
            'mannwhitneyu': mannwhitneyu,
            'wilcoxon': wilcoxon,
            'ttest_ind': ttest_ind,
            'ttest_rel': ttest_rel,
            'kstest': kstest,
            'chisquare': chisquare,
            'friedmanchisquare': friedmanchisquare}

_difference_functions = {'subtract' : lambda x, y: x.mean() - y.mean(),
                         'f_statistic' : lambda x: f_oneway(x)[0]}

_transform_functions = {'sqrt' : sqrt,
                        'log' : log,
                        'clr' : clr}

def statistical_tests():
    return _sig_tests.keys()

def difference_functions():
    return _difference_functions.keys()

def transform_functions():
    return _transform_functions.keys()

def ancom(table: pd.DataFrame,
          metadata: qiime.MetadataCategory,
          statistical_test: str = 'f_oneway') -> pd.DataFrame:

    if statistical_test not in statistical_tests():
        raise ValueError("Unknown statistical test: %s" % statistical_test)

    statistical_test = _sig_tests[statistical_test]
    _metadata = metadata.to_series()
    ancom_results, _ = _ancom_(table, _metadata,
                               significance_test=statistical_test)

    return ancom_results


# dictionary to callables
def volcanoplot(output_dir : str,
                table : pd.DataFrame,
                metadata : qiime.MetadataCategory,
                ancom_results : pd.DataFrame,
                transform_function : str = 'clr',
                difference_function: str = None):


    output_file(os.path.join(output_dir, 'index.html'))

    metadata = metadata.to_series()
    cats = list(set(metadata))
    transform_function_name = transform_function
    transform_function = _transform_functions[transform_function]
    transformed_table = table.apply(transform_function, axis=1)

    # set default for difference_function
    if difference_function is None:
        if len(cats) == 2:
            difference_function = 'subtract'
        else:  # len(categories) > 2
            difference_function = 'fstatistic'

    _d_func = _difference_functions[difference_function]
    difference_function = lambda x: _d_func(*[x[metadata==c] for c in cats])

    # effectively doing a groupby operation wrt to the metadata
    fold_change = transformed_table.apply(difference_function, axis=0)

    volcano_results = pd.DataFrame({transform_function_name: fold_change,
                                    'W' : ancom_results.W})
    source = ColumnDataSource(volcano_results)

    hover = HoverTool(
            tooltips=[
                ("Feature ID", "@index"),
                ("(%s fold change, W)" % transform_function_name,
                 "(@" + transform_function_name + ", @W)")
            ]
        )

    p = figure(plot_width=600, plot_height=600, tools=[hover],
           title="ANCOM Volcano Plot")

    p.circle(transform_function_name, 'W',
             size=10, source=source)
    p.xaxis.axis_label = transform_function_name
    p.yaxis.axis_label = 'W'
    save(p)
