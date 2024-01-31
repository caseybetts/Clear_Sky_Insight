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


def create_feature_class(revs):
    """ Creates feature classes for each rev and saves to a geodatabase """

    arcpy.AddMessage("Here are the revs from CreateRevFeatureClass: " + str(revs))

