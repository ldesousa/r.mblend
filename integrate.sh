#!/bin/bash

cd ~/git/r.mblend

# Check PEP8 compliance
pep8 --config=tools/pep8config.txt r.mblend.py

# Copy files to svn folder
cd ~/git/r.mbelnd
cp ~/git/r.mblend/*.py ~/git/r.mblend/*.html  ~/git/r.mblend/*.png . 

# Apply propset
~/git/r.mblend/tools/module_svn_propset.sh r.mblend.py r.mblend.html

# SVN add
svn add *

# Commit
svn commit -m