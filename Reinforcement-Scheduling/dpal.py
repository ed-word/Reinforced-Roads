import pandas as pd
import chardet
from math import sqrt, pi, sin, cos, tan, atan2 as arctan2
def OSGB36toWGS84(E, N):
    # E, N are the British national grid coordinates - eastings and northings
    # The Airy 180 semi-major and semi-minor axes used for OSGB36 (m)
    a, b = 6377563.396, 6356256.909
    F0 = 0.9996012717  # scale factor on the central meridian
    lat0 = 49 * pi / 180  # Latitude of true origin (radians)
    # Longtitude of true origin and central meridian (radians)
    lon0 = -2 * pi / 180
    N0, E0 = -100000, 400000  # Northing & easting of true origin (m)
    e2 = 1 - (b * b) / (a * a)  # eccentricity squared
    n = (a - b) / (a + b)

    # Initialise the iterative variables
    lat, M = lat0, 0

    while N - N0 - M >= 0.00001:  # Accurate to 0.01mm
        lat = (N - N0 - M) / (a * F0) + lat
        M1 = (1 + n + (5. / 4) * n**2 + (5. / 4) * n**3) * (lat - lat0)
        M2 = (3 * n + 3 * n**2 + (21. / 8) * n**3) * \
            sin(lat - lat0) * cos(lat + lat0)
        M3 = ((15. / 8) * n**2 + (15. / 8) * n**3) * \
            sin(2 * (lat - lat0)) * cos(2 * (lat + lat0))
        M4 = (35. / 24) * n**3 * sin(3 * (lat - lat0)) * cos(3 * (lat + lat0))
        # meridional arc
        M = b * F0 * (M1 - M2 + M3 - M4)

    # transverse radius of curvature
    nu = a * F0 / sqrt(1 - e2 * sin(lat)**2)

    # meridional radius of curvature
    rho = a * F0 * (1 - e2) * (1 - e2 * sin(lat)**2)**(-1.5)
    eta2 = nu / rho - 1

    secLat = 1. / cos(lat)
    VII = tan(lat) / (2 * rho * nu)
    VIII = tan(lat) / (24 * rho * nu**3) * \
        (5 + 3 * tan(lat)**2 + eta2 - 9 * tan(lat)**2 * eta2)
    IX = tan(lat) / (720 * rho * nu**5) * \
        (61 + 90 * tan(lat)**2 + 45 * tan(lat)**4)
    X = secLat / nu
    XI = secLat / (6 * nu**3) * (nu / rho + 2 * tan(lat)**2)
    XII = secLat / (120 * nu**5) * (5 + 28 * tan(lat)**2 + 24 * tan(lat)**4)
    XIIA = secLat / (5040 * nu**7) * (61 + 662 * tan(lat) **
                                      2 + 1320 * tan(lat)**4 + 720 * tan(lat)**6)
    dE = E - E0

    # These are on the wrong ellipsoid currently: Airy1830. (Denoted by _1)
    lat_1 = lat - VII * dE**2 + VIII * dE**4 - IX * dE**6
    lon_1 = lon0 + X * dE - XI * dE**3 + XII * dE**5 - XIIA * dE**7

    # Want to convert to the GRS80 ellipsoid.
    # First convert to cartesian from spherical polar coordinates
    H = 0  # Third spherical coord.
    x_1 = (nu / F0 + H) * cos(lat_1) * cos(lon_1)
    y_1 = (nu / F0 + H) * cos(lat_1) * sin(lon_1)
    z_1 = ((1 - e2) * nu / F0 + H) * sin(lat_1)

    # Perform Helmut transform (to go between Airy 1830 (_1) and GRS80 (_2))
    s = -20.4894 * 10**-6  # The scale factor -1
    # The translations along x,y,z axes respectively
    tx, ty, tz = 446.448, -125.157, + 542.060
    # The rotations along x,y,z respectively, in seconds
    rxs, rys, rzs = 0.1502,  0.2470,  0.8421
    rx, ry, rz = rxs * pi / (180 * 3600.), rys * pi / \
        (180 * 3600.), rzs * pi / (180 * 3600.)  # In radians
    x_2 = tx + (1 + s) * x_1 + (-rz) * y_1 + (ry) * z_1
    y_2 = ty + (rz) * x_1 + (1 + s) * y_1 + (-rx) * z_1
    z_2 = tz + (-ry) * x_1 + (rx) * y_1 + (1 + s) * z_1

    # Back to spherical polar coordinates from cartesian
    # Need some of the characteristics of the new ellipsoid
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a_2, b_2 = 6378137.000, 6356752.3141
    # The eccentricity of the GRS80 ellipsoid
    e2_2 = 1 - (b_2 * b_2) / (a_2 * a_2)
    p = sqrt(x_2**2 + y_2**2)

    # Lat is obtained by an iterative proceedure:
    lat = arctan2(z_2, (p * (1 - e2_2)))  # Initial value
    latold = 2 * pi
    while abs(lat - latold) > 10**-16:
        lat, latold = latold, lat
        nu_2 = a_2 / sqrt(1 - e2_2 * sin(latold)**2)
        lat = arctan2(z_2 + e2_2 * nu_2 * sin(latold), p)

    # Lon and height are then pretty easy
    lon = arctan2(y_2, x_2)
    H = p / cos(lat) - nu_2

    # Uncomment this line if you want to print the results
    # print([(lat-lat_1)*180/pi, (lon - lon_1)*180/pi])

    # Convert to degrees
    lat = lat * 180 / pi
    lon = lon * 180 / pi

    # Job's a good'n.
    return lat, lon


with open('dts.csv', 'rb') as f:
    result = chardet.detect(f.read())
    
dt = pd.read_csv('dts.csv',sep=',',encoding=result['encoding'])

dp = [ [0]*17521 for i in range(2549)]
cs = {'Serious':2,'Slight':1,'Fatal':3}
data = []
days = [0,31,28,31,30,31,30,31,31,30,31,30,31]
dsm = [0]*13
for i in range(1,13):
    dsm[i] = dsm[i-1] + days[i]
for i in range(2549):
    date = str(dt.ix[i]['Accident Date'])
    time = str(dt.ix[i]['Time (24hr)'])
    if len(time) == 4:
        hrs = int(time[:2])
        mn = int(time[2:])
    elif len(time) == 3:
        hrs = int(time[:1])
        mn = int(time[1:])
    dy,mt,yr = map(int,date.split('/'))
    cur = (dsm[mt]+dy)*24*2 + hrs*2 + int(mn/30)
    wt = int(dt.ix[i]['Number of Vehicles'] + cs[dt.ix[i]['Casualty Severity']])
    tm = []
    tm.append(cur)
    tm.append(wt)
    data.append(tm)

dp[0][data[0][0]] = data[0][1]

for i in range(1,2549):
    for j in range(1,17521):
        dp[i][j] = dp[i-1][j]
        dp[i][j] = max(dp[i][j],dp[i][j-1])
        if data[i][0] == j:
            dp[i][j] = max(dp[i][j],data[i][1]+dp[i-1][j-1])
            
            

print(max(dp[2548]))

i = 2548
j = 17520
st = set()
while i != 0 and j!=0:
    if dp[i-1][j] == dp[i][j]:
        i-=1
    elif dp[i-1][j-1] + data[i][1] == dp[i][j]:
        st.add(i)
        i-=1
        j-=1
    elif dp[i][j] == dp[i][j-1]:
        j-=1

lats = []
lons = []
goto = []
time = []
severity = [] 
for i in range(2549):
    est = dt.ix[i]['Grid Ref: Easting']
    nrt = dt.ix[i]['Grid Ref: Northing']
    to_srv = st.__contains__(i)
    lat,lon = OSGB36toWGS84(est,nrt)
    lats.append(lat)
    lons.append(lon)
    goto.append(to_srv)
    severity.append(data[i][1])
    time.append(data[i][0])

dt_f = pd.DataFrame(data={'lats':lats,'lons':lons,'goto':goto,'time':time,'severity':severity},index=None)
dt_f = dt_f.sort_values('time')
dt_f.to_csv('final.csv',sep=',')
print(dt_f)