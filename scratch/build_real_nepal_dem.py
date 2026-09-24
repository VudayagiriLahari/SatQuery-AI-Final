import urllib.request
import math
import io
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.merge import merge
import numpy as np

print("Calculating AWS Open Data SRTM / Mapzen elevation tiles for Nepal Rasuwa bounds...")

# Open reference GeoTIFF to get exact CRS, transform, dimensions
with rasterio.open("data/test_images/nepal_before_flood.tif") as ref:
    dst_crs = ref.crs
    dst_transform = ref.transform
    dst_width = ref.width
    dst_height = ref.height
    bounds = ref.bounds

print(f"Nepal bounds: {bounds}, dimensions: {dst_width}x{dst_height}")

def deg2num(lat_deg, lon_deg, zoom=10):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# Gather required tiles covering bounds
zoom = 10
tiles = set()
for lat in [bounds.bottom, bounds.top]:
    for lon in [bounds.left, bounds.right]:
        tiles.add(deg2num(lat, lon, zoom))

print("Required zoom 10 tiles:", tiles)

sources = []
for xtile, ytile in tiles:
    url = f"https://elevation-tiles-prod.s3.amazonaws.com/geotiff/{zoom}/{xtile}/{ytile}.tif"
    print(f"Downloading SRTM tile: {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'SatQuery/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ds = rasterio.open(io.BytesIO(resp.read()))
            sources.append(ds)
            print(f"Loaded tile ({xtile}, {ytile}) - shape: {ds.shape}, CRS: {ds.crs}")
    except Exception as e:
        print(f"Tile download error for ({xtile}, {ytile}): {e}")

if sources:
    mosaic, out_trans = merge(sources)
    print(f"Merged DEM mosaic shape: {mosaic.shape}, CRS: {sources[0].crs}")
    
    destination = np.zeros((1, dst_height, dst_width), dtype=np.float32)
    
    reproject(
        source=mosaic,
        destination=destination,
        src_transform=out_trans,
        src_crs=sources[0].crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    
    # Clip any invalid nodata to minimum terrain elevation
    destination[destination < 0] = 500.0 # Min valley floor in Trishuli is ~600m
    
    print(f"Reprojected Nepal DEM! Elevation range: Min {destination.min():.1f}m, Max {destination.max():.1f}m, Mean {destination.mean():.1f}m")
    
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': -9999.0,
        'width': dst_width,
        'height': dst_height,
        'count': 1,
        'crs': dst_crs,
        'transform': dst_transform
    }
    
    with rasterio.open("scratch/nepal_dem.tif", "w", **profile) as dst:
        dst.write(destination[0], 1)
        
    print("Saved scratch/nepal_dem.tif successfully!")
else:
    print("Error: No elevation tiles could be downloaded.")
