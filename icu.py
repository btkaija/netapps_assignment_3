import sys, time, requests, os
import xml.etree.ElementTree as ET
import smtplib, getpass, json
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from geopy import Nominatim
import getopt, geocoder, ephem, math

def usage():
    print ("icu.py -z zipcode -s satellite_name")

def get_times(tle, elevation, location):
    sat = ephem.readtle(str(tle[0]), str(tle[1]), str(tle[2]))

    horizon = '-0:34'
    viewer = ephem.Observer()
    viewer.lon, viewer.lat = location.longitude, location.latitude
    now = datetime.utcnow()
    viewer.date = now
    viewer.horizon=horizon
    i = 0
    times = []

    #get 50 times to view satellite
    while i < 50:
        sat.compute(viewer)
        np = viewer.next_pass(sat)
        next_pass_times = np[::2]
        if None in next_pass_times:
            break
        sun = ephem.Sun()
        sun.compute(viewer)
        sun_alt = math.degrees(sun.alt)
        if sat.eclipsed is False:
            times.append(next_pass_times[0].datetime().strftime("%Y-%m-%dT%H:%M:%S"))
            i = i + 1
        viewer.date = next_pass_times[-1]
    return times

def get_tle(satellite):
    space_base_URL = "https://www.space-track.org"
    auth_path = "/ajaxauth/login"
    logout_path = "/ajaxauth/logout"
    user = "andrewgs@vt.edu"
    passw = "Holotrackvexsentinal_691"
    query = "/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/"
    query = query + str(satellite)
    query = query + "/orderby/TLE_LINE0 asc/format/3le"
    cred = {"identity": user, "password": passw}
    s = requests.Session()
    r1 = s.post(space_base_URL + auth_path, data=cred)
    r2 = s.get(space_base_URL + query)
    result = r2.text
    s.get(space_base_URL + logout_path)
    return result

def led_and_sound_sec():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(25, GPIO.OUT)
    GPIO.output(25, True)
    #make sound here
    os.system('omxplayer notification.mp3')
    #turn off led
    GPIO.output(25, False)
    

#will return true of false based on if the time is considered night
def is_night(latitude, longitude, date_time):
        
    #separate date from time here
    date_time = date_time.split('T')
    #array of time to compare to result
    time_val = time.mktime(time.strptime('1999-'+date_time[1], '%Y-%H:%M:%S'))
    time_val = datetime.fromtimestamp(time_val)
    
    time_val = time_val.hour*60*60 + time_val.minute*60 + time_val.second
    date = date_time[0]

    #date format --> YYYY-MM-DD
    sun_data_req = 'http://api.sunrise-sunset.org/json?lat='+latitude+'&lng='+longitude+'&date='+date
    r = requests.get(sun_data_req)
    result = json.loads(r.text)
    
    #formatting result
    sunrise = result['results']['sunrise']
    sunset = result['results']['sunset']
    #print ''
    #print date_time, sunrise, sunset
    sunrise = time.mktime(time.strptime('1999-'+sunrise, '%Y-%I:%M:%S %p'))
    sunset = time.mktime(time.strptime('1999-'+sunset, '%Y-%I:%M:%S %p'))
    sunrise = datetime.fromtimestamp(sunrise) - timedelta(hours=1)
    sunset = datetime.fromtimestamp(sunset) + timedelta(hours=1)
    sunrise = sunrise.hour*60*60 + sunrise.minute*60 + sunrise.second
    sunset = sunset.hour*60*60 + sunset.minute*60 + sunset.second
    if(time_val>sunrise and time_val<sunset):
        return False
    else:
        return True
    

def is_weather_clear(latitude, longitude, date_time):
    sky_request = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?&featureType=Forecast_Gml2Point&propertyName=sky'

    lat_lon_req = '&gmlListLatLon='+latitude+','+longitude
    
    #YYYY-MM-DDTHH:MM:SS format
    #datetime = '2015-11-15T12:00:00'
    
    time_req = '&requestedTime='+date_time
    
    r = requests.get(sky_request+lat_lon_req+time_req)
    try:
        cover = int((ET.fromstring(r.text)[1][0][2].text).split('.')[0])
    except:
        #print 'Error retrieving weather data for'+date_time
        #print r.text
        cover = 101

    if cover < 25:
        return [True, cover]
    else:
        return [False, cover]

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


#main
try:
    arg1, arg2 = getopt.getopt(sys.argv[1:], "-z:, -s:")
except getopt.GetoptError as err:
    print (str(err))
    usage()
    sys.exit(2)
if len(arg1) != 2:
    usage()
    sys.exit(2)
zip_code = ''
satellite = ''
for i in arg1:
    if (i[0] == '-z'):
        zip_code = i[1]
    else:
        satellite = i[1]

result = get_tle(satellite)

print ''
print "Satellite Info: "+result

result = result.split('\n')
geolocator = Nominatim()
location = geolocator.geocode(zip_code + ", United States")
g = geocoder.elevation((location.latitude, location.longitude))


times = get_times(result, g.meters, location)
#print times
clear_times = []

print 'NOTE: all times are in UTC time'
print ''

#loop through each time found and check to see if visible
for t in times:
    clear = is_weather_clear(str(location.latitude),str(location.longitude), t)
    night = is_night(str(location.latitude),str(location.longitude), t)
    if(clear[0] and night):
        print 'Clear time found! --> '+t
        print 'The cloud cover is will only be at '+str(clear[1])+'%'
        clear_times.append(t)
        if(len(clear_times)==5):
            break

print ''
print 'Viewable events show below'
print clear_times
print ''
print 'Begining to wait for the viewable events listed above'
print ''
#enter loop waiting for events to occur

event_num = 0

while(1):
    now = datetime.utcnow()
    new_event = clear_times[event_num]

    check_time = time.mktime(time.strptime(new_event, '%Y-%m-%dT%H:%M:%S'))
    check_time = datetime.fromtimestamp(check_time) - timedelta(seconds=(15*60))
    #compare now, check_time to see if event will occur
    if(now>check_time):
        print 'Viewable event is occurring soon! (15 min from now: '+str(now)+')'
        event_num = event_num+1
        if event_num == len(clear_times):
            print 'All events have occured for the requested satellite.'
            break
        #send notifications
        led_and_sound_sec()
        send_text_msg('A viewable event for the satellite with id: '+satellite+'''
                      is occurring in the zip code: '''+zip_code+' in 15 minutes from '+str(now))

    #wait for 10 seconds before checking the time again
    time.sleep(10)
#end
