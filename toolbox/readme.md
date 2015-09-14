## Python Toolbox

The NVG.pyt provides a smaple toolbox that demonstrates reading one or more NVG files into file geodatabase feature classes.

In addition a sample Writer tool has been included that demonsrates the creation of NVG fies for use on ComBAT. This tool only takes polyline and polygon features due to 
an implmentation issue within ComBAT when handling points. ComBAT does not wite out the symbol tag (a mandatory tag) in NVG files that are created solely from the sketch toolbar. 
Features with an APP6A symbol cod will be written. At present the tool does not support writing symbol codes and this will be added later.

The process of writing creating features for use on ComBAT requires a set of layer files. This are under development and wil be added to the archive in due course.

The example is not the best implementation as it curently creates feature classes for each returned type regardless of whether there are any features returned.
This functionality will be added at a later point.

### Note

The accompanying xml files should not be editied directly. These are maintained by ArcGIS.
