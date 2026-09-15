# Referans hesaplar

Simülasyondaki JavaScript'in bağımsız bir kontrolü. `noaa.py` dışındaki her dosya
doğrudan çalıştırılabilir.

| Dosya | Ne yapar |
|---|---|
| `noaa.py` | NOAA güneş konumu algoritması (yükselti, azimut, deklinasyon, zaman denklemi) |
| `heliostat.py` | Bisektör kuralı, gölgelenme kontrolü, gün boyu açılar ve kosinüs verimi |
| `modes.py` | Altı yönlendirme yöntemi; ışık lekesinin kuzey cephedeki yeri ve isabet oranı |
| `single_axis.py` | Tek eksen + sabit hız için en iyi eksen araması (numpy + scipy) |
| `float32_check.py` | AVR'de 32-bit float ile hesaplanırsa oluşan hata (numpy) |

```bash
pip install -r requirements.txt   # sadece single_axis.py ve float32_check.py için
python heliostat.py
```

Güneş konumunu bağımsız bir referansa karşı doğrulamak isterseniz `pip install pvlib`
kurup `pvlib.solarposition.get_solarposition` çıktısıyla karşılaştırın. 2026'nın tamamı
10 dakikalık adımlarla tarandığında (güneş > 3°, 25 170 an) ölçülen sapma yükseltide
ort. 0.003° / maks 0.014°, azimutta ort. 0.005° / maks 0.027°.
