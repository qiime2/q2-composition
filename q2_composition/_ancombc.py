# ----------------------------------------------------------------------------
# Copyright (c) 2016-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import subprocess
import tempfile
import pandas as pd
import os
import formulaic

import qiime2
from qiime2.metadata import NumericMetadataColumn, CategoricalMetadataColumn

from ._format import DataLoafPackageDirFmt


def run_commands(cmds, verbose=True):
    if verbose:
        print('Running external command line application(s). This may print'
              ' messages to stdout and/or stderr.')
        print('The command(s) being run are below. These commands cannot be'
              ' manually re-run as they will depend on temporary files that no'
              ' longer exist.')
    for cmd in cmds:
        if verbose:
            print('\nCommand:', end=' ')
            print(' '.join(cmd), end='\n\n')
        subprocess.run(cmd, check=True)


def ancombc(table: pd.DataFrame, metadata: qiime2.Metadata, formula: str,
            p_adj_method: str = 'holm', prv_cut: float = 0.1, lib_cut: int = 0,
            reference_levels: str = None, neg_lb: bool = False,
            tol: float = 1e-05, max_iter: int = 100, conserve: bool = False,
            alpha: float = 0.05) -> DataLoafPackageDirFmt:

    return _ancombc(
        table=table,
        metadata=metadata,
        formula=formula,
        p_adj_method=p_adj_method,
        prv_cut=prv_cut,
        lib_cut=lib_cut,
        reference_levels=reference_levels,
        neg_lb=neg_lb,
        tol=tol,
        max_iter=max_iter,
        conserve=conserve,
        alpha=alpha,
    )


# utility functions for formula parsing and column validation
def _parse_terms(formula):
    parse = formulaic.parser.parser.DefaultFormulaParser(
        include_intercept=False)
    terms = parse.get_ast(formula=formula).flatten()
    formula_terms = _leaf_collector(terms)
    return formula_terms


def _leaf_collector(term):
    if isinstance(term, formulaic.parser.types.Token):
        return [str(term)]

    if type(term) is not list:
        return []

    return _leaf_collector(term[1]) + _leaf_collector(term[2])


def _ancombc(table, metadata, formula, p_adj_method, prv_cut, lib_cut,
             reference_levels, neg_lb, tol, max_iter, conserve, alpha):

    meta = metadata.to_dataframe()

    # error on IDs found in table but not in metadata
    missing_ids = table.index.difference(meta.index).values

    if missing_ids.size > 0:
        raise KeyError('Not all samples present within the table were found in'
                       ' the associated metadata file. Please make sure that'
                       ' all samples in the FeatureTable are also present in'
                       ' the metadata.'
                       ' Sample IDs not found in the metadata: %s'
                       % missing_ids)

    # column validation for the formula parameter
    formula_terms = _parse_terms(formula=formula)
    for term in formula_terms:
        metadata.get_column(term)

    # Pulling default reference levels based on formula terms
    if reference_levels is None:
        reference_levels = []
        for term in formula_terms:
            if isinstance(metadata.get_column(term),
                          CategoricalMetadataColumn):
                term_alpha_value = (metadata.get_column(term)
                                    .to_dataframe()
                                    .sort_values(term)[term][0])
                ref_level_pair = term + '::' + str(term_alpha_value)
                reference_levels.append(ref_level_pair)

    if isinstance(reference_levels, str):
        reference_levels = [reference_levels]

    # column & level validation for the reference_levels parameter
    reference_level_columns = []
    for i in reference_levels:
        column = i.split('::')[0]
        level_value = i.split('::')[1]
        # check that multiple values for the same column aren't provided
        if column in reference_level_columns:
            raise ValueError('Multiple `reference_level` pairs with the same'
                             ' column were provided. Please only include one'
                             ' `reference_level` pair per column from the'
                             ' terms in the formula. `reference_level` column'
                             ' with multiple groups that was included:'
                             ' "%s"' % term)
        else:
            reference_level_columns.append(column)

        # check that reference_level columns are present in the metadata
        ref_column = metadata.get_column(column)

        # check that each chosen column contains discrete values
        if isinstance(ref_column, NumericMetadataColumn):
            raise TypeError('One of the `reference_levels` columns is not'
                            ' a categorical Metadata column. Please make'
                            ' sure that all chosen reference level columns'
                            ' are categorical, and not numeric.'
                            ' Non-categorical column selected:'
                            ' %s' % column)

        if level_value not in pd.unique(meta[column].values):
            raise ValueError('Value provided in `reference_levels`'
                             ' parameter not found in the associated'
                             ' column within the metadata. Please make'
                             ' sure each column::value pair is present'
                             ' within the metadata file.'
                             ' \n\n'
                             ' column::value pair with a value that was'
                             ' not found: "%s"' % i)

        # check that reference_level columns are also in the formula
        if column not in formula_terms:
            raise ValueError('`reference_levels` column "%s" was not found'
                             ' within the `formula` terms.' % column)

        # check that IDs associated with chosen reference level(s) are
        # present within the input table
        level_value_idx = meta.index[meta[column] == level_value]
        table_idx = table.index

        if level_value_idx.intersection(table_idx).empty:
            raise ValueError('Value provided in `reference_levels`'
                             ' parameter not associated with any IDs'
                             ' in the feature table. Please make sure'
                             ' the value(s) selected in each'
                             ' column::value pair are associated with'
                             ' IDs present in the feature table.'
                             ' \n\n'
                             ' Value not associated with any IDs in'
                             ' the table: "%s"' % level_value,
                             ' IDs not found in table:'
                             ' "%s"' % level_value_idx)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        biom_fp = os.path.join(temp_dir_name, 'input.biom.tsv')
        meta_fp = os.path.join(temp_dir_name, 'input.map.txt')

        table.to_csv(biom_fp, sep='\t', header=True)
        meta.to_csv(meta_fp, sep='\t', header=True)

        output_loaf = DataLoafPackageDirFmt()

        cmd = ['run_ancombc.R',
               '--inp_abundances_path', biom_fp,
               '--inp_metadata_path', meta_fp,
               '--formula', str(formula),
               '--p_adj_method', p_adj_method,
               '--prv_cut', str(prv_cut),
               '--lib_cut', str(lib_cut),
               '--reference_levels', str(reference_levels),
               '--neg_lb', str(neg_lb),
               '--tol', str(tol),
               '--max_iter', str(max_iter),
               '--conserve', str(conserve),
               '--alpha', str(alpha),
               '--output_loaf', str(output_loaf)
               ]

        try:
            run_commands([cmd])
        except subprocess.CalledProcessError as e:
            raise Exception('An error was encountered while running ANCOM-BC'
                            ' in R (return code %d), please inspect stdout and'
                            ' stderr to learn more.' % e.returncode)

        return output_loaf
