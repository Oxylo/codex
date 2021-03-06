"""
Module for actuarial projections
"""
import numpy as np
import pandas as pd
from load import read_xlswb
from settings import XLSWB
from utils import (calculate_cumulative_index,
                   calculate_cumulative_index_conjugate, modulo_map)
from vectorize import (pensiondate, future_service_years,
                       past_service_years, total_service_years,
                       nprojection_years, age, ft_base,
                       employee_contribution,
                       eur_return)


class Tableau:
    """  Tableau with benefit projections
    """

    def __init__(self, xlswb=XLSWB, nsimuls=1, maxyears=None):
        self.xlswb = xlswb
        self.nsimuls = nsimuls
        self.maxyears = maxyears
        self.data = self._read()
        self.tableau = self.create()

    def _read(self):
        """ Return named tuple with sheets from given workbook
        """
        return read_xlswb(self.xlswb)

    def _merge(self):
        """ Merge data into tableau length Employees x Claims x Years x Simulations
        """
        # calculate number of projection years for each employee/claim
        # combination
        assumption = [assumption for assumption in
                      self.data.tbl_assumption.itertuples(index=False)][0]
        emp = pd.DataFrame(self.data.tbl_employee[['id', 'geboortedatum']])
        clm = (
          pd.DataFrame(self.data.tbl_pension_plan[['regeling_id', 'aanspraak',
                                                   'pensioenlfd']])
          )
        emp['ones'], clm['ones'] = 1, 1
        empxclm = pd.merge(left=emp, right=clm, on='ones')
        empxclm['nprojectionyears'] = (
          nprojection_years(birthdate=empxclm.geboortedatum,
                            calculation_date=assumption.rekendatum,
                            pension_age=empxclm.pensioenlfd).apply(int)
          )

        # build tableau Employee x Claim x Year x Simulation
        cols = ['id', 'regeling_id', 'aanspraak']
        empxclmxyr = (np.repeat(np.array(empxclm[cols].values),
                      repeats=np.array(empxclm.nprojectionyears), axis=0))
        empxclmxyr = pd.DataFrame(data=empxclmxyr,
                                  columns=['id', 'regeling_id', 'aanspraak'])
        empxclmxyr['ones'] = 1
        cols = ['id', 'regeling_id', 'aanspraak']
        empxclmxyr['BOY'] = (empxclmxyr.groupby(cols)['ones'].cumsum())
        sim = pd.DataFrame(data={'simulnr': range(1, self.nsimuls + 1),
                           'ones': self.nsimuls * [1]})
        cols = ['id', 'regeling_id', 'aanspraak', 'simulnr', 'BOY']
        empxclmxyrxsim = (
          pd.merge(empxclmxyr, sim).sort_values(cols).
          reset_index().drop(['index', 'ones'], axis=1)
          )
        empxclmxyrxsim['id'] = empxclmxyrxsim.id.apply(int)
        # for merging with employee data on id
        empxclmxyrxsim['regeling_id'] = empxclmxyrxsim.regeling_id.apply(int)
        # for merging with claim data on regeling_id, aanspraak

        # merge employee & pensionplan data into tableau
        self.data.tbl_employee.set_index('id', inplace=True)
        tab = empxclmxyrxsim.join(self.data.tbl_employee, on='id')
        cols = ['regeling_id', 'aanspraak']
        self.data.tbl_pension_plan.set_index(cols, inplace=True)
        tab = tab.join(self.data.tbl_pension_plan, on=cols)
        return tab

    def _add_age(self, tab):
        """ Add age related colums to tableau
        """

        assumption = [assumption for assumption in
                      self.data.tbl_assumption.itertuples(index=False)][0]

        # calculate age etc.
        tab['pensioendatum'] = pensiondate(tab.geboortedatum, tab.pensioenlfd)
        tab['fsy0'] = future_service_years(assumption.rekendatum,
                                           tab.pensioendatum)
        tab['psy0'] = past_service_years(tab.datum_in_dienst,
                                         assumption.rekendatum, method='PwC')
        tab['tsy'] = total_service_years(tab.psy0, tab.fsy0)
        tab['fsy'] = tab['fsy0'] - tab['BOY'] + 1
        tab['leeftijd0'] = age(tab.pensioenlfd, tab.fsy0).astype(int)
        tab['leeftijd0_adjusted'] = tab.leeftijd0 + assumption.age_adjustment
        tab['leeftijd'] = age(tab.pensioenlfd, tab.fsy)
        tab['leeftijd_low'] = tab.leeftijd.values.astype(int)
        tab['leeftijd_low_adjusted'] = (tab.leeftijd_low +
                                        assumption.age_adjustment)
        return tab

    def _lookup_increments(self, tab):
        """ Add increments like inflation, intrest, return etc.
        """
        # merge (cumulative) indices into tableau
        tab['simulnr_cpy'] = tab.simulnr

        # inflation
        n = self.data.lookup_inflation.index.get_level_values('simulnr').max()
        tab['simulnr'] = tab.simulnr_cpy.map(lambda x: modulo_map(x, n))
        tab = tab.join(self.data.lookup_inflation, on=['BOY', 'simulnr'])
        # PJM : simulnr --> simulnr_cpy
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr_cpy'])
        tab['pct_prijsinflatie_primo_idx'] = (
          grouped['pct_prijsinflatie_primo'].apply(calculate_cumulative_index)
          )
        tab['simulnr'] = tab.simulnr_cpy

        # salary increase
        n = (self.data.lookup_salincrease.index.
             get_level_values('simulnr').max())
        tab['simulnr'] = tab.simulnr_cpy.map(lambda x: modulo_map(x, n))
        tab = tab.join(self.data.lookup_salincrease,
                       on=['leeftijd_low', 'simulnr'])
        # PJM
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr_cpy'])
        tab['pct_salstijging_primo_idx'] = (
          grouped['pct_salstijging_primo'].apply(calculate_cumulative_index)
          )
        tab['simulnr'] = tab.simulnr_cpy

        # indexation (actives)
        n = (self.data.lookup_indexation.index.
             get_level_values('simulnr').max())
        tab['simulnr'] = tab.simulnr_cpy.map(lambda x: modulo_map(x, n))

        lookup_indexation_actives = self.data.lookup_indexation.loc['actief']
        tab = tab.join(lookup_indexation_actives, on=['BOY', 'simulnr'])
        # PJM
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr_cpy'])
        tab['pct_indexatie_primo_idx'] = (
            grouped['pct_indexatie_primo'].
            apply(calculate_cumulative_index)
            )
        tab['pct_indexatie_primo_idx_shifted'] = (
          grouped['pct_indexatie_primo_idx'].shift().fillna(1)
          )

        # indexation (inactives)
        lookup_indexation_inactives = (
          self.data.lookup_indexation.loc['inactief']
          )
        tab = tab.join(lookup_indexation_inactives,
                       on=['BOY', 'simulnr'], rsuffix='_inactief')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        tab['pct_indexatie_primo_inactief_idx'] = (
            grouped['pct_indexatie_primo_inactief'].
            apply(calculate_cumulative_index)
            )
        tab['pct_indexatie_primo_inactief_idx_shifted'] = (
          grouped['pct_indexatie_primo_inactief_idx'].shift().fillna(1)
          )
        tab['simulnr'] = tab.simulnr_cpy

        # intrest
        n = (self.data.lookup_intrest.index.
             get_level_values('simulnr').max())
        tab['simulnr'] = tab.simulnr_cpy.map(lambda x: modulo_map(x, n))
        tab = tab.join(self.data.lookup_intrest, on=['BOY', 'simulnr'])
        # PJM
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr_cpy'])
        tab['pct_rente_ultimo_idx'] = (
            grouped['pct_rente_ultimo'].apply(calculate_cumulative_index))
        tab['pct_rente_ultimo_idx_shifted'] = (
          grouped['pct_rente_ultimo_idx'].shift().fillna(1)
          )
        tab['simulnr'] = tab.simulnr_cpy

        # return
        n = (self.data.lookup_return.index.
             get_level_values('simulnr').max())
        tab['simulnr'] = tab.simulnr_cpy.map(lambda x: modulo_map(x, n))
        tab = tab.join(self.data.lookup_return,
                       on=['leeftijd0', 'BOY', 'simulnr'])
        # PJM
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr_cpy'])
        tab['pct_rendement_ultimo_idx'] = (
            grouped['pct_rendement_ultimo'].apply(calculate_cumulative_index))
        tab['pct_rendement_ultimo_idx_shifted'] = (
          grouped['pct_rendement_ultimo_idx'].shift().fillna(1)
          )
        tab['simulnr'] = tab.simulnr_cpy

        # nqx
        cols = ['geslacht', 'leeftijd0_adjusted', 'leeftijd_low_adjusted']
        tab = tab.join(self.data.lookup_nqx, on=cols)
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        tab['nqx_primo_idx'] = (
            grouped['nqx_primo'].apply(calculate_cumulative_index_conjugate)
            )
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        tab['nqx_primo_idx_shifted'] = (
          grouped['nqx_primo_idx'].shift().fillna(1)
          )

        # tariff
        cols = ['tarief_id', 'aanspraak', 'geslacht', 'leeftijd_low']
        tab = tab.join(self.data.lookup_tariff, on=cols)
        return tab

        # reset simulnr column
        # tab.drop('simulnr_cpy', inplace=True, axis=1)

    def _run_projections(self, tab):
        """ Add benefit projections to tableau

        Note: yes, finally we can go vectorized!
        """
        assumption = [assumption for assumption in
                      self.data.tbl_assumption.itertuples(index=False)][0]
        # require pension base at start for final pay plan
        tab['pt_pensioengrondslag0'] = ft_base(tab.ft_salaris,
                                               tab.franchise,
                                               tab.max_salaris)

        tab['psy'] = tab.psy0 + tab.BOY
        tab['premie_franchise'] = (tab.premie_franchise *
                                   tab.pct_prijsinflatie_primo_idx)
        tab['premie_plafond'] = (tab.premie_plafond *
                                 tab.pct_prijsinflatie_primo_idx)
        tab['aow'] = assumption.aow * tab.pct_prijsinflatie_primo_idx
        tab['ft_salaris'] = tab.ft_salaris * tab.pct_salstijging_primo_idx
        tab['ft_premiegrondslag'] = ft_base(tab.ft_salaris.values,
                                            tab.premie_franchise.values,
                                            tab.premie_plafond.values)
        tab['pt_premiegrondslag'] = (tab.ft_premiegrondslag.values *
                                     tab.pt_percentage)
        tab['eigen_bijdrage'] = employee_contribution(tab.ft_premiegrondslag,
                                                      tab.pct_eigen_bijdrage,
                                                      tab.pt_percentage)
        tab['pro_rata'] = np.minimum(tab.fsy.values, 1)

        tab['discount'] = tab.eigen_bijdrage / tab.pct_rente_ultimo_idx_shifted
        # Cast colum to be summed from object to float!
        tab['discount'] = tab.discount.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        cum_discount = grouped['discount'].cumsum()
        tab['cum_eigen_bijdrage'] = tab.pct_rente_ultimo_idx * cum_discount

        tab['eur_rendement'] = eur_return(tab.cum_eigen_bijdrage,
                                          tab.eigen_bijdrage,
                                          tab.pct_rente_ultimo,
                                          tab.BOY, adjust=0)
        tab['op_premievrij'] = (tab.op_premievrij *
                                tab.pct_indexatie_primo_inactief_idx)
        tab['np_premievrij'] = (tab.np_premievrij *
                                tab.pct_indexatie_primo_inactief_idx)

        tab['franchise'] = tab.franchise * tab.pct_prijsinflatie_primo_idx
        tab['max_salaris'] = tab.max_salaris * tab.pct_prijsinflatie_primo_idx
        tab['ft_pensioengrondslag'] = ft_base(tab.ft_salaris.values,
                                              tab.franchise.values,
                                              tab.max_salaris.values)
        tab['pt_pensioengrondslag'] = (tab.ft_pensioengrondslag.values *
                                       tab.pt_percentage)

        # projection of benefits
        # DB
        defined_benefit = (
          tab.aanspraak.isin(['OPLL', 'NPLLRS', 'NPTL-O', 'NPTL-OT'])
          )

        # average pay
        avg_pay = defined_benefit & (tab.type_regeling == 'ML')
        tab['inkoop_ml'] = (avg_pay * tab.pro_rata * tab.percentage *
                            tab.pt_pensioengrondslag)
        # Cast colum to be summed from object to float!
        tab['inkoop_ml'] = tab.inkoop_ml.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        tab['tijdsevenredig_ml'] = avg_pay * grouped['inkoop_ml'].cumsum()
        tab['discount'] = (avg_pay * tab.inkoop_ml /
                           tab.pct_indexatie_primo_idx_shifted)
        # Cast colum to be summed from object to float!
        tab['discount'] = avg_pay * tab.discount.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        cum_discount = avg_pay * grouped['discount'].cumsum()
        tab['tijdsevenredig_ml'] = (avg_pay *
                                    tab.pct_indexatie_primo_idx_shifted *
                                    cum_discount)
        # Cast colum to be summed from object to float!
        tab['tijdsevenredig_ml'] = tab.tijdsevenredig_ml.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        opbouw_ml = avg_pay * grouped['tijdsevenredig_ml'].diff()
        tab['opbouw_ml'] = avg_pay * ((tab.BOY == 1) * tab.tijdsevenredig_ml +
                                      (tab.BOY != 1) * opbouw_ml.fillna(0))
        tab['backservice_ml'] = (avg_pay * tab.pct_indexatie_primo *
                                 (tab.tijdsevenredig_ml - tab.opbouw_ml))

        # final pay
        final_pay = defined_benefit & (tab.type_regeling == 'EL')
        # Cast colum to be summed from object to float!
        tab['pt_pensioengrondslag'] = tab.pt_pensioengrondslag.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        pt_grondslag_shifted = (
          grouped['pt_pensioengrondslag'].shift().fillna(0)
          )
        tab['pt_pensioengrondslag_shifted'] = (
          (tab.BOY == 1) * tab.pt_pensioengrondslag0 +
          (tab.BOY != 1) * pt_grondslag_shifted
          )
        tab['backservice_el'] = (
          final_pay * np.maximum(0, tab.psy - 1) * tab.percentage *
          np.maximum(0, tab.pt_pensioengrondslag -
                     tab.pt_pensioengrondslag_shifted
                     ))
        tab['inkoop_el'] = (final_pay * tab.percentage *
                            tab.pt_pensioengrondslag)
        tab['opbouw_el'] = final_pay * (tab.inkoop_el + tab.backservice_el)
        # Cast colum to be summed from object to float!
        tab['opbouw_el'] = tab.opbouw_el.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        tab['tijdsevenredig_el'] = final_pay * grouped['opbouw_el'].cumsum()

        # both average pay and final pay
        tab['inkoop'] = avg_pay * tab.inkoop_ml + final_pay * tab.inkoop_el
        tab['opbouw'] = avg_pay * tab.opbouw_ml + final_pay * tab.opbouw_el
        tab['backservice'] = (avg_pay * tab.backservice_ml + final_pay *
                              tab.backservice_el)
        tab['tijdsevenredig'] = (avg_pay * tab.tijdsevenredig_ml +
                                 final_pay * tab.tijdsevenredig_el)
        tab['verzekerd'] = (defined_benefit * (tab.tijdsevenredig +
                            np.maximum(0, tab.fsy - 1) * tab.percentage *
                            tab.pt_pensioengrondslag))
        tab['eur_premie_db'] = (
          defined_benefit * (tab.opbouw - tab.backservice) * tab.tarief_primo
          )

        # DC
        c = tab.aanspraak.isin(['VARL'])
        tab['pct_staffel'] = c * tab.tarief_primo * tab.percentage
        tab['eur_premie_dc'] = (c * tab.pro_rata * tab.pct_staffel *
                                tab.pt_pensioengrondslag)
        timing_investments = 1 - assumption.timing_belegging
        cf_timing_factor = ((1 + timing_investments *
                             tab.pct_rendement_ultimo) /
                            (1 + tab.pct_rendement_ultimo))
        tab['discount_varl'] = (c * tab.eur_premie_dc * cf_timing_factor *
                                tab.nqx_primo_idx_shifted /
                                tab.pct_rendement_ultimo_idx_shifted)
        # Cast colum to be summed from object to float!
        tab['discount_varl'] = c * tab.discount_varl.astype('float')
        grouped = tab.groupby(['id', 'regeling_id', 'aanspraak', 'simulnr'])
        tab['cum_discount'] = (grouped['discount_varl'].cumsum())
        tab['capital'] = (c * (tab.pct_rendement_ultimo_idx /
                          tab.nqx_primo_idx) * tab.cum_discount)

        # universal premium
        tab['eur_premie'] = (defined_benefit * tab.eur_premie_db + c *
                             tab.eur_premie_dc)
        tab['eur_backservice'] = (defined_benefit * tab.backservice *
                                  tab.tarief_primo)

        # remove temporary variables
        todrop = ['inkoop_ml', 'inkoop_el', 'opbouw_ml', 'opbouw_el',
                  'backservice_ml', 'backservice_el',
                  'tijdsevenredig_ml', 'tijdsevenredig_el', 'discount',
                  'pt_pensioengrondslag0', 'eur_premie_db', 'eur_premie_dc']
        tab.drop(todrop, axis=1, inplace=True)
        return tab

    def create(self):
        tableau = self._merge()
        tableau = self._add_age(tableau)
        tableau = self._lookup_increments(tableau)
        return self._run_projections(tableau)

    def long_to_wide(self, df, default=True):
        if default:
            wide_format = df.swaplevel(i=2, j=3).unstack()
        else:
            wide_format = df.swaplevel(i=2, j=4).unstack()
        wide_format.columns = wide_format.columns.droplevel()
        wide_format.rename(index=str, columns={"OPLL": "tar_OPLL",
                                               "NPLLRS": "tar_NPLLRS"},
                           inplace=True)
        return wide_format

    def add_summary(self):
        """ Return summary: 1 record per employee x plan x simulation
        """
        tar = self.data.lookup_tar_at_pensionage

        # create lookup table 1: 100/70 combi tarief
        # indexed by: pensioenlfd x geslacht x leeftijd x simulnr
        # required for: converting DC capitals to DB claim)
        lookup_combi = tar.unstack(level='aanspraak_id')
        lookup_combi.columns = pd.Index(['tar_NPLLRS', 'tar_OPLL'])
        lookup_combi['tar_combi'] = (lookup_combi.tar_OPLL +
                                     0.7 * lookup_combi.tar_NPLLRS)

        # create lookup table 2: capital at pension date DB plans
        # indexed by: regeling_id x id x simulnr
        # required for: converting DB claims to DC capital
        db_claims = ['OPLL', 'NPLLRS']
        db = self.tableau[(self.tableau.fsy == 1) &
                          (self.tableau.aanspraak.isin(db_claims))]
        selected_columns = ['regeling_id', 'id', 'pensioenlfd',
                            'geslacht', 'leeftijd0', 'aanspraak',
                            'simulnr', 'tijdsevenredig']
        db = db[selected_columns].copy()
        n = self.data.lookup_tar_at_pensionage.index.get_level_values(
          'simulnr').max()
        db['simulnr_tmp'] = db.simulnr.map(lambda x: modulo_map(x, n))
        db['leeftijd0'] = db.leeftijd0.astype(np.int64)  # cast: object --> int
        joined = db.join(tar, on=['pensioenlfd', 'geslacht', 'aanspraak',
                                  'leeftijd0', 'simulnr_tmp'])
        joined['capital_db'] = joined.tijdsevenredig * joined.tar
        remove = ['pensioenlfd', 'geslacht', 'leeftijd0', 'aanspraak',
                  'tijdsevenredig', 'tar', 'simulnr_tmp']
        joined.drop(remove, axis=1, inplace=True)
        grouped = joined.groupby(['regeling_id', 'id', 'simulnr'])
        lookup_capital = grouped.sum()

        # join lookup tables into summary frame
        summary_cols = ['regeling_id', 'id', 'simulnr', 'aow',
                        'cum_eigen_bijdrage', 'geslacht', 'leeftijd0',
                        'memo', 'naam', 'pensioenlfd', 'type_regeling',
                        'geboortedatum', 'ft_salaris', 'pt_percentage',
                        'premie_franchise', 'premie_plafond',
                        'pct_eigen_bijdrage', 'eigen_bijdrage',
                        'capital', 'tijdsevenredig']
        selected_rows = ((self.tableau.fsy == 1) &
                         (self.tableau.aanspraak.isin(['OPLL', 'VARL'])))
        summary = self.tableau[selected_rows][summary_cols]
        summary.rename({'ft_salaris': 'projectie_ft_salaris',
                        'premie_franchise': 'projectie_premie_franchise',
                        'premie_plafond': 'projectie_premie_plafond',
                        'aow': 'projectie_aow'}, axis=1, inplace=True)
        summary['simulnr_tmp'] = summary.simulnr.map(
          lambda x: modulo_map(x, n))
        summary = summary.join(lookup_combi,
                               on=['pensioenlfd', 'geslacht',
                                   'leeftijd0', 'simulnr_tmp'])
        summary = summary.join(lookup_capital,
                               on=['regeling_id', 'id', 'simulnr'])
        summary['aow'] = self.data.tbl_assumption['aow'][0]
        employees = self.data.tbl_employee
        summary = summary.join(employees[['ft_salaris', 'op_premievrij',
                                          'np_premievrij']], on='id')
        plans = self.data.tbl_pension_plan.groupby(
          'regeling_id')[['premie_franchise', 'premie_plafond']].first()
        summary = summary.join(plans, on=['regeling_id'])
        summary['projectie_op_dc'] = summary.capital / summary.tar_combi
        summary['projectie_op'] = (summary.tijdsevenredig +
                                   summary.projectie_op_dc)
        pv = ((summary.op_premievrij * summary.tar_OPLL +
               summary.np_premievrij * summary.tar_NPLLRS) / summary.tar_combi)
        summary['projectie_op_plus_pv'] = summary.projectie_op + pv
        summary['projectie_op_plus_pv_aow'] = (
          summary.projectie_op_plus_pv + summary.projectie_aow)
        summary['capital'] = summary.capital.fillna(0)
        summary['capital_db'] = summary.capital_db.fillna(0)
        summary['capital'] = summary.capital + summary.capital_db
        summary['projectie_op_wg'] = (
          summary.capital - summary.cum_eigen_bijdrage) / summary.tar_combi
        summary['projectie_op_wn'] = (
          summary.projectie_op - summary.projectie_op_wg)
        pension_salary = np.minimum(summary.ft_salaris, summary.premie_plafond)
        summary['eigen_bijdrage0'] = (
          summary.pt_percentage * summary.pct_eigen_bijdrage *
          np.maximum(0, pension_salary - summary.premie_franchise))
        final_cols = ['id', 'regeling_id', 'simulnr','naam', 'geboortedatum',
                      'geslacht', 'leeftijd0', 'ft_salaris', 'pt_percentage',
                      'aow', 'np_premievrij', 'op_premievrij', 'memo',
                      'type_regeling', 'pensioenlfd', 'pct_eigen_bijdrage',
                      'eigen_bijdrage0', 'premie_franchise', 'premie_plafond',
                      'projectie_ft_salaris', 'projectie_aow',
                      'projectie_premie_franchise', 'projectie_premie_plafond',
                      'projectie_op', 'projectie_op_plus_pv',
                      'projectie_op_plus_pv_aow', 'projectie_op_wg',
                      'projectie_op_wn', 'tar_NPLLRS', 'tar_OPLL',
                      'cum_eigen_bijdrage', 'capital']
        return summary[final_cols]
