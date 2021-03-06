""" utils.py
Boiler plate code besides formulae, to keep main program short & tidy.
"""
import numpy as np
import pandas as pd
import pickle


class CashFlows:

    def __init__(self, infile='/home/pieter/Desktop/cashflows_AG2014_67.pkl',
                 pension_age=67, start=2017, end=2064):
        self.infile = infile
        self.cashflows = self.load_cfs()
        self.pension_age = pension_age
        self.start = start
        self.end = end

    def load_cfs(self):
        f = open(self.infile, 'rb')
        cfs = pickle.load(f)
        f.close()
        return cfs.sort_index()

    def pv(self, calc_year, pension_age, sex_insured, age_insured,
           insurance_id, intrest):
        return present_value(
            self.cashflows.loc[(calc_year, pension_age, sex_insured,
                                age_insured)][insurance_id], intrest=intrest
            )

    def predict_factors_at_pensionage(self, calc_year, intrest=2.5):
        n = self.end + 1 - self.start
        ins_id = 2 * n * ['OPLL'] + 2 * n * ['NPLLRS'] + 2 * n * ['NPTLO']
        sex_in = 3 * (n * ['M'] + n * ['F'])
        cal_yr = 6 * list(range(self.start, self.start + n))
        factors = pd.DataFrame({'aanspraak_id': ins_id,
                                'geslacht': sex_in,
                                'calc_year': cal_yr,
                                'pensioenlfd': self.pension_age})

        factors['tar'] = factors.apply(lambda row: self.pv(row['calc_year'],
                                       self.pension_age,
                                       row['geslacht'],
                                       self.pension_age,
                                       row['aanspraak_id'],
                                       intrest), axis=1)
        return factors


def create_index(lst):
    """ Build index length sum(lst)

    Parameters
    ----------
        lst : list or numpy array of int

    Returns
    -------
        created_index : numpy array

    Notes
    -----
        None

    Examples
    --------
        >>> create_index([3, 2, 4])
        array(0, 1, 2, 0, 1, 0, 1, 2, 3])
    """
    expanded = [range(item) for item in lst]
    return flatten(expanded)


def flatten(lst):
    """ Converts list of lists to flat list

    Parameters
    ----------
        lst : list of lists

    Returns
    -------
        flat_list : numpy array

    Notes
    ----
        None

    Examples
    --------
    >>> flatten([[1, 2, 3], [4, 5, 6]])
    array([1, 2, 3, 4, 5, 6])

    """
    return np.array([item for sublist in lst for item in sublist])


def repeat(df, lst):
    """ Repeat each row of df number of times given in lst

    Parameters
    ----------
    df : DataFrame
        Contains rows to be repeated.
    lst : list
        Contains how many times each row in df needs to be repeated.


    Returns
    -------
    repeated : DataFrame

    Notes
    -----
        Number of items in lst must be equal to number of rows in df.


    Examples
    --------
        >>> df = pd.DataFrame(data=[3, 8, 7])
        >>> lst = [2, 4, 3]
        >>> repeat(df, lst)
        0    3
        0    3
        1    8
        1    8
        1    8
        1    8
        2    7
        2    7
        2    7
    """
    return df.loc[df.index.repeat(lst)]


def shift(obj):
    """ Shift 1 position forward, replacing first element with 0

    Parameters
    ----------
    obj : numpy array or Series

    Return
    ------
    shifted : numpy array or Series

    """
    if isinstance(obj, np.ndarray):
        shifted = np.roll(obj, shift=1)
        shifted[0] = 0
    elif isinstance(obj, pd.Series):
        shifted = obj.shift(1).fillna(0)
    return shifted


def prepend_zero(df):
    """"Prepend zero indexed row with value 0

    Parameters
    ----------
        df : single column dataframe

    Returns
    -------
        df : same df with 1 additional row prepended
    """
    df.loc[0] = 0
    return df.sort_index()


def calculate_cumulative_index(df):
    """ Return cumulative index

    Parameters
    ----------
        df : single column df

    Returns
    -------
        df : sigle column df containing cumulative index

    """
    return (1 + df).cumprod()


def calculate_cumulative_index_conjugate(df):
    """ Return cumulative index (conjugate)

    Parameters
    ----------
        df : single column df

    Returns
    -------
        df : sigle column df containing conjugate cumulative index

    """
    return (1 - df).cumprod()


def get_tar_at_pensiondate(csv_file, long_format=False):
    """ DEPRECIATED - use predict_factors_at_pensionage
    from the CashFlows class
    """
    df = pd.read_csv(csv_file)
    index = ['geslacht', 'leeftijd', 'pensioenlfd']
    if long_format:
        df_long = pd.wide_to_long(df, stubnames='tar',
                                  i=index,
                                  j='aanspraak',
                                  sep='_',
                                  suffix='\D+')
        return df_long
    else:
        return df.set_index(index)


def present_value(cfs, intrest=2.5):
    """ Return present value of given series of cashflows at either
    fixed intrest rate or yield curve

    Parameters
    ----------
        cfs : Series
        intrest : float or Series containing yield curve

    Return
    ------
        pv : float
    """

    if isinstance(intrest, pd.Series):
        intrest = intrest.values
        n = min(len(intrest), len(cfs))
        yearnr = np.arange(n)
        v = 1 / (1 + intrest[:n]/100.)**yearnr

    if isinstance(intrest, int):
        n = len(cfs)
        yearnr = np.arange(n)
        v = 1 / (1 + intrest/100.)**yearnr

    return sum(v * cfs[:n])


def stack_lookup_table(df, colname='value'):
    """ Converts lookup table to long format for performing easy lookups
    """
    if len(df.columns) > 1:
        df.columns.name = 'simulnr'
        stacked = df.stack()
        stacked = pd.DataFrame(stacked, columns=[colname])
        # here we have to so some wranging to make sure index
        # simulnr is casted to int
        current_index = list(stacked.index.names)
        stacked = stacked.reset_index()
        stacked['simulnr'] = stacked.simulnr.astype('int')
        stacked = stacked.set_index(current_index)
        return stacked
    else:
        df['simulnr'] = 1
        return df.set_index('simulnr', append=True)


def modulo_map(x, n):
    """ Maps any positive int to int in (1, 2, .... n})
    """
    return (x - 1)%n + 1


def calculate_portfolio_return(lifecycle, stocks, bonds):
    """ Return portfiolio return combining LC, stocks, bonds

    Parameters
    ----------
        lifecycle : lookup table indexed by leeftijd
        stocks    : lookup table indexed by jaar
        bonds     : lookup table indexed by jaar

    Return
    ------
        lookup_table_return : lookup table indexed by leeftijd, jaar, simulnr

    """
    # construct new df
    lifecycle['tmp'] = 1
    stocks['tmp'] = 1

    df = pd.merge(lifecycle.reset_index(),
                  stocks.reset_index(), on='tmp')
    lifecycle.drop('tmp', inplace=True, axis=1)
    stocks.drop('tmp', inplace=True, axis=1)

    df = df[['leeftijd', 'jaar', 'simulnr']]
    max_age = lifecycle.reset_index().leeftijd.max()
    df = df[df.leeftijd + df.jaar <= max_age + 1]

    # join lifecycle & returns stocks & bonds into df
    df['future_age'] = df.leeftijd + df.jaar - 1
    df = df.join(lifecycle, on='future_age')

    df['simulnr_cpy'] = df.simulnr
    n = stocks.index.get_level_values('simulnr').max()
    df['simulnr'] = df.simulnr_cpy.map(lambda x: modulo_map(x, n))
    df = df.join(stocks, on=['jaar', 'simulnr'])

    n = bonds.index.get_level_values('simulnr').max()
    df['simulnr'] = df.simulnr_cpy.map(lambda x: modulo_map(x, n))
    df = df.join(bonds, on=['jaar', 'simulnr'])
    df['simulnr'] = df.simulnr_cpy
    df.drop('simulnr_cpy', inplace=True, axis=1)

    df['pct_rendement_ultimo'] = (
        df.pct_aandelen * df.pct_rendement_aandelen +
        (1 - df.pct_aandelen) * df.pct_rendement_obligaties
        )
    df.drop('future_age', inplace=True, axis=1)
    return df.set_index(['leeftijd', 'jaar', 'simulnr'])


def max_percentage_difference(df, test_cols, calculated_cols):
    """ Return percentage maximum difference between test_cols and calculated_cols

    Parameters
    ----------
    df              : DataFrame
        contains columns to be compared
    test_cols       : list of str
    calculated_cols : list of str

    Returns
    -------
    max_pct_difference  : float
        max. % difference (between 0 and 100)
    """
    test_values = df[test_cols].values
    calculated_values = df[calculated_cols].values
    deltas = test_values - calculated_values
    pct_deltas = np.divide(deltas, test_values, where=test_values!=0)
    return 100 * np.max(np.abs(pct_deltas))


def compare(df, test_cols, calculated_cols):
    """ Compares indicated colums elementwise

    Parameters
    ----------
    df        : DataFrame
    test_cols : list of str
    calculated_cols : list of str

    Returns
    -------
    result    : DataFrame
        long format, sorted by pct_diff in descending order


    Example
    -------
    >>> df = pd.DataFrame({'a': [10, 20, 30],
                           'b': [ 9, 21, 29],
                           'c': [85, 70, 90],
                           'd': [86, 71, 91]},
                 index=pd.MultiIndex.from_tuples([(1, 1), (1, 2), (2, 1)]))
    >>> df.index.set_names(['idx1', 'idx2'], inplace=True)
    >>> result = compare(df, ['a', 'c'], ['b', 'd'])
    >>> result.rename(index=str, columns={'test_col': 'tc',
                                          'calculated_col': 'cc',
                                          'test_value': 'tv',
                                          'calculated_value': 'cv',
                                          'pct_diff': '%d'})

    >>>                tc  cc  tv  cv  %d
        idx1    idx2
           1       1   a   b   10  9   10.00
           1       2   a   b   20  21  5.00
           2       1   a   b   30  29  3.33
           1       2   c   d   70  71  1.43
           1       1   c   d   85  86  1.18
           2       1   c   d   90  91  1.11
    """
    test_values = df[test_cols].stack()
    calculated_values = df[calculated_cols].stack()
    test_levels = test_values.index.get_level_values(-1)
    calculated_levels = calculated_values.index.get_level_values(-1)
    result = pd.DataFrame([test_levels, calculated_levels,
                           test_values.values, calculated_values.values],
                          index=['test_col', 'calculated_col', 'test_value',
                                 'calculated_value']).T

    new_index = test_values.index.droplevel(-1)
    result.set_index(new_index, inplace=True)
    pct_diff = (lambda x, y: np.abs(x - y) if y == 0
                else 100 * np.abs((x - y) / y))
    result['pct_diff'] = np.vectorize(pct_diff)(
        result.calculated_value, result.test_value)
    result.sort_values(by='pct_diff', ascending=False, inplace=True)
    result['pct_diff'] = result.pct_diff.map(lambda x: round(x, 2))
    return result
