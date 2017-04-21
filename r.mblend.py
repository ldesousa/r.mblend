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
WEIGHT_MAX = 10000

def getTemporaryIdentifier():
    global index
    global TMP_MAPS
    id = 'tmp_raster_' + str(os.getpid()) + str(index)
    index = index + 1
    TMP_MAPS.append(id)
    return id


def cleanup():
    print("Temporary raster to remove:")
    print(TMP_MAPS)
    gscript.run_command('g.remove', type='raster', name=','.join(TMP_MAPS), flags='f')


def main():
    options, flags = gscript.parser()
    high = options['high']
    low = options['low']
    print(high, low)
    
    # TODO
    # 1. Obtain resolution
    # 2. Add input for distance cut off

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

	# Compute difference between the two rasters and vectorise to points
    diff = getTemporaryIdentifier()
    diff_points = getTemporaryIdentifier()
    gscript.mapcalc(diff + " = highRes - lowResInter")
    gscript.run_command('r.to.vect', input=diff, output=diff_points, type='point')

	# Obtain edge points of the high resolution raster
    interpol_area_buff = getTemporaryIdentifier()
    diff_points_edge = getTemporaryIdentifier()
	# 1. buffer around area of interest - pixel size must be known
    gscript.run_command('v.buffer', input=interpol_area, output=interpol_area_buff, type='area', distance=20)
	# 2. get the points along the edge
    gscript.run_command('v.select', ainput=diff_points, binput=interpol_area_buff, output=diff_points_edge, operator='overlap')

    # Get points in low resolution farther away from high resolution raster
    dist_high = getTemporaryIdentifier()
    weights = getTemporaryIdentifier()
    weight_points = getTemporaryIdentifier()
    interpol_area_in_buff = getTemporaryIdentifier()
    weight_points_all_edges = getTemporaryIdentifier()
    weight_points_edge = getTemporaryIdentifier()
    # 1. Distance to High resolution raster
    gscript.run_command('r.grow.distance', input=high, distance=dist_high)
    # 2. Rescale to the interval [0,10000]: these are the weights
    gscript.run_command('r.rescale', input=dist_high, output=weights, to='0,' + str(WEIGHT_MAX))
    # 3. Vectorise distances to points
    gscript.run_command('r.to.vect', input=weights, output=weight_points, type='point')
    # 4. Create inner buffer to interpolation area 
    gscript.run_command('v.buffer', input=interpol_area, output=interpol_area_in_buff, type='area', distance='-20')
    # 5. Select points at the border
    gscript.run_command('v.select', ainput=weight_points, binput=interpol_area_in_buff, output=weight_points_all_edges, operator='disjoint')
    # 6. Select those with higher weights
    gscript.run_command('v.extract', input=weight_points_all_edges, output=weight_points_edge, where="value>9500")

    # Merge the two point edges and set low res edge to zero
    points_edges = getTemporaryIdentifier()
    gscript.run_command('v.db.update', map=weight_points_edge, column='value', value='0')
    gscript.run_command('v.patch', input=weight_points_edge+','+diff_points_edge, output=points_edges, flags='e')


if __name__ == '__main__':
    atexit.register(cleanup)
    gscript.use_temp_region()
    main()

