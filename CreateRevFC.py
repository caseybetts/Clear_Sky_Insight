# Author: Casey Betts, 2024
# Creates feature classes from an ONV layer

import arcpy
import pandas as pd


def find_revs(onv_layer):
    """ Returns a list of unique revs given an ONV feature class """

    field = ['rev_num']
    revs = set()

    with arcpy.da.SearchCursor(onv_layer,field) as cursor:
        for row in cursor:
            for num in row:
                revs.add(num)

    return revs

def rev_feature_classes(onv_layer, rev_nums):
    """ Creates feature classes for each rev and saves to a geodatabase """

    arcpy.AddMessage("Here are the revs from CreateRevFeatureClass: " + str(rev_nums))
    revs = list(rev_nums[1:-1].split(", "))

    # Select each set of features
    for rev in list(revs):

        selection = f"\"rev_num\" = {rev}"
        output_name = "C:\\Users\\ca003927\\OneDrive - Maxar Technologies Holdings Inc\\Private Drop\\Git\\Clear_Sky_Insight\\CSI_GeoDatabase.gdb\\rev_" + rev

        arcpy.AddMessage("Current rev: " + rev)
        arcpy.conversion.ExportFeatures(onv_layer, 
                                        output_name,
                                        selection)
        
def export(layer, location, name, identifier):
    """ Exports the given layer to the given location with the given identifier appended to the given name """

    output_name = str(name) + "_" + str(identifier)
    location = str(location) + "\\"
    arcpy.AddMessage(location + output_name)
    # arcpy.conversion.ExportFeatures(layer, location + output_name)
    arcpy.management.MultipartToSinglepart(layer, location + output_name)

def subdivide(layer, location, name, identifier, parts, direction):
    """ Exports a layer divided into equal area pieces """

    output_name = str(name) + "_" + str(identifier)
    location = str(location) + "\\"
    arcpy.AddMessage(location + output_name)
    out_path = location + output_name

    arcpy.management.SubdividePolygon(layer, out_path, "EQUAL_AREAS", "" , "50 SquareKilometers", "" , 90, "STRIPS")

def orders_by_rev(orders_layer, onv_layer, location):
    """ Creates a feature class of orders for each rev """

    for rev in find_revs(onv_layer):

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
        
        # Export the order layer
        export(orders_layer, location, "PROD", rev)




# 1) Find rev numbers
# 2) Iterate on rev numbers
# 	2.1) Select rev from ONV file
# 	2.2) Select PROD orders by location of the ONV
# 	2.3) Export PROD order layer
# 3) Iterate on PROD order layers by rev
# 	3.1) Iterate over orders
# 		3.1.1) Subdivide order by area 
        
        # arcpy.management.BatchProject(r"'Clear Sky Insight\Full_Original_AOI';MBG_test_1", r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\CSI_Subdivide.gdb", 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]', None, '')
        # # Get geospatial data
        # m = mp.ArcGISProject("CURRENT")
        # layer = m.listMaps()[0].listLayers()[0] 
        # #get_geospatial(prod)
        # prod = arcpy.GetParameter(0)
        # geojson = arcpy.arcpy.conversion.FeaturesToJSON(prod, r'C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\out.geojson', geoJSON='GEOJSON')
