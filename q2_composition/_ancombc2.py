# ----------------------------------------------------------------------------
# Copyright (c) 2016-2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import biom
import formulaic
from formulaic.parser.types import Token
import importlib.resources
import logging
import pandas as pd
import os
from pathlib import Path
from rpy2.robjects.conversion import Converter
import rpy2.robjects.conversion as conversion
from rpy2.robjects.packages import importr
from rpy2.robjects.methods import RS4
from rpy2.robjects import pandas2ri, default_converter
import rpy2.robjects as ro
from rpy2.rinterface import NULL as RNULL
from rpy2.rinterface_lib.callbacks import logger as rpy2_logger
import shutil

import qiime2
from qiime2.metadata import NumericMetadataColumn, CategoricalMetadataColumn
from qiime2.plugin.util import transform
from typing import Union

from q2_composition._format import (
    ANCOMBC2OutputDirFmt, ANCOMBC2SliceMapping, DataLoafPackageDirFmt
)


r_base = importr('base')
r_stats = importr('stats')
r_phyloseq = importr('phyloseq')
r_ancombc2 = importr('ANCOMBC')

rpy2_logger.setLevel(logging.ERROR)


def ancombc2(
    table: biom.Table,
    metadata: qiime2.Metadata,
    fixed_effects_formula: str,
    random_effects_formula: str | None = None,
    reference_levels: list[str] | None = None,
    p_adjust_method: str = 'holm',
    prevalence_cutoff: float = 0.1,
    group: str | None = None,
    structural_zeros: bool = False,
    asymptotic_cutoff: bool = False,
    alpha: float = 0.05,
    diff_robust: bool = False,
    num_processes: int = 1,
) -> ANCOMBC2OutputDirFmt:
    '''
    Wraps the `ancombc2` R function from the ANCOMBC package.

    Parameters
    ----------
    See plugin_setup.py for parameter descriptions.

    Returns
    -------
    ANCOMBC2OutputDirFmt
        A directory format containing the ANCOMBC2 model's per-feature
        statistics and per-feature structural zero designations if
        `structural_zeros` is set.
    '''
    if structural_zeros and group is None:
        msg = (
           'The structural zeros option was enabled but no group variable '
           'was provided. Strucutural zeros are detected according to some '
           'grouping, so a group variable must be provided.'
        )
        raise ValueError(msg)

    # process formulae
    fixed_effects_formula = _process_formula(fixed_effects_formula, metadata)
    if random_effects_formula is not None:
        random_effects_formula = _process_formula(
            random_effects_formula, metadata
        )

    # construct phyloseq object
    r_phyloseq_object = _create_phyloseq_object(
        table, metadata, reference_levels
    )

    # call ancombc2
    if group is not None:
        group = r_base.make_names(group)[0]

    with conversion.localconverter(default_converter + _get_none_converter()):
        output = r_ancombc2.ancombc2(
            data=r_phyloseq_object,
            fix_formula=fixed_effects_formula,
            rand_formula=random_effects_formula,
            p_adj_method=p_adjust_method,
            prv_cut=prevalence_cutoff,
            group=group,
            struc_zero=structural_zeros,
            alpha=alpha,
            neg_lb=asymptotic_cutoff,
            n_cl=num_processes,
            verbose=True,
        )

    # extract data of interest from the returned R list
    model_statistics = output[output.names.index('res')]
    with (ro.default_converter + pandas2ri.converter).context():
        model_statistics_df = ro.conversion.get_conversion().rpy2py(
            model_statistics
        )

    slices = _split_into_slices(model_statistics_df, diff_robust)

    structural_zeros = output[output.names.index('zero_ind')]
    if structural_zeros != RNULL:
        with (ro.default_converter + pandas2ri.converter).context():
            structural_zeros_df = ro.conversion.get_conversion().rpy2py(
                structural_zeros
            )

        structural_zeros_df = _process_structural_zeros(structural_zeros_df)
        slices['structural_zeros'] = structural_zeros_df

    # rename columns to original names
    slices = _rename_variables_post(slices, metadata)

    # split categorical variables from levels and annotate references
    slices = _process_categorical_variables(slices, metadata, table)

    return transform(data=slices, to_type=ANCOMBC2OutputDirFmt)


def _process_formula(formula: str, metadata: qiime2.Metadata) -> str:
    '''
    Processes and validates `formula`. Variables in `formula` are ensured to
    be present in `metadata` and are converted to valid R identifiers as
    needed.

    Parameters
    ----------
    formula : str
        The formula to be processed.
    metadata : qiime2.Metadata
        The per-sample metadata.

    Returns
    -------
    str
        The validated formula with variables renamed to valid R identifiers
        as needed.

    Raises
    ------
    ValueError
        If an unexpected token type is encountered while parsing `formula`.
    '''
    formula = _rename_variables_pre(formula, metadata)

    # parse formula into tokens
    parser = formulaic.parser.parser.DefaultFormulaParser(
        include_intercept=False
    )
    tokens = list(parser.get_tokens(formula))

    # validate formula
    _validate_formula(tokens, metadata)

    # convert names
    renamed_tokens = []
    for token in tokens:
        if token.kind == Token.Kind.NAME:
            r_identifier = r_base.make_names(str(token))[0]
            renamed_tokens.append(str(r_identifier))
        else:
            renamed_tokens.append(str(token))

    # reconstruct formula
    # NOTE: whitespace may differ from the original formula, but this should
    # not affect validity or semantics
    processed_formula = ' '.join(renamed_tokens)

    return processed_formula


def _rename_variables_pre(formula: str, metadata: qiime2.Metadata) -> str:
    '''
    Renames all variables in the formula to valid R identifiers as necessary.

    Parameters
    ----------
    formula : str
        The formula string.
    metadata : qiime2.Metadata
        The per-sample metadata.

    Returns
    -------
    str
        The formula with renamed variables where necessary.
    '''
    for column in metadata.columns:
        r_name = r_base.make_names(column)[0]
        formula = formula.replace(column, r_name)

    return formula


def _validate_formula(tokens: list[Token], metadata: qiime2.Metadata) -> None:
    '''
    Asserts that the formula variables in `tokens` are present in the
    metadata. Also ensures that a dependent variable is not present in the
    formula.

    Parameters
    ----------
    tokens : list[Token]
        A list of token parsed from the formula.
    metadata : qiime2.Metadata
        The per-sample metadata.

    Raises
    ------
    ValueError
        If the formula is empty.
    ValueError
        If a dependent variable is specified in the formula.
    ValueError
        If one of the variables in `variables` is not a column in `metadata`.
    '''
    if not tokens:
        msg = (
            'A formula was found to be empty. An empty formula, whether for '
            'fixed effects or random effects is not valid. If you do not '
            'wish to specify a random effects formula simply do not provide '
            'that parameter.'
        )
        raise ValueError(msg)

    if '~' in tokens:
        msg = (
            'A "~" symbol was detected in your formula. The dependent '
            'variable should not be included in the formula.'
        )
        raise ValueError(msg)

    variables = [t for t in tokens if t.kind == Token.Kind.NAME]

    unique_variables = list(set(variables))

    for variable in unique_variables:
        variable = str(variable)
        variable = _get_original_variable_name(variable, metadata)
        try:
            metadata.get_column(variable)
        except ValueError:
            msg = (
                f'The "{variable}" variable was not found in your metadata. '
            )
            raise ValueError(msg)


def _get_original_variable_name(
    variable: str, metadata: qiime2.Metadata
) -> str:
    '''
    Returns the original spelling of `variable` as it exists in the metadata,
    whether or not it was renamed when it was ensured to be a valid R
    identifier.

    Parameters
    ----------
    variable : str
        The variable name for which to get the original spelling.

    Returns
    -------
    str
        The original spelling of `variable`.
    '''
    for column in metadata.columns:
        r_name = r_base.make_names(column)[0]
        if r_name == variable:
            return column

    return variable


def _create_phyloseq_object(
    table: biom.Table,
    metadata: qiime2.Metadata,
    reference_levels: list[str] | None = None
) -> RS4:
    '''
    Create an R phyloseq object that contains the feature table and metadata.

    Parameters
    ----------
    table : biom.Table
        The feature table to be wrapped in a phyloseq object.
    metadata : qiime2.Metadata
        The metadata to be wrapped in a phyloseq object.
    reference_levels : list[str] or None
        The desired reference levels of each of the categorical metadata
        variables included in the ANCOMBC2 formula. Specified as a list of
        "column_name::column_value" where "column_value" is the desired
        reference level of the "column_name" column.

    Returns
    -------
    RS4
        An R phyloseq object containing the feature table and metadata.
    '''
    # convert the feature table to an R matrix with rownames=features and
    # colnames=samples
    table_df = table.to_dataframe(dense=True)

    with (ro.default_converter + pandas2ri.converter).context():
        r_table_df = ro.conversion.get_conversion().py2rpy(table_df)

    r_matrix = r_base.as_matrix(r_table_df)

    # construct phyloseq OTU table
    r_phyloseq_otu_table = r_phyloseq.otu_table(r_matrix, taxa_are_rows=True)

    # construct phyloseq sample (meta)data
    r_metadata_df = _convert_metadata(metadata, reference_levels)
    r_phyloseq_sample_data = r_phyloseq.sample_data(r_metadata_df)

    # wrap table and metadata into phyloseq container object
    return r_phyloseq.phyloseq(r_phyloseq_otu_table, r_phyloseq_sample_data)


def _convert_metadata(
    metadata: qiime2.Metadata,
    reference_levels: list[str] | None = None
) -> RS4:
    '''
    Converts a `qiime2.Metadata` object into an R dataframe. The
    qiime2 metadata column types are converted into their R equivalents and
    categorical columns are releveled according to `reference_levels`.

    Parameters
    ----------
    metadata : qiime2.Metadata
        The sample metadata.
    reference_levels : list[str] or None
        The desired reference levels of each of the categorical metadata
        variables included in the model formula. Specified as a list of
        "column_name::column_value" where "column_value" is the desired
        reference level of the "column_name" column.

    Returns
    -------
    RS4
        The metadata in an R dataframe.

    Raises
    ------
    ValueError
        Under various conditions: unrecognized qiime2.Metadata column types,
        nonexistent metadata columns, nonexistent reference levels,
        specification of a reference level for a non-categorical variable
        level.

    '''
    # convert metadata to R dataframe
    df = metadata.to_dataframe()
    with (ro.default_converter + pandas2ri.converter).context():
        r_df = ro.conversion.get_conversion().py2rpy(df)

    # ensure columns are renamed to R's fancy
    r_base.colnames(r_df)[:] = r_base.make_names(r_base.colnames(r_df))

    # convert column types
    for column_name in metadata.columns:
        column = metadata.get_column(column_name)
        r_column_name = r_base.make_names(column_name)[0]
        col_index = r_df.colnames.index(r_column_name)

        if isinstance(column, CategoricalMetadataColumn):
            r_df[col_index] = r_base.as_factor(r_df.rx2[r_column_name])
        elif isinstance(column, NumericMetadataColumn):
            r_df[col_index] = r_base.as_numeric(r_df.rx2[r_column_name])
        else:
            msg = (
                f'An unrecognized metadata column type ({type(column)}) was '
                'encountered while translating the metadata into R.'
            )
            raise ValueError(msg)

    # relevel categorical metadata columns
    if reference_levels is not None:
        columns_seen = []
        for level_spec in reference_levels:
            column_name, reference_level = _extract_column_reference_level(
                level_spec
            )

            if column_name not in metadata.columns:
                msg = (
                    f'The "{column_name}" column that was specified in the '
                    'column-reference pair was not found in the metadata.'
                )
                raise ValueError(msg)

            column = metadata.get_column(column_name)
            if isinstance(column, NumericMetadataColumn):
                msg = (
                    'Can not specify a reference level for the numeric '
                    f'metadata column {column_name}.'
                )
                raise ValueError(msg)

            column_levels = metadata.to_dataframe()[column_name].unique()
            if reference_level not in column_levels:
                msg = (
                    f'The specified reference level "{reference_level}" was '
                    f'not found in the "{column_name}" metadata column.'
                )
                raise ValueError(msg)

            if column_name in columns_seen:
                msg = (
                    'Only specify a reference level for a given categorical '
                    f'column once. The "{column_name}" column was specified '
                    'multiple times.'
                )
                raise ValueError(msg)

            columns_seen.append(column_name)

            r_column_name = r_base.make_names(column_name)[0]
            r_df[r_df.colnames.index(r_column_name)] = r_stats.relevel(
                r_df.rx2[r_column_name], ref=reference_level
            )

    return r_df


def _extract_column_reference_level(
    level_specification: str
) -> tuple[str, str]:
    '''
    Extract the column name and reference level value from a
    column name/reference level pair. Such a pair is in the format
    "column_name::column_value".

    Parameters
    ----------
    level_specification : str
        The column name/column value pair indicating the desired reference
        level. Looks like `column_name::column_value`.

    Returns
    -------
    tuple[str]
        A tuple containing (column_name, reference_level) values that are
        extracted from the level specification.
    '''
    level_spec_fields = tuple(level_specification.split('::'))

    if len(level_spec_fields) < 2:
        msg = (
            f'No reference level was detected for the {level_specification} '
            'column-reference pair. Make sure to separate the column name and '
            'reference level with "::".'
        )
        raise ValueError(msg)
    elif len(level_spec_fields) > 2:
        msg = (
            'More than one reference level were detected for the '
            f'{level_specification} column-reference pair. The expected '
            'format is "column_name::reference_level". Make sure that "::" '
            'occurs only once in each column-reference pair.'
        )
        raise ValueError(msg)

    return level_spec_fields


def _get_none_converter() -> Converter:
    '''
    Creates an rpy2.robjects.conversion.Converter object that will convert
    any python `None` to an R `NULL` used within its context handler.

    Returns
    -------
    Converter
        The rpy2 converter object.
    '''
    converter = Converter("None Converter")
    converter.py2rpy.register(type(None), lambda _: RNULL)

    return converter


def _split_into_slices(
    model_statistics: pd.DataFrame, diff_robust: bool = False
) -> ANCOMBC2SliceMapping:
    '''
    Splits the single-table model statistics output by ANCOMBC2 into per-slice
    dataframes. See the `ANCOMBC2OutputDirFmt` for a description of the slices.

    Parameters
    ----------
    model_statistics : pd.DataFrame
        A dataframe containing all of the above detailed columns for each
        variable in the model.
    diff_robust : bool
        Whether to parse the "diff_robust" columns from the ANCOMBC2 output.

    Returns
    -------
    ANCOMBC2SliceMapping
        A dictionary mapping the name of the slice to the slice's columns.
    '''
    model_statistics = model_statistics.copy(deep=True)
    slices = ANCOMBC2SliceMapping()
    slice_names = list(ANCOMBC2OutputDirFmt.REQUIRED_SLICES)

    if not diff_robust:
        diff_robust_columns = model_statistics.columns[
            model_statistics.columns.str.startswith('diff_robust_')
        ]
        model_statistics.drop(diff_robust_columns, axis=1, inplace=True)
    else:
        slice_names.append('diff_robust')
        # sort slice names by decreasing length so that a slice name that is
        # a prefix of another can not grab prefix-containing columns
        slice_names.sort(key=lambda name: len(name), reverse=True)

    for slice_name in slice_names:
        # subset model statistics to columns from slice of interest
        slice_columns = model_statistics.columns[
            model_statistics.columns.str.startswith(f'{slice_name}_')
        ]
        slice_df = model_statistics[slice_columns]

        # remove processsed columns to solve prefix issue
        model_statistics.drop(slice_columns, axis=1, inplace=True)

        # include taxon column in each slice
        slice_df.insert(0, 'taxon', model_statistics['taxon'])

        # remove slice prefix from column names where present
        slice_df = slice_df.rename(
            lambda name: name.removeprefix(f'{slice_name}_'), axis='columns'
        )

        slices[slice_name] = slice_df

    return slices


def _rename_variables_post(
    slices: ANCOMBC2SliceMapping, metadata: qiime2.Metadata
) -> ANCOMBC2SliceMapping:
    '''
    Renames any variables in the ANCOMBC2 output that were renamed to their
    equivalent R-style identifiers back to their original names.

    Parameters
    ----------
    slices : ANCOMBC2SliceMapping
        The raw slices as transformed from ANCOMBC2's output.
    metadata : qiime2.Metadata
        The per-sample metadata containing the original variable names.

    Returns
    -------
    ANCOMBC2SliceMapping
        The slices with any R-style identifiers renamed.
    '''
    # create a mapping from r-style identifiers to original identifiers
    r_names = {}
    for column in metadata.columns:
        r_name = r_base.make_names(column)[0]
        r_names[r_name] = column

    # rename any columns that contain an r-style identifier
    for slice_df in slices.values():
        for slice_column in slice_df.columns:
            for r_name, name in r_names.items():
                if slice_column.startswith(r_name):
                    renamed = name + slice_column.removeprefix(r_name)
                    slice_df.rename(
                        {slice_column: renamed}, axis='columns', inplace=True
                    )

    return slices


def _process_categorical_variables(
    slices: ANCOMBC2SliceMapping, metadata: qiime2.Metadata, table: biom.Table
) -> ANCOMBC2SliceMapping:
    '''
    Renames categorical variable columns in each slice in order to make the
    distinction between a metadata variable and its given level clear, by
    separating the two as follows: 'some-variable::some-level'.

    Each column is also annotated with its variable, level, and reference
    level.

    Parameters
    ----------
    slices : ANCOMBC2SliceMapping
        The raw slices as transformed from the ANCOMBC2 method's output.
    metadata : qiime2.Metadata
        The per-sample metadata that contains information about each variable
        present in the ANCOMBC2 output.
    table : The inputted feature table.

    Returns
    -------
    ANCOMBC2SliceMapping
        The slices with any categorical variable columns renamed and annotated
        with their reference levels as explained above.
    '''
    # restructure categorical variable columns into 'variable::level' format
    for slice_df in slices.values():
        for slice_column in slice_df.columns:
            if _is_categorical(slice_column, metadata):
                variable, level = _parse_variable_and_level(
                    slice_column, metadata
                )
                slice_df.rename(
                    {slice_column: variable + '::' + level},
                    axis='columns',
                    inplace=True
                )

    # deduce reference level of each categorical variable and annotate columns
    reference_levels = _deduce_reference_levels(slices['lfc'], metadata, table)

    for slice_name, slice_df in slices.items():
        for column in slice_df.columns:
            if _is_categorical(column, metadata):
                variable, level = _parse_variable_and_level(column, metadata)
                slice_df[column].attrs['variable'] = variable
                slice_df[column].attrs['level'] = level

                # the structural zeros slice does not have reference levels
                if slice_name != 'structural_zeros':
                    reference_level = reference_levels[variable]
                    slice_df[column].attrs['reference'] = reference_level

    return slices


def _is_categorical(column: str, metadata: qiime2.Metadata) -> bool:
    '''
    Determines whether `column` refers to a categorical variable.

    Parameters
    ----------
    column : str
        The column name as returned by ANCOMBC2. If in reference to a
        categorical column then a level will be appended to the variable name.
    metadata : qiime2.Metadata
        The per-sample metadata.

    Returns
    -------
    bool
        Whether `column` refers to a categorical variable.
    '''
    # reverse sort to handle md columns that are prefixes of other md columns
    for md_column in sorted(list(metadata.columns), reverse=True):
        if column.startswith(md_column):
            if isinstance(
                metadata.get_column(md_column), CategoricalMetadataColumn
            ):
                return True

            return False

    return False


def _parse_variable_and_level(
    column: str, metadata: qiime2.Metadata
) -> tuple[str, str]:
    '''
    Parses `column` into its variable name and level name components. Assumes
    that `column` refers to a categorical variable.

    Parameters
    ----------
    column : str
        The model statistics column name that is a concatenation of a variable
        name and a level name.
    metadata : qiime2.Metadata
        The per-sample metadata.

    Returns
    -------
    tuple[str, str]
        The variable name and the level name.

    Raises
    ------
    ValueError
        If `column` does not refer to categorical variable.
    ValueError
        If the categorical variable referenced by `column`
        was not found in the metadata.
    '''
    # reverse sort to handle md columns that are prefixes of other md columns
    for md_column in sorted(metadata.columns, reverse=True):
        if column.startswith(md_column):
            if not isinstance(
                metadata.get_column(md_column), CategoricalMetadataColumn
            ):
                msg = (
                    f'The {column} column does not refer to a categorical '
                    'variable.'
                )
                raise ValueError(msg)

            variable = md_column
            if column[len(variable):len(variable) + 2] == '::':
                level = column[len(variable) + 2:]
            else:
                level = column[len(variable):]

            return variable, level

    msg = (
        f'The categorical variable referenced by {column} was not found in '
        'the metadata.'
    )
    raise ValueError(msg)


def _deduce_reference_levels(
    slice_df: pd.DataFrame, metadata: qiime2.Metadata, table: biom.Table
) -> dict[str, str]:
    '''
    Determines which reference level was selected for each categorical
    variable in `slice_df`. Only one slice is needed because each slice
    contains the same variables.

    Note that we could be more informed by passing any reference levels
    specified by the user into this function, however, because the user is not
    required to specify a reference level for each (or any) categorical
    variable in the model we must still in some circumstances empircally
    determine which levels were set as reference by ANCOMBC2. So for
    simplicity's sake we just do so for all variables.

    Parameters
    ---------
    slice_df : pd.DataFrame
        A slice of ANCOMBC2 output.
    metadata : qiime2.Metadata
        The per-sample metadata, used to establish the set of all levels for
        each categorical variable.
    table : biom.Table
        The inputted feature table. Used to subset the levels of the
        categorical variables to those that were processed by ANCOMBC2 (which
        are those that are represented in the table).

    Returns
    -------
    dict[str, str]
        A mapping from variable to its reference level.

    Raises
    ------
    ValueError
        If the number of deduced reference levels is not equal to one.
    '''
    reference_levels_map = {}
    for column in slice_df.columns:
        # a column is categorical if has been processed into the
        # 'variable::level' format
        if _is_categorical(column, metadata):
            variable, _ = _parse_variable_and_level(column, metadata)

            if variable in reference_levels_map:
                continue

            # find all levels present in the slice for this variable; the
            # remaining unseen level in the table is the reference level
            non_reference_levels = {
                 _parse_variable_and_level(c, metadata)[1]
                 for c in slice_df.columns if variable in c
            }

            # get unique levels of variable represented in table
            metadata_df = metadata.to_dataframe()
            table_levels = metadata_df.loc[
                metadata_df.index.isin(table.ids())
            ][variable].dropna().unique()

            reference_levels = set(table_levels) - non_reference_levels
            if len(reference_levels) != 1:
                msg = (
                    'Deduced more than one or no reference levels. The number '
                    'of variable levels reported by ANCOMBC2 is not exactly '
                    'one less than the number of levels present in the '
                    'feature table. The deduced reference levels are: '
                    f'{reference_levels}.'
                )
                raise ValueError(msg)

            reference_level, = reference_levels
            reference_levels_map[variable] = reference_level

    return reference_levels_map


def _process_structural_zeros(
    structural_zeros_df: pd.DataFrame
) -> pd.DataFrame:
    '''
    Reformats the column names in the structural zeros output in a similiar
    fashion to how column names are reformatted during the slice splitting
    of the model statistics.

    Incoming column names look like:
        structural_zero (some-variable-name = some-level-name)

    and are reformatted to:
        some-variable-namesome-level-name

    This concatenation is meant to model what ANCOMBC2 does with the model
    statistics columns.

    Note that only categorical columns are present in the structural zeros
    output.

    Parameters
    ----------
    structural_zeros_df : pd.DataFrame
        The raw structural zeros table as returned by ANCOMBC2.

    Returns
    -------
    pd.DataFrame
        The structural zeros table with columns renamed.
    '''
    def _rename(column: str) -> str:
        column = column.removeprefix('structural_zero ')
        column = column.removeprefix('(').removesuffix(')')
        column = column.replace(' = ', '')
        return column

    return structural_zeros_df.rename(lambda c: _rename(c), axis='columns')

def ancombc2_visualizer(
    output_dir: str,
    data: Union[ANCOMBC2OutputDirFmt, DataLoafPackageDirFmt],
    taxonomy: pd.DataFrame = None
):
    '''
    Generates a diverging barplot of per-feature log-fold change values. If
    a taxonomy is provided, an interactive taxonomy tree can be used to subset
    the features displayed in th barplot.

    Parameters
    ----------
    output_dir : str
        The path to the data/ directory in the to-be-created visualization.
    data : ANCOMBC2SliceMapping
        The ancombc2 slice data to visualize
    taxonomy : pd.DataFrame | None
        The taxonomy associated with the features present in `slices`.
        Optional.
    '''
    slices_path = Path(output_dir) / 'slices'
    os.mkdir(slices_path)
    shutil.copytree(str(data), slices_path, dirs_exist_ok=True)

    dist_dir = (
        importlib.resources.files('q2_composition') /
        '_ancombc2_visualizer' / 'dist'
    )
    shutil.copytree(Path(str(dist_dir)), output_dir, dirs_exist_ok=True)

    if taxonomy is not None:
        # subset taxonomy to only features present in the ancombc2 slices
        slice_map = transform(data=data, to_type=ANCOMBC2SliceMapping)
        try:
            slice_feature_ids = slice_map['lfc']['taxon'].unique()
        except KeyError:
            slice_feature_ids = slice_map['lfc']['id'].unique()
        taxonomy = taxonomy[taxonomy.index.isin(slice_feature_ids)]

        if len(taxonomy) == 0:
            msg = (
                'No features remained in your taxonomy after intersecting '
                'it with the features present in your ANCOMBC2 data. Ensure '
                'that the taxonomy provided contains the features present in '
                'the ANCOMBC2 slices.'
            )
            raise ValueError(msg)

        taxonomy_fp = Path(output_dir) / 'taxonomy.tsv'
        taxonomy.to_csv(str(taxonomy_fp), sep='\t')
