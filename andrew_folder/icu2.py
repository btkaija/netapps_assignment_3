import getopt, sys, requests, geocoder, ephem, datetime, math
from geopy import Nominatim

def usage():
    print ("icu.py -z zipcode -s satellite_name")

#--------------------------------------------------
def seconds_between(d1, d2):
    return abs((d2 - d1).seconds)

def datetime_from_time(tr):
    year, month, day, hour, minute, second = tr.tuple()
    dt = datetime.datetime(year, month, day, hour, minute, int(second))
    return dt

def get_next_pass(lon, lat, alt, tle):

    sat = ephem.readtle(str(tle[0]), str(tle[1]), str(tle[2]))

    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.long = str(lon)
    observer.elevation = alt
    observer.pressure = 0
    observer.horizon = '-0:34'

    now = datetime.datetime.utcnow()
    observer.date = now

    tr, azr, tt, altt, ts, azs = observer.next_pass(sat)

    duration = int((ts - tr) *60*60*24)
    rise_time = datetime_from_time(tr)
    max_time = datetime_from_time(tt)
    set_time = datetime_from_time(ts)

    observer.date = max_time

    sun = ephem.Sun()
    sun.compute(observer)
    sat.compute(observer)

    sun_alt = math.degrees(sun.alt)

    visible = False
    if sat.eclipsed is False and -18 < degrees(sun_alt) < -6 :
        visible = True

    return {
             "rise_time": timegm(rise_time.timetuple()),
             "rise_azimuth": degrees(azr),
             "max_time": timegm(max_time.timetuple()),
             "max_alt": degrees(altt),
             "set_time": timegm(set_time.timetuple()),
             "set_azimuth": degrees(azs),
             "elevation": sat.elevation,
             "sun_alt": sun_alt,
             "duration": duration,
             "visible": visible
           }

def fun(tle, elevation, location):
    sat = ephem.readtle(str(tle[0]), str(tle[1]), str(tle[2]))


    horizon = '-0:34'
    viewer = ephem.Observer()
    viewer.lon, viewer.lat = location.longitude, location.latitude
    now = datetime.datetime.utcnow()
    viewer.date = now
    viewer.horizon=horizon
    i = 0	
    j = 0
    while i < 1 and j < 5:
        sat.compute(viewer)
        np = viewer.next_pass(sat)
        next_pass_times = (np[0], np[2], np[4])
        if None in next_pass_times:
            break
	sun = ephem.Sun()
	sun.compute(viewer)
	sun_alt = math.degrees(sun.alt)
	if sat.eclipsed is False and -18 < math.degrees(sun_alt) < -6:
		print "Next pass: " + next_pass_times[0].datetime().strftime("%Y-%m-%dT%H:%M:%S")        
		print ""
		i = i + 1
        j = j + 1
	t = datetime.datetime.fromtimestamp(next_pass_times[2])
	print t
        viewer.date = next_pass_times[2]
    print j
#--------------------------------------------------
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
    return r2.text

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
result = result.split('\n')
geolocator = Nominatim()
location = geolocator.geocode(zip_code + ", United States")
g = geocoder.elevation((location.latitude, location.longitude))

print (location.address)
print ((location.latitude, location.longitude))
print g.meters
fun(result, g.meters, location)
