#!/usr/bin/env python

#%module
#% description: Blend tow rasters of different spatial resolution
#% keyword: raster
#% keyword: resolution
#%end
#%option HIGH
#% key: high
#%end
#%option LOW
#% key: low
#%end

import os
import atexit
import grass.script as gscript

index = 0
TMP_MAPS = []


def getTemporaryIdentifier():
    global index
    id = 'tmp_raster_' + str(os.getpid()) + str(index)
    index = index + 1
    TMP_MAPS.append(id)
    return id


def cleanup():
    gscript.run_command('g.remove', type='raster', name=','.join(TMP_MAPS), flags='f')


def main():
    options, flags = gscript.parser()
    high = options['high']
    low = options['low']
    print(high, low)

	# Set the region to the two input rasters
    gscript.run_command('g.region', raster=high + "," + low)
    print gscript.region()

    # Make cell size compatible
    low_res_inter = getTemporaryIdentifier()
    gscript.run_command('r.resamp.interp', input=low, output=low_res_inter, method='nearest')

	# Vectorise rasters
    high_vect = getTemporaryIdentifier()
    low_vect = getTemporaryIdentifier()
    gscript.run_command('r.to.vect', input=high, output=high_vect, type='area')
    gscript.run_command('r.to.vect', input=low, output=low_vect, type='area')

    # Dissolve and overlay to obtain extent to interpolate
    low_extent = getTemporaryIdentifier()
    high_extent = getTemporaryIdentifier()
    interpol_area = getTemporaryIdentifier()
    gscript.run_command('v.db.addcolumn', map=low_vect, columns="flag integer")
    gscript.run_command('v.db.update', map=low_vect, col="flag", qcol="1")
    gscript.run_command('v.dissolve', input=low_vect, output=low_extent, column="flag")
    gscript.run_command('v.db.addcolumn', map=high_vect, columns="flag integer")
    gscript.run_command('v.db.update', map=high_vect, col="flag", qcol="1")
    gscript.run_command('v.dissolve', input=high_vect, output=high_extent, column="flag")
    gscript.run_command('v.overlay', ainput=low_extent, binput=high_extent, output=interpol_area, operator='not')


if __name__ == '__main__':
    atexit.register(cleanup)
    gscript.use_temp_region()
    main()

