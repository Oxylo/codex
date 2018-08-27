""" utils.py
Boiler plate code besides formulae, to keep main program short & tidy.
"""
import numpy as np
import pandas as pd


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
