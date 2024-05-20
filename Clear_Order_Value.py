# Author: Casey Betts, 2024
# This file executes the funcitons necessary to create a layer of orders in clear weather
# with overlapping order's dollar values combined
# File will require a PROD active orders layer and a today's ONV layer to run

import arcpy

def ms_export(layer, location, name):
    """ Exports the given layer to the given location with the given identifier appended to the given name """

    out_file = str(location) + "\\" + str(name)
    arcpy.AddMessage("Output file name: " + out_file)
    arcpy.management.MultipartToSinglepart(layer, out_file)

#  Select orders intersecting a given rev 
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
def create_strip_overlay(orders_layer, rev):
    """ Creates a .gdb layer containing a strip overlay of the given layer """
    
    # with arcpy.EnvManager(outputCoordinateSystem='PROJCS["WGS_1984_World_Mercator",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],UNIT["Meter",1.0]]'):
    arcpy.cartography.GridIndexFeatures("CSI_" + rev + "_strips", orders_layer, "INTERSECTFEATURE", "NO_USEPAGEUNIT", None, "15 Kilometers", "60 Kilometers", None, 369, 853, None, "NO_LABELFROMORIGIN")
        
    return "CSI_" + rev + "_strips"

# Create point feature from layer
def create_point_feature(orders_layer, out_feature_class):
    """ Given an order layer and output location this creates a point featuer at the center of each order """
    
    arcpy.management.FeatureToPoint(orders_layer, out_feature_class, "CENTROID")

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

# Create order layers
def create_order_layers(prod, onv, rev):
    """ Creates the Base order layer, the feature_to_polygon layer, and the spatial join layer """

    # Select the orders under the rev
    select_orders_by_rev(prod, onv, rev)
    
    # Export the order layer (strip overlay does not seem to work without an exported feature)
    arcpy.management.MultipartToSinglepart(prod, "CSI_" + rev + "_PROD")
    prod_layer = "CSI_" + rev + "_PROD"

    # Add a field to the prod layer and calculate the CSI value
    arcpy.management.CalculateField(prod_layer, "CSI_Value", "(100-(!tasking_priority!-700))**1.5", "PYTHON3", '', "LONG", "NO_ENFORCE_DOMAINS")
    
    # Create an overlay of strip sized polygons
    strip_layer = create_strip_overlay(prod_layer, rev)
    arcpy.AddMessage("stirp layer: " + strip_layer)
    
    # Create a feature to polygon layer
    arcpy.management.FeatureToPolygon("CSI_" + rev + "_PROD" + ";" + "CSI_" + rev + "_strips", 
                                      "CSI_" + rev + "_FtP", 
                                      None, 
                                      "ATTRIBUTES", 
                                      None)

    # Create a spatial join layer to combine overlaping polygons into one and sum the CSI_value
    arcpy.analysis.SpatialJoin("CSI_" + rev + "_FtP", 
                               prod_layer, 
                               "CSI_" + rev + "_SJ", 
                               "JOIN_ONE_TO_ONE", 
                               "KEEP_ALL", 
                               'FID_PROD_76429 "FID_PROD_76429" true true false 4 Long 0 0,First,#,PROD_76429,CSI_Value,-1,-1;CSI_Value "CSI_Value" true true false 8 Double 0 0,Sum,#,PROD_76429,CSI_Value,-1,-1;', "HAVE_THEIR_CENTER_IN", 
                               None, 
                               '')

# Create weather shapefile
def create_cloud_shape(onv, weather, rev):
    """ Creates a shapefile of the areas on a given rev that have cloud cover """

    # Clip weather raster to rev
    #r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\EWS-Forecasts\ACMFS_2024-01-26T00-18-07-000Z_-PT1M39S.tif\Band_1"
    arcpy.management.Clip(weather, 
                          "-180 -90 180 90", 
                          "CSI_" + rev + "_weather_raster", 
                          onv, 
                          "0", 
                          "ClippingGeometry", 
                          "NO_MAINTAIN_EXTENT")
    
    rev_raster = "CSI_" + rev + "_weather_raster"
    
    # Create a polygon from the weather raster
    with arcpy.EnvManager(outputZFlag="Disabled", outputMFlag="Disabled"):
        arcpy.conversion.RasterToPolygon(rev_raster, 
                                         "CSI_" + rev + "_clouds", 
                                         "SIMPLIFY", 
                                         "Value", 
                                         "SINGLE_OUTER_PART", 
                                         None)
        
def add_layers_to_map(layer1):
    """ Will add the desired layers to the map and symbolize them """

    # Get the active map document and data frame
    project = arcpy.mp.ArcGISProject("CURRENT")
    map = project.activeMap

    # Add the feature layer to the map
    map.addDataFromPath(layer1)

    # Get the symbology from the symbology template layer
    clear_orders = map.listLayers()[0]
    source_layer_name = r"Clear_Orders_Symbology_Template"

    for layer in map.listLayers():
        if layer.name == source_layer_name:
            source_layer = layer
            break
    else:
        raise Exception(f"Source layer '{source_layer_name}' not found in the TOC.")
    
    # Apply the symbology to the target layer
    clear_orders.symbology = source_layer.symbology

# Run full series
def run(prod, onv, weather, rev):
    """ Runs all the functions """

    # Path to the geodatabase
    arcpy.env.workspace = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\CSI_GeoDatabase.gdb\\"

    # Create order layers
    # create_order_layers(prod, onv, rev)
    sj_layer = "CSI_" + rev + "_SJ"

    # create_cloud_shape(onv, weather, rev)
    cloud_layer = "CSI_" + rev + "_clouds"

    # Create order layer in clear areas only
    add_layers_to_map(arcpy.analysis.Erase(sj_layer, cloud_layer, "CSI_" + rev + "_clear_orders", None))

 
