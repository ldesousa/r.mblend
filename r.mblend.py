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

index = 0
TMP_MAPS = []


def getTemporaryIdentifier():
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


if __name__ == '__main__':
    gscript.use_temp_region()
	atexit.register(cleanup)
    main()

