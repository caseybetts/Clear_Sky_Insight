# Clear_Sky_Insight
Uses retroactive weather data to assess the performance of a satellite collection plan against its revenue potential 

## How to run
1. Open the tool in an instance of ArcPro
2. Parameters
   - Off Nadir View layer
   - Orders Layer (can be active or archive version if available)
   - Weather Rastor Layer of cloud data
3. Click Run

# Output
The tool will output a layer to the table of contents that is a modified Orders Layer. This layer will include all the orders of the input layer that did not have cloud cover over them. This is to provide a retroactive view into what orders it would have been possible to collect a clear image over. The new layer will also have a new column in the attribute table called value. This is an aggragation of overlaping order's priorities. For example if three orders overlap eachother and the have priorities 10, 20 and 30 then the new value will be the sum of them, 60. The tool will slice overlaping orders on edges to ensure an accurate priority aggragation value at all points. This will allow for analysis to be combined with each shape's area to find an accurate estimate of value for a partiular collection. 
