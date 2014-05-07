import arcpy,os
import xml.etree.ElementTree as ET


def nvgParse(nvgFile):
    """Extracts any points, polylines, polygons or circles from the open file
    object nvgFile. This should be a file in the nvg spec and opened for reading.

    returns a tuple of four lists ([points],[polylines],[polygons],[circles]) zero
    length lists are returned if a feature type is not present
    """
    points = []
    polylines = []
    polygons = []
    circles = []

    objs = ['point','polyline','polygon','circle'] # feature types to extract

    # get the xml elements
    tree = ET.ElementTree()
    tree.parse(nvgFile)
    root = tree.getroot()
    ## due to the stuctue of NVG versions we need to modify the tags to extract.
    ## versions 1.4 and 1.5 use multiple namespaces whereas 0.3 didnt. this affects
    ## the way ElementTree returns its elements
    if root.attrib['version'] == '0.3':
        arcpy.AddMessage("Processing NVG version 0.3")
        pntTag = 'point'
        polyTag = 'polygon'
        lineTag = 'polyline'
        circleTag = 'circle'
    elif root.attrib['version'] == '1.4.0':
        arcpy.AddMessage("Processing NVG version 1.4.0")
        pntTag = '{http://tide.act.nato.int/schemas/2008/10/nvg}point'
        polyTag = '{http://tide.act.nato.int/schemas/2008/10/nvg}polygon'
        lineTag = '{http://tide.act.nato.int/schemas/2008/10/nvg}polyline'
        circleTag = '{http://tide.act.nato.int/schemas/2008/10/nvg}circle'
        objs = [pntTag,polyTag,lineTag,circleTag]
    elif root.attrib['version'] == '1.5.0':
        arcpy.AddMessage("Processing NVG version 1.5.0")
        pntTag = '{http://tide.act.nato.int/schemas/2009/10/nvg}point'
        polyTag = '{http://tide.act.nato.int/schemas/2009/10/nvg}polygon'
        lineTag = '{http://tide.act.nato.int/schemas/2009/10/nvg}polyline'
        circleTag = '{http://tide.act.nato.int/schemas/2009/10/nvg}circle'
        objs = [pntTag,polyTag,lineTag,circleTag]
    else:
        # rasise an arcpy execute error and kill the tool with an unsupport version
        # error
        error = "UNSUPPORTED VERSION: use versions 0.3, 1.4.0 or 1.5.0 only."
        arcpy.AddError(error)
        raise arcpy.ExecuteError
    # extract out each element in the list this also picks out some child nodes
    elements = root.iter()
    for element in elements:
        if element.tag in objs:
            if element.tag == pntTag:
                points.append(element.attrib)
            elif element.tag == lineTag:
                polylines.append(element.attrib)
            elif element.tag == polyTag:
                polygons.append(element.attrib)
            elif element.tag == circleTag:
                circles.append(element.attrib)
        else:
            print "--- " + element.tag + " not used ---"

    return points,polylines,polygons,circles

## This is a python port of the HQ ARRC COORDINATES CONVERSION CALCULATOR.html
## The port is based on the work conducted by Rob Ashmore, PJHQ J5(OA) Joint Analyst, June 2002

## Ported by Cpl Dave Barrett, GASC, 16 Geo Sp Sqn, 26/09/2013

##'----------------------------------------------------------------------------------------------------------
##'NOTES
##'----------------------------------------------------------------------------------------------------------
##'
##'This set of routines can be used to convert between the following three coordinate systems:
##'  1. UTM
##'  2. Latitude / Longitude
##'  3. MGRS
##'
##'There are four basic routines, which cover:
##'  1. Latitude / Longitude ...TO... UTM
##'  2. UTM ...TO... Latitude / Longitude
##'  3. MGRS ...TO... UTM
##'  4. UTM ...TO... MGRS
##'
##'The routines that convert between Latitude / Longitude and MGRS use the above routines to calculate
##'the position in UTM as an intermediate step.
##'
##'The following datastructures are assumed for the three coordinate sysetms:
##'  1. UTM
##'     a. Zone - as String, with letter in lower case - e.g. "42s"
##'     b. Easting - as Double
##'     c. Northing - as Double
##'  2. Latitude / Longitude
##'     a. Latitude - as Double, in decimal degrees - e.g. 32deg45min = 32.75
##'     b. Latitudinal Hemisphere - as String, either "E" or "W".
##'     c. Longitude - as Double, in decimal degrees
##'     d. Longitudinal Hemisphere - as String, either "N" or "s".
##'  3. MGRS
##'     a. Zone - as String, including UTM and two character zone - e.g. "42sWB"
##'     b. X Loc - as String (5-characters long)
##'     c. Y Loc - as String (5-characters long)
##'
##'The conversion routines have been extracted from the "HQ ARRC COORDINATES CONVERSION CALCULATOR.htm".
##'Correct implementation has been checked by comparing the output from these routines with that from
##'the original HTML file (and JAVA code). Examples are included in the Z_TestConvert routine at the end of
##'this module.
##'
##'Unfortunately, I have no understanding of the mathematics behind the calculations - hence, variable names
##'are not especially descriptive and comments relate to program flow only!
##'
##'Rob Ashmore, PJHQ J5(OA) Joint Analyst, June 2002
##'(whilst deployed in Aghanistan on Op JACANA)

import math

## Define some constants to be used during the calculations

zoneletterString = "abcdefghjklmnpqrstuvwxyz"
# datum constants
datumName = "WGS84"
datumSpheroid = "WGS84"
datumSemimajor = float(6378137)
datumE2 = 0.00669438
datumA = 1 - datumE2 / 4 * (1 + 3 * datumE2 / 16 * (1 + 5 * datumE2 / 12))
datumB = 3 * datumE2 / 8 * (1 + datumE2 / 4 * (1 + 15 * datumE2 / 32))
datumC = 15 * datumE2 * datumE2 * (1 + 3 * datumE2 / 4) / 256
datumD = 35 * datumE2 * datumE2 * datumE2 / 3072
datumDx = 0
datumDy = 0
datumDz = 0

# grid constants
gridName = "UTM"
gridFE = float(500000)
gridFN = float(10000000)
gridScaleFactor = 0.9996
gridLatOrig = 0
gridZoneWidth = float(6)
gridZoneStart = float(-180)

def eqns(inLa,inAa,inE2,inK0,inA,inB,inC,inD):
    """These are the quations used in the utm to/from lat lon conversion routines.
    Returns the follwoing values outM,outV,outN,outT
    """
    ## i don not know what these variables are computing but they are used in the conversion to and from utm and lat lon
    outM = inK0 * inAa * ((inA * inLa) - (inB * math.sin(2 * inLa)) + (inC * math.sin(4 * inLa)) - (inD * math.sin(6 * inLa)))
    outV = (inK0 * inAa) / math.sqrt(1 - (inE2 * math.sin(inLa) * math.sin(inLa)))
    outN = (inE2 * math.cos(inLa) * math.cos(inLa)) / (1 - inE2)
    outT = math.tan(inLa) * math.tan(inLa)

    return outM,outV,outN,outT

## define th functions to carry out the conversions
def latlon2utm(lat,lon):
    """converts latitude and longitude to utm. Returns UTM grid in the form ##X ####### ######.
    e.g. 30U 2345678 234567
    """
    ## check if the lat / lon are in the correct range
    if lat < -84 or lat > 84:
        print "Latitude should be between -90 and +90"
        return None
    if lon < -180 or lon >180:
        print "Longitude should be between -180 and +180"
        return None
    ## find utm zone and central meridian
    lat = math.radians(lat - gridLatOrig)
    iZoneNum = int(1 + ((lon - gridZoneStart) / gridZoneWidth))
    dblCentMer = (gridZoneWidth * (iZoneNum - 0.5))+ gridZoneStart
    strZoneLet = zoneletterString[(int((lat * 9 / math.pi + 4) * 2.5) + 3)-1] ## the final -1 has been added to correct for the string indexing
    utmZone = str(iZoneNum) + strZoneLet
    ## calculate the eastings and northings
    lon = math.radians(lon - dblCentMer)
    dblVp = lon * math.cos(lat)
    ## call the Eqns function
    result = eqns(lat,datumSemimajor,datumE2,gridScaleFactor,datumA,datumB,datumC,datumD)
    outM = result[0]
    outV = result[1]
    outN = result[2]
    outT = result[3]

    ## compute the out eastings and northings
    outEasting = (((((2 * outT -58) * outT +14) * outN + (outT - 18) * outT + 5) * dblVp * dblVp / 20 + outN - outT + 1) * dblVp * dblVp / 6 + 1) * outV * dblVp + gridFE
    outNorthing = ((((outT - 58) * outT + 61) * dblVp * dblVp / 30 + (9 + 4 * outN) * outN - outT + 5) * dblVp * dblVp / 12 + 1) * outV * dblVp * dblVp * math.tan(lat) / 2 + outM

    ## remove the decimal part of the eastings and northings
    outEasting = math.trunc(outEasting)
    outNorthing = math.trunc(outNorthing)

    ## check on the lat
    if lat < 0:
        outNorthing = outNorthing + gridFN

    utm = str(iZoneNum) + strZoneLet + " " + str(outEasting) + " " + str(outNorthing)
    return utm

def utm2latlon(utm):
    """Converts utm to lat and lon. utm2latlon(utmGrid) returns a tuple of (lat,lon)
    """
    utm = ''.join(e for e in utm if e.isalnum())
    iZoneNum = int(utm[:2])
    strZoneLet = utm[2]
    dblEasting = float(utm[3:9])
    dblNorthing = float(utm[9:])

    ## check the zone number / letter are correct
    if iZoneNum < 1 or iZoneNum > 61:
        print "Invalid utm zone number!"
        return None
    if not strZoneLet in zoneletterString:
        print "Invalid utm zone letter!"
        return None

    ## do the basic sums
    dblOutCm = gridZoneWidth * (iZoneNum - 0.5) + gridZoneStart

    if strZoneLet < 'n':
        dblNorthing = dblNorthing - gridFN

    dblLa = dblNorthing / (gridScaleFactor * datumSemimajor * (1 - datumE2))
    dblDlat = 1
    while abs(dblDlat) > 0.000000001:
        result = eqns(dblLa, datumSemimajor,datumE2,gridScaleFactor,datumA,datumB,datumC,datumD)
        dblM = result[0]
        dblV = result[1]
        dblN = result[2]
        dblT = result[3]
        dblDlat = (dblNorthing - dblM) * (1 + dblN) / dblV
        dblLa = dblLa + dblDlat

    dblU = (dblEasting - gridFE) / dblV

    lon = (((((4 * dblT + 3) * 2 * dblN + (6 * dblT + 7) * 4 * dblT + 5) * dblU * dblU / 20 - dblN - 2 * dblT - 1) * dblU * dblU / 6 + 1) * dblU / math.cos(dblLa)) / (math.pi / 180) + dblOutCm
    lat = (dblLa - ((((2 + dblT) * 45 * dblT + 61) * dblU * dblU / 30 + (4 * dblN - 1) * dblN + (3 * dblN - 1) * 3 * dblT - 5) * dblU * dblU / 12 + 1) * dblU * dblU / 2 * (1 + dblN) * math.tan(dblLa)) / (math.pi/180) + gridLatOrig
    return lat,lon

def mgrs2utm(mgrs):
    """Converts mgrs to utm. requires the zone number to be 2 digits, if <10 then pad with leading 0.
    requires a 10 figure grid at the moment. A function will be written to clean mgrs prior to use
    """
    ##ToDo
    ## write code to check if the zone number is less than ten and adjust the slices to extract the other parts
    mgrs = ''.join(e for e in mgrs if e.isalnum()) #removes spaces in the input grid
    iZoneNum = int(mgrs[:2])
    strZoneLet1 = mgrs[2].lower()
    strZoneLet2 = mgrs[3].lower()
    strZoneLet3 = mgrs[4].lower()

    dblEasting = float(mgrs[5:10])
    dblNorthing = float(mgrs[10:])

    ## do the sums
    dblL = 885000 * (zoneletterString.find(strZoneLet1) - 11.5)
    dblX = zoneletterString.find(strZoneLet2)

    dblX = dblX - (8 * int(dblX / 8))
    dblEasting = (dblX + 1) * 100000 + 1 * dblEasting
    dblX = zoneletterString.find(strZoneLet3)

    if iZoneNum / 2 == int(iZoneNum / 2):
        dblX = dblX - 5

    dblNorthing = dblX * 100000 + 1 * dblNorthing
    dblNorthing = dblNorthing + 2000000 * int(((dblL - dblNorthing) / 2000000))
    if dblNorthing < 0:
        dblNorthing += gridFN

    ## assembly the utm grid
    utm = str(iZoneNum) + strZoneLet1 + " " + str(math.trunc(dblEasting)) + " " + str(math.trunc(dblNorthing))
    return utm

def utm2mgrs(utm):
    """Converts utm grid to mgrs. requires the utm zome number to be 2 digits eg if < 10 then pad with a zero. 9 becomes 09.
    """
    utm = ''.join(e for e in utm if e.isalnum()) #removes spaces in the input grid
    iZoneNum = int(utm[:2])
    strZoneLet1 = utm[2].lower()
    dblEasting = float(utm[3:9])
    dblNorthing = float(utm[9:])

    ## check the zone number / letter are correct
    if iZoneNum < 1 or iZoneNum > 61:
        print "Invalid utm zone number!"
        return None
    if not strZoneLet1 in zoneletterString:
        print "Invalid utm zone letter!"
        return None

    ## do the sums
    dblY = int(dblEasting / 100000)
    dblEasting = dblEasting - dblY * 100000
    dblY = dblY + (iZoneNum - int((iZoneNum -1) / 3) * 3 - 1) * 8 - 1
    strZoneLet2 = zoneletterString[dblY].upper()

    dblY = int(dblNorthing / 100000)
    dblNorthing = dblNorthing - dblY * 100000
    if iZoneNum / 2 == int(iZoneNum / 2):
        dblY = dblY + 5
    while dblY > 19:
        dblY -= 20

    strZoneLet3 = zoneletterString[dblY].upper()

    # this section of the code has been changed to handle situations where the coordiante of x or y
    # is less than 5 digits in length. it will pad a zero to the front of the coordinate.

    # this needs to be adjusted so that a precision can be specified in the output coordinate
    x = str(math.trunc(dblEasting))
    y = str(math.trunc(dblNorthing))

    if len(x) < 5:
        x = "0" + x
    if len(y) < 5:
        y = "0" + y

    mgrs = str(iZoneNum) + strZoneLet1 + " " + strZoneLet2 + strZoneLet3 + " " + x[:3] + " " + y[:3]

    return mgrs

def mgrs2latlon(mgrs):
    """Uses the mgrs2utm and utm2latlon to provide an easy interface to go direct to lat and lon form mgrs.
    """
    utm = mgrs2utm(mgrs)
    lat,lon = utm2latlon(utm) ## the utm2latlon retuns a tuple of (lat,lon) so python automatically unpacks the values for us.
    return lat,lon

def latlon2mgrs(lat,lon):
    """Uses the latlon2utm and utm2mgrs to provide anuy easy way to go directly from lat and lon to mgrs
    """
    utm = latlon2utm(lat,lon)
    mgrs = utm2mgrs(utm)
    return mgrs


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Convert NATO Vector Graphic"
        self.alias = "nvgConvert"

        # List of tool classes associated with this toolbox
        self.tools = [NVG2FC]


class NVG2FC(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "NATO Vector Graphic to Feature Class "
        self.description = "Converts data from iGeoSit in the NATO Vector Graphic format to Feature Class"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="NVG File",
            name="nvgFile",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output Workspace",
            name="outWksp",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param0.filter.list = ['nvg']
        param1.filter.list = ['Local Database']
        params = [param0,param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # get the path to the file and open the file for reading, then parse the contents
        # and extract the features
        arcpy.env.overwriteOutput = True
        path = parameters[0].valueAsText
        nvg = open(path,'r')
        features = nvgParse(nvg)
        nvg.close()

        fgdb = parameters[1].valueAsText

        # define the feature class name base
        name = os.path.basename(path)[:-4]
        fcnameBase = arcpy.ValidateTableName(name,fgdb)
        point_name = "Point_" + fcnameBase
        polyline_name = "Polyline_" + fcnameBase
        polygon_name = "Polygon_" + fcnameBase

        pointfc = os.path.join(fgdb,point_name)
        linefc = os.path.join(fgdb,polyline_name)
        polygonfc = os.path.join(fgdb,polygon_name)
        # process each feature type and create the features. This will be done using an
        # insert cursor.
        ## process the point features first
        if len(features[0]) != 0:
            points = features[0] # this is a list with a dictionary for each feature type
            pointfc = arcpy.CreateFeatureclass_management(fgdb,point_name,'POINT',spatial_reference=4326)
            arcpy.AddField_management(pointfc,'label','TEXT',field_length=255)

            messages.addMessage("Creating Points")
            # create the insert cursor for the point fc
            fields = ["SHAPE@XY","label"]
            cur = arcpy.da.InsertCursor(pointfc,fields)
            for point in points:
                # create the geometry
                X,Y = float(point['x']),float(point['y'])
                pnt = (X,Y)
                if 'label' in point:
                    label = point['label']
                else:
                    label = 'NO LABEL FOUND'
                cur.insertRow([pnt,label])
            del cur
            messages.addMessage("Finished Points")

        ## process the polylines
        if len(features[1]) != 0:
            lines = features[1] # this is a list with a dictionary for each feature type
            linefc = arcpy.CreateFeatureclass_management(fgdb,polyline_name,'POLYLINE',spatial_reference=4326)
            arcpy.AddField_management(linefc,'label','TEXT',field_length=255)

            messages.addMessage("Creating Lines")
            # create the insert cursor for the point fc
            fields = ["SHAPE@","label"]
            cur = arcpy.da.InsertCursor(linefc,fields)
            for line in lines:
                # extract the coordinate pairs for each line
                points = line['points'].split(" ")
                coords = [point.split(',') for point in points]
                pnt = arcpy.Point()
                array = arcpy.Array()
                for coord in coords:
                    pnt.X = float(coord[0])
                    pnt.Y = float(coord[1])
                    array.add(pnt)
                polyline = arcpy.Polyline(array)
                array.removeAll()
                if 'label' in line:
                    label = line['label']
                else:
                    label = 'NO LABEL FOUND'
                cur.insertRow([polyline,label])

            del cur
            messages.addMessage("Finished Lines")

        if len(features[2]) != 0:
            polygons = features[2] # this is a list with a dictionary for each feature type
            polygonfc = arcpy.CreateFeatureclass_management(fgdb,polygon_name,'POLYGON',spatial_reference=4326)
            arcpy.AddField_management(polygonfc,'label','TEXT',field_length=255)

            messages.addMessage("Creating Polygons")
            # create the insert cursor for the point fc
            fields = ["SHAPE@","label"]
            cur = arcpy.da.InsertCursor(polygonfc,fields)
            for polygon in polygons:
                ## it may be possible to have this done in one go and to ignore the
                ## the sample data did not give me the option to do this so I have covered
                ## all bases for now.
                if 'rect' in polygon:
                    if polygon['rect'] == 'true':
                        # if rectangle is true need to handle the coordinates as they are
                        # stored as BL, TL, TR, BR pairs
                        points = polygon['points'].split(" ")
                        coords = [point.split(',') for point in points]
                        pnt = arcpy.Point()
                        array = arcpy.Array()
                        for coord in coords:
                            pnt.X = float(coord[0])
                            pnt.Y = float(coord[1])
                            array.add(pnt)
                        # close the polygon
                        array.add(array.getObject(0))
                        polyGeom = arcpy.Polygon(array)
                        array.removeAll()
                    else:
                        # handle ploygons that rect tag and it is set to false
                        points = polygon['points'].split(" ")
                        coords = [point.split(',') for point in points]
                        pnt = arcpy.Point()
                        array = arcpy.Array()
                        for coord in coords:
                            pnt.X = float(coord[0])
                            pnt.Y = float(coord[1])
                            array.add(pnt)
                        # close the polygon
                        array.add(array.getObject(0))
                        polyGeom = arcpy.Polygon(array)
                        array.removeAll()
                else:
                    points = polygon['points'].split(" ")
                    coords = [point.split(',') for point in points]
                    pnt = arcpy.Point()
                    array = arcpy.Array()
                    for coord in coords:
                        pnt.X = float(coord[0])
                        pnt.Y = float(coord[1])
                        array.add(pnt)
                    # close the polygon
                    array.add(array.getObject(0))
                    polyGeom = arcpy.Polygon(array)
                    array.removeAll()
                if 'label' in polygon:
                    label = polygon['label']
                else:
                    label = "NO LABEL FOUND"
                # insert the feature into the cursor
                cur.insertRow([polyGeom,label])
            del cur
            messages.addMessage("Finished Polygons")

        ## when processing circles they need to be inserted into the polygon feature class
        ## if it doesn't exist then create the polygon as above.
        if not arcpy.Exists(polygonfc):
            # create the feature class then insert the cirlces otherwise just process
            # insert the circles.
            polygonfc = arcpy.CreateFeatureclass_management(fgdb,polygon_name,'POLYGON',spatial_reference=4326)
            arcpy.AddField_management(polygonfc,'label','TEXT',field_length=255)

        if len(features[3]) != 0:
            messages.addMessage("Creating Circles")
            circles = features[3]
            fields = ["SHAPE@","label"]
            cur = arcpy.da.InsertCursor(polygonfc,fields)
            # create the circles based on the centre point and buffer distance
            # the circles appear to be created in a projected coordinate system then
            # they are drawn in GCS so appear flattened when dawn in degrees. Therefore
            # the point is projected into utm and buffered in metres. The resulting polyon
            # is then projected back to GCS and inserted into the feature.
            for circle in circles:
                lat,lon = float(circle['cy']),float(circle['cx'])
                utm = latlon2utm(lat,lon)
                ZoneNumber = int(utm[:2])
                # from the zone number need to get the correct wkid for the spatial reference
                # also need to know if it is north or south of equator based on the sign
                # of the latitude
                if lat >= 0:
                    wkid = 32600 + ZoneNumber
                else:
                    wkid = 32700 + ZoneNumber
                pnt = arcpy.Point()
                pnt.X = int(utm.split(" ")[1])
                pnt.Y = int(utm.split(" ")[2])
                sr = arcpy.SpatialReference(wkid)
                pGeom = arcpy.PointGeometry(pnt,sr)
                radius = float(circle['r'])
                projCircle = pGeom.buffer(radius)
                circleGeom = projCircle.projectAs(arcpy.SpatialReference(4326))
                if'label' in circle:
                    label = circle['label']
                else:
                    label = "NO LABEL FOUND"
                cur.insertRow([circleGeom,label])
            del cur
            messages.addMessage("Finsihed Circles")
        return