# ----------------------------------------------------------------------------
# Copyright (c) 2016-2022, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import subprocess
import tempfile
import pandas as pd
import os
import qiime2
from q2_stats._format import DataLoafPackageDirFmt


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


def ancombc(table: pd.DataFrame, metadata: qiime2.Metadata,
            formula: str, p_adj_method: str = 'holm', prv_cut: float = 0.1,
            lib_cut: int = 0, group: str = None, level_ordering: str = None,
            struc_zero: bool = False, neg_lb: bool = False, tol: float = 1e-05,
            max_iter: int = 100, conserve: bool = False,
            alpha: float = 0.05) -> (DataLoafPackageDirFmt,
                                     DataLoafPackageDirFmt):

    return _ancombc(
        table=table,
        metadata=metadata,
        formula=formula,
        p_adj_method=p_adj_method,
        prv_cut=prv_cut,
        lib_cut=lib_cut,
        group=group,
        level_ordering=level_ordering,
        struc_zero=struc_zero,
        neg_lb=neg_lb,
        tol=tol,
        max_iter=max_iter,
        conserve=conserve,
        alpha=alpha,
    )


def _column_validation(value, parameter, metadata):
    if value not in metadata.columns:
        raise ValueError('Value provided in the `%s` parameter was not found'
                         ' in any of the metadata columns. Please make sure to'
                         ' only include values that are present within the'
                         ' metadata columns.'
                         ' \n\n'
                         ' Value that was not found as a metadata column: "%s"'
                         % (parameter, value))


def _ancombc(table, metadata, formula, p_adj_method, prv_cut, lib_cut,
             group, level_ordering, struc_zero, neg_lb, tol, max_iter,
             conserve, alpha):

    meta = metadata.to_dataframe()

    # error on IDs found in table but not in metadata
    missing_ids = table.index.difference(meta.index).values

    if not (set(table.index).issubset(set(meta.index))):
        raise KeyError('Not all samples present within the table were found in'
                       ' the associated metadata file. Please make sure that'
                       ' all samples in the FeatureTable are also present in'
                       ' the metadata.'
                       ' Sample IDs not found in the metadata: %s'
                       % missing_ids)

    # column validation for the group parameter
    if group is not None:
        _column_validation(group, 'group', meta)
    else:
        group = ''

    # column & level validation for the level_ordering parameter
    if level_ordering is not None:
        for i in level_ordering:
            column = i.split('::')[0]
            level_value = i.split('::')[1]

            _column_validation(column, 'level_ordering', meta)

            if level_value not in pd.unique(meta[column].values):
                raise ValueError('Value provided in `level_ordering` parameter'
                                 ' not found in the associated column within'
                                 ' the metadata. Please make sure each'
                                 ' column::value pair is present within the'
                                 ' metadata file.'
                                 ' \n\n'
                                 ' column::value pair with a value that was'
                                 ' not found: "%s"' % i)
    else:
        level_ordering = ''

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir_name = '.'
        biom_fp = os.path.join(temp_dir_name, 'input.biom.tsv')
        meta_fp = os.path.join(temp_dir_name, 'input.map.txt')

        table.to_csv(biom_fp, sep='\t', header=True)
        meta.to_csv(meta_fp, sep='\t', header=True)

        output_loaf = DataLoafPackageDirFmt()
        output_zeros = DataLoafPackageDirFmt()

        cmd = ['run_ancombc.R',
               '--inp_abundances_path', biom_fp,
               '--inp_metadata_path', meta_fp,
               '--formula', str(formula),
               '--p_adj_method', p_adj_method,
               '--prv_cut', str(prv_cut),
               '--lib_cut', str(lib_cut),
               '--group', str(group),
               '--level_ordering', str(level_ordering),
               '--struc_zero', str(struc_zero),
               '--neg_lb', str(neg_lb),
               '--tol', str(tol),
               '--max_iter', str(max_iter),
               '--conserve', str(conserve),
               '--alpha', str(alpha),
               '--output_loaf', str(output_loaf),
               '--output_zeros', str(output_zeros)
               ]

        try:
            run_commands([cmd])
        except subprocess.CalledProcessError as e:
            raise Exception('An error was encountered while running ANCOM-BC'
                            ' in R (return code %d), please inspect stdout and'
                            ' stderr to learn more.' % e.returncode)

        return output_loaf, output_zeros
