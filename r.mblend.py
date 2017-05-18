#!/usr/bin/env python

############################################################################
#
# MODULE:       r.mblend
#
# AUTHOR(S):    Luís Moreira de Sousa
#
# PURPOSE:      Blends two rasters of different spatial resolution.
#
# COPYRIGHT:    (c) 2017 Luís Moreira de Sousa
#
#               This programme is released under the European Union Public 
#               Licence v 1.1. Please consult the LICENCE file for details.
#
#############################################################################

#%module
#% description: Blends two rasters of different spatial resolution
#% keyword: raster
#% keyword: resolution
#%end
#%option HIGH
#% key: high
#%end
#%option LOW
#% key: low
#%end
#%option OUTPUT
#% key: output
#%end
#%option
#% key: far_edge
#% key_desc: value
#% type: double
#% description: Percentage of distance to high resolution raster used to determine far edge. Number between 0 and 100; 95% by default.
#% answer: 95
#% multiple: no
#% required: no
#%end

import os
import atexit
from time import gmtime, strftime
import grass.script as gscript

index = 0
TMP_MAPS = []
WEIGHT_MAX = 10000
COL_VALUE = 'value'
COL_FLAG = 'flag'


def getTemporaryIdentifier():
    global index
    global TMP_MAPS
    id = 'tmp_' + str(os.getpid()) + str(index)
    index = index + 1
    TMP_MAPS.append(id)
    return id


def cleanup():
    while len(TMP_MAPS) > 0:
        gscript.run_command('g.remove', type='all', name=TMP_MAPS.pop(), flags='f', quiet=True)


def main():

    options, flags = gscript.parser()
    high = options['high']
    low = options['low']
    output = options['output']
    far_edge = float(options['far_edge'])
    
    if(high is None or high == ""):
        print('ERROR: high is a mandatory parameter.')
        exit()
    
    if(low is None or low == ""):
        print('ERROR: low is a mandatory parameter.')
        exit()
     
    if(output is None or output == ""):
        print('ERROR: output is a mandatory parameter.')
        exit()
           
    if(far_edge < 0 or far_edge > 100):
        print('ERROR: far_edge must be a percentage between 0 and 100.')
        exit()

	# Set the region to the two input rasters
    gscript.run_command('g.region', raster=high + "," + low)
    # Determine cell side
    region = gscript.region()
    print(region)
    if region['nsres'] > region['ewres']:
        cell_side = region['nsres']
    else:
        cell_side = region['ewres']

    # Make cell size compatible
    low_res_inter = getTemporaryIdentifier()
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.resamp.interp input=low")
    gscript.run_command('r.resamp.interp', input=low, output=low_res_inter, method='nearest')
    
    # Obtain extent to interpolate
    low_extent_rast = getTemporaryIdentifier()
    high_extent_rast = getTemporaryIdentifier()
    low_extent = getTemporaryIdentifier()
    high_extent = getTemporaryIdentifier()
    interpol_area = getTemporaryIdentifier()
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " mapcalc low_extent_rast")
    gscript.mapcalc(low_extent_rast + ' = ' + low + ' * 0')
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " mapcalc high_extent_rast")
    gscript.mapcalc(high_extent_rast + ' = ' + high + ' * 0')
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.to.vect output=low_extent")
    gscript.run_command('r.to.vect', input=low_extent_rast, output=low_extent, type='area')
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.to.vect output=high_extent")
    gscript.run_command('r.to.vect', input=high_extent_rast, output=high_extent, type='area')
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.overlay output=interpol_area")
    gscript.run_command('v.overlay', ainput=low_extent, binput=high_extent, output=interpol_area, operator='not')

	# Compute difference between the two rasters and vectorise to points
    diff = getTemporaryIdentifier()
    diff_points = getTemporaryIdentifier()
    gscript.mapcalc(diff + ' = ' + high + ' - ' + low_res_inter)
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.to.vect output=diff_points")
    gscript.run_command('r.to.vect', input=diff, output=diff_points, type='point')

	# Obtain edge points of the high resolution raster
    interpol_area_buff = getTemporaryIdentifier()
    diff_points_edge = getTemporaryIdentifier()
	# 1. buffer around area of interest - pixel size must be known
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.buffer output=interpol_area_buff")
    gscript.run_command('v.buffer', input=interpol_area, output=interpol_area_buff, type='area', distance=cell_side)
	# 2. get the points along the edge
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.select output=diff_points_edge")
    gscript.run_command('v.select', ainput=diff_points, binput=interpol_area_buff, output=diff_points_edge, operator='overlap')

    # Get points in low resolution farther away from high resolution raster
    dist_high = getTemporaryIdentifier()
    weights = getTemporaryIdentifier()
    weight_points = getTemporaryIdentifier()
    interpol_area_in_buff = getTemporaryIdentifier()
    weight_points_all_edges = getTemporaryIdentifier()
    weight_points_edge = getTemporaryIdentifier()
    # 1. Distance to High resolution raster
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.grow.distance")
    gscript.run_command('r.grow.distance', input=high, distance=dist_high)
    # 2. Rescale to the interval [0,10000]: these are the weights
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.rescale output=weights")
    gscript.run_command('r.rescale', input=dist_high, output=weights, to='0,' + str(WEIGHT_MAX))
    # 3. Vectorise distances to points
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.to.vect output=weight_points")
    gscript.run_command('r.to.vect', input=weights, output=weight_points, type='point')
    # 4. Create inner buffer to interpolation area 
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.buffer output=interpol_area_in_buff")
    gscript.run_command('v.buffer', input=interpol_area, output=interpol_area_in_buff, type='area', distance='-' + str(cell_side))
    # 5. Select points at the border
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.select output=weight_points_all_edges")
    gscript.run_command('v.select', ainput=weight_points, binput=interpol_area_in_buff, output=weight_points_all_edges, operator='disjoint')
    # 6. Select those with higher weights
    cut_off = str(far_edge / 100 * WEIGHT_MAX)
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.extract output=weight_points_edge")
    gscript.run_command('v.extract', input=weight_points_all_edges, output=weight_points_edge, where=COL_VALUE + '>' + cut_off)

    # Merge the two point edges and set low res edge to zero
    points_edges = getTemporaryIdentifier()
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.db.update map=weight_points_edge")
    gscript.run_command('v.db.update', map=weight_points_edge, column=COL_VALUE, value='0')
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.patch output=points_edges")
    gscript.run_command('v.patch', input=weight_points_edge+','+diff_points_edge, output=points_edges, flags='e')

    # Interpolate stitching raster
    stitching_full = getTemporaryIdentifier()
    interpol_area_mask = getTemporaryIdentifier()
    stitching = getTemporaryIdentifier()
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.surf.idw output=stitching_full")
    gscript.run_command('v.surf.idw', input=points_edges, column=COL_VALUE, output=stitching_full, power=2, npoints=50)
    # Create mask
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " v.to.rast output=interpol_area_mask")
    gscript.run_command('v.to.rast', input=interpol_area, output=interpol_area_mask, use='val', value=1)
    # Crop to area of interest
    print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " mapcalc output=stitching")
    gscript.mapcalc(stitching + ' = if(' + interpol_area_mask + ',' + stitching_full+ ')')
    
    # Apply stitching
    smooth_low_res = getTemporaryIdentifier()
    # Sum to low res
    gscript.mapcalc(smooth_low_res + ' = ' + low_res_inter + ' + ' + stitching)
    # Add both rasters
    try:
        print("[r.mblend] " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " r.patch output=output")
        gscript.run_command('r.patch', input=smooth_low_res + ',' + high, output=output)
    except Exception, ex: 
        print('Failed to create smoothed raster.')
        exit()
        
    print('SUCCESS: smoothed raster created.')


if __name__ == '__main__':
    atexit.register(cleanup)
    gscript.use_temp_region()
    main()

