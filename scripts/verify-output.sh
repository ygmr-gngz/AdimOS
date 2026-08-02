#!/usr/bin/env bash
# verify-output.sh — render SONRASI çalışır, gerçek video dosyasını/URL'sini
# ölçer ve her metriği eşiğiyle karşılaştırır. Tahmin yok — tüm değerler
# ffprobe/ffmpeg ile ölçülür. Herhangi bir satır FAIL ise exit 1.
#
# Kullanım:
#   bash scripts/verify-output.sh <video_url_veya_dosya> [requested_seconds] [tolerance_seconds]
#
# requested_seconds/tolerance_seconds verilmezse süre kontrolü atlanır
# (video_jobs.requested_duration_seconds / duration_tolerance_seconds panelden
# elle kopyalanabilir).
set -uo pipefail

VIDEO="${1:-}"
REQUESTED="${2:-}"
TOLERANCE="${3:-8}"

if [ -z "$VIDEO" ]; then
  echo "Kullanım: bash scripts/verify-output.sh <video_url_veya_dosya> [requested_seconds] [tolerance_seconds]" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Ortama göre python/python3 seç. command -v yeterli değil: Windows'ta
# "python3" genelde gerçek Python değil, çalıştırılınca "Python bulunamadı"
# yazıp Microsoft Store'a yönlendiren bir App Execution Alias stub'ı olabilir
# (var olması onu çalışır kılmaz) — bu yüzden gerçekten ÇALIŞTIĞI test edilir.
PY=""
for candidate in python python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "1" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "HATA: çalışan bir python bulunamadı (python3 stub olabilir, bkz. Windows App Execution Alias)" >&2
  exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0

row() {
  # row "isim" "değer" "eşik" "OK|FAIL"
  local name="$1" value="$2" thresh="$3" status="$4"
  printf "  %-20s %-16s eşik: %-24s %s\n" "$name" "$value" "$thresh" "$status"
  if [ "$status" = "OK" ]; then
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "verify-output.sh — hedef: $VIDEO"
[ -n "$REQUESTED" ] && echo "istenen süre: ${REQUESTED}s +- ${TOLERANCE}s"
echo

# ── ffprobe format/stream verisi tek seferde çekilir ──────────────────────
PROBE_JSON="$(ffprobe -v error -show_format -show_streams -print_format json "$VIDEO" 2>"$TMPDIR/probe_err.log")"
if [ -z "$PROBE_JSON" ]; then
  echo "HATA: ffprobe video/URL'yi okuyamadı:" >&2
  cat "$TMPDIR/probe_err.log" >&2
  exit 1
fi
echo "$PROBE_JSON" > "$TMPDIR/probe.json"

# ── Python: probe.json'dan teknik metrikleri çıkar + eşiklerle karşılaştır ──
read -r DUR_VAL DUR_STATUS DUR_THRESH \
     PIXFMT_VAL PIXFMT_STATUS \
     ACODEC_VAL ACODEC_STATUS <<PYEOF
$("$PY" - "$TMPDIR/probe.json" "$REQUESTED" "$TOLERANCE" <<'PYSCRIPT'
import json, sys
probe_path, requested, tolerance = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.load(open(probe_path, encoding="utf-8"))
fmt = data.get("format", {})
streams = data.get("streams", [])
vstream = next((s for s in streams if s.get("codec_type") == "video"), {})
astream = next((s for s in streams if s.get("codec_type") == "audio"), {})

dur = float(fmt.get("duration", 0) or 0)
if requested:
    req, tol = float(requested), float(tolerance)
    lo, hi = req - tol, req + tol
    dur_status = "OK" if lo <= dur <= hi else "FAIL"
    dur_thresh = f"{req:.0f}+-{tol:.0f}s_[{lo:.0f}-{hi:.0f}]"
else:
    dur_status, dur_thresh = "OK", "atlandi(hedef_yok)"

pix_fmt = vstream.get("pix_fmt", "yok")
pix_status = "OK" if pix_fmt == "yuv420p" else "FAIL"

acodec = astream.get("codec_name", "yok")
asr = astream.get("sample_rate", "?")
ach = astream.get("channels", "?")
acodec_str = f"{acodec}_{asr}_{ach}ch"
acodec_status = "OK" if acodec == "aac" else "FAIL"

print(f"{dur:.2f} {dur_status} {dur_thresh} {pix_fmt} {pix_status} {acodec_str} {acodec_status}")
PYSCRIPT
)
PYEOF

echo "=== TEKNİK ==="
row "duration_sec" "$DUR_VAL" "$DUR_THRESH" "$DUR_STATUS"
row "pix_fmt" "$PIXFMT_VAL" "yuv420p" "$PIXFMT_STATUS"
row "audio_codec" "$ACODEC_VAL" "aac" "$ACODEC_STATUS"

# ── faststart: moov atomu mdat'tan önce mi (byte-offset karşılaştırması) ──
LOCAL_FILE="$VIDEO"
DOWNLOADED=0
if echo "$VIDEO" | grep -qE '^https?://'; then
  LOCAL_FILE="$TMPDIR/dl.mp4"
  curl -s -L -o "$LOCAL_FILE" "$VIDEO"
  DOWNLOADED=1
fi
FASTSTART_STATUS=$("$PY" -c "
d = open('$LOCAL_FILE', 'rb').read(20_000_000)
moov, mdat = d.find(b'moov'), d.find(b'mdat')
print('OK' if (moov != -1 and mdat != -1 and moov < mdat) else 'FAIL')
" 2>/dev/null || echo "FAIL")
row "faststart" "$FASTSTART_STATUS" "moov<mdat" "$FASTSTART_STATUS"

# ── Ses: mean_volume, LUFS, true peak, sessizlik ──────────────────────────
VOL_OUT=$(ffmpeg -i "$VIDEO" -af volumedetect -f null - 2>&1)
MEAN_VOL=$(echo "$VOL_OUT" | grep -oE "mean_volume:\s*[-0-9.]+" | grep -oE "[-0-9.]+" | head -1)
MEAN_VOL="${MEAN_VOL:-0}"
MEAN_VOL_STATUS=$("$PY" -c "print('OK' if $MEAN_VOL > -45 else 'FAIL')")
row "mean_volume_db" "$MEAN_VOL" "> -45dB" "$MEAN_VOL_STATUS"

LOUDNORM_OUT=$(ffmpeg -i "$VIDEO" -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1)
LUFS_JSON=$(echo "$LOUDNORM_OUT" | "$PY" -c "
import sys, re, json
txt = sys.stdin.read()
m = re.search(r'\{[^{}]*\"input_i\"[^{}]*\}', txt, re.DOTALL)
print(json.dumps(json.loads(m.group(0))) if m else '{}')
")
INTEGRATED_LUFS=$(echo "$LUFS_JSON" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('input_i','0'))")
TRUE_PEAK=$(echo "$LUFS_JSON" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('input_tp','0'))")
LUFS_STATUS=$("$PY" -c "print('OK' if -18.0 <= $INTEGRATED_LUFS <= -14.0 else 'FAIL')")
TP_STATUS=$("$PY" -c "print('OK' if $TRUE_PEAK <= -1.5 else 'FAIL')")
row "integrated_lufs" "$INTEGRATED_LUFS" "-18..-14" "$LUFS_STATUS"
row "true_peak_dbtp" "$TRUE_PEAK" "<= -1.5" "$TP_STATUS"

SILENCE_OUT=$(ffmpeg -i "$VIDEO" -af silencedetect=noise=-40dB:d=0.3 -f null - 2>&1)
MAX_SILENCE=$(echo "$SILENCE_OUT" | grep -oE "silence_duration:\s*[0-9.]+" | grep -oE "[0-9.]+" | sort -rn | head -1)
MAX_SILENCE="${MAX_SILENCE:-0}"
SILENCE_STATUS=$("$PY" -c "print('OK' if $MAX_SILENCE <= 3.0 else 'FAIL')")
row "max_silence_sec" "$MAX_SILENCE" "<= 3.0s" "$SILENCE_STATUS"

# ── Görsel: 8 eşit aralıklı kare çıkar, visual_metrics.py'ye gönder ────────
echo
echo "=== GÖRSEL ==="
DUR_FOR_FRAMES=$("$PY" -c "print(max(float('$DUR_VAL' or 0), 1.0))")
FRAME_DIR="$TMPDIR/frames"
mkdir -p "$FRAME_DIR"
ffmpeg -i "$VIDEO" -vf "fps=8/$DUR_FOR_FRAMES" -vsync vfr "$FRAME_DIR/f%03d.png" -y >/dev/null 2>&1

FRAME_FILES=("$FRAME_DIR"/f*.png)
if [ -e "${FRAME_FILES[0]}" ] && [ "${#FRAME_FILES[@]}" -ge 2 ]; then
  VISUAL_OUT=$("$PY" "$SCRIPT_DIR/visual_metrics.py" "${FRAME_FILES[@]}")
  EDGE_AVG=$(echo "$VISUAL_OUT" | grep edge_density_avg | cut -d= -f2)
  CONTENT_PCT=$(echo "$VISUAL_OUT" | grep content_pixel_pct | cut -d= -f2)
  FRAME_DIFF=$(echo "$VISUAL_OUT" | grep frame_diff_avg | cut -d= -f2)
  EDGE_STATUS=$("$PY" -c "print('OK' if $EDGE_AVG >= 2.5 else 'FAIL')")
  CONTENT_STATUS=$("$PY" -c "print('OK' if $CONTENT_PCT >= 15 else 'FAIL')")
  DIFF_STATUS=$("$PY" -c "print('OK' if $FRAME_DIFF >= 6 else 'FAIL')")
  row "edge_density_avg" "$EDGE_AVG" ">= 2.5" "$EDGE_STATUS"
  row "content_pixel_pct" "$CONTENT_PCT" ">= 15" "$CONTENT_STATUS"
  row "frame_diff_avg" "$FRAME_DIFF" ">= 6" "$DIFF_STATUS"
else
  row "edge_density_avg" "OLCULEMEDI" ">= 2.5" "FAIL"
  row "content_pixel_pct" "OLCULEMEDI" ">= 15" "FAIL"
  row "frame_diff_avg" "OLCULEMEDI" ">= 6" "FAIL"
fi

echo
echo "=== SONUÇ: $FAIL_COUNT FAIL / $PASS_COUNT OK ==="
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
