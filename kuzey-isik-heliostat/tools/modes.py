"""Alti farkli ayna yonlendirme yontemini karsilastirir ve isik lekesinin
kuzey cepheye nereye dustugunu yazdirir."""
import math, random
from noaa import sun_position
from heliostat import (LAT,LON,TZ,W,M,T,unit,sub,dot,add,scale,sun_vec,vec_to_angles,
                       reflect,hit_facade,mirror_shaded,WIN_W,WIN_H,D2R,R2D)

REF_H, REF_MIN = 13, 0   # sabit ayna referans saati

def bisector(s): return unit(add(s,T))

def ref_normal(mo,d):
    el,az,_,_ = sun_position(2026,mo,d,REF_H,REF_MIN,0,LAT,LON,TZ)
    return bisector(sun_vec(el,az))

def n_from_angles(pan,tilt):
    p,t=pan*D2R,tilt*D2R
    return (math.cos(t)*math.sin(p), math.cos(t)*math.cos(p), math.sin(t))

def target_aligned(s):
    """Hedefe hizali montaj: birincil eksen T yonunde. (theta = gelis acisi, rho = spin)"""
    n=bisector(s)
    theta=math.acos(max(-1,min(1,dot(n,T))))*R2D
    # T'ye dik referans: yukari bilesen
    up=(0,0,1.0)
    e1=unit(sub(up, scale(T, dot(up,T))))
    e2=(T[1]*e1[2]-T[2]*e1[1], T[2]*e1[0]-T[0]*e1[2], T[0]*e1[1]-T[1]*e1[0])
    rho=math.atan2(dot(n,e2), dot(n,e1))*R2D
    return theta,rho,n

MODES=['bisektor','hedefe_hizali','gunes_takibi','sabit','sadece_pan','ldr']

def normal_for(mode,s,nref,rng):
    if mode=='bisektor':      return bisector(s)
    if mode=='hedefe_hizali': return target_aligned(s)[2]     # ayni normal, farkli mekanik
    if mode=='gunes_takibi':  return s
    if mode=='sabit':         return nref
    if mode=='sadece_pan':
        pan,_=vec_to_angles(bisector(s)); _,tref=vec_to_angles(nref)
        return n_from_angles(pan,tref)
    if mode=='ldr':
        pan,tilt=vec_to_angles(bisector(s))
        return n_from_angles(pan+rng.gauss(0,0.8), tilt+rng.gauss(0,0.8))

for mo,d,lab in [(12,21,'KIS GUNDONUMU'),(6,21,'YAZ GUNDONUMU')]:
    nref=ref_normal(mo,d); rng=random.Random(7)
    print(f"\n######## {lab} ({d:02d}.{mo:02d}) — ISIK LEKESI KUZEY CEPHEDE NEREYE DUSUYOR? ########")
    print(f"   (pencere merkezi x=0.00 z={W[2]:.2f} | pencere {WIN_W}x{WIN_H} m -> x +-{WIN_W/2:.2f}, z {W[2]-WIN_H/2:.2f}..{W[2]+WIN_H/2:.2f})")
    hdr=f"{'saat':>5}"+''.join(f"{m:>22}" for m in MODES); print(hdr)
    stats={m:[0,0] for m in MODES}
    for mins in range(int(8*60),int(17*60)+1,10):
        h,mi=divmod(mins,60)
        el,az,_,_=sun_position(2026,mo,d,h,mi,0,LAT,LON,TZ)
        if el<=0.5: continue
        s=sun_vec(el,az)
        if mirror_shaded(s): continue
        line=f"{h:02d}:{mi:02d}"
        for m in MODES:
            n=normal_for(m,s,nref,rng)
            p=hit_facade(n,s)
            stats[m][1]+=1
            if p is None: line+=f"{'--- gokyuzune ---':>22}"
            else:
                inwin = abs(p[0])<=WIN_W/2 and abs(p[1]-W[2])<=WIN_H/2
                if inwin: stats[m][0]+=1
                line+=f"{('x%+5.2f z%+5.2f %s'%(p[0],p[1],'OK' if inwin else '  ')):>22}"
        if mins%60==0: print(line)
    print(f"{'ISABET':>5}"+''.join(f"{(f'{stats[m][0]}/{stats[m][1]}  %{100*stats[m][0]/max(1,stats[m][1]):.0f}'):>22}" for m in MODES))

# --- Hedefe hizali montaj eksen acilari ---
print("\n\n######## HEDEFE HIZALI (TARGET-ALIGNED) MONTAJ EKSEN ACILARI ########")
print(f"{'saat':>5} {'KIS theta':>10} {'KIS rho':>9} {'YAZ theta':>10} {'YAZ rho':>9}")
for hh in range(9,17):
    out=f"{hh:02d}:00"
    for mo,d in [(12,21),(6,21)]:
        el,az,_,_=sun_position(2026,mo,d,hh,0,0,LAT,LON,TZ)
        if el<=0.5: out+=f"{'-':>10}{'-':>9}"; continue
        th,rho,_=target_aligned(sun_vec(el,az))
        out+=f"{th:10.2f}{rho:9.2f}"
    print(out)

# --- Hassasiyet / leke boyutu ---
print("\n\n######## HASSASIYET ve LEKE BOYUTU (mesafe 10 m) ########")
Lm=math.dist(W,M)
for err in [0.1,0.25,0.5,1.0,2.0]:
    print(f"  Ayna normalinde {err:4.2f} deg hata -> isin {2*err:4.2f} deg sapar -> pencerede {100*Lm*math.tan(2*err*D2R):6.1f} cm kayma")
for size in [0.3,0.6,1.0]:
    spread=Lm*math.tan(0.53*D2R)
    print(f"  {size:.1f} m ayna -> pencerede leke ~ {size+spread:.2f} m (gunesin 0.53 deg cap yayilmasi +{spread*100:.0f} cm)")
print(f"\n  Gunes 15 deg/sa doner -> ayna normali 7.5 deg/sa -> 60 sn'de {7.5/60:.3f} deg -> lekede {100*Lm*math.tan(2*(7.5/60)*D2R):.1f} cm adim")
print(f"  Standart servo 1 deg cozunurluk -> lekede {100*Lm*math.tan(2*1*D2R):.0f} cm adim  (YETERSIZ)")
print(f"  3:1 reduktor + writeMicroseconds (~0.2 deg) -> lekede {100*Lm*math.tan(2*0.2*D2R):.0f} cm  (IYI)")

# --- Enerji ---
print("\n\n######## ENERJI (1 m2 ayna, %90 yansitma, DNI 850 W/m2 acik kis gunu) ########")
DNI, A, R = 850, 1.0, 0.90
for lab,cosv in [('Kis ogle',0.963),('Kis ortalama',0.932),('Ekinoks ort.',0.827),('Yaz ort.',0.753)]:
    P=DNI*A*R*cosv
    print(f"  {lab:14} cos={cosv:.3f} -> {P:5.0f} W  (~{P*93:6.0f} lm, 1.1x1.1 m lekede ~{P*93/1.21:7.0f} lux)")
