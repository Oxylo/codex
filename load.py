"""
Read Excel workbook containing tables with employees, assumptions,
pension plans and various lookup tables
"""
import pandas as pd
from collections import namedtuple
from utils import stack_lookup_table, calculate_portfolio_return


def read_xlswb(xlswb):
    """ Read sheets from given Excel workbook.

    Return
    ------
    Named tuple containing sheets read from xlswb
    """

    Data = namedtuple('Data', ['tbl_employee', 'tbl_assumption',
                               'tbl_pension_plan', 'lookup_inflation',
                               'lookup_salincrease', 'lookup_indexation',
                               'lookup_intrest', 'lookup_lifecycle',
                               'lookup_return_stocks', 'lookup_return_bonds',
                               'lookup_tar_at_pensionage', 'lookup_nqx',
                               'lookup_tariff', 'lookup_return'])

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
                                     sheet_name='lookup_prijsinflatie',
                                     converters={'jaar': int})
    selection = (lookup_inflation.omschrijving_id ==
                 tbl_assumption.prijsinflatie_id.values[0])
    lookup_inflation = (lookup_inflation[selection].
                        drop(labels='omschrijving_id', axis=1))
    lookup_inflation.set_index('jaar', inplace=True)
    lookup_inflation = stack_lookup_table(lookup_inflation,
                                          colname='pct_prijsinflatie_primo')

    # lookup_salarisstijging : read (omschrijving_id ==
    # tbl_assumptie.salarisstijging_id) & index on leeftijd
    print('lookup_salarisstijging')
    lookup_salincrease = pd.read_excel(xlswb, sheet_name='lookup_salarisstijging')
    selection = (lookup_salincrease.omschrijving_id ==
                 tbl_assumption.salarisstijging_id.values[0])
    lookup_salincrease = (lookup_salincrease[selection].
                          drop(labels='omschrijving_id', axis=1))
    lookup_salincrease.set_index('leeftijd', inplace=True)
    lookup_salincrease = stack_lookup_table(lookup_salincrease,
                                            colname='pct_salstijging_primo')

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
    lookup_indexation = stack_lookup_table(lookup_indexation,
                                           colname='pct_indexatie_primo')

    # lookup_rente : read (omschrijving_id ==
    # tbl_assumptie.rente_id) & index on jaar
    print('lookup_rente')
    lookup_intrest = pd.read_excel(xlswb, sheet_name='lookup_rente')
    selection = (lookup_intrest.omschrijving_id ==
                 tbl_assumption.rente_id.values[0])
    lookup_intrest = (lookup_intrest[selection].
                      drop(labels='omschrijving_id', axis=1))
    lookup_intrest.set_index('jaar', inplace=True)
    lookup_intrest = stack_lookup_table(lookup_intrest,
                                        colname='pct_rente_ultimo')

    # lookup_lifecycle: read (omschrijving_id ==
    # tbl_assumptie.lifecycle_id) & index on leeftijd
    print('lookup_lifecycle')
    lookup_lifecycle = (
      pd.read_excel(xlswb, sheet_name='lookup_lifecycle')
      )
    selection = (lookup_lifecycle.omschrijving_id ==
                 tbl_assumption.lifecycle_id.values[0])
    lookup_lifecycle = (lookup_lifecycle[selection].
                        drop(labels='omschrijving_id', axis=1))
    lookup_lifecycle.set_index('leeftijd', inplace=True)

    # lookup_rendement_aandelen : read (omschrijving_id ==
    # tbl_assumptie.rendement_aandelen_id) & index on jaar
    print('lookup_rendement_aandelen')
    lookup_return_stocks = (
      pd.read_excel(xlswb, sheet_name='lookup_rendement_aandelen')
      )
    selection = (lookup_return_stocks.omschrijving_id ==
                 tbl_assumption.rendement_aandelen_id.values[0])
    lookup_return_stocks = (lookup_return_stocks[selection].
                            drop(labels='omschrijving_id', axis=1))
    lookup_return_stocks.set_index('jaar', inplace=True)
    lookup_return_stocks = stack_lookup_table(lookup_return_stocks,
                                              colname='pct_rendement_aandelen')

    # lookup_rendement_obligaties : read (omschrijving_id ==
    # tbl_assumptie.rendement_obligaties_id) & index on jaar
    print('lookup_rendement_obligaties')
    lookup_return_bonds = (
      pd.read_excel(xlswb, sheet_name='lookup_rendement_obligaties')
      )
    selection = (lookup_return_bonds.omschrijving_id ==
                 tbl_assumption.rendement_obligaties_id.values[0])
    lookup_return_bonds = (lookup_return_bonds[selection].
                           drop(labels='omschrijving_id', axis=1))
    lookup_return_bonds.set_index('jaar', inplace=True)
    lookup_return_bonds = stack_lookup_table(lookup_return_bonds,
                                             colname='pct_rendement_obligaties')

    # lookup_tar_at_pensionage : read (omschrijving_id ==
    # tbl_assumptie.tar_at_pensionage_id) &
    # index on leeftijd (*pensioenlfd*, geslacht, *aanspraak_id*, leeftijd)
    print('lookup_tar_at_pensionage')
    lookup_tar_at_pensionage =(
      pd.read_excel(xlswb, sheet_name='lookup_tar_at_pensionage',
                    converters={'pensioenlfd': int, 'leeftijd': int})
      )
    selection = (lookup_tar_at_pensionage.omschrijving_id ==
                 tbl_assumption.tar_at_pensionage_id.values[0])
    lookup_tar_at_pensionage = (lookup_tar_at_pensionage[selection].
                                drop(labels='omschrijving_id', axis=1))
    lookup_tar_at_pensionage.set_index(['pensioenlfd', 'geslacht',
                                        'aanspraak_id', 'leeftijd'],
                                       inplace=True)
    lookup_tar_at_pensionage = stack_lookup_table(lookup_tar_at_pensionage,
                                                  colname='tar')

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

    # ----convert lifecycle, stocks/bond returns to portfolio returns -------

    lookup_return = calculate_portfolio_return(lookup_lifecycle,
                                               lookup_return_stocks,
                                               lookup_return_bonds)

    # -----------------------------------------------------------------------

    data = Data(tbl_employee, tbl_assumption, tbl_pension_plan,
                lookup_inflation, lookup_salincrease,
                lookup_indexation, lookup_intrest,
                lookup_lifecycle, lookup_return_stocks,
                lookup_return_bonds, lookup_tar_at_pensionage,
                lookup_nqx, lookup_tariff, lookup_return)

    return data
