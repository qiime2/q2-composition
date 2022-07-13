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
import numpy as np
import os
import qiime2


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
            group: str = None, struc_zero: bool = False, neg_lb: bool = False,
            tol: float = 1e-05, max_iter: int = 100, conserve: bool = False,
            alpha: float = 0.05, global_test: bool = False) -> pd.DataFrame:

    return _ancombc(
        table=table,
        metadata=metadata,
        formula=formula,
        p_adj_method=p_adj_method,
        prv_cut=prv_cut,
        lib_cut=lib_cut,
        group=group,
        struc_zero=struc_zero,
        neg_lb=neg_lb,
        tol=tol,
        max_iter=max_iter,
        conserve=conserve,
        alpha=alpha,
        global_test=global_test
    )

def _ancombc(table, metadata, formula, p_adj_method, prv_cut, lib_cut, group,
             struc_zero, neg_lb, tol, max_iter, conserve, alpha, global_test):
    # create series from metadata column
    meta = metadata.to_dataframe()

    # check for variable lengths and warn if there's only one value per group.
    # ANCOM will fail silently later bc of this and that is harder to debug.
    variables = np.unique(np.hstack([x.split("*")
                                    for x in formula.split("+")]))
    variables = np.array([x.strip() for x in variables])

    var_counts = pd.DataFrame.from_dict(orient='index', data={
        var: {'n_groups': len(meta[var].dropna().unique())}
        for var in variables
        })
    if (var_counts['n_groups'] < 2).all():
        raise ValueError("None of the columns in the metadata satisfy"
                         " ANCOM-BC's requirements. All columns in the"
                         " formula should have more than one value.")

    # filter the metadata so only the samples present in the table are used.
    # this also re-orders it for the correct condition selection.
    # it must be re-ordered for ANCOM-BC to correctly input the conditions.
    # meta = meta.reindex([table.index])

    # force re-order based on the data to ensure conds are selected correctly.
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir_name = '.'
        biom_fp = os.path.join(temp_dir_name, 'input.biom.tsv')
        meta_fp = os.path.join(temp_dir_name, 'input.map.txt')
        summary_fp = os.path.join(temp_dir_name, 'output.summary.txt')

        table.to_csv(biom_fp, sep='\t', header=True)
        meta.to_csv(meta_fp, sep='\t', header=True)

        if group is None:
            group = formula

        # most likely need to wrap commands in R formulae quoting using ``
        cmd = ['run_ancombc.R',
               '--inp_abundances_path', biom_fp,
               '--inp_metadata_path', meta_fp,
               '--formula', formula,
               '--p_adj_method', p_adj_method,
               '--prv_cut', str(prv_cut),
               '--lib_cut', str(lib_cut),
               '--group', group,
               '--struc_zero', str(struc_zero),
               '--neg_lb', str(neg_lb),
               '--tol', str(tol),
               '--max_iter', str(max_iter),
               '--conserve', str(conserve),
               '--alpha', str(alpha),
               '--global', str(global_test),
               '--output', summary_fp
               ]

        # cmd = list(map(str, cmd))

        try:
            global_test = run_commands([cmd])
        except subprocess.CalledProcessError as e:
            raise Exception('An error was encountered while running ANCOM-BC'
                            ' in R (return code %d), please inspect stdout and'
                            ' stderr to learn more.' % e.returncode)

        summary = pd.read_csv(filepath_or_buffer=summary_fp, index_col=0)

        summary.index.set_names('feature-id', inplace=True)
        return summary
