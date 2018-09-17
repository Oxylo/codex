import os
import pandas as pd
import sys
import pytest
from codex import Tableau

# ----- fixtures ------------------------------------------------------

TESTDATA = 'codex_test_data_db.xls'
MAXERROR = 0.25  # THRESHOLD = 0.25 percent

main_dir = os.path.dirname(__file__)
abs_file_path = os.path.join(main_dir, TESTDATA)

tab = Tableau(xlswb=abs_file_path, nsimuls=1, maxyears=1)
pwc = pd.read_excel(abs_file_path, sheet_name='test_waarden')
# tar_AG2014_67 = main_dir + '/tar_AG2014_op_pensioendatum.csv'


# ------ test add_summary----------------------------------------------

def test_add_summary():

    summary = tab.add_summary()

    cols = ['projectie_op',
            'projectie_op_wg',
            'projectie_op_wn',
            'cum_eigen_bijdrage',
            'projectie_op_plus_pv_aow',
            'eigen_bijdrage0']

    test_results = pwc.join(summary[cols],
                            on=['regeling_id', 'deelnemer_id'])

    test_results['verschil_op_plus_pv_aow'] = (
        test_results.pwc_projectie_op_plus_pv_aow -
        test_results.projectie_op_plus_pv_aow
        )
    condition = (test_results.pwc_projectie_op_plus_pv_aow == 0)
    test_results['pct_verschil_op_plus_pv_aow'] = (
        100 * (condition * 0 + (1 - condition) *
               test_results.verschil_op_plus_pv_aow /
               test_results.pwc_projectie_op_plus_pv_aow)
        )

    test_results['verschil_op_wg'] = (test_results.xls_projectie_op_wg -
                                      test_results.projectie_op_wg)
    condition = (test_results.xls_projectie_op_wg == 0)
    test_results['pct_verschil_op_wg'] = (
        100 * (condition * 0 + (1 - condition) *
               test_results.verschil_op_wg / test_results.xls_projectie_op_wg)
        )

    test_results['verschil_op_wn'] = (test_results.xls_projectie_op_wn -
                                      test_results.projectie_op_wn)
    condition = (test_results.xls_projectie_op_wn == 0)
    test_results['pct_verschil_op_wn'] = (
        100 * (condition * 0 + (1 - condition) *
               test_results.verschil_op_wn / test_results.xls_projectie_op_wn)
        )

    test_results['verschil_eigen_bijdrage0'] = (
        test_results.pwc_eigen_bijdrage0 - test_results.eigen_bijdrage0
        )
    condition = (test_results.pwc_eigen_bijdrage0 == 0)
    test_results['pct_verschil_eigen_bijdrage0'] = (
        100 * (condition * 0 + (1 - condition) *
               test_results.verschil_eigen_bijdrage0 / test_results.
               pwc_eigen_bijdrage0)
        )

    test_stats = (test_results['pct_verschil_op_plus_pv_aow'].abs().max(),
                  test_results['pct_verschil_op_wg'].abs().max(),
                  test_results['pct_verschil_op_wn'].abs().max(),
                  test_results['pct_verschil_eigen_bijdrage0'].abs().max())

    deltas = ['regeling_id',
              'deelnemer_id',
              'pct_verschil_op_plus_pv_aow',
              'pct_verschil_op_wg',
              'pct_verschil_op_wn',
              'pct_verschil_eigen_bijdrage0']

    print('\n')
    print(test_results[deltas])

    assert (max(test_stats) < MAXERROR)

# ------ [end tests] --------------------------------------------------
