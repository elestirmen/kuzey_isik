"""Tek eksen + sabit hizla surulen aynanin en iyi eksenini ve hizini arar.
Klasik kutup ekseni (7.5 derece/saat) varsayiminin bu hedef icin
neden yetmedigini sayisal olarak gosterir."""
import math, numpy as np
from scipy.optimize import minimize
from noaa import sun_position
D2R=math.pi/180; R2D=180/math.pi
LAT,LON,TZ=38.6317,34.9128,3.0
W=np.array([0,0,1.80]); M=np.array([0,10.0,2.20])
T=(W-M)/np.linalg.norm(W-M)

def sunv(el,az):
    e,a=el*D2R,az*D2R
    return np.array([math.cos(e)*math.sin(a), math.cos(e)*math.cos(a), math.sin(e)])
def rot(axis,ang):
    a=axis/np.linalg.norm(axis); K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3)+math.sin(ang)*K+(1-math.cos(ang))*K@K
def spot(n,s):
    d=-s+2*np.dot(s,n)*n; d/=np.linalg.norm(d)
    if d[1]>=-1e-9: return None
    k=(0-M[1])/d[1]
    return np.array([M[0]+k*d[0], M[2]+k*d[2]])

def day_samples(mo,d,h0=8,h1=17):
    out=[]
    for mins in range(h0*60,h1*60+1,10):
        h,mi=divmod(mins,60)
        el,az,_,_=sun_position(2026,mo,d,h,mi,0,LAT,LON,TZ)
        if el<=1: continue
        s=sunv(el,az)
        if s[1]>=0: continue                      # duvar arkasi
        u=(0-M[1])/s[1]; x=M[0]+u*s[0]; z=M[2]+u*s[2]
        if abs(x)<=5 and 0<=z<=6: continue        # evin golgesi
        out.append((mins/60.0,s))
    return out

POL=np.array([0,math.cos(LAT*D2R),math.sin(LAT*D2R)])
print("Kutup ekseni (goksel kutba bakan) ENU:",np.round(POL,4), f" -> azimut 0 (Kuzey), yukselti {LAT} deg")

for mo,d,lab in [(12,21,'KIS'),(3,21,'EKINOKS'),(6,21,'YAZ')]:
    S=day_samples(mo,d)
    tm=np.mean([t for t,_ in S])
    # referans: orta saatteki ideal normal
    sm=min(S,key=lambda r:abs(r[0]-tm))[1]; n0=(sm+T)/np.linalg.norm(sm+T)
    def cost(p):
        aaz,ael,w=p
        a=np.array([math.cos(ael*D2R)*math.sin(aaz*D2R),math.cos(ael*D2R)*math.cos(aaz*D2R),math.sin(ael*D2R)])
        e=[]
        for t,s in S:
            n=rot(a,(t-tm)*w*D2R)@n0
            p2=spot(n,s)
            e.append(50.0 if p2 is None else np.linalg.norm(p2-np.array([W[0],W[2]])))
        return math.sqrt(np.mean(np.square(e)))
    best=None
    for a0 in [(0,LAT),(180,-LAT),(0,90),(90,0),(180,0)]:
        for w0 in [7.5,-7.5,15,-15]:
            r=minimize(cost,[a0[0],a0[1],w0],method='Nelder-Mead',
                       options={'xatol':1e-4,'fatol':1e-6,'maxiter':4000,'maxfev':6000})
            if best is None or r.fun<best.fun: best=r
    aaz,ael,w=best.x
    a=np.array([math.cos(ael*D2R)*math.sin(aaz*D2R),math.cos(ael*D2R)*math.cos(aaz*D2R),math.sin(ael*D2R)])
    errs=[]
    for t,s in S:
        n=rot(a,(t-tm)*w*D2R)@n0; p2=spot(n,s)
        errs.append(999 if p2 is None else np.linalg.norm(p2-np.array([W[0],W[2]])))
    print(f"\n--- {lab} ({d:02d}.{mo:02d}) | {len(S)} ornek, {S[0][0]:.1f}-{S[-1][0]:.1f} saat ---")
    print(f"  EN IYI TEK EKSEN: azimut {aaz%360:7.2f} deg, yukselti {ael:6.2f} deg | sabit hiz {w:6.3f} deg/saat")
    print(f"  (kutup ekseniyle aci farki: {math.acos(abs(np.dot(a,POL)))*R2D:5.2f} deg)")
    print(f"  RMS hata {np.mean(errs):.3f} m ort / {max(errs):.3f} m maks  -> 1.2x1.4 m pencereye {'SIGAR' if max(errs)<0.55 else 'SIGMAZ'}")

print("\n\n######## KISITLI SENARYOLAR ########")
def evaluate(a,w,mo,d,n0=None,tm=None):
    S=day_samples(mo,d)
    if not S: return None
    if tm is None: tm=np.mean([t for t,_ in S])
    if n0 is None:
        sm=min(S,key=lambda r:abs(r[0]-tm))[1]; n0=(sm+T)/np.linalg.norm(sm+T)
    errs=[]
    for t,s in S:
        n=rot(a,(t-tm)*w*D2R)@n0; p2=spot(n,s)
        errs.append(999 if p2 is None else np.linalg.norm(p2-np.array([W[0],W[2]])))
    return np.mean(errs),max(errs)

print("\nA) Eksen = KUTUP EKSENI (azimut 0, yukselti 38.63), hiz serbest:")
for mo,d,lab in [(12,21,'KIS'),(3,21,'EKINOKS'),(6,21,'YAZ')]:
    bw,be=None,1e9
    for w in np.arange(-16,16,0.05):
        r=evaluate(POL,w,mo,d)
        if r and r[1]<be: be,bw=r[1],w
    r=evaluate(POL,bw,mo,d)
    print(f"  {lab:8} en iyi hiz {bw:6.2f} d/sa -> ort {r[0]:.3f} m, maks {r[1]:.3f} m  {'SIGAR' if r[1]<0.55 else 'SIGMAZ'}")

print("\nB) Eksen = KUTUP, hiz tam 7.50 d/sa (klasik heliostat):")
for mo,d,lab in [(12,21,'KIS'),(3,21,'EKINOKS'),(6,21,'YAZ')]:
    for w in (7.5,-7.5):
        r=evaluate(POL,w,mo,d)
        print(f"  {lab:8} hiz {w:+5.2f} -> ort {r[0]:7.3f} m, maks {r[1]:7.3f} m  {'SIGAR' if r[1]<0.55 else 'SIGMAZ'}")

print("\nC) TEK SABIT GEOMETRI tum yil (azimut 180, yukselti -26.5, hiz 10.9 d/sa) — sadece gunluk sifirlama:")
aF=np.array([math.cos(-26.5*D2R)*math.sin(180*D2R),math.cos(-26.5*D2R)*math.cos(180*D2R),math.sin(-26.5*D2R)])
for mo,d,lab in [(12,21,'KIS'),(2,5,'SUBAT'),(3,21,'EKINOKS'),(5,1,'MAYIS'),(6,21,'YAZ'),(9,13,'EYLUL'),(11,1,'KASIM')]:
    r=evaluate(aF,10.9,mo,d)
    print(f"  {lab:8} ort {r[0]:.3f} m, maks {r[1]:.3f} m  {'SIGAR' if r[1]<0.55 else 'SIGMAZ'}")
