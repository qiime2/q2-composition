from pathlib import Path
from collections import OrderedDict

import altair as alt
import pandas as pd
import numpy as np

import qiime2
from q2_composition import DataLoafPackageDirFmt

def _plot_differentials(
        output_dir,
        df,
        category,
        effect_size_column,
        feature_id_column,
        error_column,
        significance_column,
        significance_threshold,
        effect_size_threshold,
        feature_ids):

    if len(df) == 0:
        raise ValueError("No features present in input.")

    if feature_ids is not None:
        df = df.query(f'`{feature_id_column}` in @feature_ids.index')

    df = df[df[significance_column] <= significance_threshold]
    df = df[np.abs(df[effect_size_column]) >= effect_size_threshold]

    if len(df) == 0:
        raise ValueError("No features remaining after applying filters.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_fn = '-'.join(f'{category}-ancombc-barplot.html'.split())
    fig_fp = output_dir / Path(fig_fn)

    # For readability, only the most specific named taxonomy will be
    # included in the y-axis label. The full taxonomy text will be in
    # the tool-tip. Because it's possible that the most specific
    # taxonomic name are not unique, this code simply appends a number
    # to non-unique names. Providing separate labels for ticks, which
    # would avoid this, doesn't seem straight-forward in altair (e.g.,
    # see https://github.com/altair-viz/altair/issues/938).
    y_labels = OrderedDict()
    for i, e in enumerate(df[feature_id_column]):
        fields = [field for field in e.split(';') if field != '__']

        most_specific = fields[-1]
        if most_specific in y_labels:
            y_labels[f"{most_specific} ({i})"] = None
        else:
            y_labels[most_specific] = None
    df['y_label'] = y_labels.keys()

    df['feature'] = [id_.replace(';', ' ') for id_ in df[feature_id_column]]
    df['enriched'] = ["enriched" if x else "depleted"
                      for x in df[effect_size_column] > 0]


    df['error-upper'] = df[effect_size_column] + df[error_column]
    df['error-lower'] = df[effect_size_column] - df[error_column]

    # Normally we would call bars.mark_rule to add standard error marks
    # (opposed to alt.Chart.mark_bar, but I want to color the the standard
    # error marks differently so they stand out against the bars themselves.
    # As far as I can tell, I can only do this by creating two separate charts,
    # so this shared y-axis will be used for both of those.
    shared_y = alt.Y("y_label",
                     title="Feature ID (most specific, if taxonomic)",
                     sort=alt.EncodingSortField(field=effect_size_column,
                                                op="min", order="descending"))

    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X('lfc', title="Log Fold Change (LFC)"),
        y=shared_y,
        tooltip=alt.Tooltip(["feature", effect_size_column,
                             significance_column, error_column,
                             "error-lower", "error-upper"]),
        color=alt.Color('enriched', title="Relative to reference",
                        sort="descending")
    )

    error = alt.Chart(df).mark_rule(color='black').encode(
        x='error-lower',
        x2='error-upper',
        y=shared_y,
    )

    chart = (bars + error).properties()
    chart.save(fig_fp)
    return fig_fp

def da_barplot(output_dir: str,
               data: DataLoafPackageDirFmt,
               effect_size_column: str='lfc',
               feature_id_column: str='id',
               error_column: str='se',
               significance_column: str='q_val',
               significance_threshold: float = 1.0,
               effect_size_threshold: float = 0.0,
               feature_ids: qiime2.Metadata = None):

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_fp = output_dir / Path(f'index.html')

    with open(index_fp, 'w') as index_f:
        index_f.write('<html><body>\n')
        categorical_data = {}
        for e in data.data_slices.iter_views(pd.DataFrame):
            categorical_data[str(e[0]).replace('_slice.csv','')] = e[1]
        columns = [e for e in categorical_data[effect_size_column].columns
                   if e not in '(Intercept)']

        figure_data = []
        for category in columns:
            if category == 'id':
                continue
            df = pd.concat([categorical_data[effect_size_column][feature_id_column],
                            categorical_data[effect_size_column][category],
                            categorical_data[error_column][category],
                            categorical_data[significance_column][category]],
                           keys=[feature_id_column, effect_size_column,
                                 error_column, significance_column],
                           axis=1)
            figure_data.append((category, df))

            try:
                figure_fp = _plot_differentials(
                    output_dir, df, category,
                    effect_size_column=effect_size_column,
                    feature_id_column=feature_id_column,
                    error_column=error_column,
                    significance_column=significance_column,
                    significance_threshold=significance_threshold,
                    effect_size_threshold=effect_size_threshold,
                    feature_ids=feature_ids)
                figure_fn = figure_fp.parts[-1]
                index_f.write(f"<a href=./{figure_fn}>{category}</a><hr>\n")
            except ValueError as e:
                index_f.write(
                    f"Plotting {category} failed with error: {str(e)} <hr>\n")
        index_f.write('</body></html>')

