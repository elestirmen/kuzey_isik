"""Heliostat geometrisi: bisektor kurali, golgelenme ve kosinus verimi.

ENU koordinatlari: x = Dogu, y = Kuzey, z = Yukari.
Orijin: kuzey cephesinin dibi, pencere ortasinin tam altinda.
"""
import math
from noaa import sun_position
D2R=math.pi/180; R2D=180/math.pi

LAT,LON,TZ = 38.6317, 34.9128, 3.0
# ENU: x=Dogu, y=Kuzey, z=Yukari. Orijin: kuzey cephesinin dibi, pencere ortasinin altinda.
W  = (0.0, 0.0, 1.80)    # pencere merkezi
M  = (0.0, 10.0, 2.20)   # ayna merkezi (duvarin guney yuzu)
HOUSE_H, HOUSE_W = 6.0, 10.0
WIN_W, WIN_H = 1.20, 1.40

def unit(v):
    n=math.sqrt(sum(c*c for c in v)); return tuple(c/n for c in v)
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def scale(a,k): return (a[0]*k,a[1]*k,a[2]*k)

def sun_vec(elev,az):
    e,a=elev*D2R,az*D2R
    return (math.cos(e)*math.sin(a), math.cos(e)*math.cos(a), math.sin(e))
def vec_to_angles(n):
    az=(math.atan2(n[0],n[1])*R2D)%360.0
    el=math.asin(max(-1,min(1,n[2])))*R2D
    return az,el

T = unit(sub(W,M))                 # aynadan pencereye birim vektor
T_az,T_el = vec_to_angles(T)

def reflect(s,n):                  # gelen -s yonunde, yansiyan yon
    return unit(add(scale(s,-1), scale(n, 2*dot(s,n))))

def hit_facade(n,s):
    d=reflect(s,n)
    if d[1] >= -1e-9: return None   # cepheye dogru gitmiyor
    k=(0.0-M[1])/d[1]
    if k<=0: return None
    return (M[0]+k*d[0], M[2]+k*d[2], k)

def mirror_shaded(s):
    """Ev, aynayi golgeliyor mu? (guneye dogru isin evin kuzey cephesini kesiyor mu)"""
    if s[1] >= 0: return 'duvar'     # gunes kuzeyde -> duvarin arkasinda, ayna isik almiyor
    u=(0.0-M[1])/s[1]
    x=M[0]+u*s[0]; z=M[2]+u*s[2]
    if abs(x) <= HOUSE_W/2 and 0 <= z <= HOUSE_H: return 'ev'
    return None

def main():
    print(f"Hedef (aynadan pencereye): azimut {T_az:.2f} deg, yukselti {T_el:.2f} deg, mesafe {math.dist(W,M):.2f} m\n")

    def day_report(mo,d,label):
        print(f"=== {label}  ({d:02d}.{mo:02d}.2026) ===")
        print(f"{'saat':>5} {'gun.yuk':>8} {'gun.az':>8} {'PAN':>8} {'TILT':>8} {'gelis':>7} {'cos':>6} {'dPAN/dk':>8} {'durum':>8}")
        prev=None; rows=[]
        tmin=int(4*60); tmax=int(21*60)
        for mins in range(tmin,tmax,10):
            h,mi=divmod(mins,60)
            el,az,_,_ = sun_position(2026,mo,d,h,mi,0,LAT,LON,TZ)
            if el<=0.5: continue
            s=sun_vec(el,az)
            n=unit(add(s,T))
            pan,tilt=vec_to_angles(n)
            theta=math.acos(max(-1,min(1,dot(s,n))))*R2D
            sh=mirror_shaded(s)
            rate = None if prev is None else ((pan-prev[0]+180)%360-180)/((mins-prev[1]))
            rows.append((mins,el,az,pan,tilt,theta,math.cos(theta*D2R),rate,sh))
            prev=(pan,mins)
        for r in rows:
            if r[0]%60: continue
            h,mi=divmod(r[0],60)
            rt = f"{r[7]*60:8.2f}" if r[7] is not None else "     -  "
            print(f"{h:02d}:{mi:02d} {r[1]:8.2f} {r[2]:8.2f} {r[3]:8.2f} {r[4]:8.2f} {r[5]:7.2f} {r[6]:6.3f} {rt} {str(r[8] or 'ISIK'):>8}")
        ok=[r for r in rows if r[8] is None]
        if ok:
            rates=[abs(r[7])*60 for r in ok if r[7] is not None]
            e0,e1=divmod(ok[0][0],60); f0,f1=divmod(ok[-1][0],60)
            print(f"  -> Ayna gunes goruyor: {e0:02d}:{e1:02d} - {f0:02d}:{f1:02d}  ({len(ok)*10/60:.1f} saat)")
            print(f"  -> Ort. kosinus verimi: {sum(r[6] for r in ok)/len(ok):.3f} | en iyi {max(r[6] for r in ok):.3f}")
            print(f"  -> PAN hizi: ort {sum(rates)/len(rates):.2f} d/sa, MAKS {max(rates):.2f} d/sa")
            print(f"  -> PAN araligi {min(r[3] for r in ok):.1f}..{max(r[3] for r in ok):.1f} | TILT {min(r[4] for r in ok):.1f}..{max(r[4] for r in ok):.1f}")
        print()

    for mo,d,lab in [(12,21,'KIS GUNDONUMU'),(3,21,'EKINOKS'),(6,21,'YAZ GUNDONUMU'),(9,13,'BUGUN')]:
        day_report(mo,d,lab)


if __name__ == '__main__':
    main()
