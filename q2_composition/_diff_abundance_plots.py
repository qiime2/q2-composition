# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from pathlib import Path
import urllib.parse
from collections import Counter
import pkg_resources

import altair as alt
import pandas as pd
import numpy as np

import qiime2
from q2_composition import DataLoafPackageDirFmt
import q2templates


def _plot_differentials(
        output_dir,
        df,
        title,
        feature_id_label,
        effect_size_label,
        significance_label,
        error_label,
        feature_ids,
        effect_size_threshold,
        significance_threshold):

    if len(df) == 0:
        raise ValueError("No features present in input.")

    # ensure that all columns are of the types required internally
    df = df.astype({feature_id_label: pd.StringDtype(),
                    error_label: pd.Float64Dtype(),
                    significance_label: pd.Float64Dtype(),
                    effect_size_label: pd.Float64Dtype()})

    if feature_ids is not None:
        df = df.query(f'`{feature_id_label}` in @feature_ids')

    df = df[df[significance_label] <= significance_threshold]
    df = df[np.abs(df[effect_size_label]) >= effect_size_threshold]

    if len(df) == 0:
        raise ValueError("No features remaining after applying filters.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_title = urllib.parse.quote_plus(title)
    fig_fn = Path(f'{safe_title}-ancombc-barplot.html')
    fig_fp = output_dir / fig_fn

    # For readability, only the most specific named taxonomy will be
    # included in the y-axis label. The full taxonomy text will be in
    # the tool-tip. Because it's possible that the most specific
    # taxonomic name are not unique, this code simply prepends a number
    # to names. Providing separate labels for ticks, which
    # would avoid this, doesn't seem straight-forward in altair (e.g.,
    # see https://github.com/altair-viz/altair/issues/938).
    y_labels = []
    seen = Counter()
    for i, e in enumerate(df[feature_id_label]):
        fields = [field for field in e.split(';') if not field.endswith('__')]
        most_specific = fields[-1]
        if most_specific in seen:
            y_labels.append(f"{seen[most_specific]}: {most_specific} *")
        else:
            y_labels.append(most_specific)
        seen[most_specific] += 1
    df['y_label'] = y_labels

    df['feature'] = [id_.replace(';', ' ') for id_ in df[feature_id_label]]
    df['enriched'] = ["enriched" if x else "depleted"
                      for x in df[effect_size_label] > 0]

    df['error-upper'] = df[effect_size_label] + df[error_label]
    df['error-lower'] = df[effect_size_label] - df[error_label]

    # Normally we would call bars.mark_rule to add standard error marks
    # (opposed to alt.Chart.mark_bar, but I want to color the the standard
    # error marks differently so they stand out against the bars themselves.
    # As far as I can tell, I can only do this by creating two separate charts,
    # so this shared y-axis will be used for both of those.
    shared_y = alt.Y("y_label",
                     title="Feature ID (most specific, if taxonomic)",
                     sort=alt.EncodingSortField(field=effect_size_label,
                                                op="min", order="descending"))

    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X('lfc', title="Log Fold Change (LFC)"),
        y=shared_y,
        tooltip=alt.Tooltip(["feature", effect_size_label,
                             significance_label, error_label,
                             "error-lower", "error-upper"]),
        color=alt.Color('enriched', title="Relative to reference",
                        sort="descending")
    )

    error = alt.Chart(df).mark_rule(color='black').encode(
        x='error-lower',
        x2='error-upper',
        y=shared_y,
    )

    chart = (bars + error).properties(title=title)
    chart = chart.configure_legend(
        strokeColor='gray',
        padding=10,
        cornerRadius=10,
    )

    chart.save(fig_fp)
    return fig_fp


def da_barplot(output_dir: str,
               data: DataLoafPackageDirFmt,
               effect_size_label: str = 'lfc',
               feature_id_label: str = 'id',
               error_label: str = 'se',
               significance_label: str = 'q_val',
               significance_threshold: float = 1.0,
               effect_size_threshold: float = 0.0,
               feature_ids: qiime2.Metadata = None):

    # setup for the index.html page
    ASSETS = pkg_resources.resource_filename('q2_composition',
                                             'assets')
    index = Path(ASSETS, 'diff_abundance_plots', 'index.html')

    # collect the user-provided labels for validation
    provided_slice_labels = set([effect_size_label,
                                 significance_label,
                                 error_label])

    slice_data = {}
    for e in data.data_slices.iter_views(pd.DataFrame):
        slice_data[str(e[0]).replace('_slice.csv', '')] = e[1]

    observed_slice_labels = set(slice_data.keys())
    missing_slice_labels = provided_slice_labels - observed_slice_labels
    if len(missing_slice_labels) > 0:
        raise KeyError(
            f"Provide label(s) ({' '.join(missing_slice_labels)}) "
            "are not present in input. Available options are: "
            f"{' '.join(observed_slice_labels)}.")

    # exclude the Intercept column from plots
    column_labels = [e for e in slice_data[effect_size_label].columns
                     if e not in '(Intercept)']

    if feature_id_label not in column_labels:
        raise KeyError(f"Feature id header \"{feature_id_label}\" is not "
                       "present in input. Available options are: "
                       f"{' '.join(column_labels)}.")

    # create figure_data, which contains the cross-slice data for each
    # column of the input dataloaf. some of this logic likely makes sense
    # to move into a transformer which handles the arrangement of data
    # into a multi-index dataframe.
    #
    # if the input dataloaf looks like:
    # slice1: lfc
    # feature-id skin gut
    # f1 0.2 5.4
    # f2 1.2 0.1
    # slice2: q_value
    # feature-id skin gut
    # f1 0.9 0.01
    # f2 0.05 0.8
    #
    # figure_data for a specific category will look like:
    # feature-id lfc q_value
    # f1 0.2 0.9
    # f2 1.2 0.05
    # or:
    # feature-id lfc q_value
    # f1 5.4 0.01
    # f2 0.1 0.8
    figure_data = []
    for column_label in column_labels:
        if column_label == feature_id_label:
            continue
        df = pd.concat(
            [slice_data[effect_size_label][feature_id_label],
             slice_data[effect_size_label][column_label],
             slice_data[error_label][column_label],
             slice_data[significance_label][column_label]],
            keys=[feature_id_label, effect_size_label,
                  error_label, significance_label],
            axis=1)

        try:
            figure_fp = _plot_differentials(
                output_dir, df,
                title=column_label,
                effect_size_label=effect_size_label,
                feature_id_label=feature_id_label,
                error_label=error_label,
                significance_label=significance_label,
                significance_threshold=significance_threshold,
                effect_size_threshold=effect_size_threshold,
                feature_ids=feature_ids)
            figure_fn = figure_fp.parts[-1]
            figure_data.append((True, figure_fn, column_label, None))
        except ValueError as e:
            figure_data.append((False, None, column_label, str(e)))

    context = {
        'figures': figure_data
    }
    q2templates.render(str(index), output_dir, context=context)
