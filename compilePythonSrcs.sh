#!/bin/bash
pyflakes3 test.py
python3 compile_it.py test.py test.pyc
pyflakes3 feinstaubpi.py
python3 compile_it.py feinstaubpi.py feinstaubpi.pyc 
