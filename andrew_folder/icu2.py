import getopt, sys, requests, geocoder, ephem, datetime, math
from geopy import Nominatim

def usage():
    print ("icu.py -z zipcode -s satellite_name")

#--------------------------------------------------
def fun(tle, elevation, location):
    sat = ephem.readtle(str(tle[0]), str(tle[1]), str(tle[2]))

    horizon = '-0:34'
    viewer = ephem.Observer()
    viewer.lon, viewer.lat = location.longitude, location.latitude
    now = datetime.datetime.utcnow()
    viewer.date = now
    viewer.horizon=horizon
    i = 0	
    times = []
    while i < 100:
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
times = fun(result, g.meters, location)
print times
