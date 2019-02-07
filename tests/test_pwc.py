"""
Compare codex results with PwC
"""

import os
import pandas as pd
from utils import compare
from codex import Tableau

# ----- settings for this test ----------------------------------------

TESTDATA = 'codex_test_data_pwc.xlsx'
MAXERROR = 0.25  # Absolute difference must be less than 0.25 percent
TEST_COLS = ['pwc_projectie_op_plus_pv_aow', 'pwc_eigen_bijdrage0',
             'xls_projectie_op_wg',  'xls_projectie_op_wn']
CALCULATED_COLS = ['projectie_op_plus_pv_aow', 'eigen_bijdrage0',
                   'projectie_op_wg',  'projectie_op_wn']
MERGE_INDEX = ['regeling_id', 'deelnemer_id']
NSIMULS = 1

# ----- fixtures ------------------------------------------------------

main_dir = os.path.dirname(__file__)
abs_file_path = os.path.join(main_dir, TESTDATA)

tab = Tableau(xlswb=abs_file_path, nsimuls=NSIMULS)
test_values = pd.read_excel(abs_file_path, sheet_name='test_waarden')

# ------ test add_summary----------------------------------------------

def test_add_summary():

    calculated_values = tab.add_summary()
    merged = test_values.join(calculated_values[CALCULATED_COLS],
                              on=MERGE_INDEX)
    merged.set_index(MERGE_INDEX, inplace=True)
    comp = compare(merged, TEST_COLS, CALCULATED_COLS)

    print('\n\n*** Top 20 differences: ***')
    print(comp.head(20))

    assert (comp.pct_diff.max() < MAXERROR)

# ------ [end tests] --------------------------------------------------
