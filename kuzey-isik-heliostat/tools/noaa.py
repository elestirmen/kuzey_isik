import math, datetime as dt

D2R = math.pi/180.0; R2D = 180.0/math.pi

def julian_day(y, mo, d, hour_utc):
    if mo <= 2:
        y -= 1; mo += 12
    A = math.floor(y/100); B = 2 - A + math.floor(A/4)
    jd = math.floor(365.25*(y+4716)) + math.floor(30.6001*(mo+1)) + d + B - 1524.5
    return jd + hour_utc/24.0

def sun_position(year, month, day, hour, minute, second, lat, lon, tz_hours, refraction=True):
    """NOAA solar position. Returns (elevation_deg, azimuth_deg_from_N_CW, declination, eot_min)."""
    hour_utc = hour + minute/60.0 + second/3600.0 - tz_hours
    jd = julian_day(year, month, day, hour_utc)
    t = (jd - 2451545.0)/36525.0

    L0 = (280.46646 + t*(36000.76983 + t*0.0003032)) % 360.0
    M  = 357.52911 + t*(35999.05029 - 0.0001537*t)
    e  = 0.016708634 - t*(0.000042037 + 0.0000001267*t)
    Mr = M*D2R
    C  = (math.sin(Mr)*(1.914602 - t*(0.004817 + 0.000014*t))
        + math.sin(2*Mr)*(0.019993 - 0.000101*t)
        + math.sin(3*Mr)*0.000289)
    Ltrue = L0 + C
    omega = 125.04 - 1934.136*t
    lam = Ltrue - 0.00569 - 0.00478*math.sin(omega*D2R)
    eps0 = 23.0 + (26.0 + ((21.448 - t*(46.815 + t*(0.00059 - t*0.001813))))/60.0)/60.0
    eps  = eps0 + 0.00256*math.cos(omega*D2R)

    decl = math.asin(math.sin(eps*D2R)*math.sin(lam*D2R))*R2D

    y = math.tan(eps*D2R/2.0)**2
    L0r = L0*D2R
    eot = 4.0*R2D*( y*math.sin(2*L0r) - 2*e*math.sin(Mr)
                   + 4*e*y*math.sin(Mr)*math.cos(2*L0r)
                   - 0.5*y*y*math.sin(4*L0r) - 1.25*e*e*math.sin(2*Mr) )

    tst = (hour*60.0 + minute + second/60.0) + eot + 4.0*lon - 60.0*tz_hours
    ha = (tst/4.0) - 180.0
    while ha < -180: ha += 360
    while ha >  180: ha -= 360

    latr = lat*D2R; dr = decl*D2R; har = ha*D2R
    cosz = math.sin(latr)*math.sin(dr) + math.cos(latr)*math.cos(dr)*math.cos(har)
    cosz = max(-1.0, min(1.0, cosz))
    zen = math.acos(cosz)*R2D
    elev = 90.0 - zen

    # azimuth from North, clockwise
    az = math.atan2(math.sin(har), math.cos(har)*math.sin(latr) - math.tan(dr)*math.cos(latr))*R2D
    az = (az + 180.0) % 360.0

    if refraction and elev > -1.0:
        er = elev*D2R
        if elev > 85: r = 0.0
        elif elev > 5:  r = 58.1/math.tan(er) - 0.07/math.tan(er)**3 + 0.000086/math.tan(er)**5
        elif elev > -0.575: r = 1735.0 + elev*(-518.2 + elev*(103.4 + elev*(-12.79 + elev*0.711)))
        else: r = -20.772/math.tan(er)
        elev += r/3600.0
    return elev, az, decl, eot
