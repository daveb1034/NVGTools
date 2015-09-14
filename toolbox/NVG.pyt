import arcpy, os
import nvgReader
import nvgWriter


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "NATO Vector Graphics"
        self.alias = "nvg"

        # List of tool classes associated with this toolbox
        self.tools = [LoadNVG,WriteNVG]


class LoadNVG(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Load NVG"
        self.description = "Loads features from NVG version 1.4.0 files into feature classes."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input NVG File",
            name="in_nvg",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param1 = arcpy.Parameter(
            displayName="Output File Geodatabase",
            name="outGDB",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param0.filter.list = ['nvg']
        param1.filter.list = ["Local Database"]

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
        nvgs = (parameters[0].valueAsText).split(';')
        gdb = parameters[1].valueAsText
        sr = arcpy.SpatialReference(4326)

        # define the fields to be added to output feature classes.
        # SHAPE@ field used for the insert cursor only.
        fields = ["SHAPE@","uri","style","label","symbol","modifiers","course",
                    "speed","width","min_alt","max_alt","parentNode"]

        for nvg in nvgs:
            # read the nvg file
            messages.addMessage("Reading features from: " + nvg)

            reader = nvgReader.Reader(nvg)
            points,polylines,polygons,multipoints = reader.read()

            # this should be an attribute of the Reader Class
            # probably in a statistics method.
            totalFeats = len(points) + len(polylines) + len(polygons) + len(multipoints)

            messages.addMessage("Read: " + str(totalFeats) + " NVG Features")


            featureTypes = ['point','polyline','polygon','multipoint']

            fcs = []
            # create the feature classes
            for fType in featureTypes:
                # create the output name
                name = os.path.basename(nvg) + "_" + fType
                outName = arcpy.ValidateTableName(name,gdb)
                outName = arcpy.CreateUniqueName(outName,gdb)

                outFC = arcpy.CreateFeatureclass_management(gdb,os.path.basename(outName),fType.upper(),spatial_reference=sr)
                # add the required fields
                for field in fields[1:]:
                    arcpy.AddField_management(outFC,field,"TEXT",field_length=255)
                fcs.append(outFC)


            # load the features into each feature class
            for fc in fcs:
                fcName = arcpy.Describe(fc).baseName
                # this picks up multipoints as
                if '_point' in fcName:
                    messages.addMessage("Loading: " + str(len(points)) + " Points into: " + fcName)
                    cursor = arcpy.da.InsertCursor(fc,fields)
                    for point in points:
                        cursor.insertRow(point)

                elif '_polyline' in fcName:
                    messages.addMessage("Loading: " + str(len(polylines)) + " Polylines into: " + fcName)
                    cursor = arcpy.da.InsertCursor(fc,fields)
                    for polyline in polylines:
                        cursor.insertRow(polyline)

                elif '_polygon' in fcName:
                    messages.addMessage("Loading: " + str(len(polygons)) + " Polygons into: " + fcName)
                    cursor = arcpy.da.InsertCursor(fc,fields)
                    for polygon in polygons:
                        cursor.insertRow(polygon)

                elif '_multipoint' in fcName:
                    messages.addMessage("Loading: " + str(len(multipoints)) + " Multipoints into: " + fcName)
                    cursor = arcpy.da.InsertCursor(fc,fields)
                    for multipoint in multipoints:
                        cursor.insertRow(multipoint)

                del cursor

        return


class WriteNVG(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Write NVG"
        self.description = """Writes features from 1 or more feature class into
                              NVG version 1.4.0 file. The input features must be
                              from the ComBAT Layer pack supplied with this tool
                              to ensure that the features are loaded correctly."""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Feature Class(es) File",
            name="in_fcs",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param1 = arcpy.Parameter(
            displayName="Output NVG File",
            name="outNVG",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")

        param0.filter.list = ['Polygon','Polyline']
        param1.filter.list = ['nvg']

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
        fcs = (parameters[0].valueAsText).split(';')
        outFile = parameters[1].valueAsText

        writer = nvgWriter.Writer()
        writer.write(fcs,outFile,prettyXML=True)

        return
