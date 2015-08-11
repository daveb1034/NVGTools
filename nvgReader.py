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
import math

# version 1.4 namespaces
# this may not be needed if so it will be deleted
namespaces = {'nvg':'http://tide.act.nato.int/schemas/2008/10/nvg'}

# need to handle file paths passed to the scrip that have \t etc in the path
# by default this is not handled correctly
nvg = r"E:\Google Drive\NVG\nvg_1_4\APP6A_SAMPLE.nvg"

# <a>, <g> and <composite> features not yet implemented

#geometry mapping
geomMap = {"point":"POINT", "text":"POINT", "multipoint":"MULTIPOINT",
            "circle":"POLYGON", "ellipse":"POLYGON", "polyline":"POLYLINE",
            "corridor":"POLYLINE", "polygon":"POLYGON", "arc":"POLYLINE",
            "arcband":"POLYGON"}

def geo2arithetic(inAngle):
    """converts a bearing to aritmetic angle.
    """
    outAngle = -1.0
    # Force input angle into 0 to 360 range
    if inAngle > 360.0:
        inAngle = math.fmod(inAngle,360.0)

    # if anlge is 360 make it 0
    if inAngle == 360.0:
        inAngle = 0.0

    #0 to 90
    if (inAngle >= 0.0 and inAngle <= 90.0):
        outAngle = math.fabs(inAngle - 90.0)

    #90 to 360
    if (inAngle > 90.0 and inAngle < 360.0):
        outAngle = 360.0 - (inAngle - 90.0)

    return outAngle

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
        self.esriPolygon = []
        self.esriPolyline = []
        self.esriPoint = []
        self.esriMultiPoint = []

        # define Spatial Reference Objects
        self.wgs84 = arcpy.SpatialReference(4326)
        self.world_merc = arcpy.SpatialReference(3395)

        return


    def _getElement(self,tag):
        """Return all elements with given tag.
        """
        return self.dom.getElementsByTagName(tag)

    def _cleanPoints(self,points):
        """Cleans a string of point coordinate pairs and returns a list of
        numerical coordinate pairs
        """
        # get a list of coord pairs as strings from points
        # [['x1','y1'],['x2','y2'],[...]]
        listPoints = [p.split(",") for p in points.rstrip().split(" ")]

        # convert each coord to float
        fPoints = [[float(x) for x in row] for row in listPoints]

        return fPoints

    def _projectGeometry(geometry, spatial_refernce):
        """Projects the input geometry into the spatial_reference

        THis is used to ensure the maths works on the geometry functions
        """
        projected = geometry.projectAs(spatial_refernce)

        return projected

    def _buildPoint(self,x,y):
        """build a point geometry from x,y coordinates.
        """
        # construct the geometry
        pnt = arcpy.Point(x,y)
        pGeom = arcpy.PointGeometry(pnt,self.wgs84)

        return pGeom

    def _buildGeometry(self,points,geometry_type,saptial_reference):
        """Builds the relevant geometry from a string of points based on the
        geometry_type and spatial_reference.

        Valid Geometyr Types are:
            POLYGON
            POLYLINE
            MULTIPOINT

        Valid Spatial References are
        self.wgs84 - used for all default shapes
        self.world_merc - used for ellipses, arcs, and arcbands

        the returned geometry will always be projected as wgs84
        """
        # clean the point string
        cPoints = self._cleanPoints(points)

        # array to hold point objects
        array = arcpy.Array

        for point in cPoint:
            pnt = arcpy.Point()
            pnt.X = point[0]
            pnt.Y = point[1]
            array.add(pnt)

        if geometry_type == 'POLYGON':
            geom = arcpy.Polygon(array,spatial_reference)
        elif geometry_type == 'POLYLINE':
            geom = arcpy.Polyline(array,spatial_reference)
        elif geometry_type == 'MULITPOINT':
            geom = arcpy.Multipoint(array,spatial_reference)

        # ensure final geom is returned in wgs84
        if geom.spatialReference.factoryCode != 4326:
            geom = self._projectGeometry(geom,self.wgs84)
        return geom

    def _pointString(self,points):
        """Returns a string in the format required by NVG for point coordinates.

        This method is used to parse the output of _buildElliptical and _buildCircular
        into a format used by the geometry construction methods.
        """
        s = ''
        for pnt in points:
            pnt = str(pnt).strip('[]')
            s = s + pnt + " "

        return points

    def _buildElliptical(self,cx,cy,rx,ry,rotation,startangle=0,endangle=360):
        """Generates a set of point cordinates that describe an ellipse or an arc.

        Coordinates need to be projected before using the tools.
        """
        points = []
        # projects the cx,cy to world mercator
        pGeom = arcpy.PointGeometry(arcpy.Point(cx,cy),self.wgs84)
        centrePnt = self._projectGeometry(pGeom,self.world_merc)
        X = centrePnt.firstPoint.X
        Y = centrePnt.firstPoint.Y

        rotation = math.radians(rotation)
        step = 1

        # generate points and rotate
        for theata in range(startangle,endangle,step):
            #caclulate points on the ellipse
            theata = math.radians(theata)
            X = rx * math.cos(theata)
            Y = ry * math.sin(theata)

            # rotate point aund the centre
            X = cx + X * math.cos(rotation) + Y * math.sin(rotation)
            Y = cy - X * math.sin(rotation) + Y * math.cos(rotation)

            points.apend([X,Y])

        # build the geometry
        if startangle != 0 or endangle != 360:
            geom = self._buildGeometry(self._pointString(points),"POLYLINE",self.world_merc)
        else:
            geom = self._buildGeometry(self._pointString(points),"POLYGON",self.world_merc)

        return geom

    def _buildCircle(self,cx,cy,r):
        """Returns arcpy.Polygon circle from the cx, cy and radius.

        The radius needs to be in the same units as the cx,cy location.
        """
        # may need to move the projection code to a seperate method as it will
        # need to be done multiple times

        # project the point to world mercator
        pGeom_wgs84 = arcpy.PointGeometry(arcpy.Point(cx,cy),self.wgs84)
        pGeom_WM = self._projectGeometry(pGeom_wgs84,self.world_merc)

        # buffer the point by the radius
        polygon_wm = pGeom_WM.buffer(r)
        # return the polygon in wgs84 geographics
        polygon = self._projectGeometry(polygon_wm,self.wgs84)

        return polygon

    def _buildArcband(self,cx,cy,r1,r2,startangle,endangle):
        """Builds a wedge describing an area between two concentric circles.
        """
        # project the point to metres
        pGeom = arcpy.PointGeometry(arcpy.Point(cx,cy),self.wgs84)
        centrePnt = self._projectGeometry(pGeom,self.world_merc)
        X = centrePnt.firstPoint.X
        Y = centrePnt.firstPoint.Y

        # convert the start and end angles to arithmetic
        startangle = math.radians(geo2arithetic(startangle))
        endangle = math.radians(geo2arithetic(endangle))

        x_end = x + r2*math.cos(startangle)
        y_end = x + r2*math.sin(startangle)

        # create a point every 0.1 of a degree
        i = math.radians(0.1)

        points = []
        # if r1 == 0 then we create a cone
        if r1 == 0.0:
            points.append([X,Y])

            a = startangle
            while startangle >= endangle:
                x = X + r2*math.cos(a)
                y = Y + r2*math.sin(a)
                points.append([x,y])
                a -= i
        else:
            # calculate outer edge
            while a >= endangle:
                x = X + r2*math.cos(a)
                y = Y + r2*math.sin(a)
                a -= i
                points.append([x,y])

            # calculate the inner edge
            a = endangle
            while a <= startangle:
                a += i
                x = X + r1*math.cos(a)
                y = Y + r1*math.sin(a)
                points.append([x,y])

            # close the polygon
            points.append([x_end,y_end])

        # build the geom
        geom = self._buildGeometry(self._pointString,"POLYGON",self.world_merc)

        return geom

    def _readAttributes(self,element):
        """reads attrbiutes from
        """
        # get all the attributes for the element
        attributes = element.attributes
        data = []
        # collect all the attributes that could be present for all features
        # any not present will be returned as None
        # uri
        if attributes.get('uri'):
            data.append(attributes.get('uri').value)
        else:
            data.append(None)
        # style
        if attributes.get('style'):
            data.append(attributes.get('style').value)
        else:
            data.append(None)
        # label
        # this wil need an addiitonal check to get the content tag for text elements
        # as this will be loaded into the label field
        if attributes.get('label'):
            data.append(attributes.get('label').value)
        # reads the contents of any content tags and appends to the text variable
        # this may not be the best way to extract data from content and further work
        # is needed.
        elif element.getElementsByTagName('content'):
            content = element.getElementsByTagName('content')
            text = ''
            for node in content:
                text += node.firstChild.data
                text += ' '
            data.append(text)
        else:
            data.apend(None)
        # symbol
        if attributes.get('symbol'):
            data.append(attributes.get('symbol').value)
        else:
            data.append(None)
        # modifier(s) not correctly specified in version 1.4
        if attributes.get('modifier'):
            data.append(attributes.get('modifier').value)
        elif attributes.get('modifiers'):
            data.append(attributes.get('modifiers').value)
        else:
            data.append(None)
        # course
        if attributes.get('course'):
            data.append(attributes.get('course').value)
        else:
            data.append(None)
        # speed
        if attributes.get('speed'):
            data.append(attributes.get('speed').value)
        else:
            data.append(None)
        # width
        if attributes.get('width'):
            data.append(attributes.get('width').value)
        else:
            data.append(None)
        # minaltitude
        if attributes.get('minaltitude'):
            data.append(attributes.get('minaltitude').value)
        else:
            data.append(None)
        # maxaltitude
        if attributes.get('maxaltitude'):
            data.append(attributes.get('maxaltitude').value)
        else:
            data.append(None)
        # parent node
        data.append(element.parentNode.nodeName)
        return data

    def read(self):
        """reads all elements in an NVG into the relevant esri feature types.
        """
        # works through each element type and creates the geometry and extracts
        # attributes. The final ouput of this is list of geometries with associated
        # attributes.

        # lists for the results
        points = []
        polylines = []
        polygons = []
        multipoints = []

        # read point features
        pElems = self._getElement('point')

        # build geometries and get the aributes for each point element
        for pElem in pElems:
            pGeom = self._buildPoint(pElem.attributes.get('x').value,
                                    pElem.attributes.get('y').value)
            pAttrs = self._readAttributes(pElem)
            pAttrs.insert(0,pGeom)
            points.append(pAttrs)

        # text
        tElems = self._getElement('text')

        # build geometries and get the aributes for each text element
        for tElem in tElems:
            tGeom = self._buildPoint(tElem.attributes.get('x').value,
                                    tElem.attributes.get('y').value)
            tAttrs = self._readAttributes(tElem)
            tAttrs.insert(0,tGeom)
            points.append(tAttrs)

        # polyline
        lines = ['polyline','corridor','arc']
        for line in lines:
            if line == 'arc':
                lnElems = self._getElement(line)
                for lnElem in lnElems:
                    lnGeom = self._buildElliptical(lnElem.attributes.get('cx').value,
                                            lnElem.attributes.get('cy').value,
                                            lnElem.attributes.get('rx').value,
                                            lnElem.attributes.get('ry').value,
                                            lnElem.attributes.get('rotation').value,
                                            lnElem.attributes.get('startangle').value,
                                            lnElem.attributes.get('endangle').value)
                    lnAttrs = self._readAttributes(lnElem)
                    lnAttrs.insert(0,lnGeom)
                    polylines.append(lnAttrs)

            else:
                # builds gemetries and reads attributes for polyines and corridor
                lnElems = self._getElement(line)

                # build geometries and get the aributes for each text element
                for lnElem in lnElems:
                    lnGeom = self._buildGeometry(lnElem.attributes.get('points').value,
                                                'POLYLINE',self.wgs84)
                    lnAttrs = self._readAttributes(lnElem)
                    lnAttrs.insert(0,lnGeom)
                    polylines.append(lnAttrs)

        return points, polylines

if __name__ =="__main__":
    reader = Reader(nvg,namespaces)





