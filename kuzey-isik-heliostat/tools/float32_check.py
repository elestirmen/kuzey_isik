# AVR Arduino'da double == float (32 bit). Gunes konumu hesabini float32 ile yapinca
# ne kadar hata olusur? Iki formulasyonu karsilastir: (a) tam Julian Gun, (b) J2000'den gun sayisi.
import math, numpy as np
from noaa import sun_position, julian_day
F=np.float32
D2R=math.pi/180; R2D=180/math.pi

def sun_f32(year,month,day,hour,minute,lat,lon,tz,use_jd_directly):
    hu=F(hour)+F(minute)/F(60)-F(tz)
    if use_jd_directly:
        jd=F(julian_day(year,month,day,float(hu)))          # ~2.46e6 -> float32 felaketi
        t=F((jd-F(2451545.0))/F(36525.0))
    else:
        n=F(julian_day(year,month,day,float(hu))-2451545.0) # ~9700 -> kucuk sayi
        t=F(n/F(36525.0))
    L0=F(np.mod(F(280.46646)+t*(F(36000.76983)+t*F(0.0003032)),F(360)))
    M =F(357.52911)+t*(F(35999.05029)-F(0.0001537)*t)
    e =F(0.016708634)-t*(F(0.000042037)+F(0.0000001267)*t)
    Mr=F(M*F(D2R))
    C =F(np.sin(Mr))*(F(1.914602)-t*(F(0.004817)+F(0.000014)*t))+F(np.sin(2*Mr))*(F(0.019993)-F(0.000101)*t)+F(np.sin(3*Mr))*F(0.000289)
    om=F(125.04)-F(1934.136)*t
    lam=F(L0+C)-F(0.00569)-F(0.00478)*F(np.sin(F(om*F(D2R))))
    eps0=F(23.0)+(F(26.0)+((F(21.448)-t*(F(46.815)+t*(F(0.00059)-t*F(0.001813)))))/F(60))/F(60)
    eps=eps0+F(0.00256)*F(np.cos(F(om*F(D2R))))
    decl=F(np.arcsin(F(np.sin(F(eps*F(D2R))))*F(np.sin(F(lam*F(D2R))))))*F(R2D)
    y=F(np.tan(F(eps*F(D2R))/F(2)))**2
    L0r=F(L0*F(D2R))
    eot=F(4.0)*F(R2D)*(y*F(np.sin(2*L0r))-F(2)*e*F(np.sin(Mr))+F(4)*e*y*F(np.sin(Mr))*F(np.cos(2*L0r))
        -F(0.5)*y*y*F(np.sin(4*L0r))-F(1.25)*e*e*F(np.sin(2*Mr)))
    tst=F(F(hour)*F(60)+F(minute))+eot+F(4.0)*F(lon)-F(60.0)*F(tz)
    ha=F(tst/F(4.0))-F(180.0)
    latr=F(lat*F(D2R)); dr=F(decl*F(D2R)); har=F(ha*F(D2R))
    cosz=F(np.sin(latr))*F(np.sin(dr))+F(np.cos(latr))*F(np.cos(dr))*F(np.cos(har))
    el=F(90.0)-F(np.arccos(np.clip(cosz,-1,1)))*F(R2D)
    az=F(np.arctan2(F(np.sin(har)),F(np.cos(har))*F(np.sin(latr))-F(np.tan(dr))*F(np.cos(latr))))*F(R2D)
    return float(el),float((az+180.0)%360.0)

LAT,LON,TZ=38.6317,34.9128,3.0
print(f"{'zaman':>14} {'ref el':>8} {'f32-JD el':>10} {'hata':>8} | {'ref az':>8} {'f32-JD az':>10} {'hata':>8} || {'f32-n el':>9} {'hata':>8} {'f32-n az':>9} {'hata':>8}")
worst_jd=worst_n=0
for (mo,d) in [(1,15),(3,21),(6,21),(12,21)]:
    for h in [9,12,15]:
        el,az,_,_=sun_position(2026,mo,d,h,0,0,LAT,LON,TZ,refraction=False)
        a1,b1=sun_f32(2026,mo,d,h,0,LAT,LON,TZ,True)
        a2,b2=sun_f32(2026,mo,d,h,0,LAT,LON,TZ,False)
        e1,f1=a1-el,((b1-az+180)%360)-180
        e2,f2=a2-el,((b2-az+180)%360)-180
        worst_jd=max(worst_jd,abs(e1),abs(f1)); worst_n=max(worst_n,abs(e2),abs(f2))
        print(f"{mo:02d}-{d:02d} {h:02d}:00 {el:8.3f} {a1:10.3f} {e1:8.3f} | {az:8.3f} {b1:10.3f} {f1:8.3f} || {a2:9.3f} {e2:8.3f} {b2:9.3f} {f2:8.3f}")
print(f"\nEN KOTU HATA  ->  tam Julian Gun ile float32: {worst_jd:.3f} deg   |   J2000 gun sayisi ile float32: {worst_n:.4f} deg")
print(f"Ayna hatasi = gunes hatasi/2 -> pencerede kayma:")
for v,lab in [(worst_jd,'tam JD'),(worst_n,'J2000 gun sayisi')]:
    print(f"   {lab:18}: {100*10.01*math.tan(v*D2R):8.1f} cm")
