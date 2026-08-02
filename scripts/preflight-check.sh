#!/usr/bin/env bash
# preflight-check.sh — deploy ÖNCESİ çalışır, canlı bağlantı GEREKTİRMEZ.
# Herhangi bir adım başarısızsa exit 1. Tüm adımlar OK olmadan deploy etme.
#
# Kullanım: bash scripts/preflight-check.sh   (repo kökünden)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY=""
for candidate in python python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "1" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done

FAIL_COUNT=0
step() {
  # step "isim" <komut...>
  local name="$1"; shift
  printf "%-55s" "[$name]"
  if "$@" >/tmp/preflight_step.log 2>&1; then
    echo "OK"
  else
    echo "FAIL"
    echo "  --- çıktı ---"
    sed 's/^/  /' /tmp/preflight_step.log | tail -30
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "=== preflight-check.sh — $(date) ==="
echo

# ── 1. Backend: constants senkron + python import ──────────────────────────
step "backend: generate_content_constants.py --check" \
  "$PY" backend/scripts/generate_content_constants.py --check

step "backend: python import (app.main)" \
  bash -c 'cd "'"$ROOT"'/backend" && SUPABASE_URL=https://preflight.invalid SUPABASE_SERVICE_ROLE_KEY=eyJpreflight.invalid.stub OPENAI_API_KEY=preflight-stub '"$PY"' -c "
from unittest.mock import patch, MagicMock
with patch(\"supabase.create_client\", return_value=MagicMock()):
    from app.main import app
    assert len(app.routes) > 0
print(\"routes:\", len(app.routes))
"'

step "backend: compileall" \
  bash -c 'cd "'"$ROOT"'/backend" && "'"$PY"'" -m compileall -q app'

# ── 2. Remotion: tsc + build + compositions.json ────────────────────────────
step "remotion: tsc --noEmit (server)" \
  bash -c 'cd "'"$ROOT"'/remotion" && npx tsc --noEmit -p tsconfig.server.json'

step "remotion: npm run build" \
  bash -c 'cd "'"$ROOT"'/remotion" && npm run build'

step "remotion: public/compositions.json var mı" \
  test -f "$ROOT/remotion/public/compositions.json"

step "remotion: sync-content-types.ts --check" \
  bash -c 'cd "'"$ROOT"'/remotion" && npx tsx scripts/sync-content-types.ts --check'

# ── 3. Docker build context simülasyonu (backend) ──────────────────────────
# Railway Root Directory=backend/ — repo kökündeki shared/, assets/, remotion/
# COPY . . ile İMAJA GİRMEZ. generated_constants.py gibi vendorlanmış
# dosyaların backend/ İÇİNDE olduğunu doğrula.
step "docker-context: generated_constants.py backend/ içinde" \
  test -f "$ROOT/backend/app/core/generated_constants.py"

step "docker-context: backend/ tar listesinde shared/ YOK (izole test)" \
  bash -c '
    cnt=$(tar -cf - -C "'"$ROOT"'/backend" --exclude=.git --exclude=__pycache__ . 2>/dev/null | tar -tf - | grep -c "^\./shared" || true)
    [ "$cnt" = "0" ]
  '

# ── 4. Yasak desen taramaları ────────────────────────────────────────────────
# 4a. Modül seviyesinde (import anında) dosya sistemi erişimi yasak —
#     bu sınıf hata üç kez sistemi çökertti (Remotion bridge, sync-content-types
#     prebuild, Python content_constants.py). Path(__file__) İÇİNDE fonksiyon
#     kullanımı (lazy, .exists() ile korunan) serbest — yalnızca gerçek
#     İMPORT-TIME OKUMA riski taşıyanlar yasak.
#     backend/scripts/ hariç: bu dosyalar app.main tarafından import edilmez,
#     Railway'in yüklediği canlı serviste hiç çalışmaz — bu riskin kapsamı dışı.
#     asset_validator.py / visual_library.py: manuel incelendi (bkz. postmortem
#     — lazy _load_manifest()/.exists() guard'lı, import anında dosya OKUMUYOR,
#     yalnızca Path NESNESİ kuruyor). assets/ ve remotion/public/ de backend/
#     context'i dışında olduğu için bu iki dosyanın FONKSİYONEL etkisi zaten
#     bilinen bir kısıtlama (P6 görsel sistem kapsamında, bu preflight'ın konusu
#     değil) — burada yalnızca YENİ bir eager-read'in sızmadığını doğruluyoruz.
step "yasak-desen: modül seviyesi dosya erişimi (backend/app/)" \
  bash -c '
    hits=$(git grep --untracked -n "^[A-Z_]*.*=.*get_constant\|^.*= *open(\|^.*Path(__file__)" -- backend/app/ 2>/dev/null \
      | grep -v "backend/app/modules/content/asset_validator.py:.*_REMOTION_PUBLIC" \
      | grep -v "backend/app/modules/content/visual_library.py:.*_MANIFEST_PATH" \
      | grep -v "backend/app/modules/content/visual_library.py:.*_ASSET_REGISTRY_PATH")
    if [ -n "$hits" ]; then echo "$hits"; exit 1; fi
    exit 0
  '

# 4b. render_cost_usd kolonu canlıda yok (bkz. postmortem) — bu ada gerçek
#     DB update olarak yazan kod olmamalı (log/yorum satırları serbest).
step "yasak-desen: render_cost_usd kolonuna yazma" \
  bash -c '
    hits=$(git grep --untracked -n "\"render_cost_usd\"\s*:" -- backend/app remotion/src 2>/dev/null)
    if [ -n "$hits" ]; then echo "$hits"; exit 1; fi
    exit 0
  '

# 4c. Sessiz TTS/duration fallback deseni: "except ... return True, 0.0" gibi
#     satırlar zaten loglu (kabul edilir) — burada yalnızca yeni tip bir
#     sessiz varsayılan sızıntısını yakalamak için DEFAULT_DURATION_SECONDS
#     benzeri isimlerin composition dosyalarına geri girmediğini doğrula.
step "yasak-desen: DEFAULT_DURATION_SECONDS geri gelmemiş (EducationalReel120)" \
  bash -c '! grep -q "DEFAULT_DURATION_SECONDS" "'"$ROOT"'/remotion/src/compositions/EducationalReel120.tsx"'

echo
if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "=== SONUÇ: $FAIL_COUNT adım FAIL — deploy ETME ==="
  exit 1
fi
echo "=== SONUÇ: tüm adımlar OK ==="
exit 0
