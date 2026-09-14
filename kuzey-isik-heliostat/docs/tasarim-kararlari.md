# Tasarım kararları ve doğrulanmış sayılar

Ürgüp (38.6317° K, 34.9128° D, UTC+3, ~1043 m rakım).

## Varsayılan geometri

ENU koordinatları: x = Doğu, y = Kuzey, z = Yukarı. Orijin, kuzey cephesinin dibinde,
pencere ortasının tam altında.

| | x | y | z |
|---|---:|---:|---:|
| Pencere merkezi | 0.00 | 0.00 | 1.80 |
| Ayna merkezi | 0.00 | 10.00 | 2.20 |

Ev 10 m geniş, 6 m saçak yüksekliğinde. Pencere 1.2 × 1.4 m, ayna 1 × 1 m.
Aynadan pencereye: 10.01 m, azimut 180.0°, yükselti −2.29°.

## Temel kural

`n = normalize(s + t)` — `s` aynadan güneşe, `t` aynadan pencereye bakan birim vektör.
Güneş 15°/saat döner; ayna normali bunun yarısı kadar (bu geometride 6.4–10.9°/saat).

## Doğrulanmış performans (bisektör, açık gökyüzü)

| Tarih | Ayna ışık alır | Süre | Ort. cos γ | Tepe güç | PAN | TILT |
|---|---|---:|---:|---:|---|---|
| 21 Aralık | 08:00–17:10 | 9.3 sa | %93.2 | 705 W | 150–209° | −1…13° |
| 21 Mart | 07:00–18:30 | 11.7 sa | %83.0 | 775 W | 136–224° | 0…25° |
| 21 Haziran | 09:10–16:20 | 7.3 sa | %75.6 | 719 W | 145–216° | 26…36° |

Kışın en verimli — ışığa en çok o zaman ihtiyaç var. Yazın duvarın kendisi sabah ve
akşam aynayı gölgeliyor (güneş kuzeydoğudan doğup kuzeybatıdan batıyor).

Ev, aynayı gölgelemiyor: kış öğlesinde evin gölgesi duvara yalnızca 0.7 m yüksekliğe
kadar tırmanıyor, ayna ise 2.20 m'de.

## Yöntem karşılaştırması (21 Aralık)

| Yöntem | İsabet | Not |
|---|---:|---|
| Bisektör (2 servo) | %100 | Doğru yöntem |
| Tek eksen sabit hız | %100 | 1 motor; eksen ≈ azimut 180° / yükselti −26°, ≈ 11°/sa. Mevsimlik ayar gerekir |
| LDR kapalı döngü | %100 | Ort. 19 cm titreşim; ince ayar olarak kullanılmalı |
| Sadece PAN | %38 | Leke dikeyde kayıyor |
| Sabit ayna | %5 | — |
| Güneş takibi (`n = s`) | %0 | Işığı güneşe geri yollar — klasik hata |

Kutup ekseni + tam 7.5°/saat (klasik heliostat reçetesi) bu hedef için **çalışmıyor**
(hata 1–2.8 m), çünkü hedef kutup ekseni doğrultusunda değil. Optimizasyonla bulunan
eksen kutup ekseninden yalnızca ~13° sapıyor — yani fikir doğru, sabitler farklı.

Tek sabit geometriyle (eksen azimut 180°, yükselti −26.5°, 10.9°/sa) sadece günlük
sıfırlama yapılırsa ekinokslarda hata 0.2 m'de kalıyor, gündönümlerinde 0.7–0.95 m'ye
çıkıyor. Yani ayda bir eksen açısını düzeltmek gerekir — tarihsel heliostatlardaki
"deklinasyon ayarı" tam olarak bu.

## Kritik mühendislik kısıtı

Aynadaki 1° hata → ışında 2° → pencerede **35 cm** kayma. Toplam hata bütçesi ~0.3°.
Doğrudan sürülen servo ~1° çözünürlük verir → **3:1–4:1 redüktör şart**.

Leke boyutu = ayna kenarı + 9 cm (güneşin 0.53° açısal çapı, 10 m mesafede).
Güncelleme periyodu 60 sn yeterli: lekede 4 cm'lik adımlar oluşur.

## Donanım kararları

2 × servo (MG996R / DS3218) · DS3231 RTC + astronomik hesap (açık döngü) · ~1 m² ayna.
Servolar ayrı 6 V / 5 A beslemeden, GND ortak, servo hattında 1000 µF.

AVR'nin 32-bit float'ı yeterli: J2000'den gün sayısı formülasyonuyla hata 0.0004°.
(Tam Julian Gün kullanılırsa 0.05° — pencerede 0.9 cm, yine kabul edilebilir ama
gereksiz bir risk.) Ölçüm `tools/float32_check.py` içinde.

## Doğrulama

Güneş konumu NOAA algoritmasıyla hesaplanıyor; pvlib (NREL SPA) referansına karşı
yükseltide ≤ 0.016°, azimutta ≤ 0.007° sapma ölçüldü. Simülasyondaki JavaScript ile
`tools/` altındaki bağımsız Python hesabı isabet oranlarında birebir uyuştu
(%100 / %38 / %5 / %0).

## Açık konular

- Bahçe duvarının gerçekte cepheye paralel olup olmadığı ölçülmeli (simülasyon paralel varsayıyor).
- Kuzey referansı sahada belirlenmeli. Ürgüp'te manyetik sapma ≈ +6° doğu; öğlen en kısa
  gölge yöntemi daha güvenli.
- Rüzgâr yükü: 1 m² levhada 100 km/sa'te ≈ 500 N. Konsol ve park mekanizması buna göre.
