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

import grass.script as gscript

def main():
    options, flags = gscript.parser()
    high = options['high']
    low = options['low']
    print(high, low)

	# Set the region to the two input rasters
    gscript.run_command('g.region', raster=high + "," + low)
    print gscript.region()

if __name__ == '__main__':
    gscript.use_temp_region()
    main()

