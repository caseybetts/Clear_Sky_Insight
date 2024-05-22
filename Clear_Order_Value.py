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

# Select available orders
def select_available_orders(prod, onv, rev):
    """ Select orders accessable on a given rev based on the order's max ONA vlaue """

    # File names
    onv_rev = "CSI_" + rev + "_onv"

    # Path to the geodatabase
    arcpy.env.workspace = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\CSI_GeoDatabase.gdb\\"
   
    # Select and export the given rev
    selection = f"\"rev_num\" = {rev} And days = 0"
    arcpy.conversion.ExportFeatures(onv, onv_rev, selection)

    # Definition query
    onv_query_1 = "ona = 45"
    onv_query_2 = "ona = 30"
    onv_query_3 = "ona = 20"

    # Create an onv feature layer using query 1 
    feature_layer = arcpy.management.MakeFeatureLayer(onv_rev, "FeatureLayer", onv_query_1)
    arcpy.AddMessage("Created feature layer from " + onv_rev)

    # Select orders intersecting the current onv feature layer
    arcpy.management.SelectLayerByLocation(prod, "INTERSECT", feature_layer, None, "ADD_TO_SELECTION",)

    # Deselect orders with ONA under 31
    arcpy.management.SelectLayerByAttribute(prod, "REMOVE_FROM_SELECTION", "max_ona < 31", None)

    # Create an onv feature layer using query 2
    feature_layer = arcpy.management.MakeFeatureLayer(onv_rev, "FeatureLayer", onv_query_2)
    arcpy.AddMessage("Created feature layer from " + onv_rev)
    
    # Select order intersecting the current onv feature layer
    arcpy.management.SelectLayerByLocation(prod, "INTERSECT", feature_layer, None, "ADD_TO_SELECTION",)

    # Export featuer layer
    # arcpy.conversion.ExportFeatures(feature_layer, "CSI_" + rev + "current_featuer_layer")

    # Deselect orders with ONA under 21
    arcpy.management.SelectLayerByAttribute(prod, "REMOVE_FROM_SELECTION", "max_ona < 21", None)

    # Create an onv feature layer using query 3
    feature_layer = arcpy.management.MakeFeatureLayer(onv_rev, "FeatureLayer", onv_query_3)
    arcpy.AddMessage("Created feature layer from " + onv_rev)
    
    # Select order intersecting the current onv feature layer
    arcpy.management.SelectLayerByLocation(prod, "INTERSECT", feature_layer, None, "ADD_TO_SELECTION",)

    arcpy.conversion.ExportFeatures(prod, "CSI_" + rev + "_prod")
    
# Create order layers
def create_order_layers(prod, onv, rev):
    """ Creates the Base order layer, the feature_to_polygon layer, and the spatial join layer """

    # Layer names
    prod_layer = "CSI_" + rev + "_PROD"
    FtP_layer = "CSI_" + rev + "_FtP"
    spatial_join_layer = "CSI_" + rev + "_SJ"

    # Select the orders under the rev
    select_orders_by_rev(prod, onv, rev)
    
    # Export the order layer (strip overlay does not seem to work without an exported feature)
    arcpy.management.MultipartToSinglepart(prod, prod_layer)
    

    # Add a field to the prod layer and calculate the CSI value
    arcpy.management.CalculateField(prod_layer, "CSI_Value", "(100-(!tasking_priority!-700))**1.5", "PYTHON3", '', "LONG", "NO_ENFORCE_DOMAINS")
    
    # Create a feature to polygon layer
    arcpy.management.FeatureToPolygon(prod_layer, 
                                      FtP_layer, 
                                      None, 
                                      "ATTRIBUTES", 
                                      None)

    # Create a spatial join layer to combine overlaping polygons into one and sum the CSI_value
    arcpy.analysis.SpatialJoin(FtP_layer, 
                               prod_layer, 
                               spatial_join_layer, 
                               "JOIN_ONE_TO_ONE", 
                               "KEEP_ALL", 
                               'FID_PROD_76429 "FID_PROD_76429" true true false 4 Long 0 0,First,#,PROD_76429,CSI_Value,-1,-1;CSI_Value "CSI_Value" true true false 8 Double 0 0,Sum,#,PROD_76429,CSI_Value,-1,-1;', "HAVE_THEIR_CENTER_IN", 
                               None, 
                               '')
    
    return spatial_join_layer

# Create weather shapefile
def create_cloud_shape(onv, weather, rev):
    """ Creates a shapefile of the areas on a given rev that have cloud cover """

    # Layer name
    rev_raster = "CSI_" + rev + "_weather_raster"
    rev_clouds = "CSI_" + rev + "_clouds"

    # Clip weather raster to rev
    arcpy.management.Clip(weather, 
                          "-180 -90 180 90", 
                          rev_raster, 
                          onv, 
                          "0", 
                          "ClippingGeometry", 
                          "NO_MAINTAIN_EXTENT")
    
    
    
    # Create a polygon from the weather raster
    with arcpy.EnvManager(outputZFlag="Disabled", outputMFlag="Disabled"):
        arcpy.conversion.RasterToPolygon(rev_raster, 
                                         rev_clouds, 
                                         "SIMPLIFY", 
                                         "Value", 
                                         "SINGLE_OUTER_PART", 
                                         None)
        
    return rev_clouds
        
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

# Create feature classes for orders, weather and strips
def create_feature_classes(prod, onv, weather, rev):
    """ Runs all the functions needed to produce the feature classes"""

    # Path to the geodatabase
    arcpy.env.workspace = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\CSI_GeoDatabase.gdb\\"

    # Create order layers
    sj_layer = create_order_layers(prod, onv, rev)

    # Create cloud shape
    cloud_layer = create_cloud_shape(onv, weather, rev)
     
    # Create order layer in clear areas only
    add_layers_to_map(arcpy.analysis.Erase(sj_layer, cloud_layer, "CSI_" + rev + "_clear_orders", None))

    # Create an overlay of strip sized polygons
    strip_layer = create_strip_overlay("CSI_" + rev + "_clear_orders", rev)

# Count clear collects
def collection_metrix(inventory, weather, rev):
    """ Return a dictionary of values based on the inventory layer for a given rev """

    # Path to the geodatabase
    arcpy.env.workspace = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\CSI_GeoDatabase.gdb\\"

    # Set the feature layer name
    rev_collects = "CSI_" + rev + "_collects"
    collects_raster = "CSI_" + rev + "_collects_raster"
    collects_clouds = "CSI_" + rev + "_collects_clouds"

    # Select and export the collects on the given rev
    selection = f"\"acquisition_rev_number\" = {rev}"
    arcpy.conversion.ExportFeatures(inventory, rev_collects, selection)

    # Create a query to select rows where "weather" < 15
    clear_query = f"\"cc\" < 15 AND \"acquisition_rev_number\" = {rev}"
    cloudy_query = f"\"cc\" > 15 AND \"acquisition_rev_number\" = {rev}"

    # Create a cursor to iterate through the selected rows
    with arcpy.da.SearchCursor(inventory, ["OID@"], clear_query) as cursor:
        # Count the number of selected rows
        clear_count = sum(1 for _ in cursor)

    # Create a cursor to iterate through the selected rows
    with arcpy.da.SearchCursor(inventory, ["OID@"], cloudy_query) as cursor:
        # Count the number of selected rows
        cloudy_count = sum(1 for _ in cursor)

    arcpy.AddMessage("Number of clear collects: " + str(clear_count))
    arcpy.AddMessage("Number of cloudy collects: " + str(cloudy_count))

    # Clip weather raster to rev
    arcpy.management.Clip(weather, 
                          "-180 -90 180 90", 
                          collects_raster, 
                          inventory, 
                          "0", 
                          "ClippingGeometry", 
                          "NO_MAINTAIN_EXTENT")
    
    # Create a polygon from the weather raster
    with arcpy.EnvManager(outputZFlag="Disabled", outputMFlag="Disabled"):
        arcpy.conversion.RasterToPolygon(collects_raster, 
                                         collects_clouds, 
                                         "SIMPLIFY", 
                                         "Value", 
                                         "SINGLE_OUTER_PART", 
                                         None)


# Function to be called by the Clear Order Value tool
def run(prod, onv, weather, rev):
    """ This function controls what is run by the tool """
    pass



 
