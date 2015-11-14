import requests
import sys
import xml.etree.ElementTree as ET
import smtplib
import getpass
import json

args = sys.argv
print args

def is_night(zipcode, datetime):
    zip_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList='
   
    r = requests.get(zip_request+str(zipcode))
    lat_lon = (ET.fromstring(r.text)[0].text).split(',')
    latitude = lat_lon[0]
    longitude = lat_lon[1]
    
    #separate date from time here
    #array of time to compare to result
    time = [3, 45, 15]

    #date format --> YYYY-MM-DD
    sun_data_req = 'http://api.sunrise-sunset.org/json?lat='+latitude+'&lng='+longitude+'&date='+date
    r = requests.get(sun_data_req)
    result = json.loads(r.text)
    
    #formatting result
    sunrise = result['results']['sunrise']
    sunrise = map(int, sunrise[:-3].split(':'))
    sunset = result['results']['sunset']
    sunset = map(int, sunset[:-3].split(':'))
    sunset[0] = sunset[0]+12
    
    #compare hours to time
    if(time[0]>sunrise[0]+1 and time[0]<sunset[0]-1):
        return False
    else:
        return True


    

def is_weather_clear(zipcode, time):
    zip_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList='
    sky_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?&featureType=Forecast_Gml2Point&propertyName=sky'

    r = requests.get(zip_request+str(zipcode))
    lat_lon = (ET.fromstring(r.text)[0].text).split(',')
    latitude = lat_lon[0]
    longitude = lat_lon[1]
    #print 'Zipcode located at LAT:',latitude,'LON:',longitude
    
    lat_lon_req = '&gmlListLatLon='+latitude+','+longitude
    
    #for loop here through a range of times from start_time to stop_time
    #YYYY-MM-DDTHH:MM:SS format
    datetime = '2015-11-15T12:00:00'
    time_req = '&requestedTime='+datetime
    
    r = requests.get(sky_request+lat_lon_req+time_req)
    cover = int((ET.fromstring(r.text)[1][0][2].text).split('.')[0])

    if cover < 25:
        #print 'it is clear!'
        return True
    else:
        #print 'too cloudy to see'
        return False

def send_text_msg(msg):
    email_user = 'btkaija@gmail.com'
    bens_text_gateway = '8026983193@vtext.com'

    email_pass = getpass.getpass("Input the password for "+email_user+': ')

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email_user, email_pass)

    server.sendmail(email_user, bens_text_gateway, msg)
    print 'Text message sent to '+bens_text_gateway
    return


#send_text_msg('testing function')
clear = is_weather_clear(24060, 0, 0)
print 'viewable times'+str(clear)
