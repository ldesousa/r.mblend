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
    elevation = options['high']
    shade = options['low']
    print(elevation, shade)

if __name__ == '__main__':
    main()

