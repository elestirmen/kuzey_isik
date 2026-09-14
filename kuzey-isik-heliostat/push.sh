#!/usr/bin/env bash
# Kuzey Isik Heliostati -> GitHub   (macOS / Linux / Git Bash)
set -e
cd "$(dirname "$0")"
REPO="kuzey-isik-heliostat"
DESC="Urgup (Nevsehir) icin heliostat: 10 m kuzeydeki duvara kurulan hareketli ayna ile kuzey cephesindeki pencereye gunes isigi. Interaktif simulasyon + Arduino kodu."

[ -d .git ] || { git init -b main >/dev/null; echo "git deposu olusturuldu."; }
git add -A
if git diff --cached --quiet; then
  echo "Islenecek degisiklik yok."
else
  git commit -F - <<'MSGEOF'
Kuzey Isik Heliostati: simulasyon, Arduino kodu ve referans hesaplar

Urgup'te kuzeye bakan bir pencereye, 10 m kuzeydeki bahce duvarina kurulan
hareketli aynayla gun isigi tasiyan heliostat.

- docs/index.html: bagimliliksiz interaktif simulasyon (izometrik gorunum,
  vaziyet plani, dusey kesit, kuzey cephesi; alti yonlendirme yontemi)
- firmware/: DS3231 + 2 servo ile acik dongu Arduino kodu
- tools/: NOAA gunes konumu ve heliostat geometrisi icin Python referansi,
  pvlib (NREL SPA) ile 0.016 derece icinde dogrulandi

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Sqxdg5ixnK6kSNPFcKZfbE
MSGEOF
  echo "Commit olusturuldu."
fi

if command -v gh >/dev/null 2>&1; then
  if git remote | grep -q '^origin$'; then git push -u origin main
  else gh repo create "$REPO" --public --source . --remote origin --description "$DESC" --push; fi
  echo; echo "Hazir: $(gh repo view --json url -q .url)"
  echo "GitHub Pages: Settings > Pages > Source: main, klasor: /docs"
else
  echo
  echo "gh kurulu degil. github.com/new adresinden bos bir public depo acin, sonra:"
  echo "  git remote add origin https://github.com/<kullanici>/$REPO.git"
  echo "  git push -u origin main"
fi
