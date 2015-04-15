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

## License ##

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's
[license.txt](license.txt) file.
