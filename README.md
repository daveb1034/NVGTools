[![Stories in Ready](https://badge.waffle.io/daveb1034/NVGTools.png?label=ready&title=Ready)](https://waffle.io/daveb1034/NVGTools)
[![Stories in Progress](https://badge.waffle.io/daveb1034/NVGTools.png?label=in%20progress&title=In%20Progress)](https://waffle.io/daveb1034/NVGTools)

NVGTools
========

The NATO Vector Graphics format was developed as a means for NATO systems to share and use overlays. The format is based on SVG.

## nvgReader.py ##

Provides a means to read a nvg file and output feature classes to a file geodatabase.

This code is in active development and a release will be provided soon. This will focus on reading nvg version 1.4.0 into file geodatabases.

I have a few change of directions on the best way to read the NVG format. It has some pretty awkward concepts but I am pretty much there on the basic implementation points.

Future versions will be supported as the tools develop. In addition a means to write nvg from file geodatabase will be developed. It is likely that reading from a file geodatabase will be achieved through the use of feature templates.

## Contributing ##

Please feel free to contribute to the code. I am happy to include ideas people may have for additional functionality. The best way to do this is to either use the fork and pull workflow or raise an issue and I will attempt to add the required functionality.
