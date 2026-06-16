from PIL import Image, ImageDraw, ImageFont
import os
import uuid

_OUTPUT_DIR = "/tmp/slides"

# Renk paleti
_BG = (15, 23, 42)
_BAR = (30, 41, 59)
_ACCENT = (59, 130, 246)
_WHITE = (255, 255, 255)
_LIGHT = (226, 232, 240)
_YELLOW = (250, 204, 21)
_MUTED = (148, 163, 184)


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
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
    """16:9 yatay slayt — normal video için"""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)

    f_ch = _get_font(30)
    f_title = _get_font(62)
    f_body = _get_font(40)
    f_small = _get_font(26)

    # Üst bar
    d.rectangle([(0, 0), (W, 72)], fill=_BAR)
    d.text((44, 20), channel, font=f_ch, fill=_ACCENT)
    sec_txt = f"BÖLÜM {section_num} / {total_sections}"
    d.text((W - 260, 22), sec_txt, font=f_small, fill=_MUTED)

    # Accent çizgi
    d.rectangle([(44, 96), (W - 44, 100)], fill=_ACCENT)

    # Bölüm başlığı
    d.text((60, 120), section_title, font=f_title, fill=_WHITE)

    # İçerik
    lines = _wrap(content, 58)
    y = 230
    for line in lines[:9]:
        d.text((60, y), line, font=f_body, fill=_LIGHT)
        y += 64

    # Alt progress bar
    d.rectangle([(0, H - 48), (W, H)], fill=_BAR)
    prog_w = int(W * section_num / total_sections)
    d.rectangle([(0, H - 48), (prog_w, H)], fill=_ACCENT)

    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path


def create_shorts_slide(
    title: str,
    content: str,
    hook: str = "",
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """9:16 dikey slayt — Shorts / Reels için"""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)

    f_ch = _get_font(34)
    f_hook = _get_font(52)
    f_title = _get_font(56)
    f_body = _get_font(42)
    f_cta = _get_font(32)

    # Üst bar — kanal adı ortada
    d.rectangle([(0, 0), (W, 80)], fill=_BAR)
    bbox = d.textbbox((0, 0), channel, font=f_ch)
    cw = bbox[2] - bbox[0]
    d.text(((W - cw) / 2, 22), channel, font=f_ch, fill=_ACCENT)

    # Hook
    y = 140
    if hook:
        for part in _wrap(hook, 28):
            bbox = d.textbbox((0, 0), part, font=f_hook)
            pw = bbox[2] - bbox[0]
            d.text(((W - pw) / 2, y), part, font=f_hook, fill=_YELLOW)
            y += 68

    # Accent çizgi
    d.rectangle([(60, y + 20), (W - 60, y + 24)], fill=_ACCENT)
    y += 50

    # Başlık
    for part in _wrap(title, 24):
        bbox = d.textbbox((0, 0), part, font=f_title)
        pw = bbox[2] - bbox[0]
        d.text(((W - pw) / 2, y), part, font=f_title, fill=_WHITE)
        y += 70

    y += 20

    # İçerik
    for line in _wrap(content, 32)[:10]:
        bbox = d.textbbox((0, 0), line, font=f_body)
        pw = bbox[2] - bbox[0]
        d.text(((W - pw) / 2, y), line, font=f_body, fill=_LIGHT)
        y += 64

    # Alt CTA
    d.rectangle([(0, H - 110), (W, H)], fill=_BAR)
    cta = "👍 Beğen  💬 Yorum Yap  🔔 Abone Ol"
    bbox = d.textbbox((0, 0), cta, font=f_cta)
    cw = bbox[2] - bbox[0]
    d.text(((W - cw) / 2, H - 72), cta, font=f_cta, fill=_MUTED)

    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path


def create_post_image(
    question: str,
    answer_points: list[str],
    image_text: str = "",
    channel: str = "ADIM MÜŞAVİR",
) -> str:
    """1080x1080 kare görsel — Instagram post için"""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)

    f_ch = _get_font(32)
    f_q = _get_font(50)
    f_body = _get_font(38)
    f_footer = _get_font(28)

    # Üst bar
    d.rectangle([(0, 0), (W, 76)], fill=_BAR)
    bbox = d.textbbox((0, 0), channel, font=f_ch)
    cw = bbox[2] - bbox[0]
    d.text(((W - cw) / 2, 20), channel, font=f_ch, fill=_ACCENT)

    # Soru
    y = 110
    for line in _wrap(question, 32)[:3]:
        bbox = d.textbbox((0, 0), line, font=f_q)
        pw = bbox[2] - bbox[0]
        d.text(((W - pw) / 2, y), line, font=f_q, fill=_WHITE)
        y += 64

    # Accent çizgi
    d.rectangle([(60, y + 10), (W - 60, y + 14)], fill=_ACCENT)
    y += 40

    # Cevap maddeleri
    for point in answer_points[:5]:
        d.text((80, y), f"✓  {point}", font=f_body, fill=_LIGHT)
        y += 62

    # Alt bar
    d.rectangle([(0, H - 90), (W, H)], fill=_BAR)
    if image_text:
        bbox = d.textbbox((0, 0), image_text, font=f_footer)
        fw = bbox[2] - bbox[0]
        d.text(((W - fw) / 2, H - 58), image_text, font=f_footer, fill=_MUTED)

    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.png")
    img.save(path, "PNG")
    return path
