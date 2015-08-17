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

# namespace based on the version of the NVG document.
namespaces = {'1.4.0': 'http://tide.act.nato.int/schemas/2008/10/nvg',
              '1.5.0': 'http://tide.act.nato.int/schemas/2009/10/nvg',
              '2.0.0': 'https://tide.act.nato.int/schemas/2012/10/nvg'}

# <a>, <g> and <composite> features not yet implemented

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
    def __init__(self,nvgFile,namespaces=None):
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
        listPoints = [p.split(",") for p in points.strip().split(" ")]

        # convert each coord to float

        fPoints = [[float(x) for x in row] for row in listPoints]

        return fPoints

    def _projectGeometry(self,geometry, spatial_refernce):
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

    def _buildGeometry(self,points,geometry_type,spatial_reference):
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
        array = arcpy.Array()

        for point in cPoints:
            pnt = arcpy.Point()
            pnt.X = point[0]
            pnt.Y = point[1]
            array.add(pnt)

        if geometry_type == 'POLYGON':
            geom = arcpy.Polygon(array,spatial_reference)
        elif geometry_type == 'POLYLINE':
            geom = arcpy.Polyline(array,spatial_reference)
        elif geometry_type == 'MULTIPOINT':
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
            pnt = str(pnt).strip('[]').replace(" ","")
            s = s + pnt + " "

        return s

    def _buildElliptical(self,cx,cy,rx,ry,rotation,startangle=0,endangle=360):
        """Generates a set of point cordinates that describe an ellipse or an arc.

        Coordinates need to be projected before using the tools.
        """
        points = []
        # projects the cx,cy to world mercator
        pGeom = arcpy.PointGeometry(arcpy.Point(cx,cy),self.wgs84)
        centrePnt = self._projectGeometry(pGeom,self.world_merc)
        cX = centrePnt.firstPoint.X
        cY = centrePnt.firstPoint.Y
        rotation = math.radians(float(rotation))
        step = 1
        startangle = float(startangle)
        endangle = float(endangle)

        if startangle > endangle:
            endangle=endangle + 360

        # generate points and rotate
        for theata in range(int(startangle),int(endangle),step):
            #caclulate points on the ellipse
            theata = math.radians(float(theata))
            X = float(rx) * math.cos(theata)
            Y = float(ry) * math.sin(theata)

            # rotate point around the centre
            rotX = cX + X * math.cos(rotation) + Y * math.sin(rotation)
            rotY = cY - X * math.sin(rotation) + Y * math.cos(rotation)

            points.append([rotX,rotY])

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
        polygon_wm = pGeom_WM.buffer(float(r))
        # return the polygon in wgs84 geographics
        polygon = self._projectGeometry(polygon_wm,self.wgs84)

        return polygon

    def _buildArcband(self,cx,cy,minr,maxr,start,end):
        """Builds a wedge describing an area between two concentric circles.
        """
        # project the point to metres
        pGeom = arcpy.PointGeometry(arcpy.Point(cx,cy),self.wgs84)
        centrePnt = self._projectGeometry(pGeom,self.world_merc)
        cx = centrePnt.firstPoint.X
        cy = centrePnt.firstPoint.Y

        # convert values to float
        r1 = float(minr)
        r2 = float(maxr)
        start = float(start)
        end = float(end)

        # convert the bearings from north to maths for use in the coordinate calculations
        #start = math.radians(90 - start)
        if start > end:
            end = end + 360
            end = math.radians(90 - end)
        else:
            end = math.radians(90 - end)
        start = math.radians(90 - start)
        #Calculate the end x,y for the wedge
        x_end = cx + r2*math.cos(start)
        y_end = cy + r2*math.sin(start)

        #Set the step value for the x,y coordiantes
        i = math.radians(0.1)

        points = []
        #Calculate the outer edge of the wedge
        a = start

        #If r1 == 0 then create a wedge from the centre point
        if r1 == 0:
            #Add the start point to the array
            points.append([cx,cy])
            #Calculate the rest of the wedge
            while a >= end:
                X = cx + r2*math.cos(a)
                Y = cy + r2*math.sin(a)

                points.append([X,Y])
                a -= i
            #Close the polygon
            X = cx
            Y = cy

            points.append([X,Y])

        else:
            while a >= end:
                X = cx + r2*math.cos(a)
                Y = cy + r2*math.sin(a)
                a -= i
                points.append([X,Y])


            #Caluclate the inner edge of the wedge
            a = end
            while a <= start:
                a += i ## should this be bofore the calc or after?
                X = cx + r1*math.cos(a)
                Y = cy + r1*math.sin(a)

                points.append([X,Y])



            #Close the polygon by adding the end point
            points.append([x_end,y_end])

        # build the geom
        geom = self._buildGeometry(self._pointString(points),"POLYGON",self.world_merc)

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
            data.append(None)
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

        Returns a tuple of 4 lists: points, polylines, polygons, multipoints.
        These contain the geometry and atributes for the extracted NVG features.
        Each list contains a list for each feature in the form:
            [geom,attr1,attr2,...]
        This is can be directly inserted into a feature class with the correct schema.
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

        # get polygons, circles, ellipses and arcbands
        for polygon in ['polygon','circle','ellipse','arcband']:
            if polygon == 'polygon':
                polyElems = self._getElement('polygon')
                for polyElem in polyElems:
                    polyGeom = self._buildGeometry(polyElem.attributes.get('points').value,
                                                    'POLYGON',self.wgs84)
                    polyAttrs = self._readAttributes(polyElem)
                    polyAttrs.insert(0,polyGeom)
                    polygons.append(polyAttrs)
            elif polygon == 'circle':
                circleElems = self._getElement('circle')
                for circleElem in circleElems:
                    circleGeom = self._buildCircle(circleElem.attributes.get('cx').value,
                                                    circleElem.attributes.get('cy').value,
                                                    circleElem.attributes.get('r').value,)
                    circleAttrs = self._readAttributes(circleElem)
                    circleAttrs.insert(0,circleGeom)
                    polygons.append(circleAttrs)

            elif polygon == 'ellipse':
                ellipseElems = self._getElement('ellipse')
                for ellipseElem in ellipseElems:
                    ellipseGeom = self._buildElliptical(ellipseElem.attributes.get('cx').value,
                                                        ellipseElem.attributes.get('cy').value,
                                                        ellipseElem.attributes.get('rx').value,
                                                        ellipseElem.attributes.get('ry').value,
                                                        ellipseElem.attributes.get('rotation').value)
                    ellipseAttrs = self._readAttributes(ellipseElem)
                    ellipseAttrs.insert(0,ellipseGeom)
                    polygons.append(ellipseAttrs)

            elif polygon == 'arcband':
                arcElems = self._getElement('arcband')
                for arcElem in arcElems:
                    arcGeom = self._buildArcband(arcElem.attributes.get('cx').value,
                                                        arcElem.attributes.get('cy').value,
                                                        arcElem.attributes.get('minr').value,
                                                        arcElem.attributes.get('maxr').value,
                                                        arcElem.attributes.get('startangle').value,
                                                        arcElem.attributes.get('endangle').value)
                    arcAttrs = self._readAttributes(arcElem)
                    arcAttrs.insert(0,arcGeom)
                    polygons.append(arcAttrs)
        # build geometries and get the aributes for each multipoint element
        mpElems = self._getElement('multipoint')
        for mpElem in mpElems:
            mpGeom = self._buildGeometry(mpElem.attributes.get('points').value,
                                                    'MULTIPOINT',self.wgs84)
            mpAttrs = self._readAttributes(mpElem)
            mpAttrs.insert(0,mpGeom)
            multipoints.append(mpAttrs)

        return points, polylines, polygons, multipoints

if __name__ =="__main__":
    # need to handle file paths passed to the scrip that have \t etc in the path
    # by default this is not handled correctly
    nvg = r"C:\Users\dave\Documents\NVGData\nvg_1_4\APP6A_SAMPLE.nvg"
    reader = Reader(nvg,namespaces)
    test = reader.read()
    print test[3]





