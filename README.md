[![Stories in Ready](https://badge.waffle.io/daveb1034/NVGTools.png?label=ready&title=Ready)](https://waffle.io/daveb1034/NVGTools)
[![Stories in Progress](https://badge.waffle.io/daveb1034/NVGTools.png?label=in%20progress&title=In%20Progress)](https://waffle.io/daveb1034/NVGTools)

NVGTools
========

The NATO Vector Graphics format was developed as a means for NATO systems to share and use overlays. The format is based on SVG.

## nvgReader.py ##

Provides a means to read a nvg file and output feature classes to a file geodatabase.

The reader currently returns 4 lists which contain the geometries and atributes for supported features from an NVG 1.4.0 document.
Each item in the list can be inserted into a feature class with the relevant fields directly using an insert cursor.

Examples of usage will be provided with a sample python toolbox.

The default NVG namespaces are supported for reading versions 1.4.0, 1.5.0 and 2.0.0. The reader suports version 1.4.0 of the schema.
The code has been tested agains versions 1.5.0 and 2.0.0 however there are additional features added in 2.0.0 that have not yet been added. 
These are the rect and orbit elements. Due to the limited use of version 2.0.0 at present the focus of the project will be adding write support for version 1.4.0 then full support for 1.5.0.

## Usage

Reading NVG files is done using an instance of the Reader class. The optional namespace tag in the Reader class is not yet implemented and should be left to the default value None.

```python
import nvgReader as NVG

nvgFile = r'e:\mydata\nvg\sample.nvg'

reader = NVG.Reader(nvgFile,namespaces=None)
points, polylines, polygons, multipoints = reader.read()
```
The read method returns a tuple of 4 lists:
```python
>>> [points, polylines, polygons, multipoints]
```

Each feature is returned as a list with the geomerty objct at position 0 and the common attributes. If an attribute is not provided in the NVG file then None is returned.

The list returns the following attributes
```python
>>> [<geometry>, 'uri', 'style', 'label', 'symbol', 'modifiers', 'course', 'speed', 'width', 'min_altitude', 'max_altitude', 'parenNode']
```
## nvgWriter.py ##

The writer requires the use of a layer pack that provides the correct values for writing the style tags. Further details are provided in the toolbox directory. Point features
are not currently supported due to the need to implement APP6A and Mil2525B SIDCs in the layer packs to ensure a valid symbol tag. In addition a standard list of icons used by different C2 systems is
required to enable the use on non military symbols.

Each item will have one or more NVG features in a form ready to load into a feature class.
## Contributing ##

Please feel free to contribute to the code. I am happy to include ideas people may have for additional functionality. The best way to do this is to either use the fork and pull workflow or raise an issue and I will attempt to add the required functionality.
