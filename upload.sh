#!/bin/bash
# This script expects the SVN repository to be checked out:
# http://svn.osgeo.org/grass/grass-addons/grass7/raster/r.mblend/

cd ~/git/r.mblend

# Check PEP8 compliance
pep8 --config=tools/pep8config.txt r.mblend.py

# Copy files to svn folder
cd ~/svn/r.mblend
cp ~/git/r.mblend/*.py ~/git/r.mblend/*.html  ~/git/r.mblend/*.png  ~/git/r.mblend/*.md . 

# Apply propset
~/git/r.mblend/tools/module_svn_propset.sh r.mblend.py r.mblend.html

# SVN add
svn add *

# Commit
svn commit -m "$1"