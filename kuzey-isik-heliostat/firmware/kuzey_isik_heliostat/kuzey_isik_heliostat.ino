/* =============================================================================
   KUZEY ISIK HELIOSTATI  -  Urgup / Nevsehir
   Evin 10 m kuzeyindeki duvara kurulu ayna, gunesi kuzey cephesindeki
   pencereye sabit tutar.  Acik dongu: DS3231 saat + NOAA gunes konumu.

   Donanim : Arduino Uno/Nano (veya ESP32) + DS3231 + 2 adet servo
   Kutuphane: RTClib (Adafruit), Servo (yerlesik)

   !! SERVO BESLEMESI AYRI OLMALI: MG996R kalkista ~2.5 A ceker, Arduino'nun
      5V pini bunu veremez.  Ayri 6V / 5A adaptor kullanin, GND'leri birlestirin.
      Servo hattina 1000 uF kondansator koyun.

   KOORDINAT SISTEMI (ENU):  x = Dogu,  y = Kuzey,  z = Yukari
   Azimut : Kuzey'den saat yonunde  (K=0, D=90, G=180, B=270)
   Orijin : Kuzey cephesinin dibi, pencere ortasinin tam altinda
   ---------------------------------------------------------------------------
   TEMEL FIZIK
     s = aynadan GUNESE bakan birim vektor
     t = aynadan PENCEREYE bakan birim vektor   (sabit!)
     n = normalize(s + t)                        <-- ayna normali, BISEKTOR
   Gunes 15 derece/saat doner, ayna normali bunun yarisi kadar (~7.5 d/sa).
   ============================================================================= */

#include <Wire.h>
#include <RTClib.h>
#include <Servo.h>

// ----------------------------------------------------------------- KONUM ----
const float LAT = 38.6317f;      // Urgup enlem  (+ kuzey)
const float LON = 34.9128f;      // Urgup boylam (+ dogu)
const float TZ  = 3.0f;          // UTC+3, Turkiye'de yaz saati yok

// -------------------------------------------------------------- GEOMETRI ----
// Sahada seritmetreyle olcun; 1 cm hata pencerede 2 cm kayma demek degil,
// ama 10 m mesafede aci hatasi buyutulur - dikkatli olcun.
const float MX = 0.00f, MY = 10.00f, MZ = 2.20f;   // ayna merkezi
const float WX = 0.00f, WY =  0.00f, WZ = 1.80f;   // pencere merkezi

// ------------------------------------------------------------ SERVO PINS ----
const uint8_t PIN_PAN  = 9;
const uint8_t PIN_TILT = 10;

/* SERVO KALIBRASYONU  --  iki nokta yeter.
   Yontem: servoya bir mikrosaniye degeri yaz (seri portta u1000), AYNANIN
   gercek acisini pusula/dijital acuolcerle olc, asagiya yaz; ikinci nokta icin
   tekrarla.  Redüktor kullaniyorsaniz olcumu AYNA uzerinde yaptiginiz icin
   oran zaten kalibrasyona gomulur, ayrica girmeye gerek yok.
   Redüktor SART: duz servo ~1 derece cozunurluk verir = 10 m'de 35 cm kayma. */
struct Axis { float aLo, uLo, aHi, uHi; float minA, maxA; };
Axis PAN  = { 135.0f, 1000.0f, 225.0f, 2000.0f, 120.0f, 245.0f };
Axis TILT = {   0.0f, 1200.0f,  45.0f, 1900.0f,  -5.0f,  45.0f };

// --------------------------------------------------------------- AYARLAR ----
const float MIN_SUN_ALT = 3.0f;    // bu yukseltinin altinda calisma (atmosfer + engel)
const float DEADBAND    = 0.05f;   // bu kadar kucuk degisimde servoya dokunma
const uint32_t PERIOD   = 60000UL; // 60 sn'de bir guncelle (7.5 d/sa => 0.125 derece adim)
const float PARK_PAN    = 180.0f;  // gece/park: aynayi guneye ve asagi cevir
const float PARK_TILT   = -5.0f;
const bool  HOUSE_SHADOW_CHECK = true;
const float HOUSE_H = 6.0f, HOUSE_W = 10.0f;   // evin saçak yuksekligi ve genisligi

RTC_DS3231 rtc;
Servo sPan, sTilt;
float curPan = PARK_PAN, curTilt = PARK_TILT;
uint32_t lastRun = 0;
bool parked = true;

// hedef vektoru t (sabit) - setup'ta bir kez hesaplanir
float TX, TY, TZv;

// ======================================================== YARDIMCI MATEMATIK
static inline float d2r(float d){ return d * 0.01745329252f; }
static inline float r2d(float r){ return r * 57.2957795131f; }

/* J2000'den (2000-01-01 12:00 UTC) gecen TAM GUN sayisi.
   Dikkat: dogrudan Julian Gun (2.46 milyon) kullanmayin - AVR'de double 32 bit,
   buyuk sayida hassasiyet kaybolur.  Once tamsayi gun farkini alip kesirli
   gunu sonra eklemek hatayi 0.0004 dereceye indirir. */
long daysFromJ2000(int Y, int M, int D){
  if (M <= 2) { Y -= 1; M += 12; }
  long A = Y / 100;
  long B = 2 - A + A / 4;
  long jd0 = (long)(365.25f * (Y + 4716)) + (long)(30.6001f * (M + 1)) + D + B - 1524;
  return jd0 - 2451545L;          // .5'ler karsilikli sadelesir
}

/* NOAA gunes konumu.  Cikti: yukselti (derece, kirilma duzeltmeli) ve
   azimut (Kuzey'den saat yonunde, derece). */
void sunAltAz(const DateTime& now, float& alt, float& az){
  float hLocal = now.hour() + now.minute() / 60.0f + now.second() / 3600.0f;
  float hUT    = hLocal - TZ;
  int Y = now.year(), M = now.month(), D = now.day();
  long nd = daysFromJ2000(Y, M, D);
  float n  = (float)nd - 0.5f + hUT / 24.0f;     // J2000'den gun (kesirli)
  float T  = n / 36525.0f;                        // Julian yuzyil

  float L0 = fmod(280.46646f + T * (36000.76983f + T * 0.0003032f), 360.0f);
  if (L0 < 0) L0 += 360.0f;
  float M0 = 357.52911f + T * (35999.05029f - 0.0001537f * T);
  float ec = 0.016708634f - T * (0.000042037f + 0.0000001267f * T);
  float Mr = d2r(M0);
  float C  = sin(Mr) * (1.914602f - T * (0.004817f + 0.000014f * T))
           + sin(2 * Mr) * (0.019993f - 0.000101f * T)
           + sin(3 * Mr) * 0.000289f;
  float om  = 125.04f - 1934.136f * T;
  float lam = L0 + C - 0.00569f - 0.00478f * sin(d2r(om));
  float e0  = 23.0f + (26.0f + (21.448f - T * (46.815f + T * (0.00059f - T * 0.001813f))) / 60.0f) / 60.0f;
  float eps = e0 + 0.00256f * cos(d2r(om));

  float decl = r2d(asin(sin(d2r(eps)) * sin(d2r(lam))));

  float y   = tan(d2r(eps) / 2.0f); y = y * y;
  float L0r = d2r(L0);
  float eot = 4.0f * r2d( y * sin(2 * L0r) - 2 * ec * sin(Mr)
            + 4 * ec * y * sin(Mr) * cos(2 * L0r)
            - 0.5f * y * y * sin(4 * L0r) - 1.25f * ec * ec * sin(2 * Mr) );

  float tst = hLocal * 60.0f + eot + 4.0f * LON - 60.0f * TZ;   // gercek gunes zamani (dk)
  float ha  = tst / 4.0f - 180.0f;
  while (ha < -180.0f) ha += 360.0f;
  while (ha >  180.0f) ha -= 360.0f;

  float la = d2r(LAT), dl = d2r(decl), Ha = d2r(ha);
  float cz = sin(la) * sin(dl) + cos(la) * cos(dl) * cos(Ha);
  cz = constrain(cz, -1.0f, 1.0f);
  alt = 90.0f - r2d(acos(cz));

  az = r2d(atan2(sin(Ha), cos(Ha) * sin(la) - tan(dl) * cos(la))) + 180.0f;
  if (az < 0) az += 360.0f; if (az >= 360.0f) az -= 360.0f;

  if (alt > -1.0f && alt < 85.0f) {           // atmosferik kirilma (yaklasik)
    float t = tan(d2r(alt));
    float r = (alt > 5.0f) ? (58.1f / t - 0.07f / (t * t * t))
                           : (1735.0f + alt * (-518.2f + alt * (103.4f + alt * (-12.79f + alt * 0.711f))));
    alt += r / 3600.0f;
  }
}

// =============================================================== HELIOSTAT ==
/* Ayna normalini hesapla.  Donen deger: gunes kullanilabilir mi? */
bool mirrorAim(float alt, float az, float& pan, float& tilt, float& incidence){
  if (alt < MIN_SUN_ALT) return false;

  float ca = cos(d2r(alt)), sa = sin(d2r(alt));
  float sx = ca * sin(d2r(az)), sy = ca * cos(d2r(az)), sz = sa;

  // 1) Gunes duvarin arkasinda mi?  (ayna duvarin GUNEY yuzunde)
  if (sy >= -0.02f) return false;

  // 2) Ev aynayi golgeliyor mu?  Aynadan gunese giden isin cepheyi kesiyor mu?
  if (HOUSE_SHADOW_CHECK) {
    float u  = (0.0f - MY) / sy;                 // y=0 duzlemine kadar
    float hx = MX + u * sx, hz = MZ + u * sz;
    if (fabs(hx) <= HOUSE_W * 0.5f && hz >= 0.0f && hz <= HOUSE_H) return false;
  }

  // 3) BISEKTOR:  n = normalize(s + t)
  float nx = sx + TX, ny = sy + TY, nz = sz + TZv;
  float L  = sqrt(nx * nx + ny * ny + nz * nz);
  nx /= L; ny /= L; nz /= L;

  pan  = r2d(atan2(nx, ny)); if (pan < 0) pan += 360.0f;
  tilt = r2d(asin(constrain(nz, -1.0f, 1.0f)));
  incidence = r2d(acos(constrain(nx * sx + ny * sy + nz * sz, -1.0f, 1.0f)));

  // 4) Yumusak limitler - isin komsunun penceresine gitmesin
  if (pan  < PAN.minA  || pan  > PAN.maxA)  return false;
  if (tilt < TILT.minA || tilt > TILT.maxA) return false;
  return true;
}

// =================================================================== SERVO ==
int angleToUs(const Axis& ax, float ang){
  float a = constrain(ang, ax.minA, ax.maxA);
  float u = ax.uLo + (a - ax.aLo) * (ax.uHi - ax.uLo) / (ax.aHi - ax.aLo);
  return (int)constrain(u, 600.0f, 2400.0f);
}

void driveTo(float pan, float tilt){
  if (fabs(pan - curPan) > DEADBAND)  { sPan.writeMicroseconds(angleToUs(PAN, pan));   curPan  = pan; }
  if (fabs(tilt - curTilt) > DEADBAND){ sTilt.writeMicroseconds(angleToUs(TILT, tilt)); curTilt = tilt; }
}

void park(){
  if (!parked) { Serial.println(F("-> PARK")); }
  driveTo(PARK_PAN, PARK_TILT);
  parked = true;
}

// =================================================================== SETUP ==
void setup(){
  Serial.begin(115200);
  Wire.begin();
  if (!rtc.begin()) { Serial.println(F("HATA: DS3231 yok")); while (1) delay(1000); }
  if (rtc.lostPower()) {
    Serial.println(F("RTC sifirlandi - derleme zamani yazildi"));
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  // hedef vektoru t = normalize(W - M)  (bir kez)
  float dx = WX - MX, dy = WY - MY, dz = WZ - MZ;
  float L = sqrt(dx * dx + dy * dy + dz * dz);
  TX = dx / L; TY = dy / L; TZv = dz / L;
  float tAz = r2d(atan2(TX, TY)); if (tAz < 0) tAz += 360.0f;
  Serial.print(F("Hedef: mesafe ")); Serial.print(L, 2);
  Serial.print(F(" m, azimut "));    Serial.print(tAz, 2);
  Serial.print(F(", yukselti "));    Serial.println(r2d(asin(TZv)), 2);

  sPan.attach(PIN_PAN, 600, 2400);
  sTilt.attach(PIN_TILT, 600, 2400);
  park();
  delay(1500);
  lastRun = millis() - PERIOD;       // hemen ilk hesabi yap
}

// ==================================================================== LOOP ==
void loop(){
  handleSerial();
  if (millis() - lastRun < PERIOD) return;
  lastRun = millis();

  DateTime now = rtc.now();
  float alt, az; sunAltAz(now, alt, az);
  float pan, tilt, inc;

  if (mirrorAim(alt, az, pan, tilt, inc)) {
    driveTo(pan, tilt);
    parked = false;
    Serial.print(now.hour()); Serial.print(':');
    if (now.minute() < 10) Serial.print('0'); Serial.print(now.minute());
    Serial.print(F("  gunes ")); Serial.print(alt, 2); Serial.print('/'); Serial.print(az, 2);
    Serial.print(F("  ayna "));  Serial.print(pan, 2); Serial.print('/'); Serial.print(tilt, 2);
    Serial.print(F("  gelis "));  Serial.print(inc, 1);
    Serial.print(F("  verim %")); Serial.println(100.0f * cos(d2r(inc)), 0);
  } else {
    park();
  }
}

// ====================================================== SERI KALIBRASYON ====
/*  p<aci>  : PAN eksenini bu aciya getir      ornek:  p172.5
    t<aci>  : TILT eksenini bu aciya getir     ornek:  t12.8
    u<us>   : PAN'a ham mikrosaniye yaz        ornek:  u1480
    v<us>   : TILT'e ham mikrosaniye yaz
    k       : park
    s       : saati yaz -> sYYYY,MM,DD,hh,mm,ss                              */
void handleSerial(){
  if (!Serial.available()) return;
  char c = Serial.read();
  String a = Serial.readStringUntil('\n'); a.trim();
  switch (c) {
    case 'p': curPan  = -999; driveTo(a.toFloat(), curTilt); Serial.println(F("pan ok")); break;
    case 't': curTilt = -999; driveTo(curPan, a.toFloat());  Serial.println(F("tilt ok")); break;
    case 'u': sPan.writeMicroseconds(a.toInt());  Serial.println(F("us ok")); break;
    case 'v': sTilt.writeMicroseconds(a.toInt()); Serial.println(F("us ok")); break;
    case 'k': park(); break;
    case 's': {
      int y, mo, d, h, mi, se;
      if (sscanf(a.c_str(), "%d,%d,%d,%d,%d,%d", &y, &mo, &d, &h, &mi, &se) == 6) {
        rtc.adjust(DateTime(y, mo, d, h, mi, se)); Serial.println(F("saat yazildi"));
      }
      break; }
  }
}
