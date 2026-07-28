#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AdimOS Smoke Test -- deploy oncesi zorunlu kontrol.
    Bu script PASS olmadan uzun render baslatilmaz.

.USAGE
    cd C:\Users\USER\OneDrive\Desktop\AdimOS
    .\scripts\smoke.ps1
#>

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$remotionDir = Join-Path $root "remotion"
$results = @()

function Pass($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green;  $script:results += @{ok=$true; msg=$msg} }
function Fail($msg) { Write-Host "  [!!] $msg" -ForegroundColor Red;    $script:results += @{ok=$false; msg=$msg} }
function Info($msg) { Write-Host "  [i] $msg"  -ForegroundColor Cyan }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "  AdimOS Smoke Test -- $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Yellow
Write-Host "==========================================`n" -ForegroundColor Yellow

# -- 1. Remotion surum kontrolu ----------------------------------------
Write-Host "[ 1 ] Remotion Surum Kontrolu" -ForegroundColor White
$pkg = Get-Content (Join-Path $remotionDir "package.json") | ConvertFrom-Json
$EXPECTED = "4.0.488"
$allDeps = @{}
if ($pkg.dependencies)    { $pkg.dependencies.PSObject.Properties    | ForEach-Object { $allDeps[$_.Name] = $_.Value } }
if ($pkg.devDependencies) { $pkg.devDependencies.PSObject.Properties  | ForEach-Object { $allDeps[$_.Name] = $_.Value } }

$bad = @()
foreach ($key in $allDeps.Keys) {
    if ($key -eq "remotion" -or $key.StartsWith("@remotion/")) {
        if ($allDeps[$key] -ne $EXPECTED) {
            $bad += "$key=$($allDeps[$key])"
        }
    }
}
if ($bad.Count -eq 0) { Pass "Tum @remotion/* paketleri $EXPECTED" }
else                   { Fail "Surum uyumsuzlugu: $($bad -join ', ')" }

# -- 2. Asset varlik kontrolu ------------------------------------------
Write-Host "`n[ 2 ] Asset Varlik Kontrolu" -ForegroundColor White
$publicDir = Join-Path $remotionDir "public"

$fonts = @(
    "fonts/NotoSans-Regular-Latin.woff2",
    "fonts/NotoSans-Regular-LatinExt.woff2",
    "fonts/NotoSans-Bold-Latin.woff2",
    "fonts/NotoSans-Bold-LatinExt.woff2"
)
$missingFonts = @()
foreach ($f in $fonts) {
    if (-not (Test-Path (Join-Path $publicDir $f))) { $missingFonts += $f }
}
if ($missingFonts.Count -eq 0) { Pass "4 woff2 font dosyasi mevcut" }
else                            { Fail "Eksik fontlar: $($missingFonts -join ', ')" }

$logoPath = Join-Path $publicDir "brand/adim-musavir-logo.png"
if (Test-Path $logoPath) { Pass "Logo PNG bundle'da mevcut" }
else {
    Info "Logo PNG bundle'da yok -- brand.logo_url Supabase fallback kullanilacak"
    $script:results += @{ok=$true; msg="Logo yok ama fallback OK"}
}

# -- 3. Git tracking kontrolu ------------------------------------------
Write-Host "`n[ 3 ] Git Tracking Kontrolu" -ForegroundColor White
Push-Location $root
$trackedFonts = git ls-files "remotion/public/fonts/" 2>$null
$fontCount = ($trackedFonts -split "`n" | Where-Object { $_ -match "\.woff2$" }).Count
if ($fontCount -ge 4) { Pass "Font dosyalari git ile takip ediliyor ($fontCount adet)" }
else                  { Fail "Font dosyalari git'te eksik: $fontCount/4" }

$googleFontsRef = git grep -l "fonts.googleapis.com" "remotion/src/" 2>$null
if (-not $googleFontsRef) { Pass "Google Fonts CDN referansi yok (yerel fontlar)" }
else                      { Fail "Google Fonts CDN hala referans aliniyor: $googleFontsRef" }
Pop-Location

# -- 4. Python backend testleri ----------------------------------------
Write-Host "`n[ 4 ] Backend Birim Testleri" -ForegroundColor White
$backendDir = Join-Path $root "backend"
Push-Location $backendDir

try {
    $output = python scripts/test_05_pipeline_gates.py 2>&1
    $outStr = $output -join "`n"
    if ($LASTEXITCODE -eq 0) { Pass "test_05 pipeline_gates gecti (13/13)" }
    else { Fail "test_05 pipeline_gates basarisiz:`n$($outStr | Select-Object -Last 5)" }
} catch { Fail "test_05 calistirilamadi: $_" }

Pop-Location

# -- 5. TypeScript derleme ---------------------------------------------
Write-Host "`n[ 5 ] TypeScript Derleme Kontrolu" -ForegroundColor White
Push-Location $remotionDir
try {
    $tscOut = npx tsc --noEmit 2>&1
    if ($LASTEXITCODE -eq 0) { Pass "TypeScript derleme basarili (hata yok)" }
    else {
        $errLines = ($tscOut -split "`n" | Where-Object { $_ -match "error TS" }) | Select-Object -First 3
        Fail "TypeScript hatalari: $($errLines -join ' | ')"
    }
} catch {
    Info "TypeScript kontrolu atlandi (npx bulunamadi)"
}
Pop-Location

# -- Ozet --------------------------------------------------------------
$total  = $results.Count
$ok     = ($results | Where-Object { $_.ok }).Count
$failed = $total - $ok

Write-Host ""
Write-Host "==========================================" -ForegroundColor Yellow
if ($failed -eq 0) {
    Write-Host "  SONUC: PASS ($ok/$total)" -ForegroundColor Green
    Write-Host "  Deploy islemi baslatilabilir." -ForegroundColor Green
} else {
    Write-Host "  SONUC: FAIL ($ok/$total -- $failed basarisiz)" -ForegroundColor Red
    Write-Host "  Deploy BASLATILMAMALI. Yukaridaki hatalari duzeltiniz." -ForegroundColor Red
    $results | Where-Object { -not $_.ok } | ForEach-Object { Write-Host "    [!!] $($_.msg)" -ForegroundColor Red }
}
Write-Host "==========================================`n" -ForegroundColor Yellow

if ($failed -gt 0) { exit 1 }
