""" formulae.py

Note
----
Functions that work for scalar input only.
"""
import math as m
from datetime import date


def pensiondate(birthdate, pension_age):
    """ Return pensiondate as 1st day of birth month
    """
    return date(birthdate.year + pension_age, birthdate.month, 1)


def future_service_years(calculation_date, pension_date):
    """ Return number of future service years
    """
    return (pension_date.year - calculation_date.year +
            (pension_date.month - calculation_date.month) / 12.)


def roundup(x):
    """ Return x rounded
    """
    return int(m.ceil(x))


def past_service_years(service_date, calculation_date,
                       method='Oxylo'):
    """ Return past service years
    """
    if method == 'Oxylo':
        return (calculation_date.year - service_date.year +
                calculation_date.month - service_date.month) / 12.
    if method == 'PwC':
        delta = (calculation_date - service_date)
        return delta.days / 365.25
