NVGTools
========

The NATO Vector Graphics format was developed as a means for NATO systems to share and use overlays. The format is based on SVG.

## nvgReader.py ##

Provides a means to read a nvg file and output feature classes to a file geodatabase.

This code is in active development and a beta release is targeted for early May 2015. This will focus on reading nvg version 1.4.0 into file geodatabases.

Future versions will be supported as the tools develop. In addition a means to write nvg from file geodatabase will be developed.

## Update - 27/03/2015 ##

Reader object now able to read points into a template feature class. This currently takes around 10 secs to read around 1000 points. The major overhead is the import of arcpy.
The symbol codes where tested against a MOLE feature class as we have this available on 10.1 still and by replacing * with - in the SID the symbols where drawn. This is not a practical solution, the aim is to match the symbols to features in the military feature template layers.

## Contributing ##

Please feel free to contribute to the code. I am happy to include ideas people may have for additional functionality. The best way to do this is to either use the fork and pull workflow or raise an issue and I will attempt to add the required functionality.
