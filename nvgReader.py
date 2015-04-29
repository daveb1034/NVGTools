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

        return


    def _getElement(self,tag):
        """Return all elements with given tag.
        """
        return self.dom.getElementsByTagName(tag)

    def _readPoint(self):
        """Reads points with parent node of nvg.
        All points within the nvg file that have the parent node nvg are read
        and the geometries created and stored in self.esriPoint.
        Any point nods that are part of a composite symbol or a or g node are
        ignored.
        """
        # get the namespace for the file. need to try with mulitple namespaces
        #print self.dom.documentElement.namespaceURI
        self.esriPoint = []

        # get all the points
        points = self._getElement("point")

        # extract the attributes and add to the esriPoint
        for point in points:
            newPoint = []
            # only load points that are not part of composite symbols or members
            # a or g tags. The parent node should be <nvg>
            if not point.parentNode.nodeName == 'nvg':
                continue
            else:
                try:
                    x = float(point.getAttribute('x'))
                    y = float(point.getAttribute('y'))

                    # create the point geometry
                    pnt = (x,y)
                    newPoint.append(pnt)
                    symbol = point.getAttribute('symbol').split(':')
                    newPoint.append(symbol)
                except:
                    # if any of the mandatory attributes are missing log it and continue
                    # to next point
                    print "invalid point instance, mandatory atribute missing"
                    continue
                # get the optional attributes
                try:
                    # spec spells it as modifiers, sample data uses modifier
                    modifiers = point.getAttribute('modifier')
                    if not modifiers == '':
                        newPoint.append(modifiers)
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

                try:
                    course = point.getAttribute('course')
                    if not course == '':
                        newPoint.append(float(course))
                    else:
                        newPoint.append(None)
                except:
                    newPoint.append(None)

                try:
                    speed = point.getAttribute('speed')
                    if not speed == '':
                        newPoint.append(float(speed))
                    else:
                        newPoint.append(None)
                except:
                    newPoint.append(None)

                self.esriPoint.append(newPoint)

        return self.esriPoint

if __name__ =="__main__":
    read = Reader(nvg,namespaces)
    test = read._readPoint()


