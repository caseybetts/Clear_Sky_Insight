# Author: Casey Betts, 2024
# This file executes the funcitons necessary to create a layer of order in clear weather
# with overlapping order's dollar values combined
# File will require a PROD active orders layer and a today's ONV layer to run

import arcpy

def ms_export(layer, location, name):
    """ Exports the given layer to the given location with the given identifier appended to the given name """

    out_file = str(location) + "\\" + str(name)
    arcpy.AddMessage("Output file name: " + out_file)
    arcpy.management.MultipartToSinglepart(layer, out_file)

#  Given a rev number, the ONV layer and the PROD layer select all intersecting orders 
# Export the selection to a .gdb
def select_orders_by_rev(orders_layer, onv_layer, rev):
    """ Creates a .gdb layer containing all orders intersecting a given rev """

    # Select the rev in the ONV file
    selection = f"\"rev_num\" = {rev}"
    arcpy.management.SelectLayerByAttribute(onv_layer, 'NEW_SELECTION', selection)

    # Select the orders intersecting the ONV selection 
    arcpy.management.SelectLayerByLocation(orders_layer, 
                                            "INTERSECT", 
                                            onv_layer, 
                                            None, 
                                            "NEW_SELECTION", 
                                            "NOT_INVERT")

# Create a strip overlay of the order layer with Grid Index Features
def create_strip_overlay(orders_layer, out_feature_class):
    """ Creates a .gdb layer containing a strip overlay of the given layer """
    
    # with arcpy.EnvManager(outputCoordinateSystem='PROJCS["WGS_1984_World_Mercator",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],UNIT["Meter",1.0]]'):
    arcpy.cartography.GridIndexFeatures(out_feature_class, orders_layer, "INTERSECTFEATURE", "NO_USEPAGEUNIT", None, "15 Kilometers", "60 Kilometers", None, 369, 853, None, "NO_LABELFROMORIGIN")

# "Flatten" the orders layer by using Feature to Polygon (to divide overlaping areas from non-overlaping ones)

# Use Spatial Join to combine overlaping polygons into one and sum the price/sqkm
        
# Clip the weather raster file to layer
def weather_over_orders(weather_raster, orders_layer, output_location):
    """ Creates a raster file of the given weather file clipped to the orders layer """

    arcpy.management.Clip(weather_raster, 
                          "", 
                          output_location, 
                          orders_layer, 
                          "255", 
                          "ClippingGeometry", 
                          "NO_MAINTAIN_EXTENT")

# Run full series
def run(prod, onv, rev):
    """ Runs all the functions """

    # Path to the geodatabase
    geodatabase_path = "C:\\Users\\ca003927\\OneDrive - Maxar Technologies Holdings Inc\\Private Drop\\Git\\Clear_Sky_Insight\\CSI_GeoDatabase.gdb"
    # Select the orders under the rev
    select_orders_by_rev(prod, onv, rev)

    # Export the order layer (strip overlay does not seem to work without an exported feature)
    arcpy.management.MultipartToSinglepart(prod, geodatabase_path + "\PROD_" + rev)
    
    # Create an overlay of strip sized polygons
    create_strip_overlay(geodatabase_path + "\PROD_" + rev, geodatabase_path + "\strips_" + rev)

    # Create a point feature of the order layer
    arcpy.management.FeatureToPoint(geodatabase_path + "\PROD_" + rev, geodatabase_path + "\PROD_Point_Feature" + rev, "CENTROID")
    
    # Create a feature to polygon layer
    arcpy.management.FeatureToPolygon(geodatabase_path + "\PROD_" + rev, geodatabase_path + "\FtP_" + rev, None, "ATTRIBUTES", None)

    # Create a spatial join layer
    arcpy.analysis.SpatialJoin(geodatabase_path + "\FtP_" + rev, 
                               geodatabase_path + "\PROD_" + rev, 
                               geodatabase_path + "\SJ_" + rev, 
                               "JOIN_ONE_TO_ONE", 
                               "KEEP_ALL", 
                               'PricePerArea "PricePerArea" true true false 255 Long 0 0,Sum,#,FtP_75898,price_per_area,-1,-1', 
                               "INTERSECT", 
                               None, 
                               '')



    # weather_output_location = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\CSI_Subdivide.gdb\clipped_weather" + "_" + rev + ".tif"
    # arcpy.AddMessage(weather_output_location)
    # weather_over_orders(weather_raster, rev_orders_location, weather_output_location)

