import pandas as pd
import pytest
from codexx import formulae, iop

TEST_CASES = '/home/pieter/projects/codexx/tests/testsheet.xlsx'


@pytest.fixture
def test_cases():
    xlswb = iop.Xlswb(TEST_CASES)
    data = xlswb.load()
    df = pd.read_excel(TEST_CASES, sheet_name='test_values')
    data.testvalues = {row.testcasus_id: row for row in df.itertuples(index=False, name='Testvalues')}
    return data


def test_calc_pension_date(test_cases):
    # get case 1
    test_values = test_cases.test_values[1]
    regeling_id = test_values.regeling_id
    deelnemer_id = test_values.deelnemer_id
    assumptie_id = test_values.assumptie_id
    geboortedatum = test_cases.deelnemers[deelnemer_id]['geboortedatum']
    pensioenlfd = test_cases.regelingen[regeling_id]['pensioenlfd']
    calculated = formulae.calc_pensiondate(geboortedatum, pensioenlfd)
    test_outcome = test_values.pensioendatum
    print(calculated)
    assert (calculated == test_outcome)


