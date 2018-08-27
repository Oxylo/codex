"""
Read Excel workbook containing tables with employees, assumptions,
pension plans and various lookup tables
"""
import pandas as pd
from collections import namedtuple


def read_xlswb(xlswb):
    """ Read sheets from given Excel workbook.

    Return
    ------
    Named tuple containing sheets read from xlswb
    """

    Data = namedtuple('Data', ['tbl_employee', 'tbl_assumption',
                               'tbl_pension_plan', 'lookup_inflation',
                               'lookup_salincrease', 'lookup_indexation',
                               'lookup_intrest', 'lookup_return',
                               'lookup_combi', 'lookup_nqx', 'lookup_tariff'])

    # ---------- read data ------------------------------------------
    print('Reading data ...',)
    print('tbl_deelnemer')
    # tbl_deelnemer : read only records where (aan == True)
    tbl_employee = pd.read_excel(xlswb, sheet_name='tbl_deelnemer',
                                 true_values=['TRUE'])
    tbl_employee = (tbl_employee[tbl_employee.aan == True].
                    drop(labels='aan', axis=1))
    # date: convert format Timestamp to format datetime
    tbl_employee['geboortedatum'] = tbl_employee.geboortedatum.dt.date
    tbl_employee['datum_in_dienst'] = tbl_employee.datum_in_dienst.dt.date

    # tbl_assumptie: read 1 line
    print('tbl_assumptie')
    tbl_assumption = pd.read_excel(xlswb, sheet_name='tbl_assumptie')
    # date: convert format Timestamp to format datetime
    tbl_assumption['rekendatum'] = tbl_assumption.rekendatum.dt.date

    # tbl_regeling & tbl_aanspraak: inner join these tables
    # into tbl_pension_plan
    print('tbl_regeling')
    tbl_plan = pd.read_excel(xlswb, sheet_name='tbl_regeling',
                             true_values=['TRUE'], index_col=0)
    tbl_plan = tbl_plan[tbl_plan.aan == True].drop(labels='aan', axis=1)
    print('tbl_aanspraak')
    tbl_claim = pd.read_excel(xlswb, sheet_name='tbl_aanspraak',
                              true_values=['TRUE'])
    tbl_claim = tbl_claim[tbl_claim.aan == True].drop(labels='aan', axis=1)
    tbl_pension_plan = tbl_claim.join(tbl_plan, on='regeling_id',
                                      how='inner')
    print('OK\n')

    # ----------- read lookup tables --------------------------------

    print('Reading lookup tables ...')

    # lookup_prijsinflatie : read (omschrijving_id ==
    # tbl_assumptie.prijsinflatie_id) & index on jaar
    print('lookup_prijsinflatie')
    lookup_inflation = pd.read_excel(xlswb,
                                     sheet_name='lookup_prijsinflatie')
    selection = (lookup_inflation.omschrijving_id ==
                 tbl_assumption.prijsinflatie_id.values[0])
    lookup_inflation = (lookup_inflation[selection].
                        drop(labels='omschrijving_id', axis=1))
    lookup_inflation.set_index('jaar', inplace=True)

    # lookup_salarisstijging : read (omschrijving_id ==
    # tbl_assumptie.salarisstijging_id) & index on leeftijd
    print('lookup_salarisstijging')
    lookup_salincrease = pd.read_excel(xlswb, sheet_name='lookup_salarisstijging')
    selection = (lookup_salincrease.omschrijving_id ==
                 tbl_assumption.salarisstijging_id.values[0])
    lookup_salincrease = (lookup_salincrease[selection].
                          drop(labels='omschrijving_id', axis=1))
    lookup_salincrease.set_index('leeftijd', inplace=True)

    # lookup_indexatie : read (omschrijving_id ==
    # tbl_assumptie.indexatie_id) & index on (status, jaar)
    print('lookup_indexatie')
    lookup_indexation = pd.read_excel(xlswb,
                                      sheet_name='lookup_indexatie')
    selection = (lookup_indexation.omschrijving_id ==
                 tbl_assumption.indexatie_id.values[0])
    lookup_indexation = (lookup_indexation[selection].
                         drop(labels='omschrijving_id', axis=1))
    lookup_indexation.set_index(['status', 'jaar'], inplace=True)

    # lookup_rente : read (omschrijving_id ==
    # tbl_assumptie.rente_id) & index on jaar
    print('lookup_rente')
    lookup_intrest = pd.read_excel(xlswb, sheet_name='lookup_rente')
    selection = (lookup_intrest.omschrijving_id ==
                 tbl_assumption.rente_id.values[0])
    lookup_intrest = (lookup_intrest[selection].
                      drop(labels='omschrijving_id', axis=1))
    lookup_intrest.set_index('jaar', inplace=True)

    # lookup_rendement : read (omschrijving_id ==
    # tbl_assumptie.rendement_id) & index on leeftijd
    print('lookup_rendement')
    lookup_return = pd.read_excel(xlswb, sheet_name='lookup_rendement')
    selection = (lookup_return.omschrijving_id ==
                 tbl_assumption.rendement_id.values[0])
    lookup_return = (lookup_return[selection].
                     drop(labels='omschrijving_id', axis=1))
    lookup_return.set_index('leeftijd', inplace=True)

    # lookup_combifactor : read (omschrijving_id ==
    # tbl_assumptie.combifactor_id) & index on leeftijd (geslacht, leeftijd)
    print('lookup_combifactor')
    lookup_combi = pd.read_excel(xlswb, sheet_name='lookup_combifactor')
    selection = (lookup_combi.omschrijving_id ==
                 tbl_assumption.combifactor_id.values[0])
    lookup_combi = (lookup_combi[selection].
                    drop(labels='omschrijving_id', axis=1))
    lookup_combi.set_index(['geslacht', 'leeftijd'], inplace=True)

    # lookup_nqx : read (omschrijving_id ==
    # tbl_assumptie.nqx_id) & index on (geslacht, lfd_huidig, leeftijd)
    print('lookup_nqx')
    lookup_nqx = pd.read_excel(xlswb, sheet_name='lookup_nqx')
    selection = (lookup_nqx.omschrijving_id ==
                 tbl_assumption.nqx_id.values[0])
    lookup_nqx = (lookup_nqx[selection].
                  drop(labels='omschrijving_id', axis=1))
    lookup_nqx.set_index(['geslacht', 'lfd_huidig', 'leeftijd'],
                         inplace=True)

    # lookup_tarief : read (omschrijving_id == tbl_assumptie.tarief_id)
    # & index on leeftijd (aanspraak, geslacht, leeftijd)
    print('lookup_tarief')
    lookup_tariff = pd.read_excel(xlswb, sheet_name='lookup_tarief')
    selection = (lookup_tariff.omschrijving_id ==
                 tbl_assumption.tarief_id.values[0])
    lookup_tariff = (lookup_tariff[selection].
                     drop(labels='omschrijving_id', axis=1))
    lookup_tariff.set_index(['aanspraak', 'geslacht', 'leeftijd'],
                            inplace=True)
    print('OK')

    data = Data(tbl_employee, tbl_assumption, tbl_pension_plan,
                lookup_inflation, lookup_salincrease,
                lookup_indexation, lookup_intrest, lookup_return,
                lookup_combi, lookup_nqx, lookup_tariff)

    return data
