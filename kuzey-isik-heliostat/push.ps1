# Kuzey Isik Heliostati -> GitHub
# Bu betigi depo klasorunun icinde calistirin:
#   PowerShell'i buraya acin ve su satiri yazin:   .\push.ps1
# Gereken: git  (ve varsa gh -> https://cli.github.com)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$REPO = "kuzey-isik-heliostat"
$DESC = "Urgup (Nevsehir) icin heliostat: 10 m kuzeydeki duvara kurulan hareketli ayna ile kuzey cephesindeki pencereye gunes isigi. Interaktif simulasyon + Arduino kodu."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "git bulunamadi. https://git-scm.com/download/win adresinden kurun." -ForegroundColor Red; exit 1
}

$msg = @'
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
'@

if (-not (Test-Path .git)) {
  git init -b main | Out-Null
  Write-Host "git deposu olusturuldu." -ForegroundColor Green
}
git add -A
if (git diff --cached --quiet) {
  Write-Host "Islenecek degisiklik yok." -ForegroundColor Yellow
} else {
  $f = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($f, $msg, (New-Object System.Text.UTF8Encoding($false)))
  git commit -F $f | Out-Null
  Remove-Item $f
  Write-Host "Commit olusturuldu." -ForegroundColor Green
}

if (Get-Command gh -ErrorAction SilentlyContinue) {
  gh auth status 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Write-Host "gh oturumu yok, once: gh auth login" -ForegroundColor Yellow; exit 1 }
  if (-not (git remote | Select-String -Quiet "^origin$")) {
    gh repo create $REPO --public --source . --remote origin --description $DESC --push
  } else {
    git push -u origin main
  }
  $url = (gh repo view --json url -q .url)
  Write-Host ""
  Write-Host "Hazir: $url" -ForegroundColor Green
  Write-Host "GitHub Pages'i acmak icin: Settings > Pages > Source: main, klasor: /docs" -ForegroundColor Cyan
  Write-Host "Sonra simulasyon su adreste calisir: https://<kullanici>.github.io/$REPO/" -ForegroundColor Cyan
} else {
  Write-Host ""
  Write-Host "gh (GitHub CLI) kurulu degil. Iki secenek:" -ForegroundColor Yellow
  Write-Host "  1) https://cli.github.com adresinden kurun, 'gh auth login' yapin, bu betigi tekrar calistirin."
  Write-Host "  2) Ya da github.com/new adresinden BOS bir public depo acin ('$REPO'), sonra:"
  Write-Host ""
  Write-Host "     git remote add origin https://github.com/<kullanici>/$REPO.git"
  Write-Host "     git push -u origin main"
}
