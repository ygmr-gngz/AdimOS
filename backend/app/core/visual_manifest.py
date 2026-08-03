"""
Görsel kütüphane sabitleri — stil sözleşmesi, tema kataloğu, kalite kapıları.

Bu modül backend/ içinde git'e commitlidir (Railway Root Directory = backend/
build context'inde her zaman mevcut) — repo kökündeki assets/manifest.json'a
RUNTIME'DA bağımlı DEĞİLDİR. Üretilen görsellerin kendisi Supabase Storage'da
tutulur (bkz. app/modules/content/visual_library.py) çünkü render Remotion
Lambda üzerinde çalışır ve backend'in local diskine hiçbir zaman erişemez —
gerçek bir HTTP URL şart.

Tema/stil değiştiğinde bu dosya doğrudan düzenlenir (ayrı bir sync script
gerekmiyor — bu veri sadece backend tarafından tüketilir, Remotion tarafı
zaten çözülmüş image_url ile çalışır).
"""
from __future__ import annotations

# ── Model / maliyet sabitleri ──────────────────────────────────────
# Kaynak: OpenAI resmi fiyatlandırma sayfası (developers.openai.com/api/docs/pricing
# ve guides/image-generation), doğrulama tarihi: 2026-08-02.
# gpt-image-1 KULLANILMIYOR — 2026-10-23'te kullanımdan kalkıyor.
# gpt-image-1-mini de 2026-12-01'de kalkıyor (gpt-image-2 önerilen halef) — yalnızca
# geliştirme/test katmanında ucuz olduğu için kullanılıyor, üretimde gpt-image-2.

DEV_MODEL     = "gpt-image-1-mini"
DEV_QUALITY   = "low"
PROD_MODEL    = "gpt-image-2"
PROD_QUALITY  = "medium"

OUTPUT_SIZE = "1024x1536"   # portre — 9:16 hedefine en yakın desteklenen oran

# (model, quality) -> USD/görsel, size=1024x1536 için
IMAGE_COST_PER_UNIT: dict[tuple[str, str], float] = {
    ("gpt-image-1-mini", "low"):    0.006,
    ("gpt-image-1-mini", "medium"): 0.015,
    ("gpt-image-1-mini", "high"):   0.052,
    ("gpt-image-2", "low"):         0.005,
    ("gpt-image-2", "medium"):      0.041,
    ("gpt-image-2", "high"):        0.165,
}


def cost_per_image(model: str, quality: str) -> float:
    key = (model, quality)
    if key not in IMAGE_COST_PER_UNIT:
        raise ValueError(f"Bilinmeyen model/kalite kombinasyonu: {key}")
    return IMAGE_COST_PER_UNIT[key]


# ── Stil sözleşmesi — sabit, serbest metin prompt YOK ──────────────

STYLE_CONTRACT: dict = {
    "positive": (
        "Photorealistic editorial photograph, natural window light, warm neutral "
        "tones, shallow depth of field, calm and hopeful mood, muted color palette "
        "with deep navy and warm beige, clean uncluttered composition, vertical "
        "2:3 framing with empty space in the upper third for text overlay, no "
        "text anywhere in the image, no logos, no brand marks, no watermarks."
    ),
    "negative": (
        "Avoid: visible text, letters, numbers, signage, book titles, screen "
        "content, logos, watermarks, close-up hands with visible fingers, direct "
        "eye contact with camera, recognizable faces, exaggerated expressions, "
        "neon colors, heavy vignette, tilted horizon."
    ),
    "output_size": OUTPUT_SIZE,
    "target_size": "1080x1920",
    "overlay_navy_opacity_range": [0.25, 0.40],
    "saturation_adjustment": -8,
}


# ── Tema kataloğu — sabit enum, serbest tema YOK ───────────────────

THEMES: dict[str, dict] = {
    "calisma_masasi": {
        "label": "Çalışma masası",
        "content_tracks": ["ogrenci"],
        "target_variants": 15,
        "tags": ["masa", "defter", "sabah", "calisma", "laptop"],
        "subject_prompt": (
            "A tidy wooden study desk with an open notebook, a pen, a glass of "
            "water and a closed laptop, seen from a slightly high angle. No "
            "person visible."
        ),
    },
    "ogrenci_calisir": {
        "label": "Öğrenci çalışıyor",
        "content_tracks": ["ogrenci"],
        "target_variants": 15,
        "tags": ["ogrenci", "arkadan", "sabah", "pencere", "kitap"],
        "subject_prompt": (
            "A young adult seen from behind, sitting at a desk studying, soft "
            "morning light from a window on the left. Face not visible. Vary "
            "the clothing color and style across generations — not always dark "
            "navy — to avoid visual monotony across variants."
        ),
    },
    "kitap_defter": {
        "label": "Kitap ve defter",
        "content_tracks": ["ogrenci"],
        "target_variants": 15,
        "tags": ["kitap", "defter", "cay", "masa", "sessiz"],
        "subject_prompt": (
            "A stack of closed notebooks and a cup of tea on a wooden surface, "
            "warm side light. No readable text on covers."
        ),
    },
    "takvim_plan": {
        "label": "Takvim ve plan",
        "content_tracks": ["ogrenci"],
        "target_variants": 15,
        "tags": ["takvim", "plan", "kalem", "organizasyon"],
        "subject_prompt": (
            "A monthly paper planner on a desk with a pen resting on it, soft "
            "daylight, shallow depth of field. No readable writing."
        ),
    },
    "sabah_isik": {
        "label": "Sabah ışığı",
        "content_tracks": ["ogrenci"],
        "target_variants": 15,
        "tags": ["sabah", "isik", "bos", "huzur", "pencere"],
        "subject_prompt": (
            "An empty study corner at sunrise, warm light falling across a "
            "wooden desk and an empty chair, calm atmosphere."
        ),
    },
    "ilerleme": {
        "label": "İlerleme / merdiven",
        "content_tracks": ["ogrenci"],
        "target_variants": 15,
        "tags": ["ilerleme", "merdiven", "yukari", "hedef", "motivasyon"],
        "subject_prompt": (
            "A staircase in soft daylight seen from below, clean minimal "
            "architecture, sense of upward progress."
        ),
    },
    "mola": {
        "label": "Mola anı",
        "content_tracks": ["ogrenci"],
        "target_variants": 12,
        "tags": ["mola", "cay", "pencere", "dinlenme", "bitki"],
        "subject_prompt": (
            "A window sill with a cup of tea and a plant, blurred city light "
            "outside, quiet resting mood."
        ),
    },
    "yeniden_baslama": {
        "label": "Yeniden başlama",
        "content_tracks": ["ogrenci"],
        "target_variants": 12,
        "tags": ["bos", "defter", "kalem", "sabah", "taze"],
        "subject_prompt": (
            "An open empty notebook page with a pen placed on it, morning "
            "light, clean and inviting, no writing on the page."
        ),
    },
    "ofis_muhasebe": {
        "label": "Ofis / muhasebe",
        "content_tracks": ["danisan"],
        "target_variants": 12,
        "tags": ["ofis", "hesap", "klasor", "profesyonel", "laptop"],
        "subject_prompt": (
            "A tidy desk with a calculator, a folder and a laptop, professional "
            "office light. No visible screen content or text."
        ),
    },
    "esnaf_isletme": {
        "label": "Esnaf / işletme",
        "content_tracks": ["danisan"],
        "target_variants": 12,
        "tags": ["dukkan", "isletme", "tezgah", "sicak", "isletme"],
        "subject_prompt": (
            "A small shop counter interior at daytime, warm light, no signage, "
            "no visible text, no people."
        ),
    },
}


# ── Kalite kapıları — §6.5.5 (5 kontrol) ───────────────────────────

QUALITY_GATES = {
    "ocr_max_readable_chars": 3,
    # 100 -> 35: pilot #1/#2, tüm kare ölçümü ile 3 kabul edilmiş gerçek görsel
    # 52.8-64.6 arasında ölçüldü (STYLE_CONTRACT'ın "shallow depth of field"
    # istemi + koyu düz dokulu özneler doğaları gereği düşük Laplacian üretiyor,
    # bölge seçimiyle çözülemedi — bkz. backend/scripts/generate_assets.py
    # check_blur() docstring). 35 bu üçünün en düşüğünün belirgin altında.
    # TAM DOĞRULANMADI — reddedilen görsellerin ölçümüyle çapraz kontrol
    # pilot #2'nin _rejected_previews/ verisi kazayla silindiği için yapılamadı;
    # pilot #3'ün redleriyle doğrulanacak.
    "blur_laplacian_min": 35,
    "brightness_min": 40,
    "brightness_max": 215,
    "upper_third_flatness_min": 0.6,   # üst üçte bir metin için yeterince "boş" olmalı
    "max_regenerate_attempts": 2,
    "text_overlay_contrast_min": 4.5,
}


# ── Maliyet tavanları (video başına, prod kalite) ──────────────────

COST_CAPS = {
    "motivasyon":  {"image_usd": 0.60, "note": "7 gorsel x medium + %50 pay"},
    "reels_short": {"image_usd": 0.15, "note": "kart agirlikli, en fazla 2 gorsel"},
}


def build_prompt(theme_key: str) -> str:
    cfg = THEMES.get(theme_key)
    if not cfg:
        raise ValueError(f"Bilinmeyen tema: {theme_key}")
    return f"{cfg['subject_prompt']}\n\n{STYLE_CONTRACT['positive']}\n\n{STYLE_CONTRACT['negative']}"
