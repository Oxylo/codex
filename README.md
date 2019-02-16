# codex
Actuarial library for benefit projections and simulations.

Installation (local)
====================

    $ git clone https://github.com/Oxylo/codex.git your_project_name
    $ pip install -r requirements.txt
    
    
Usage
=====

Copy data/template.xlsx or data/template_incl_scenarios.xlsx to newdata.xlsx and fill out data in this sheet. 

    >>> from codex import Tableau
    >>> tab = Tableau(xlswb='newdata.xlsx', nsimuls=1)
    >>> detailed_output = tab.tableau
    >>> summary = tab.add_summary()


Demo
====

Run the Jupyter notebook Demo.ipynb.

Tests
=====

    $ cd codex
    $ pytest -s tests/test_pwc.py
    $ pytest -s tests/test_wtw.py
    $ pytest -s tests/test_wtw_incl_scenarios.py
    $ pytest # run all 3 tests (this can take a while, please be patient!)



How it works
============ 
When the Tableau objects is initialized, all tables from newdata.xlsx are merged into one large table (a so called Tableau) featuring one record for each combination of employee, pension plan, claim, simulation and projection year ("Cartesian product of tables"). For example if you fill your newdata.xlsx with one 50 year old employee, 3 pension plans containing 2 claims each for 2001 simulations, Tableau will contain 1 employee x 3 plans x 2 claims x 2001 simulations x 18 projection years = 216,108 records (assuming pension age to be 68 years). Projection calculations are performed on each record.
The next step is running the add_summary method, resulting in a table with 1 record for each combination of employee, pension plan and simulation number. For each record, this table contains the projected capitals and pension entitlements at the pension date. In the example above, summary will contain 1 employee x 3 plans x  2001 simulations =  6,003 records.
   


  


    
