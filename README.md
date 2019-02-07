# codex
Actuarial library for benefit projections and simulations

Installation (local)
====================

    $ git clone https://github.com/Oxylo/codex.git my_project_name
    $ pip install -r requirements.txt
    
    
Example
=======

    >>> from codex import Tableau
    >>> tab = Tableau()
    >>> detailed_output = tab.tableau
    >>> summary = tab.add_summary()


Tests
=====

    $ cd codex
    $ pytest -s tests/test_pwc.py
    $ pytest -s tests/test_wtw.py
    $ pytest -s tests/test_wtw_incl_scenarios.py
    $ pytest # run all 3 tests (this can take a while, please be patient!)



Note: 
The idea is to create a Tableau object first, containing all data and projection calculations.

Tableau objects is initialized with the following (default) parameters:
* xlswb='/home/pieter/projects/codex/data/codex_data_db.xls'
* nsimuls=1
* maxyears=None


  


    
