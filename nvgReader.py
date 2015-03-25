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

# version 1.4 namespaces
# this may not be needed if so it will be deleted
namespaces = {'nvg':'http://tide.act.nato.int/schemas/2008/10/nvg'}
# need to handle file paths passed to the scrip that have \t etc in the path
# by default this is not handled correctly
nvg = r"R:\Tasking\NVGTools\testData\nvg_1_4\APP6A_SAMPLE.nvg"

# the following section details all the attrbiutes assocaitated with each nvg
# object. Each object has a set of mandatory and optional attributes. If stated
# in the specification document the attribute is read by this tool. Any other
# attributes are currently ignored. Tuples for each are stored with a flag of
# o or m for optioanl and mandatory

class Reader(object):
    """NATO Vector Graphic Reader instance. Reads and process a NATO Vector
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
        self.version = self.dom.documentElement.getAttribute("version")
        # need to define the outputs based on the datatypes in the nvg
        self.esriPolygon = None
        self.esriPolyline = None
        self.esriPoint = None
        return
    def _point(self):
        """Reads all points from the given nvg document object.
        """
        # get the namespace for the file. need to try with mulitple namespaces
        #print self.dom.documentElement.namespaceURI
        self.esriPoint = []

        # get all the points
        points = self.dom.getElementsByTagName("point")

        # extract the attributes and add to the esriPoint
        for point in points:
            newPoint = []
            try:
                #TODO create a point geometry object rather than returning the x,y
                x = float(point.getAttribute('x'))
                newPoint.append(x)
                y = float(point.getAttribute('y'))
                newPoint.append(y)
                symbol = point.getAttribute('symbol').split(':')
                newPoint.append(symbol)
            except:
                # if any of the mandatory attributes are missing log it and continue
                # to next point
                print "invalid point instance, mandatory atribute missing"
                continue
            # get the optional attributes
            try:
                modifiers = point.getAttribute('modifiers')
                if not modifiers == '':
                    newPoint.apend(modifiers)
                else:
                    newPoint.append(None)
            except:
                newPoint.append(None)

            try:
                uri = point.getAttribute('uri')
                if not uri == '':
                    newPoint.append(uri)
                else:
                    newPoint.append(None)
            except:
                newPoint.append(None)

            try:
                label = point.getAttribute('label')
                if not label == '':
                    newPoint.append(label)
                else:
                    newPoint.append(None)
            except:
                newPoint.append(None)

            try:
                style = point.getAttribute('style')
                if not style == '':
                    newPoint.append(style)
                else:
                    newPoint.append(None)
            except:
                newPoint.append(None)
            self.esriPoint.append(newPoint)

        # TODO using the parent node handle points grouped by a or g tags
        #print points[0].parentNode.nodeName
        return

if __name__ =="__main__":
    read = Reader(nvg,namespaces)
    test = read._point()