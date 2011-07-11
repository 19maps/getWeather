#!/usr/bin/env python2
"""WeatherNetwork scraper

From WeatherNetwork.com get weather for all cities 
in a given Canadian province.  Defaults to Ontario.
Output to STOUT or text file

Usage: python getWeather.py [options] [filename]

Options:
  -p XX, --province=XX        province code: 
                                      AB BC MB NB NL NT NS
                                      NU ON PE QC SK YT
  -d X, --day=X               which day: 0 today (default), 1 tomorrow, 
                                      2 dayafter, 3 dayafter the dayafter
  -l X, --lang=X          language, E or F
  -h, --help                  show this help

Examples:
  getWeather.py               get weather for Ontario cities
                                      output to terminal
  getWeather.py -p NS         get weather for Nova Scotia cities
                                      output to terminal
  getWeather.py -p NS w.txt   get weather for Nova Scotia cities
                                      output to w.txt

"""

import re
import sys
import time
import string
import getopt
import mechanize
from BeautifulSoup import BeautifulStoneSoup
#from __future__ import print_function

__author__ = "Andrew Ross"
__copyright__ = "Copyright 2011"
__license__ = "GPL"
__version__ = "0.4"
__email__ = "andrew11@angoor.net"
__status__ = "Development"

# Source: http://www.canadapost.ca/tools/pg/manual/PGaddress-e.asp#1380608
PROVINCECODES = ('AB','BC','MB','NB','NL','NT','NS','NU','ON','PE','QC','SK','YT')
CITYLIST_FILE = 'cityList.csv'

class wnGeocoder:
	def __init__(self, province):
		self.geocoder = {}

		f = open( 'cityList.csv' )
		for l in f:
			wID,name,provID,lat,lon = l.strip().split(',')
			if string.lower( provID ) == province:
				# self.geocoder[wID] = (float(lat),float(lon))
				self.geocoder[wID] = (lat,lon)
		f.close()

	def getCoordinates( self, wid ):
		try:
			return self.geocoder[wid]
		except:
			return None


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

	# digitCharacters = set(string.digits + '-.' )  decimals do no seem to be used in these numbers
	digitCharacters = set(string.digits + '-' )

	print description

	weather = description[0]
	if day == 0:
		temperature = float( ''.join( c for c in description[1] if c in digitCharacters ) )
		humidity = float( ''.join( c for c in description[2] if c in digitCharacters ) )
		return (weather, temperature, humidity)
	else:
		high = float( ''.join( c for c in description[1] if c in digitCharacters ) )
		low = float( ''.join( c for c in description[2] if c in digitCharacters ) )
		pop = float( ''.join( c for c in description[3] if c in digitCharacters ) )
		return (weather, high, low, pop)



def getWeatherData( province, language, day ):
	cityList = getCities( province, language )
	g = wnGeocoder( province )
	cityData = []

	for city in cityList:
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
		# print(*d, sep='\t', file=f)
		print('\t'.join(map(str,d)))

	if fileName:    # restore stdout
		sys.stdout = saveStdOut
		f.close()


def main(argv):
	try:                                
		opts, args = getopt.getopt(argv, "hp:l:d:", ["help", "province=","lang=","day="])
	except getopt.GetoptError:          
		usage()                         
		sys.exit(2)                     

	province = 'on'
	language = 'e'
	day = 0

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-p", "--province"):
			if string.upper( arg ) in PROVINCECODES:
				province = string.lower( arg )
			else:
				print "ERROR: Unknown province code - ", arg
				print "  use --help for list of valid codes\n"
				sys.exit(2)
		elif opt in ("-l", "--lang"):
			if arg in ('e','E','f','F'):
				language = string.lower( arg )
			else:
				print "ERROR: Unknown language code - ", arg
				print "  use --help for list of valid codes\n"
				sys.exit(2)
		elif opt in ("-d", "--day"):
			try:
				if 0 <= int(arg) < 4:
					day = int(arg)
				else:
					print "ERROR: Unknown day - ", arg
					print "  use --help for accepted values\n"
					sys.exit(2)
			except:
				print "ERROR: Unknown day - ", arg
				print "  use --help for accepted values\n"
				sys.exit(2)
				
			

	if len(args) > 1:
			print "ERROR: Unknown arguements - ", args[1:]
			print "  use --help for accepted values\n"
	elif len(args) == 1:
			fileName = args[0]
	else:
		fileName = None

	weatherData = getWeatherData( province, language, day )
	outputWeatherData( fileName, weatherData )

	sys.exit()



if __name__ == "__main__":
    main(sys.argv[1:])



