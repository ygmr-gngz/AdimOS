from PIL import Image, ImageDraw, ImageFont
import os
import uuid

_OUTPUT_DIR = "/tmp/slides"

# Adım Müşavir marka renkleri
_WHITE      = (255, 255, 255)
_BG         = (250, 248, 245)       # krem beyaz zemin
_ORANGE     = (217, 119, 6)         # turuncu/altın — #D97706
_ORANGE_LT  = (254, 243, 199)       # açık turuncu bg
_DARK       = (30,  27,  24)        # neredeyse siyah
_GRAY       = (107, 114, 128)       # gri metin
_SEPARATOR  = (229, 221, 210)       # ince çizgi rengi


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _font_reg(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        if len(cur) + len(word) + 1 <= max_chars:
            cur += (" " if cur else "") + word
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def create_slide(
    section_title: str,
    content: str,
    section_num: int,
    total_sections: int,
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """16:9 yatay — eğitim videosu, açık profesyonel tema"""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)

    # Sol turuncu şerit
    d.rectangle([(0, 0), (14, H)], fill=_ORANGE)

    # Üst header
    d.rectangle([(0, 0), (W, 90)], fill=_DARK)
    d.text((40, 22), channel, font=_font(36), fill=_ORANGE)
    sec_txt = f"{section_num} / {total_sections}"
    bbox = d.textbbox((0, 0), sec_txt, font=_font_reg(28))
    d.text((W - bbox[2] - bbox[0] - 40, 28), sec_txt, font=_font_reg(28), fill=_GRAY)

    # Bölüm başlığı
    d.text((60, 120), section_title, font=_font(64), fill=_DARK)

    # Altı çizgi (turuncu)
    title_bbox = d.textbbox((60, 120), section_title, font=_font(64))
    line_y = title_bbox[3] + 16
    d.rectangle([(60, line_y), (min(title_bbox[2] + 20, W - 60), line_y + 5)], fill=_ORANGE)

    # İçerik
    y = line_y + 42
    for line in _wrap(content, 62)[:10]:
        d.text((60, y), line, font=_font_reg(42), fill=_DARK)
        y += 62

    # Alt ilerleme çubuğu
    d.rectangle([(0, H - 12), (W, H)], fill=_SEPARATOR)
    prog_w = int(W * section_num / total_sections)
    d.rectangle([(0, H - 12), (prog_w, H)], fill=_ORANGE)

    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path


def create_shorts_slide(
    title: str,
    content: str,
    hook: str = "",
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """9:16 dikey — Shorts / Reels, turuncu gradient"""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)

    # Üst turuncu band (yüksek)
    d.rectangle([(0, 0), (W, 520)], fill=_DARK)

    # Sol dikey turuncu şerit
    d.rectangle([(0, 0), (10, H)], fill=_ORANGE)

    # Kanal adı
    d.text((40, 40), channel, font=_font(38), fill=_ORANGE)

    # Hook — büyük, dikkat çekici
    y = 120
    if hook:
        for part in _wrap(hook, 24):
            bbox = d.textbbox((0, 0), part, font=_font(66))
            pw = bbox[2] - bbox[0]
            d.text(((W - pw) // 2, y), part, font=_font(66), fill=_WHITE)
            y += 86

    # Turuncu ayırıcı çizgi
    d.rectangle([(60, y + 20), (W - 60, y + 6)], fill=_ORANGE)
    y += 50

    # Başlık
    for part in _wrap(title, 26):
        bbox = d.textbbox((0, 0), part, font=_font(52))
        pw = bbox[2] - bbox[0]
        d.text(((W - pw) // 2, y), part, font=_font(52), fill=_ORANGE)
        y += 70

    y += 20

    # İçerik — koyu alanda
    for line in _wrap(content, 34)[:10]:
        d.text((60, y), f"▸  {line}", font=_font_reg(44), fill=_DARK)
        y += 66

    # Alt CTA bar
    d.rectangle([(0, H - 120), (W, H)], fill=_ORANGE)
    cta = "Takip et  •  Beğen  •  Kaydet"
    bbox = d.textbbox((0, 0), cta, font=_font(34))
    cw = bbox[2] - bbox[0]
    d.text(((W - cw) // 2, H - 82), cta, font=_font(34), fill=_WHITE)

    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path


def create_post_image(
    question: str,
    answer_points: list[str],
    image_text: str = "",
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """1080x1080 kare — Instagram post, turuncu tablo stili"""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)

    # Üst header
    d.rectangle([(0, 0), (W, 100)], fill=_DARK)
    d.text((40, 28), channel, font=_font(40), fill=_ORANGE)

    # Başlık (question → konu başlığı olarak kullan)
    y = 124
    for line in _wrap(question, 28)[:2]:
        bbox = d.textbbox((0, 0), line, font=_font(52))
        pw = bbox[2] - bbox[0]
        d.text(((W - pw) // 2, y), line, font=_font(52), fill=_DARK)
        y += 66

    # Turuncu çizgi
    d.rectangle([(60, y + 10), (W - 60, y + 6)], fill=_ORANGE)
    y += 36

    # Cevap maddeleri — tablo stili
    row_h = 88
    for i, point in enumerate(answer_points[:6]):
        row_bg = _ORANGE if i == 0 else (_ORANGE_LT if i % 2 == 0 else _WHITE)
        text_col = _WHITE if i == 0 else _DARK
        d.rectangle([(60, y), (W - 60, y + row_h)], fill=row_bg)
        d.text((90, y + 22), point, font=_font_reg(36), fill=text_col)
        y += row_h + 4

    # Alt bar
    d.rectangle([(0, H - 80), (W, H)], fill=_DARK)
    if image_text:
        bbox = d.textbbox((0, 0), image_text, font=_font_reg(30))
        fw = bbox[2] - bbox[0]
        d.text(((W - fw) // 2, H - 56), image_text, font=_font_reg(30), fill=_ORANGE)

    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path
