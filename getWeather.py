#!/usr/bin/env python2
"""WeatherLayer

Create a feature class containing current weather for cities in a given 
Canadian province.  Features are points with geographic coordinates.  
Attributes contain temperature, humidity, and chance of precipitation.  
Weather data obtained from the RSS feeds at www.weathernetwork.com.

Usage: getWeather.py <layerName> <province> <day> <language>

Where:
     <layerName>: path to new FeatureClass (append .shp if necessary)
     <province>:  province code:
                     AB BC MB NB NL NS NT NU ON PE QC SK YT
     <day>:       day of weather forcast:
                     'today','tomorrow','day after tomorrow',
                     'day after the day after tomorrow'
     <language>:  language of the weather forcast: english or french

Example:
     getWeather.py "C:\\data\\2011jul02.shp" BC today english

"""

import os
import re
import sys
import time
import string
import arcgisscripting
import mechanize
from BeautifulSoup import BeautifulStoneSoup

__author__ = "Andrew Ross"
__copyright__ = "Copyright 2011"
__license__ = "GPL"
__status__ = "Development"

# Source: http://www.canadapost.ca/tools/pg/manual/PGaddress-e.asp#1380608
PROVINCECODES = ('AB','BC','MB','NB','NL','NT','NS','NU','ON','PE','QC','SK','YT')
CITYLIST_FILE = 'cityList.csv'
SPATIALREFERENCE = "Coordinate Systems\Geographic Coordinate Systems\World\WGS 1984.prj"


class wnGeocoder:
	def __init__(self, province):
		self.geocoder = {}

		f = open( sys.path[0] + os.sep + CITYLIST_FILE )
		for l in f:
			try:  #skip over comments in city file
				wID,name,provID,lat,lon = l.strip().split(',')
				if string.lower( provID ) == province:
					# self.geocoder[wID] = (float(lat),float(lon))
					self.geocoder[wID] = (lat,lon)
			except:
				pass
		f.close()

	def getCoordinates( self, wid ):
		try:
			return self.geocoder[wid]
		except:
			return None

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


def usage():
    print __doc__


def getCities( province, language ):
	"""Returns list of cities for the given province, using
	given language, from weatherNetwork.com

	province: valid province code

	language: e or f
	"""

	br = mechanize.Browser()
	br.set_handle_robots( False )
	br.addheaders = [('User-agent', 'Firefox')]
	url = "http://www.theweathernetwork.com/index.php?product=weather&pagecontent=cancities" + province
	urlMatch = '^/weather/ca' + province

	if language == 'e':
		url += '_en'
	else:
		url += '_fr'

	br.open( url )

	cityData = {}
	for l in br.links(url_regex=urlMatch):
		cityData[l.url[9:]] = l.text
	return cityData


def getCityData( city, language, day ):
	br = mechanize.Browser()
	br.set_handle_robots( False )
	br.addheaders = [('User-agent', 'Firefox')]

	if language == 'e':
		url = "http://rss.theweathernetwork.com/weather/" + city
	else:
		url = "http://rss.meteomedia.com/weather/" + city

	br.open( url )
	html = br.response().read()
	soup = BeautifulStoneSoup(html)
	description = soup('item')[day].description.text.split(',')
	weather = description[0]

	if day == 0:
		try:
			temperature = float( ''.join( c for c in description[1] if c in set(string.digits + '-' ) ) )
		except:
			temperature = None
		try:
			humidity = float( ''.join( c for c in description[2] if c in set(string.digits) ) )
		except:
			humidity = None
		return (weather, temperature, humidity)
	else:
		try:
			high = float( ''.join( c for c in description[1] if c in set(string.digits + '-') ) )
		except:
			high = None
		try:
			low = float( ''.join( c for c in description[2] if c in set(string.digits + '-') ) )
		except:
			low = None
		try:
			pop = float( ''.join( c for c in description[3] if c in set(string.digits ) ) )
		except:
			pop = None
		return (weather, high, low, pop)



def getWeatherData( gp, province, language, day ):
	gp.AddMessage('Getting cities for ' + string.upper(province))
	cityList = getCities( province, language )
	g = wnGeocoder( province )
	cityData = []

	gp.AddMessage('Getting weather data')
	cityCount = 0
	for city in cityList:
		cityCount += 1
		if (cityCount % 50) == 0 :
				gp.AddMessage('  ... ' + str(cityCount) + ' of ' + str(len(cityList.keys())) + ' cities')
		cityEntry = [city, cityList[city] ]  # cityID, name

		try:
			lat,lon = g.getCoordinates( city )
			cityEntry.extend( [lat,lon] )
		except:
			continue  # unknown city code
		cityWeather = getCityData( city, language, day )
		cityEntry.extend( cityWeather )

		cityData.append( cityEntry )

	return cityData


def outputWeatherData( fileName, weatherData ):
	if fileName:     # redirect stdout to file
		saveStdOut = sys.stdout
		f = open(fileName, 'w')
		sys.stdout = f

	for d in weatherData:
		print('\t'.join(map(str,d)))

	if fileName:    # restore stdout
		sys.stdout = saveStdOut
		f.close()

def createWeatherDataLayer( gp, folder, layerName, weatherData, province, day ):
	gp.AddMessage('Creating layer: ' + layerName)
	gp.workspace = folder
	fcu = FeatureClassUtilities(gp)
	_province = string.upper( province )

	if day ==0:  # today's weather includes TEMPERATURE & HUMIDITY
		ID,NAME,LAT,LON,WEATHER,TEMP,HUMID = range(7)
		newLayer = fcu.CreateFeatureClass(folder,layerName,fcu.FeatureType.POINT,SPATIALREFERENCE,
									  [["PROV", fcu.AddFieldTypesEnum.TEXT],
									   ["NAME", fcu.AddFieldTypesEnum.TEXT],
									   ["WEATHER", fcu.AddFieldTypesEnum.TEXT],
									   ["TEMP", fcu.AddFieldTypesEnum.FLOAT],
									   ["HUMID", fcu.AddFieldTypesEnum.FLOAT],
									   ["LAT", fcu.AddFieldTypesEnum.FLOAT],
									   ["LON", fcu.AddFieldTypesEnum.FLOAT]],
									  True)
	else:   # tomorrow's weather includes HIGH, LOW & CHANCE OF PRECIPITATION
		ID,NAME,LAT,LON,WEATHER,HIGH,LOW,POP = range(8)
		newLayer = fcu.CreateFeatureClass(folder,layerName,fcu.FeatureType.POINT,SPATIALREFERENCE,
									  [["PROV", fcu.AddFieldTypesEnum.TEXT],
									   ["NAME", fcu.AddFieldTypesEnum.TEXT],
									   ["WEATHER", fcu.AddFieldTypesEnum.TEXT],
									   ["HIGH", fcu.AddFieldTypesEnum.FLOAT],
									   ["LOW", fcu.AddFieldTypesEnum.FLOAT],
									   ["POP", fcu.AddFieldTypesEnum.FLOAT],
									   ["LAT", fcu.AddFieldTypesEnum.FLOAT],
									   ["LON", fcu.AddFieldTypesEnum.FLOAT]],
									  True)

	dataCursor = gp.InsertCursor( newLayer )
	pointFeature = gp.CreateObject("Point")
	for d in weatherData:
		newFeature = dataCursor.NewRow()
		pointFeature.X = d[LON]
		pointFeature.Y = d[LAT]

		newFeature.shape = pointFeature
		newFeature.PROV = _province
		newFeature.NAME = d[NAME]
		newFeature.WEATHER = d[WEATHER]
		newFeature.LAT = d[LAT]
		newFeature.LON = d[LON]

		if day == 0:
			if d[TEMP] : newFeature.TEMP = d[TEMP]
			if d[HUMID] : newFeature.HUMID = d[HUMID]
		else:
			if d[HIGH] : newFeature.HIGH = d[HIGH]
			if d[LOW] : newFeature.LOW = d[LOW]
			if d[POP] : newFeature.POP = d[POP]


		dataCursor.InsertRow(newFeature)

	del pointFeature
	del newFeature
	del dataCursor



def main(argv):
	gp = arcgisscripting.create()
	gp.AddMessage('\n')

	if gp.ParameterCount == 4:
		folder = os.sep.join( gp.GetParameterAsText(0).split( os.sep )[:-1] )
		layerName = gp.GetParameterAsText(0).split( os.sep )[-1]
		province = string.lower( gp.GetParameterAsText(1) )
		day = {'today':0, 'tomorrow':1, 'day after tomorrow':2,
			   'day after the day after tomorrow':3}[ string.lower(gp.GetParameterAsText(2)) ]
		language = string.lower( gp.GetParameterAsText(3)[0] ) 

	else:
		usage()
		sys.exit(2)

	weatherData = getWeatherData( gp, province, language, day )
	createWeatherDataLayer( gp, folder, layerName, weatherData, province, day )



if __name__ == "__main__":
    main(sys.argv[1:])

