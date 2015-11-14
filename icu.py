import sys, time, requests, os
import xml.etree.ElementTree as ET
import smtplib, getpass, json
import RPi.GPIO as GPIO
from datetime import datetime, timedelta

args = sys.argv
print args

def led_and_sound_sec():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(25, GPIO.OUT)
    GPIO.output(25, True)
    #make sound here
    os.system('omxplayer notification.mp3')
    #turn off led
    GPIO.output(25, False)
    

def is_night(zipcode, date_time):
    zip_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList='
   
    r = requests.get(zip_request+str(zipcode))
    lat_lon = (ET.fromstring(r.text)[0].text).split(',')
    latitude = lat_lon[0]
    longitude = lat_lon[1]
    
    #separate date from time here
    date_time = date_time.split('T')
    #array of time to compare to result
    time_val = time.mktime(time.strptime('1999-'+date_time[1], '%Y-%H:%M:%S'))
    time_val = datetime.fromtimestamp(time_val)
    date = date_time[0]

    #date format --> YYYY-MM-DD
    sun_data_req = 'http://api.sunrise-sunset.org/json?lat='+latitude+'&lng='+longitude+'&date='+date
    r = requests.get(sun_data_req)
    result = json.loads(r.text)
    
    #formatting result
    sunrise = result['results']['sunrise']
    sunset = result['results']['sunset']
    sunrise = time.mktime(time.strptime('1999-'+sunrise, '%Y-%I:%M:%S %p'))
    sunset = time.mktime(time.strptime('1999-'+sunset, '%Y-%I:%M:%S %p'))
    sunrise = datetime.fromtimestamp(sunrise) + timedelta(hours=1)
    sunset = datetime.fromtimestamp(sunset) - timedelta(hours=1)

    if(time_val>sunrise and time_val<sunset):
        return False
    else:
        return True
    

def is_weather_clear(zipcode, date_time):
    zip_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList='
    sky_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?&featureType=Forecast_Gml2Point&propertyName=sky'

    r = requests.get(zip_request+str(zipcode))
    lat_lon = (ET.fromstring(r.text)[0].text).split(',')
    latitude = lat_lon[0]
    longitude = lat_lon[1]
    print 'Zipcode located at LAT:',latitude,'LON:',longitude
    
    lat_lon_req = '&gmlListLatLon='+latitude+','+longitude
    
    #for loop here through a range of times from start_time to stop_time
    #YYYY-MM-DDTHH:MM:SS format
    #datetime = '2015-11-15T12:00:00'
    
    time_req = '&requestedTime='+date_time
    
    r = requests.get(sky_request+lat_lon_req+time_req)
    try:
        cover = int((ET.fromstring(r.text)[1][0][2].text).split('.')[0])
    except:
        print 'Error retrieving weather data for date_time.'
        cover = 100

    if cover < 25:
        return True
    else:
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



date_time = '2015-11-20T12:30:00'
clear = is_weather_clear(24060, date_time)
night = is_night(24060, date_time)
print 'is clear? '+str(clear)
print 'is night? '+str(night)
led_and_sound_sec()

