""" Vectorized functions:
for better perfomance  & cleaner code
"""
import numpy as np
import formulae as f


def pensiondate(birthdate, pension_age):
    """ Vectorized version of formulae.pensiondate
    """
    v = np.frompyfunc(f.pensiondate, 2, 1)
    return v(birthdate, pension_age)


def future_service_years(calculation_date, pension_date):
    """ Vectorized version of formulae.future_service_years
    """
    vectorized = np.frompyfunc(f.future_service_years, 2, 1)
    return vectorized(calculation_date, pension_date)


def roundup(arr):
    """ Vectorized version of formulae.roundup
    """
    vectorized = np.frompyfunc(f.roundup, 1, 1)
    return vectorized(arr)


def nprojection_years(birthdate, calculation_date, pension_age):
    """ Return number of projection years for projection frame
    """
    pension_date = pensiondate(birthdate, pension_age)
    fsy = future_service_years(calculation_date, pension_date)
    return roundup(fsy)


def age(pension_age, future_service_years):
    """ Return age in years
    """
    return pension_age - future_service_years


def past_service_years(service_date, calculation_date,
                       method='Oxylo'):
    """ Vectorized version of formulae.past_service_years
    """
    vectorized = np.frompyfunc(f.past_service_years, 3, 1)
    return vectorized(service_date, calculation_date, method)


def total_service_years(past_service_years, future_service_years):
    """ Return total service years
    """
    return past_service_years + future_service_years


def ft_base(ft_salary, offset, max_salary):
    """ Return full time (premium or pension) base
    """
    return np.maximum(0, np.minimum(ft_salary, max_salary) - offset)


def employee_contribution(ft_pension_base,
                          pct_employee_contribution, pct_parttime):
    """ Return employee contribution in euros
    """
    return pct_parttime * pct_employee_contribution * ft_pension_base


def pct_to_cum_index(s, year, sign=1, adjust=0):
    """ Returns cumulative index of s

    Parameters
    ----------
    s : numpy array
        Contains fractions (like 0.02 for 2 percent etc)
    year : numpy array
        Projection year
    sign : float default 1
    adjust : float between 0 and 1
        Indicates moment of paymeny during year (see note)

    Returns
    -------
    cumulative_index : numpy array

    Note
    ----
    adjust = 0   : payment at beginning of each projection year
    adjust = 0.5 : payment at middle of eacht projection year
    adjust = 1   : payment at end of each projection year
    """

    factor = (1 + sign * s)
    adjustment = factor**(adjust - 1)
    return adjustment * factor.cumprod()


def eur_return(cumulated_capital, eur_employee_contribution,
               pct_yield_ultimo, year, adjust=0):
    """ Return euro return

    Parameters
    ----------
    cumulated_capital : Series
    eur_employee_contribution : Series
    pct_yield_ultimo : Series
    adjust : float between 0 and 1
        Indicates moment of payments during year (see note)

    Returns
    -------
    eur_return : Series

    Note
    ----
    adjust = 0   : payment at beginning of each projection year
    adjust = 0.5 : payment at middle of eacht projection year
    adjust = 1   : payment at end of each projection year
    """
    cumulated = cumulated_capital - adjust * eur_employee_contribution
    rate = pct_yield_ultimo / (1 + pct_yield_ultimo)
    return rate * cumulated

