#-------------------------------------------------------------------------------
# Name:        nvgReader.py
# Purpose:     Provide a way to import data in NVG format into ArcGIS File
#              Geodatabase format.
#
# Author:      Dave Barrett
#
# Created:     16/09/2014
# Copyright:   (c) Dave 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

"""
This module provides a number of functions and classes to read a NVG file into
an ESRI ArcGIS file geodatabase. This module requires a licensed copy of ArcGIS
in order to have access to the functions found in the arcpy site package.

The implementation proivded here attempts to read all mandatory properties from
the NVG specification for version 1.4, future versions of these tools will
include support for future versions as required.
"""
import xml.dom.minidom
import arcpy

# version 1.4 namespaces
# this may not be needed if so it will be deleted
namespaces = {'nvg':'http://tide.act.nato.int/schemas/2008/10/nvg'}

# need to handle file paths passed to the scrip that have \t etc in the path
# by default this is not handled correctly
nvg = r"E:\Google Drive\NVG\nvg_1_4\APP6A_SAMPLE.nvg"

# the following section details all the attrbiutes assocaitated with each nvg
# object. Each object has a set of mandatory and optional attributes. If stated
# in the specification document the attribute is read by this tool. Any other
# attributes are currently ignored. Tuples for each are stored with a flag of
# o or m for optioanl and mandatory

# dictionary of mandatory fields for each NVG feature
# <a>, <g> and <composite> features not yet implemented
# may need to move this into the class to enable access when the file is imported
# into other code
# this will utilise has parent etc from mindom

features = {'point':['x','y','symbol','modifiers','uri','label','style','course',
            'speed'],
            'text':['content','x','y','rotation','uri','style'],
            'multipoint':['points','symbol','modifiers','uri','label','style'],
            'circle':['cx','cy','r','uri','label','style','symbol','modifiers'],
            'ellipse':['cx','cy','rx','ry','rotation','uri','label','style',
            'modifiers','course','speed','symbol'],
            'polyline':['points','uri','label','style','symbol','modifiers'],
            'corridor':['points','width','minaltitude','maxaltitude','uri',
            'label','style','symbol','modifiers'],
            'polygon':['points','uri','label','style','symbol','modifiers'],
            'arc':['cx','cy','course','speed','rotation','startangle','endangle',
            'uri','label','style','symbol','modifiers'],
            'arcband':['cx','cy','minr','maxr','startangle','endangle','uri',
            'label','style','symbol','modifiers']}

# need to map nvg geometry to ESRI geometry types.

class Reader(object):
    """NATO Vector Graphic Reader instance. Reads and processes a NATO Vector
    Graphic to ESRI Geometry.
    """
    def __init__(self,nvgFile,namespaces):
        """Initiate the object and set the basic attributes
        """
        self.nvgFile = nvgFile
        self.namespaces = namespaces

        # parse the nvgFile
        self.dom = xml.dom.minidom.parse(self.nvgFile)

        # get the nvg version
        # consider moving this to a seperate method
        self.version = self.dom.documentElement.getAttribute("version")

        # need to define the outputs based on the datatypes in the nvg
        self.esriPolygon = None
        self.esriPolyline = None
        self.esriPoint = None

        # define Spatial Reference Objects
        self.wgs84 = arcpy.SpatialReference(4326)
        self.world_merc = arcpy.SpatialReference(3395)

        return


    def _getElement(self,tag):
        """Return all elements with given tag.
        """
        return self.dom.getElementsByTagName(tag)

    def _readGeometry(self,tag):
        """read geometry from NVG Element.

        Extracts the geometry of each NVG element and returns an appropriate
        ESRI geometry object of POINT, POLYLINE or POLYGON.
        """
        # read point and text elements
        if tag in ['text','point']:
            element = self._getElement(tag)
            x = element.getAttribute("x")
            y = element.getAttribute("y")

            pnt = arcpy.Point(x,y)



        return True

if __name__ =="__main__":
    read = Reader(nvg,namespaces)
    test = read._readGeometry("point")



