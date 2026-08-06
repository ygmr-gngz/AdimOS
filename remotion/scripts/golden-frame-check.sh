#!/usr/bin/env bash
# Golden frame testi — GERÇEK brand_settings.logo_url ile still render alır ve
# köşe logosunun opak/beyaz-kutu görünüp görünmediğini piksel düzeyinde ölçer.
#
# NEDEN BU SCRIPT VAR: 2026-08-04 postmortem — üretimde köşe logosu haftalarca
# beyaz kutu içinde render edildi (brand_settings.logo_url'deki Supabase dosyası
# JPEG kaynaklı, .convert('RGBA') sonrası alfa uçtan uca 255'te kalmış, hiç
# şeffaf değildi). Bu sırada yapılan TÜM manuel still-render testleri
# logo_url:null geçiyordu — bu, üretimin HİÇ kullanmadığı local staticFile
# fallback yolunu test ediyordu, gerçek bug'ı asla yakalayamadı çünkü o kod
# yolu hiç çalıştırılmamıştı. "Testin geçmesi" ile "üretimin çalışması" farklı
# şeylerdi ve fark edilmeden kaldı.
#
# KURAL: Bu script HER ZAMAN gerçek brand_settings'ten okur — asla null/mock
# logo_url ile test etmez. Bir sonraki kişi/oturum "hızlıca null ile test
# edeyim" derse, bu script'i çalıştırsın, bunu yeniden icat etmesin.
#
# Kullanım:
#   bash scripts/golden-frame-check.sh
set -euo pipefail
cd "$(dirname "$0")/.."

LOGO_URL=$(python -c "
import sys; sys.path.insert(0, '../backend')
from app.db.repositories.brand_repo import get_brand_settings
print(get_brand_settings().get('logo_url') or '')
")

if [ -z "$LOGO_URL" ]; then
  echo "[HATA] brand_settings.logo_url boş — gerçek logo olmadan golden frame testi anlamsız."
  echo "       (Panelden bir logo yükleyin, sonra tekrar deneyin.)"
  exit 1
fi

echo "[golden-frame] gerçek brand_settings.logo_url kullanılıyor: $LOGO_URL"

PROPS=$(cat <<EOF
{"storyboard":{"brand":{"logo_url":"$LOGO_URL","primary_color":"#0B2A4A"},"scenes":[{"id":1,"component":"MotivationHookScene","duration_seconds":10,"message":"Golden frame testi","imageUrl":"https://images.unsplash.com/photo-1517842645767-c639042777db?w=1080&h=1920&fit=crop","visual_source":"photo"}]}}
EOF
)

mkdir -p out
npx remotion still MotivationVideo out/golden-frame.png --frame=60 --props="$PROPS"

python -c "
from PIL import Image
import numpy as np
img = Image.open('out/golden-frame.png').convert('RGB')
w, h = img.size
region = np.array(img.crop((w-170, 10, w-10, 170)))
white_pct = ((region[:,:,0]>235)&(region[:,:,1]>235)&(region[:,:,2]>235)).mean()*100
print(f'[golden-frame] kose logo bolgesi beyaz piksel orani: %{white_pct:.1f}')
if white_pct > 5.0:
    print('[golden-frame] BASARISIZ -- logo opak/beyaz zeminli gorunuyor (GERCEK brand.logo_url ile test edildi)')
    raise SystemExit(1)
print('[golden-frame] GECTI')
"
