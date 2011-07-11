import os

class FeatureClassUtilities:
    '''
        http://forums.esri.com/Thread.asp?c=93&f=1729&t=301233
        Author: Andrew C 
        Date: Feb 24, 2010 
    '''

    def __init__(self, GP):
        self.GP = GP
        
    class FeatureType:
        POLYGON = "POLYGON"
        POLYLINE = "POLYLINE"
        POINT = "POINT"

    class AddFieldTypesEnum:
        TEXT = "TEXT"
        FLOAT = "FLOAT"
        DOUBLE = "DOUBLE"
        SHORT = "SHORT"
        LONG = "LONG"
        DATE = "DATE"
        BLOB = "BLOB"
        RASTER = "RASTER"

    def CreateFeatureClass(self, workspace="in_memory", fileName="temp", FeatureType=FeatureType.POINT, SpatialReference="", Fields=[],overwrite=True):
        gp = self.GP
        if gp.exists(workspace + os.sep + fileName) == True and overwrite == True:
            if gp.overwriteoutput != 1:
                gp.overwriteoutput = 1
        elif gp.exists(workspace + os.sep + fileName) == True and overwrite == False:
            gp.adderror("Feature with name: " + fileName + " alread exists")
        if SpatialReference == "":
            gp.AddWarning("No Spatial Reference Was Given")
        gp.createfeatureclass(workspace, fileName, FeatureType, "","","",SpatialReference)
        if len(Fields) > 0:
            for field in Fields:
                gp.addfield(workspace + os.sep + fileName, field[0], str(field[1]))
        return workspace + os.sep + fileName

if __name__ == "__main__":
    try:
        gp = arcgisscripting.create(9.3)
        gp.overwriteoutput = 1
        FCU = FeatureClassUtilities(gp)
        NewFeatureClass = FCU.CreateFeatureClass("in_memory","myFC",FCU.FeatureType.POINT,"",[["SomeText", FCU.AddFieldTypeEnum.TEXT],["SomeNumber", FCU.AddFieldTypeEnum.LONG]],True)
        # do other stuff then copy feature to file geodatabase.
        print 'all done'
    except:
        print 'error'