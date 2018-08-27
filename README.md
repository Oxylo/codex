# codex
Actuarial library for benefit projections and simulations

Installation (local)
====================

    $ git clone https://github.com/Oxylo/CODEX3.git codex3
    $ pip install -r requirements.txt
    
    
Run program (inside python CLI or Jupyter)
==========================================

The idea is to create a Tableau object first, containing all data and projection calculations.

Tableau objects is initialized with the following (default) parameters:
* xlswb='/home/pieter/projects/codex/data/codex_data_db.xls'
* nsimuls=1
* maxyears=None

    $ from codex import Tableau
    $ tab = Tableau()
    $ my_tableau = tab.tableau
    
