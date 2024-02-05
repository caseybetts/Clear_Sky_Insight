# Author: Casey Betts, 2024
# Creates feature classes from an ONV layer

import arcpy


def find_revs(fc):
    """ Returns a list of unique revs given an ONV feature class """

    field = ['rev_num']
    revs = set()

    with arcpy.da.SearchCursor(fc,field) as cursor:
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

