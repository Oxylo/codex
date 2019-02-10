"""
Compare codex results with WTW with scenarios
"""

import os
import pandas as pd
from utils import compare
from codex import Tableau

# ----- settings for this test ----------------------------------------

TESTDATA = 'codex_test_data_wtw_incl_scenarios.xlsx'
MAXERROR = 0.25  # Absolute difference must be less than 0.25 percent
TEST_COLS = ['wtw_projectie_op',  'wtw_projectie_kapitaal', ]
TEST_INDEX = ['regeling_id', 'deelnemer_id', 'simulatie_nr']
CALCULATED_COLS = ['projectie_op', 'capital']
CALCULATED_INDEX = ['regeling_id', 'id', 'simulnr']

NSIMULS = 2001

# ----- fixtures ------------------------------------------------------

main_dir = os.path.dirname(__file__)
abs_file_path = os.path.join(main_dir, TESTDATA)

tab = Tableau(xlswb=abs_file_path, nsimuls=NSIMULS)
test_values = pd.read_excel(abs_file_path, sheet_name='test_waarden')

# ------ test add_summary----------------------------------------------

def test_add_summary():

    calculated_values = tab.add_summary()
    calculated_values.set_index(CALCULATED_INDEX, inplace=True)
    merged = test_values.join(calculated_values[CALCULATED_COLS],
                              on=TEST_INDEX)
    merged.set_index(TEST_INDEX, inplace=True)
    comp = compare(merged, TEST_COLS, CALCULATED_COLS)

    print('\n\n*** Top 20 differences: ***')
    print(comp.head(20))

    assert (comp.pct_diff.max() < MAXERROR)

# ------ [end tests] --------------------------------------------------
