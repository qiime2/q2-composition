import os
import qiime
import pandas as pd
from skbio.stats.composition import ancom as skbio_ancom
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
    return list(_sig_tests.keys())

def difference_functions():
    return list(_difference_functions.keys())

def transform_functions():
    return list(_transform_functions.keys())

def ancom(output_dir: str,
          table: pd.DataFrame,
          metadata: qiime.MetadataCategory,
          statistical_test: str = 'f_oneway',
          transform_function : str = 'clr',
          difference_function: str = None) -> None:

    index_fp = os.path.join(output_dir, 'index.html')

    if statistical_test not in statistical_tests():
        raise ValueError("Unknown statistical test: %s" % statistical_test)

    statistical_test = _sig_tests[statistical_test]
    ancom_results = skbio_ancom(table,
                                metadata.to_series(),
                                significance_test=statistical_test)
    # scikit-bio 0.4.2 returns a single tuple from ancom, and scikit-bio 0.5.0
    # returns two tuples. We want to support both scikit-bio versions, so we
    # tuplize ancom_result to support both. Similarly, the "reject" column
    # was renamed in scikit-bio 0.5.0, so we apply a rename here (which does
    # nothing if a column called "reject" isn't found).
    ancom_results = qiime.core.util.tuplize(ancom_results)
    ancom_results[0].sort_values(by='W', ascending=False)
    ancom_results[0].rename(columns={'reject': 'Reject null hypothesis'},
                            inplace=True)

    ancom_results[0].to_csv(os.path.join(output_dir, 'ancom.csv'),
                            header=True, index=True)

    _volcanoplot(output_dir, table, metadata, ancom_results[0],
                 transform_function, difference_function)

    significant_features = ancom_results[0][
        ancom_results[0]['Reject null hypothesis']]

    with open(index_fp, 'w') as index_f:
        index_f.write('<html><body>\n')
        index_f.write('<a target="_blank" href="volcano-plot.html">'
                      'Volcano plot</a>\n')
        index_f.write('<h1>ANCOM statistical results</h1>\n')
        index_f.write('<a href="ancom.csv">Download as CSV</a><br>\n')
        index_f.write(significant_features['W'].to_frame().to_html())
        if len(ancom_results) == 2:
            ancom_results[1].to_csv(os.path.join(output_dir, 'percent-abundances.csv'),
                                    header=True, index=True)
            index_f.write('<h1>Percentile abundances of features by group</h1>\n')
            index_f.write('<a href="percent-abundances.csv">Download as CSV</a><br>\n')
            index_f.write(ancom_results[1].loc[significant_features.index].to_html())
        index_f.write('</body></html>\n')

def _volcanoplot(output_dir, table, metadata, ancom_results,
                 transform_function, difference_function) -> None:
    output_file(os.path.join(output_dir, 'volcano-plot.html'))

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
            difference_function = 'f_statistic'

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
