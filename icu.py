import requests
import sys
import xml.etree.ElementTree as ET


args = sys.argv
zip_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList='

print args

r = requests.get(zip_request+args[1])
lat_lon = (ET.fromstring(r.text)[0].text).split(',')
latitude = lat_lon[0]
longitude = lat_lon[1]

print 'LAT:',latitude,'LON:',longitude

