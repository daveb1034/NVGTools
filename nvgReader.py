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
import arcpy, os

# version 1.4 namespaces
# TODO handle mulitple namespaces other than the default.
# dc and dcterms are cmmon namespaces. This is often used for metadata within
# tags. Just need to determine what is required or if namespaces can be ignored.
namespaces = {'nvg':'http://tide.act.nato.int/schemas/2008/10/nvg'}
# need to handle file paths passed to the scrip that have \t etc in the path
# by default this is not handled correctly
nvg = r"R:\Tasking\NVGTools\testData\nvg_1_4\APP6A_SAMPLE.nvg"

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
        self.version = self.dom.documentElement.getAttribute("version")

        # need to define the outputs based on the datatypes in the nvg
        self.esriPolygon = None
        self.esriPolyline = None
        self.esriPoint = None
        self.esriSpatialReference = arcpy.SpatialReference(4326)
        return
    def _point(self):
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
        points = self.dom.getElementsByTagName("point")

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
                    pnt = arcpy.Point(x,y)
                    pntGeom = arcpy.PointGeometry(pnt)
                    newPoint.append(pntGeom)
                    symbol = point.getAttribute('symbol').split(':')
                    newPoint.append(symbol)
                except:
                    # if any of the mandatory attributes are missing log it and continue
                    # to next point
                    print "invalid point instance, mandatory atribute missing"
                    continue
                # get the optional attributes
                try:
                    modifiers = point.getAttribute('modifier') # spec spells it as modifiers, sample data uses modifier
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

    def _loadFeatueClass(self,features,geomType,workspace):
        """Load extracted data into a template feature class.

        args:
            features - the list containing the feaures to be loaded
            geomType - the geometry type passed, valid types are POINT POLYLINE, POLYGON
        """
        #TODO load the military data into the Military Feature Layer Templates
        # get the template feature class based on the geomType

        gdb = os.path.join(os.path.dirname(__file__),'gdb','template.gdb')

        # get the fc based on the geomType
        # this could be achieved based on the geometry passed into the first
        # position of each feature in features.

        if geomType == 'POINT':
            template = os.path.join(gdb,'nvgPoint')
            fcName = arcpy.CreateUniqueName('nvgPoint',workspace)
            fc = arcpy.Copy_management(template,os.path.join(workspace,fcName))
            fields = ['SHAPE@','symbol_encoding','symbol_code','modifier','uri',
                    'label','style','course','speed']

        elif geomType == 'POLYLINE':
            template = os.path.join(gdb,'nvgPolyline')

        elif geomType == 'POLYGON':
            template = os.path.join(gdb,'nvgPolygon')

        else:
            # if no valid geomType passed retun false and handle in the calling
            # code
            return False

        # create an insert cursor and pass the
        cur = arcpy.da.InsertCursor(fc,fields)
        for feature in features:
            row = [feature[0],feature[1][0],feature[1][1],feature[2],feature[3],
                    feature[4],feature[5],feature[6],feature[7]]
            cur.insertRow(row)
        del cur
        # for each point insert the row
        return True

if __name__ =="__main__":
    workspace = r'E:\scratch\scratch.gdb'
    read = Reader(nvg,namespaces)
    print "loading nvg"
    print "reading points"
    test = read._point()
    print "loading fc with points"
    read._loadFeatueClass(test,'POINT',workspace)
