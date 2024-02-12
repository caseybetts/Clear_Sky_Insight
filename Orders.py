# Author: Casey Betts, 2024
# Defines the class containing the dataframe of ordres of a specific rev

import arcpy
import json
import pandas as pd

from collections import Counter
from datetime import datetime
from math import acos, sin, cos


class Orders:
    """ Contains the dataframe and related functions of the orders dataframe for a specific rev """

    def __init__(self, layer):

        self.output_path = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Clear_Sky_Insight\Output"

        # Create dict from geoJSON file
        with open("out.geojson") as f:
            self.geodata = json.load(f) 

        # Create a list of the desired fields to include from the layer's attribute table
        fields = [  "data_acces",
                    "demand_typ",
                    "standing_t",
                    "order_numb",
                    "line_numbe",
                    "external_i",
                    "sap_custom",
                    "order_desc",
                    "area_remai",
                    "product_le",
                    "order_stat",
                    "active_tim",
                    "start_date",
                    "end_date",
                    "area",
                    "pricing",
                    "sap_con",
                    "tasking_pr",
                    "ssr_priori",
                    "backhaul_p",
                    "responsive",
                    "min_ona",
                    "max_ona",
                    "min_sun_az",
                    "max_sun_az",
                    "min_sun_el",
                    "max_sun_el",
                    "min_tar_az",
                    "max_tar_az",
                    "max_cloud_",
                    "purchase_o",
                    "purchase_1",
                    "country",
                    "stereoprod",
                    "vehicle",
                    "ge01",
                    "wv01",
                    "wv02",
                    "wv03",
                    "imagebands",
                    "percent_co",
                    "type",
                    "max_asymme",
                    "min_asymme",
                    "max_bisect",
                    "min_bisect",
                    "max_conver",
                    "min_conver",
                    "consider_f",
                    "consider_1",
                    "scan_direc",
                    "line_rate",
                    "tdi_flag",
                    "tdi_offset",
                    "parent_ord",
                    "project_no",
                    "customer_t",
                    "price_rema",
                    "time_of_da",
                    "price_per_",
                    "paired_ord",
                    "production",
                    "max_snow_c",
                    "is_partial",
                    "min_partia",
                    "selected_v",
                    "requested_",
                    "requested1",
                    "max_collec"]

        # Create a dataframe from the layer
        with arcpy.da.SearchCursor(layer, fields) as cursor:
            self.df_orders = pd.DataFrame(list(cursor), columns=fields)

        # Populate the max/min lat/lon coords for each order
        self.add_columns()
        self.populate_geodata()
        self.populate_dimensions()

        arcpy.AddMessage(self.df_orders.head())

        # Output dataframe to csv file
        self.output_df_to_csv()

    def add_columns(self):
        """ Adds the needed columns to the dataframe """

        # Add max/min coord columns to dataframe
        self.df_orders["x_max"] = ""
        self.df_orders["x_min"] = ""
        self.df_orders["y_max"] = ""
        self.df_orders["y_min"] = ""

        # Add dimension columns to dataframe
        self.df_orders["width"] = ""
        self.df_orders["height"] = ""

    def populate_geodata(self):
        """ Creates and populates the geodata fields for the orders dataframe """

        # Populate geo data columns
        for direction in ["x", "y"]:
            for value in ["max", "min"]:
                # Find duplicate order ids (former multipart polygons)
                counts = Counter(self.df_orders.external_i).items()
                self.duplicates = [order for order, count in counts if count > 1]
                self.count_dict = dict(counts)
                self.df_orders[direction + "_" + value] = self.df_orders.apply(lambda x: self.get_geodata(direction, value, x.external_i), axis=1)

    def get_geodata(self, direction, value, order):
        """ Returns the vertex coordinate for of the given type for the given order """
        
        # Determine if there are duplicates of the order id
        if order in self.duplicates:
            self.count_dict[order] -= 1
            skips = self.count_dict[order]

            # Iterate through orders in the geodata dict
            for feature in self.geodata['features']:

                # Find the feature for the given order
                if feature["properties"]["external_i"] == order:

                    # If the number of skips is 0
                    if skips == 0:

                        # Return the correct coordinate value
                        if direction == "x":
                            vals = [i for i, j in feature['geometry']['coordinates'][0]]
                        else:
                            vals = [j for i, j in feature['geometry']['coordinates'][0]]

                        if value == "max":
                            return max(vals)
                        else:
                            return min(vals)

                    else:
                        skips -= 1

        else:

            # Iterate through orders in the geodata dict
            for feature in self.geodata['features']:

                # Find the feature for the given order
                if feature["properties"]["external_i"] == order:

                    if direction == "x":
                        vals = [i for i, j in feature['geometry']['coordinates'][0]]
                    else:
                        vals = [j for i, j in feature['geometry']['coordinates'][0]]

                    if value == "max":
                        return max(vals)
                    else:
                        return min(vals)

        return "Not found"

    def populate_dimensions(self):
        """ Creates and populates the width and height fields for the orders dataframe """

        # Apply the calculated width to each row 
        self.df_orders["width"] = self.df_orders.apply(lambda p: self.get_distance((p.y_min, p.x_min), (p.y_min, p.x_max)), axis=1)


    def get_distance(self, a, b):
        """ Returns the distance between two points given at tuple of (lat, lon) of each """

        lat1, lon1 = a
        lat2, lon2 = b

        return acos(sin(lat1)*sin(lat2)+cos(lat1)*cos(lat2)*cos(lon2-lon1))*6371

    def output_df_to_csv(self):
        """ Creates a .csv file with the data from the orders dataframe """

        # Create a timestamp string
        timestamp = str(datetime.now())[:19]
        timestamp = timestamp.replace(':','-')

        display_columns = [  
                    "external_i",
                    "sap_custom",
                    "tasking_pr",
                    "responsive",
                    "ge01",
                    "wv01",
                    "wv02",
                    "wv03",
                    "x_max",
                    "x_min",
                    "y_max",
                    "y_min",
                    "width",
                    "height"]
        
        # Creates a .csv file from the dataframe of all changes needed
        self.df_orders.loc[:, display_columns].to_csv(self.output_path + "\\" + "_" + timestamp + " Table.csv")


        


