import shutil
import os
import json

base_data_dir = "data"

# 1. Nepal Municipalities / Boundaries
shutil.copyfile("scratch/nepal_municipalities.geojson", os.path.join(base_data_dir, "boundaries", "nepal_villages.geojson"))
shutil.copyfile("scratch/nepal_municipalities_visual.geojson", os.path.join(base_data_dir, "boundaries", "nepal_villages_visual.geojson"))
print("Installed real Nepal Municipalities into data/boundaries/nepal_villages.geojson")

# 2. Nepal Population (Census 2021)
shutil.copyfile("scratch/nepal_municipalities.geojson", os.path.join(base_data_dir, "population", "nepal_population.geojson"))
print("Installed real Nepal CBS Census population data into data/population/nepal_population.geojson")

# 3. Nepal Road Network
shutil.copyfile("scratch/nepal_roads.geojson", os.path.join(base_data_dir, "roads", "nepal_roads.geojson"))
print("Installed real Nepal OSM road network into data/roads/nepal_roads.geojson")

# 4. Nepal Buildings
shutil.copyfile("scratch/nepal_buildings.geojson", os.path.join(base_data_dir, "buildings", "nepal_buildings.geojson"))
print("Installed real Nepal OSM building footprints into data/buildings/nepal_buildings.geojson")

# 5. Nepal Facilities / Safe Shelters
shutil.copyfile("scratch/nepal_facilities.geojson", os.path.join(base_data_dir, "pois", "nepal_facilities.geojson"))
print("Installed real Nepal evacuation facilities into data/pois/nepal_facilities.geojson")

# 6. Nepal DEM
shutil.copyfile("scratch/nepal_dem.tif", os.path.join(base_data_dir, "dem", "nepal_dem_elevation.tif"))
print("Installed real Nepal SRTM DEM elevation raster into data/dem/nepal_dem_elevation.tif")
