# Set the region to the two input rasters
g.region raster=highRes,lowRes

# Make cell size compatible
r.resamp.interp input=lowRes output=lowResInter method=nearest

# Vectorise
r.to.vect input=highRes output=highRes type=area
r.to.vect input=lowRes output=lowRes type=area

# Dissolve
v.db.addcolumn map=lowRes columns="flag integer"
v.db.update lowRes col=flag qcol="1"
v.dissolve input=lowRes output=lowResExtent column=flag --overwrite

# Overlay difference to obtain area to interpolate
v.overlay ainput=lowResExtent binput=highResExtent output=interpol_area operator=not

# Compute difference between the two rasters
r.mapcalc "diff = highRes - lowResInter"

# Vectorise differences into points
r.to.vect input=diff output=diffPoints type=point

# Get highRes edge points
# 1. buffer around area of interest - pixel size must be known
v.buffer input=interpol_area output=interpol_area_buff type=area distance=20
# 2. get the points along the edge
v.select ainput=diffPoints binput=interpol_area_buff output=diffPointsEdge operator=overlap

# Distance to High resolution raster
r.grow.distance input=highRes distance=dist_highRes

# Rescale to the interval [0,10000]: these are the weights
r.rescale input=dist_highRes output=weights to=0,10000

# Get farther away points (with distance)
# 1. Vectorise distances to points
r.to.vect input=weights output=weightPoints type=point
# 2. Create inner buffer to interpolation area 
v.buffer input=interpol_area output=interpol_area_in_buff type=area distance=-20
# 3. Select points at the border
v.select ainput=weightPoints binput=interpol_area_in_buff output=wieghtPointsAllEdges operator=disjoint
# 4. Select those with higher weights
v.extract input=wieghtPointsAllEdges output=weightPointsEdge where="value>9500"

# Merge the two point edges
# 1. Bring values to zero
v.db.update map=weightPointsEdge column=value value=0
# 2. Merge
v.patch input=weightPointsEdge,diffPointsEdge output=pointsEdges -e

# Interpolate stitching raster
v.surf.idw input=pointsEdges column=value output=stitchingFull power=2 npoints=50 --overwrite
# Create mask
v.to.rast in=interpol_area out=interpol_area_mask use=val value=1 --overwrite
# Crop to area of interest
r.mapcalc "stitching = if(interpol_area_mask,stitchingFull)"

# Apply stitching
# Sum to low res
r.mapcalc "smoothLowRes = lowRes + stitching"
# Add both rasters
r.patch input=smoothLowRes,highRes output=result

# Next steps
https://github.com/wenzeslaus/python-grass-addon

