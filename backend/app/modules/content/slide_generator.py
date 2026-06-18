from PIL import Image, ImageDraw, ImageFont
import os
import uuid

_OUTPUT_DIR = "/tmp/slides"

# Adım Müşavir marka renkleri
_WHITE     = (255, 255, 255)
_BG        = (250, 248, 245)
_BG_DARK   = (18,  17,  15)
_ORANGE    = (217, 119,   6)
_ORANGE_LT = (254, 243, 199)
_ORANGE_DK = (180,  98,   4)
_DARK      = (28,  25,  23)
_GRAY      = (107, 114, 128)
_GRAY_LT   = (209, 213, 219)
_SURFACE   = (40,  37,  34)
_GREEN     = (22, 163,  74)
_RED       = (220,  38,  38)
_BLUE      = (37, 99, 235)
_SEPARATOR = (229, 221, 210)
_TEAL      = (15, 118, 110)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: continue
    return ImageFont.load_default()


def _font_reg(size: int) -> ImageFont.FreeTypeFont:
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: continue
    return ImageFont.load_default()


def _wrap(text: str, max_chars: int) -> list[str]:
    if not text:
        return []
    words = text.split()
    lines, cur = [], ""
    for word in words:
        if len(cur) + len(word) + 1 <= max_chars:
            cur += (" " if cur else "") + word
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines


def _save(img: Image.Image) -> str:
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path


def _draw_rounded_rect(d: ImageDraw.ImageDraw, xy: tuple, radius: int, fill: tuple):
    x0, y0, x1, y1 = xy
    d.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    d.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    d.ellipse([x0, y0, x0 + 2*radius, y0 + 2*radius], fill=fill)
    d.ellipse([x1 - 2*radius, y0, x1, y0 + 2*radius], fill=fill)
    d.ellipse([x0, y1 - 2*radius, x0 + 2*radius, y1], fill=fill)
    d.ellipse([x1 - 2*radius, y1 - 2*radius, x1, y1], fill=fill)


# ─────────────────────────────────────────────────────────────
# 16:9 — Uzun video slaytı
# ─────────────────────────────────────────────────────────────

def create_slide(
    section_title: str,
    content: str,
    section_num: int,
    total_sections: int,
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG)
    d   = ImageDraw.Draw(img)

    # ── Üst header bar
    d.rectangle([(0, 0), (W, 88)], fill=_DARK)
    d.text((44, 20), channel, font=_font(38), fill=_ORANGE)
    pct = f"{section_num} / {total_sections}"
    bb  = d.textbbox((0, 0), pct, font=_font_reg(28))
    d.text((W - (bb[2]-bb[0]) - 40, 26), pct, font=_font_reg(28), fill=_GRAY)

    # ── Sol turuncu aksan şeridi
    d.rectangle([(0, 88), (10, H - 16)], fill=_ORANGE)

    # ── Bölüm başlık alanı
    y_title = 120
    if section_title:
        d.text((50, y_title), section_title, font=_font(68), fill=_DARK)
        bb2 = d.textbbox((50, y_title), section_title, font=_font(68))
        line_y = bb2[3] + 14
        d.rectangle([(50, line_y), (min(bb2[2] + 24, W - 50), line_y + 6)], fill=_ORANGE)
        y_content = line_y + 48
    else:
        y_content = y_title + 20

    # ── İçerik — madde işaretli
    wrapped = _wrap(content, 65)
    for line in wrapped[:12]:
        prefix = "▸  " if not line.startswith("▸") else ""
        d.text((50, y_content), prefix + line, font=_font_reg(44), fill=_DARK)
        y_content += 64

    # ── Alt ilerleme çubuğu
    d.rectangle([(0, H - 16), (W, H)], fill=_SEPARATOR)
    prog_w = int(W * section_num / max(total_sections, 1))
    d.rectangle([(0, H - 16), (prog_w, H)], fill=_ORANGE)

    return _save(img)


def create_intro_slide(title: str, subtitle: str = "", channel: str = "ADIM MÜŞAVİR") -> str:
    """16:9 — açılış slaytı, koyu arka plan + büyük başlık"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG_DARK)
    d   = ImageDraw.Draw(img)

    # Sol turuncu bant
    d.rectangle([(0, 0), (16, H)], fill=_ORANGE)

    # Kanal adı (küçük, üstte)
    d.text((60, 50), channel, font=_font(36), fill=_ORANGE)

    # Merkez başlık
    title_lines = _wrap(title, 36)
    total_h = len(title_lines) * 100 + (len(_wrap(subtitle, 50)) * 64 if subtitle else 0) + 40
    y = (H - total_h) // 2

    for line in title_lines:
        bb = d.textbbox((0, 0), line, font=_font(88))
        pw = bb[2] - bb[0]
        d.text(((W - pw) // 2, y), line, font=_font(88), fill=_WHITE)
        y += 106

    # Turuncu çizgi ayırıcı
    d.rectangle([(W//2 - 200, y + 16), (W//2 + 200, y + 22)], fill=_ORANGE)
    y += 50

    # Alt başlık
    for line in _wrap(subtitle, 50)[:3]:
        bb = d.textbbox((0, 0), line, font=_font_reg(52))
        pw = bb[2] - bb[0]
        d.text(((W - pw) // 2, y), line, font=_font_reg(52), fill=_GRAY_LT)
        y += 70

    # Alt bilgi bar
    d.rectangle([(0, H - 72), (W, H)], fill=_SURFACE)
    cta = "adimmusavir.com  •  Mali Müşavirlik & SGS Academy"
    bb = d.textbbox((0, 0), cta, font=_font_reg(28))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, H - 52), cta, font=_font_reg(28), fill=_GRAY)

    return _save(img)


def create_question_slide(question_text: str, topic: str, channel: str = "ADIM MÜŞAVİR") -> str:
    """16:9 — soru çözüm: soru ekranı, sarı arka plan aksan"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG)
    d   = ImageDraw.Draw(img)

    # Üst header
    d.rectangle([(0, 0), (W, 88)], fill=_DARK)
    d.text((44, 20), channel, font=_font(36), fill=_ORANGE)
    d.text((W - 420, 20), "SORU ÇÖZÜMLERİ", font=_font(30), fill=_GRAY)

    # Konu etiketi
    d.text((44, 114), f"Konu: {topic}", font=_font_reg(36), fill=_GRAY)

    # Soru kutusu
    box_y = 160
    _draw_rounded_rect(d, (44, box_y, W - 44, box_y + 420), 20, _ORANGE_LT)
    d.rectangle([(44, box_y), (56, box_y + 420)], fill=_ORANGE)
    d.text((80, box_y + 24), "SORU", font=_font(38), fill=_ORANGE)

    q_y = box_y + 80
    for line in _wrap(question_text, 72)[:7]:
        d.text((80, q_y), line, font=_font_reg(44), fill=_DARK)
        q_y += 60

    # Alt bar
    d.rectangle([(0, H - 72), (W, H)], fill=_SURFACE)
    cta = "adimmusavir.com  •  SMMM / YMM Sınav Hazırlığı"
    bb = d.textbbox((0, 0), cta, font=_font_reg(28))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, H - 52), cta, font=_font_reg(28), fill=_GRAY)

    return _save(img)


def create_answer_slide(
    explanation: str,
    correct_answer: str,
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """16:9 — soru çözüm: cevap + açıklama ekranı"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG)
    d   = ImageDraw.Draw(img)

    d.rectangle([(0, 0), (W, 88)], fill=_DARK)
    d.text((44, 20), channel, font=_font(36), fill=_ORANGE)
    d.text((W - 340, 20), "ÇÖZÜM", font=_font(30), fill=_GREEN)

    # Doğru cevap kutusu
    _draw_rounded_rect(d, (44, 106, W//2 - 24, 230), 16, (220, 252, 231))
    d.text((70, 124), "✓  DOĞRU CEVAP:", font=_font(36), fill=_GREEN)
    d.text((70, 172), correct_answer[:80], font=_font(40), fill=_DARK)

    # Açıklama
    y = 264
    d.text((44, y), "Neden?", font=_font(44), fill=_DARK)
    line_y = y + 58
    d.rectangle([(44, line_y), (180, line_y + 6)], fill=_ORANGE)
    y = line_y + 40

    for line in _wrap(explanation, 68)[:10]:
        d.text((44, y), line, font=_font_reg(44), fill=_DARK)
        y += 60

    d.rectangle([(0, H - 72), (W, H)], fill=_SURFACE)
    cta = "adimmusavir.com  •  Daha fazla soru çözümü için takip edin"
    bb = d.textbbox((0, 0), cta, font=_font_reg(28))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, H - 52), cta, font=_font_reg(28), fill=_GRAY)

    return _save(img)


def create_summary_slide(
    title: str,
    summary_rows: list[dict],
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """16:9 — özet tablo slaytı"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG)
    d   = ImageDraw.Draw(img)

    d.rectangle([(0, 0), (W, 88)], fill=_DARK)
    d.text((44, 20), channel, font=_font(36), fill=_ORANGE)
    d.text((W - 200, 20), "ÖZET", font=_font(30), fill=_ORANGE)

    d.text((44, 112), title, font=_font(58), fill=_DARK)
    d.rectangle([(44, 182), (440, 188)], fill=_ORANGE)

    row_h, y = 100, 210
    for i, row in enumerate(summary_rows[:7]):
        bg = _ORANGE_LT if i % 2 == 0 else _WHITE
        d.rectangle([(44, y), (W - 44, y + row_h)], fill=bg)
        label = str(row.get("label", ""))
        value = str(row.get("value", ""))
        d.text((70, y + 22), label, font=_font(38), fill=_ORANGE_DK)
        d.text((500, y + 22), value, font=_font_reg(38), fill=_DARK)
        y += row_h + 6

    d.rectangle([(0, H - 72), (W, H)], fill=_SURFACE)
    cta = "adimmusavir.com  •  Mali Müşavirlik & SMMM Sınav Hazırlığı"
    bb = d.textbbox((0, 0), cta, font=_font_reg(28))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, H - 52), cta, font=_font_reg(28), fill=_GRAY)

    return _save(img)


def create_cta_slide(channel: str = "ADIM MÜŞAVİR") -> str:
    """16:9 — final CTA slaytı"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _DARK)
    d   = ImageDraw.Draw(img)

    d.rectangle([(0, 0), (16, H)], fill=_ORANGE)
    d.rectangle([(0, H//2 - 4), (W, H//2 + 4)], fill=_SURFACE)

    d.text((60, 60), channel, font=_font(44), fill=_ORANGE)

    lines = ["Mali Müşavirlik, SGS Academy,", "Muhasebe & Vergi Danışmanlığı"]
    y = H // 2 - 180
    for line in lines:
        bb = d.textbbox((0, 0), line, font=_font(72))
        pw = bb[2] - bb[0]
        d.text(((W - pw) // 2, y), line, font=_font(72), fill=_WHITE)
        y += 96

    d.rectangle([(W//2 - 300, y + 20), (W//2 + 300, y + 26)], fill=_ORANGE)
    y += 64

    url = "www.adimmusavir.com"
    bb = d.textbbox((0, 0), url, font=_font(64))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, y), url, font=_font(64), fill=_ORANGE)
    y += 88

    subs = "Beğen  •  Yorum Yap  •  Abone Ol  •  Kaydet"
    bb = d.textbbox((0, 0), subs, font=_font_reg(40))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, y), subs, font=_font_reg(40), fill=_GRAY_LT)

    return _save(img)


# ─────────────────────────────────────────────────────────────
# 9:16 — Shorts / Reels
# ─────────────────────────────────────────────────────────────

def create_shorts_slide(
    title: str,
    content: str,
    hook: str = "",
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), _BG_DARK)
    d   = ImageDraw.Draw(img)

    # Arka plan gradient efekti (basit dikdörtgenlerle)
    for i in range(4):
        shade = tuple(min(255, c + i * 8) for c in _SURFACE)
        d.rectangle([(0, i * H//4), (W, (i+1) * H//4)], fill=shade)

    # Sol aksan
    d.rectangle([(0, 0), (12, H)], fill=_ORANGE)

    # Üst kanal bilgisi
    d.text((32, 44), channel, font=_font(36), fill=_ORANGE)
    d.rectangle([(32, 96), (W - 32, 100)], fill=_SURFACE)

    # HOOK alanı — büyük, dikkat çekici
    y = 130
    if hook:
        for line in _wrap(hook, 22):
            bb = d.textbbox((0, 0), line, font=_font(72))
            pw = bb[2] - bb[0]
            d.text(((W - pw) // 2, y), line, font=_font(72), fill=_WHITE)
            y += 94
        y += 16

    # Turuncu ayırıcı
    d.rectangle([(80, y), (W - 80, y + 8)], fill=_ORANGE)
    y += 36

    # Başlık
    if title:
        for line in _wrap(title, 24):
            bb = d.textbbox((0, 0), line, font=_font(54))
            pw = bb[2] - bb[0]
            d.text(((W - pw) // 2, y), line, font=_font(54), fill=_ORANGE)
            y += 72
        y += 12

    # İçerik maddeler
    if content:
        for i, line in enumerate(_wrap(content, 32)[:10]):
            bullet_color = _ORANGE if i == 0 else _WHITE
            d.text((60, y), f"▸", font=_font(40), fill=bullet_color)
            d.text((110, y), line, font=_font_reg(42), fill=_WHITE if i > 0 else _ORANGE_LT)
            y += 62

    # Alt CTA bandı
    d.rectangle([(0, H - 160), (W, H)], fill=_ORANGE)
    cta_lines = ["Takip Et  •  Beğen  •  Kaydet", "adimmusavir.com"]
    cy = H - 148
    for line in cta_lines:
        bb = d.textbbox((0, 0), line, font=_font(34))
        pw = bb[2] - bb[0]
        d.text(((W - pw) // 2, cy), line, font=_font(34), fill=_WHITE)
        cy += 50

    return _save(img)


def create_shorts_cta_slide(channel: str = "ADIM MÜŞAVİR") -> str:
    """9:16 — Shorts final CTA slaytı"""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), _BG_DARK)
    d   = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (12, H)], fill=_ORANGE)

    y = H // 2 - 260
    d.text((60, 60), channel, font=_font(38), fill=_ORANGE)

    for line in ["Daha fazlası için", "takip etmeyi", "unutmayın!"]:
        bb = d.textbbox((0, 0), line, font=_font(80))
        pw = bb[2] - bb[0]
        d.text(((W - pw) // 2, y), line, font=_font(80), fill=_WHITE)
        y += 104

    d.rectangle([(W//2 - 200, y + 20), (W//2 + 200, y + 26)], fill=_ORANGE)
    y += 66

    url = "adimmusavir.com"
    bb = d.textbbox((0, 0), url, font=_font(64))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, y), url, font=_font(64), fill=_ORANGE)

    d.rectangle([(0, H - 120), (W, H)], fill=_ORANGE)
    subs = "Beğen  •  Abone Ol  •  Kaydet"
    bb = d.textbbox((0, 0), subs, font=_font(36))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, H - 88), subs, font=_font(36), fill=_WHITE)

    return _save(img)


# ─────────────────────────────────────────────────────────────
# 1:1 — Instagram Post
# ─────────────────────────────────────────────────────────────

def create_post_image(
    question: str,
    answer_points: list[str],
    image_text: str = "",
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), _BG)
    d   = ImageDraw.Draw(img)

    # Üst header
    d.rectangle([(0, 0), (W, 108)], fill=_DARK)
    d.text((44, 28), channel, font=_font(42), fill=_ORANGE)

    # Başlık
    y = 130
    for line in _wrap(question, 28)[:2]:
        bb = d.textbbox((0, 0), line, font=_font(54))
        pw = bb[2] - bb[0]
        d.text(((W - pw) // 2, y), line, font=_font(54), fill=_DARK)
        y += 68

    d.rectangle([(60, y + 12), (W - 60, y + 18)], fill=_ORANGE)
    y += 48

    # Tablo satırları
    row_h = 96
    for i, point in enumerate(answer_points[:7]):
        bg = _ORANGE if i == 0 else (_ORANGE_LT if i % 2 == 0 else _WHITE)
        tc = _WHITE if i == 0 else _DARK
        _draw_rounded_rect(d, (60, y, W - 60, y + row_h), 10, bg)
        d.text((90, y + 28), point[:54], font=_font_reg(36), fill=tc)
        y += row_h + 6

    # Alt bar
    d.rectangle([(0, H - 88), (W, H)], fill=_DARK)
    footer = image_text or "adimmusavir.com  |  Mali Müşavirlik"
    bb = d.textbbox((0, 0), footer, font=_font_reg(30))
    pw = bb[2] - bb[0]
    d.text(((W - pw) // 2, H - 62), footer, font=_font_reg(30), fill=_ORANGE)

    return _save(img)
