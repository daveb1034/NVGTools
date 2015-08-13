[![Stories in Ready](https://badge.waffle.io/daveb1034/NVGTools.png?label=ready&title=Ready)](https://waffle.io/daveb1034/NVGTools)
[![Stories in Progress](https://badge.waffle.io/daveb1034/NVGTools.png?label=in%20progress&title=In%20Progress)](https://waffle.io/daveb1034/NVGTools)

NVGTools
========

The NATO Vector Graphics format was developed as a means for NATO systems to share and use overlays. The format is based on SVG.

### Whats New? ###

The code for the reader is at point where a full scale these is required. With the exception of a, g and composite features which are supported by appending the parnet node of each feature in the attibutes.
There is no direct equivalent feature type in ArcGIS. These features are used to group elements together.

## nvgReader.py ##

Provides a means to read a nvg file and output feature classes to a file geodatabase.

The reader currently returns 4 lists which contain the geometries and atributes for supported features from an NVG 1.4.0 document.
each item in the list can be inserted into a feature class with the relevant fields directly using an insert cursor.

Examples of usage will be provided with a sample python toolbox.

The reader does not support namespaces other than the default NVG. This will be added later as will support for versions 1.5.0 and 2.0.0 of the NVG specification.

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


Each item will have one or more NVG features in a form ready to load into a feature class.
## Contributing ##

Please feel free to contribute to the code. I am happy to include ideas people may have for additional functionality. The best way to do this is to either use the fork and pull workflow or raise an issue and I will attempt to add the required functionality.
