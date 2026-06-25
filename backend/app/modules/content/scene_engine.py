"""
Motion Graphics Engine v2 — Full-Screen Professional Educational Video.

Design system:
  - PAD=32 edge-to-edge, content fills canvas
  - No nested card-in-card. Accent bands replace cards.
  - Font scale: title=56-68, heading=44-48, body=30-34, label=22
  - Turkish labels only. Scene labels hardcoded in TR.

Scene types:
  intro, hook, definition, concept, content, comparison,
  example, question, option_analysis, answer, exam_tip,
  summary, cta, shorts
"""
import io as _io
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip

W, H, FPS = 1280, 720, 30
PAD = 32        # screen edge margin

# ── Brand palette ────────────────────────────────────────────
BG    = (14,  13,  12)
SURF  = (30,  28,  25)
SURF2 = (44,  40,  36)
SURF3 = (56,  51,  46)
OG    = (249, 115,  22)   # brand orange
OGDK  = (160,  70,   8)
GR    = ( 34, 197,  94)   # green (correct)
GRD   = ( 16, 100,  46)
RD    = (220,  38,  38)   # red (wrong)
RDD   = (100,  20,  20)
BL    = ( 59, 130, 246)   # blue
YL    = (234, 179,   8)   # yellow / tip
WH    = (248, 248, 248)   # near-white
LG    = (160, 155, 150)   # light gray
MG    = ( 95,  90,  85)   # mid gray
DG    = ( 52,  48,  44)   # dark gray

# ── Logo watermark ───────────────────────────────────────────
_WM_IMG: Image.Image | None = None
_WM_OPACITY: float = 0.07
_WM_POSITION: str = "center"
_WM_ENABLED: bool = False


def configure_watermark(
    logo_bytes: bytes | None,
    opacity: float = 0.07,
    position: str = "center",
    size: float = 0.30,
    enabled: bool = True,
) -> None:
    """Video üretiminden önce çağrılır. Tüm sahnelere otomatik filigran ekler."""
    global _WM_IMG, _WM_OPACITY, _WM_POSITION, _WM_ENABLED
    _WM_OPACITY = max(0.0, min(float(opacity), 1.0))
    _WM_POSITION = position
    _WM_ENABLED = enabled and logo_bytes is not None and len(logo_bytes) > 0
    if _WM_ENABLED:
        raw = Image.open(_io.BytesIO(logo_bytes)).convert("RGBA")
        target_w = max(1, int(W * float(size)))
        ratio = target_w / max(raw.width, 1)
        target_h = max(1, int(raw.height * ratio))
        _WM_IMG = raw.resize((target_w, target_h), Image.LANCZOS)
    else:
        _WM_IMG = None


def _apply_watermark(img: Image.Image) -> Image.Image:
    if _WM_IMG is None:
        return img
    wm = _WM_IMG.copy()
    r, g, b, a = wm.split()
    a = a.point(lambda x: int(x * _WM_OPACITY))
    wm = Image.merge("RGBA", (r, g, b, a))
    ww, wh = wm.size
    pos_map = {
        "center":       ((W - ww) // 2, (H - wh) // 2),
        "top-right":    (W - ww - PAD, PAD + 28),
        "top-left":     (PAD, PAD + 28),
        "bottom-right": (W - ww - PAD, H - wh - PAD),
        "bottom-left":  (PAD, H - wh - PAD),
    }
    px, py = pos_map.get(_WM_POSITION, pos_map["center"])
    result = img.copy()
    result.paste(wm, (px, py), wm)
    return result


# ── Pre-computed gradient background ────────────────────────
_GRAD_BG: Image.Image | None = None

def _get_bg() -> Image.Image:
    global _GRAD_BG
    if _GRAD_BG is None:
        bg = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(bg)
        for y in range(H):
            r = max(8, int(20 - 8 * (y / H)))
            g = max(8, int(18 - 6 * (y / H)))
            b = max(8, int(16 - 4 * (y / H)))
            d.line([(0, y), (W, y)], fill=(r, g, b))
        _GRAD_BG = bg
    return _GRAD_BG.copy()


# ── Easing ───────────────────────────────────────────────────
def _eo(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3      # cubic ease-out (more punch)

def _p(t: float, start: float, dur: float) -> float:
    return _eo(max(0.0, (t - start) / max(dur, 0.001)))

def _slide_offset(t: float, start: float, dur: float, dist: int = 28) -> int:
    return int(dist * (1 - _eo(max(0.0, (t - start) / max(dur, 0.001)))))


# ── Font cache ───────────────────────────────────────────────
_FC: dict = {}
_FONT_PATHS = [
    ("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",              True),
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",           False),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",          True),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",               False),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  True),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", False),
    ("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",                 True),
    ("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",                 False),
]

def _f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _FC:
        font = ImageFont.load_default()
        for path, is_bold in _FONT_PATHS:
            if is_bold == bold and os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size)
                    break
                except Exception:
                    pass
        _FC[key] = font
    return _FC[key]


# ── Text helpers ─────────────────────────────────────────────
def _tw(text: str, font) -> int:
    try:
        b = font.getbbox(str(text))
        return max(1, b[2] - b[0])
    except Exception:
        return max(1, len(str(text)) * 10)

def _th(font) -> int:
    try:
        b = font.getbbox("Ag")
        return max(1, b[3] - b[1])
    except Exception:
        return 20

def _cx(text: str, font) -> int:
    return max(PAD, (W - _tw(text, font)) // 2)

def _wrap(text: str, font, max_w: int) -> list[str]:
    text = str(text)
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if _tw(test, font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text[:80]]


# ── Draw primitives ──────────────────────────────────────────
def _txt(d, text: str, x: int, y: int, font, color, alpha: float):
    if alpha <= 0:
        return
    r, g, b = color
    d.text((x, y), str(text), font=font, fill=(r, g, b, int(255 * min(alpha, 1.0))))

def _box(d, xy, color, alpha: float = 1.0, radius: int = 0):
    if alpha <= 0:
        return
    r, g, b = color
    fill = (r, g, b, int(255 * min(alpha, 1.0)))
    try:
        if radius > 0:
            d.rounded_rectangle(xy, radius=radius, fill=fill)
        else:
            d.rectangle(xy, fill=fill)
    except (AttributeError, TypeError):
        d.rectangle(xy, fill=fill)

def _line(d, xy1, xy2, color, alpha: float = 1.0, width: int = 2):
    if alpha <= 0:
        return
    r, g, b = color
    d.line([xy1, xy2], fill=(r, g, b, int(255 * alpha)), width=width)

def _growing_line(d, x1: int, y: int, x2: int, progress: float,
                  color=OG, alpha: float = 0.8, width: int = 3):
    if progress <= 0:
        return
    end = x1 + int((x2 - x1) * progress)
    _line(d, (x1, y), (end, y), color, alpha, width)


# ── Frame boilerplate ────────────────────────────────────────
def _frame_start(t: float = 0.0):
    base = _get_bg()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # Full-width top accent strip (breathes)
    breathe = 0.55 + 0.12 * abs(float(np.sin(t * 0.65)))
    _box(d, [(0, 0), (W, 5)], OG, 0.7 * breathe)
    return base, ov, d

def _composite(base, ov) -> np.ndarray:
    merged = Image.alpha_composite(base.convert("RGBA"), ov)
    if _WM_ENABLED and _WM_IMG is not None:
        merged = _apply_watermark(merged)
    return np.array(merged.convert("RGB"))

def _brand(d, t: float, delay: float = 0.0):
    f = _f(18, bold=True)
    _txt(d, "ADIM MÜŞAVİR", PAD, 18, f, OG, _p(t, delay, 0.35))

def _progress(d, scene_num: int, total: int):
    if total <= 1:
        return
    bw = int(W * scene_num / max(total, 1))
    _box(d, [(0, H - 5), (bw, H)], OG, 0.55)

def _label_badge(d, text: str, t: float, delay: float = 0.08,
                 color=OG, bg=None):
    """Small badge below brand — e.g. 'TANIM', 'SORU'"""
    f = _f(17, bold=True)
    bg_color = bg or SURF2
    p = _p(t, delay, 0.32)
    w = _tw(text, f) + 20
    _box(d, [(PAD, 46), (PAD + w, 70)], bg_color, p, radius=4)
    _txt(d, text, PAD + 10, 50, f, color, p)
    return PAD + w + 14   # returns x after badge

def _section_title(d, title: str, y: int, t: float, delay: float,
                   font_size: int = 44, color=WH):
    """Full-width section title with growing underline."""
    f = _f(font_size, bold=True)
    p = _p(t, delay, 0.40)
    xo = _slide_offset(t, delay, 0.40, 24)
    _txt(d, title[:62], PAD + xo, y, f, color, p)
    uw = min(_tw(title[:62], f), W - PAD * 2)
    _growing_line(d, PAD, y + _th(f) + 8, PAD + uw, _p(t, delay + 0.22, 0.30))
    return y + _th(f) + 22


# ══════════════════════════════════════════════════════════════
# SCENE RENDERERS
# ══════════════════════════════════════════════════════════════

def render_intro_scene(title: str, subtitle: str = "", duration: float = 5.0) -> VideoClip:
    f_t = _f(60, bold=True)
    f_s = _f(30)
    t_lines = _wrap(title, f_t, W - PAD * 2)
    lh = _th(f_t) + 16

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t, 0.1)

        # Center accent bar grows from center
        bp = _p(t, 0.12, 0.50)
        bw = int(560 * bp)
        if bw > 0:
            _box(d, [(W//2 - bw//2, H//2 - 118), (W//2 + bw//2, H//2 - 113)], OG, 0.95)

        # Corner brackets
        ca = _p(t, 0.0, 0.35)
        _box(d, [(W - 80, 0), (W, 4)], OG, 0.35 * ca)
        _box(d, [(W - 4, 0), (W, 64)], OG, 0.25 * ca)
        _box(d, [(0, H - 4), (60, H)], OG, 0.25 * ca)

        # Title lines — slide up
        block_h = len(t_lines) * lh
        for i, line in enumerate(t_lines):
            p = _p(t, 0.30 + i * 0.14, 0.48)
            yo = _slide_offset(t, 0.30 + i * 0.14, 0.48, 28)
            _txt(d, line, _cx(line, f_t), H//2 - block_h//2 + i * lh + yo, f_t, WH, p)

        # Subtitle
        if subtitle:
            sp = _p(t, 0.82, 0.42)
            sl = _wrap(subtitle[:110], f_s, W - PAD * 2)
            for i, line in enumerate(sl):
                _txt(d, line, _cx(line, f_s), H//2 + block_h//2 + 42 + i * (_th(f_s) + 8), f_s, LG, sp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_hook_scene(lines: list[str], duration: float = 4.5) -> VideoClip:
    """
    Impact statement — full canvas, very large text.
    First line: 68px bold. Rest: 34px sub.
    """
    f_big = _f(64, bold=True)
    f_sub = _f(34)

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # Full-width background band slightly lighter
        bp = _p(t, 0.0, 0.3)
        _box(d, [(0, H//2 - 160), (W, H//2 + 160)], SURF, 0.35 * bp)

        # Left accent strip
        lp = _p(t, 0.1, 0.35)
        _box(d, [(0, 60), (8, H - 40)], OG, 0.6 * lp)

        big_line = lines[0] if lines else ""
        sub_lines = lines[1:] if len(lines) > 1 else []

        bl = _wrap(big_line, f_big, W - PAD * 2 - 20)
        bh = len(bl) * (_th(f_big) + 14)
        sub_total_h = sum(_th(f_sub) + 10 for _ in sub_lines)
        total_h = bh + (sub_total_h + 24 if sub_lines else 0)
        start_y = H // 2 - total_h // 2

        for i, line in enumerate(bl):
            p = _p(t, 0.16 + i * 0.10, 0.40)
            yo = _slide_offset(t, 0.16 + i * 0.10, 0.40, 22)
            _txt(d, line, _cx(line, f_big), start_y + i * (_th(f_big) + 14) + yo, f_big, WH, p)

        sy = start_y + bh + 28
        for i, line in enumerate(sub_lines[:4]):
            p = _p(t, 0.58 + i * 0.16, 0.36)
            sl = _wrap(line, f_sub, W - PAD * 2 - 20)
            for wl in sl:
                _txt(d, wl, _cx(wl, f_sub), sy, f_sub, LG, p)
                sy += _th(f_sub) + 10

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_definition_scene(
    term: str,
    definition_lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float = 6.5,
) -> VideoClip:
    """Full-screen definition: huge orange term + direct-on-BG definition lines."""
    f_term = _f(58, bold=True)
    f_def  = _f(30)
    lh = _th(f_def) + 16

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # "TANIM" badge
        _label_badge(d, "TANIM", t)

        # Term — slides from left, large orange
        tp = _p(t, 0.20, 0.42)
        xo = _slide_offset(t, 0.20, 0.42, 30)
        _txt(d, term[:55], PAD + xo, 76, f_term, OG, tp)

        # Full-width underline grows
        sep = _p(t, 0.42, 0.32)
        _growing_line(d, PAD, 76 + _th(f_term) + 6, W - PAD, sep, OG, 0.7, 3)

        # Definition lines — directly on background
        cy = 76 + _th(f_term) + 28
        for i, line in enumerate(definition_lines[:7]):
            lp = _p(t, 0.60 + i * 0.18, 0.34)
            yo = _slide_offset(t, 0.60 + i * 0.18, 0.34, 14)
            # Accent dot
            _box(d, [(PAD, cy + yo + 12), (PAD + 8, cy + yo + 12 + 8)], OG, lp * 0.8, radius=4)
            wl = _wrap(line, f_def, W - PAD * 2 - 22)
            for wi, wline in enumerate(wl):
                _txt(d, wline, PAD + 22, cy + yo + wi * _th(f_def), f_def, WH, lp)
            cy += lh * max(1, len(wl)) + 4

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_concept_scene(
    title: str,
    lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float = 6.5,
) -> VideoClip:
    """Numbered list — large circle numbers, full-width text."""
    f_t   = _f(44, bold=True)
    f_num = _f(26, bold=True)
    f_txt = _f(30)
    num_d = 46   # number circle diameter
    lh = max(_th(f_txt), num_d) + 16

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Full-height left accent stripe
        sp = _p(t, 0.1, 0.38)
        _box(d, [(0, 44), (10, H - 5)], OG, 0.55 * sp)

        # Title
        tp = _p(t, 0.18, 0.40)
        xo = _slide_offset(t, 0.18, 0.40, 22)
        _txt(d, title[:65], PAD + 14 + xo, 62, f_t, WH, tp)
        _growing_line(d, PAD + 14, 62 + _th(f_t) + 6, min(PAD + 14 + _tw(title[:65], f_t) + 12, W - PAD),
                      _p(t, 0.36, 0.28), OG, 0.7, 3)

        cy = 62 + _th(f_t) + 30
        for i, line in enumerate(lines[:6]):
            ts = 0.52 + i * 0.24
            lp = _p(t, ts, 0.34)
            yo = _slide_offset(t, ts, 0.34, 16)

            # Number circle
            cx_num = PAD + 14
            cy_num = cy + yo
            _box(d, [(cx_num, cy_num), (cx_num + num_d, cy_num + num_d)], OG, lp, radius=num_d // 2)
            ns = str(i + 1)
            _txt(d, ns, cx_num + (num_d - _tw(ns, f_num)) // 2, cy_num + (num_d - _th(f_num)) // 2, f_num, WH, lp)

            # Line text
            tx = cx_num + num_d + 16
            wrapped = _wrap(line, f_txt, W - tx - PAD)
            for wi, wl in enumerate(wrapped):
                _txt(d, wl, tx, cy + yo + (0 if wi == 0 else wi * _th(f_txt)), f_txt, WH, lp)
            cy += lh * max(1, len(wrapped)) + 2

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_content_scene(
    title: str,
    lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float | None = None,
) -> VideoClip:
    """Bullet point content — full-screen, large text."""
    f_t = _f(44, bold=True)
    f_b = _f(30)
    dot_size = 10
    lh = _th(f_b) + 18
    if duration is None:
        duration = max(4.0, min(2.5 + len(lines) * 1.6, 12.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Left accent strip
        _box(d, [(0, 44), (8, H - 5)], OG, 0.45 * _p(t, 0.08, 0.35))

        # Title
        tp = _p(t, 0.14, 0.40)
        xo = _slide_offset(t, 0.14, 0.40, 22)
        _txt(d, title[:65], PAD + 14 + xo, 62, f_t, WH, tp)
        _growing_line(d, PAD + 14, 62 + _th(f_t) + 6, min(PAD + 14 + _tw(title[:65], f_t) + 12, W - PAD),
                      _p(t, 0.34, 0.28), OG, 0.65, 3)

        cy = 62 + _th(f_t) + 28
        for i, line in enumerate(lines[:8]):
            ts = 0.50 + i * 0.24
            lp = _p(t, ts, 0.34)
            yo = _slide_offset(t, ts, 0.34, 14)

            raw = line.strip().lstrip("•-").strip()
            # Bullet dot
            _box(d, [(PAD + 14, cy + yo + _th(f_b) // 2 - dot_size // 2),
                     (PAD + 14 + dot_size, cy + yo + _th(f_b) // 2 + dot_size // 2)], OG, lp, radius=5)
            tx = PAD + 14 + dot_size + 14
            wrapped = _wrap(raw, f_b, W - tx - PAD)
            for wi, wl in enumerate(wrapped):
                _txt(d, wl, tx, cy + yo + wi * _th(f_b), f_b, WH, lp)
            cy += lh * max(1, len(wrapped)) + 2

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_comparison_scene(
    left_title: str,
    left_lines: list[str],
    right_title: str,
    right_lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float = 7.0,
) -> VideoClip:
    """True split-screen — each half has its own colored background fill."""
    f_hdr = _f(30, bold=True)
    f_txt = _f(26)
    lh = _th(f_txt) + 16
    mid = W // 2
    inner_pad = 28

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Left panel BG — slides in from left
        lp = _p(t, 0.10, 0.42)
        xo = _slide_offset(t, 0.10, 0.42, 40)
        _box(d, [(-xo, 44), (mid - 6 - xo, H - 5)], BL, 0.10 * lp)
        _box(d, [(-xo, 44), (8 - xo, H - 5)], BL, 0.7 * lp)   # left edge accent
        _txt(d, left_title[:30], inner_pad - xo, 60, f_hdr, BL, lp)
        _growing_line(d, inner_pad - xo, 60 + _th(f_hdr) + 6,
                      mid - 22 - xo, _p(t, 0.36, 0.26), BL, 0.7, 2)
        cy = 60 + _th(f_hdr) + 24
        for i, line in enumerate(left_lines[:6]):
            lp2 = _p(t, 0.50 + i * 0.20, 0.32)
            yo = _slide_offset(t, 0.50 + i * 0.20, 0.32, 12)
            wl = _wrap(line, f_txt, mid - inner_pad * 2 - 16)
            for wi, w in enumerate(wl):
                _txt(d, w, inner_pad - xo, cy + yo + wi * _th(f_txt), f_txt, WH, lp2)
            cy += lh * max(1, len(wl))

        # Right panel BG — slides in from right
        rp = _p(t, 0.20, 0.42)
        xo2 = _slide_offset(t, 0.20, 0.42, 40)
        _box(d, [(mid + 6 + xo2, 44), (W + xo2, H - 5)], OG, 0.10 * rp)
        _box(d, [(W - 8 + xo2, 44), (W + xo2, H - 5)], OG, 0.7 * rp)  # right edge accent
        _txt(d, right_title[:30], mid + inner_pad + xo2, 60, f_hdr, OG, rp)
        _growing_line(d, mid + inner_pad + xo2, 60 + _th(f_hdr) + 6,
                      W - inner_pad + xo2, _p(t, 0.44, 0.26), OG, 0.7, 2)
        cy2 = 60 + _th(f_hdr) + 24
        for i, line in enumerate(right_lines[:6]):
            rp2 = _p(t, 0.58 + i * 0.20, 0.32)
            yo2 = _slide_offset(t, 0.58 + i * 0.20, 0.32, 12)
            wl = _wrap(line, f_txt, mid - inner_pad * 2 - 16)
            for wi, w in enumerate(wl):
                _txt(d, w, mid + inner_pad + xo2, cy2 + yo2 + wi * _th(f_txt), f_txt, WH, rp2)
            cy2 += lh * max(1, len(wl))

        # Center divider
        dp = _p(t, 0.15, 0.40)
        top_y = 44 + int(((H - 49) // 2) * (1 - dp))
        bot_y = 44 + int(((H - 49) // 2) * (1 + dp))
        _line(d, (mid, top_y), (mid, bot_y), DG, 0.5, 2)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_example_scene(
    scenario: str,
    details: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float = 6.5,
) -> VideoClip:
    """Full-screen example: yellow scenario banner + detail lines."""
    f_lbl = _f(18, bold=True)
    f_scn = _f(32, bold=True)
    f_det = _f(28)
    lh = _th(f_det) + 16

    sc_lines = _wrap(scenario, f_scn, W - PAD * 2 - 16)
    sc_h = len(sc_lines) * (_th(f_scn) + 10) + 36

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # "ÖRNEK" badge
        _label_badge(d, "ÖRNEK", t, color=BG, bg=YL)

        # Scenario band — full-width, slides up
        sp = _p(t, 0.20, 0.42)
        yo = _slide_offset(t, 0.20, 0.42, 22)
        _box(d, [(0, 78 + yo), (W, 78 + sc_h + yo)], SURF2, sp * 0.95)
        _box(d, [(0, 78 + yo), (W, 82 + yo)], YL, sp * 0.9)   # top accent
        _box(d, [(0, 78 + sc_h - 4 + yo), (W, 78 + sc_h + yo)], YL, sp * 0.4)

        for i, line in enumerate(sc_lines):
            _txt(d, line, PAD + 16, 78 + 14 + i * (_th(f_scn) + 10) + yo, f_scn, WH, sp)

        # Detail lines — directly on background
        cy = 78 + sc_h + 22
        for i, line in enumerate(details[:5]):
            ts = 0.62 + i * 0.22
            lp = _p(t, ts, 0.34)
            yo2 = _slide_offset(t, ts, 0.34, 12)
            _box(d, [(PAD + 10, cy + yo2 + _th(f_det) // 2 - 5),
                     (PAD + 18, cy + yo2 + _th(f_det) // 2 + 5)], OG, lp, radius=4)
            wrapped = _wrap(line, f_det, W - PAD * 2 - 28)
            for wi, wl in enumerate(wrapped):
                _txt(d, wl, PAD + 32, cy + yo2 + wi * _th(f_det), f_det, WH, lp)
            cy += lh * max(1, len(wrapped)) + 4

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_question_scene(
    question_text: str,
    options: list[str],
    duration: float | None = None,
) -> VideoClip:
    """Full-screen question — large text, full-width option bars."""
    f_ql  = _f(20, bold=True)
    f_q   = _f(30, bold=True)
    f_opt = _f(26)
    f_lbl = _f(20, bold=True)
    opt_h = 72    # option bar height

    q_lines = _wrap(question_text, f_q, W - PAD * 2 - 16)
    qband_h = len(q_lines) * (_th(f_q) + 10) + 36

    if duration is None:
        duration = max(8.0, min(4.0 + len(q_lines) * 1.0 + len(options) * 1.0 + 1.5, 20.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # "SORU" badge
        _label_badge(d, "SORU", t, color=WH, bg=OG)

        # Question band — full-width
        qp = _p(t, 0.24, 0.46)
        _box(d, [(0, 80), (W, 80 + qband_h)], SURF2, qp * 0.92)
        _box(d, [(0, 80), (8, 80 + qband_h)], OG, qp)   # left accent
        for i, line in enumerate(q_lines):
            lp = _p(t, 0.46 + i * 0.08, 0.34)
            _txt(d, line, PAD + 16, 80 + 14 + i * (_th(f_q) + 10), f_q, WH, lp)

        # Options — full-width bars
        opt_y = 80 + qband_h + 16
        for i, opt in enumerate(options[:4]):
            ts = 1.00 + i * 0.35
            op = _p(t, ts, 0.34)
            xo = _slide_offset(t, ts, 0.34, 44)

            oy = opt_y + i * (opt_h + 8)
            _box(d, [(PAD + xo, oy), (W - PAD + xo, oy + opt_h)], SURF2, op * 0.92, radius=6)

            # Letter badge
            badge_d = opt_h - 16
            _box(d, [(PAD + 12 + xo, oy + 8), (PAD + 12 + badge_d + xo, oy + 8 + badge_d)],
                 OG, op, radius=badge_d // 2)
            lbl = "ABCD"[i]
            _txt(d, lbl, PAD + 12 + (badge_d - _tw(lbl, f_lbl)) // 2 + xo,
                 oy + 8 + (badge_d - _th(f_lbl)) // 2, f_lbl, WH, op)

            # Option text
            tx = PAD + 12 + badge_d + 16
            opt_txt = str(opt).lstrip("ABCD)").strip()
            opt_txt = opt_txt.lstrip(") ").strip()
            wl = _wrap(opt_txt, f_opt, W - tx - PAD - xo - 16)
            for wi, wline in enumerate(wl[:2]):
                _txt(d, wline, tx + xo, oy + (opt_h - _th(f_opt) * min(len(wl), 2)) // 2 + wi * (_th(f_opt) + 2), f_opt, WH, op)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_option_analysis_scene(
    options: list[str],
    correct_option: str,
    analysis_lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float | None = None,
) -> VideoClip:
    """Full-width option bars: wrong=red dimmed, correct=green bright."""
    f_hdr = _f(22, bold=True)
    f_opt = _f(24)
    f_lbl = _f(19, bold=True)
    f_exp = _f(22)
    opt_h = 66

    correct_idx = max(0, "ABCD".find(correct_option.upper()[:1]))
    if duration is None:
        duration = max(9.0, min(5.5 + len(options) * 0.8 + len(analysis_lines) * 0.7, 20.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Header bar — full width
        hp = _p(t, 0.10, 0.38)
        _box(d, [(0, 46), (W, 86)], SURF2, hp * 0.95)
        _box(d, [(0, 46), (8, 86)], OG, hp)
        _txt(d, "ŞIK ANALİZİ", PAD + 14, 56, f_hdr, OG, hp)

        # Options
        opt_y = 96
        for i, opt in enumerate(options[:4]):
            ts = 0.28 + i * 0.28
            op = _p(t, ts, 0.34)
            oy = opt_y + i * (opt_h + 8)
            is_c = (i == correct_idx)

            bar_col = (16, 55, 25) if is_c else (55, 18, 18)
            _box(d, [(0, oy), (W, oy + opt_h)], bar_col, op * 0.88)

            border_col = GR if is_c else RD
            _box(d, [(0, oy), (8, oy + opt_h)], border_col, op * 0.9)

            badge_d = opt_h - 16
            lbl_bg = GR if is_c else RD
            _box(d, [(PAD + 8, oy + 8), (PAD + 8 + badge_d, oy + 8 + badge_d)],
                 lbl_bg, op, radius=badge_d // 2)
            lbl = "ABCD"[i]
            _txt(d, lbl, PAD + 8 + (badge_d - _tw(lbl, f_lbl)) // 2,
                 oy + 8 + (badge_d - _th(f_lbl)) // 2, f_lbl, WH, op)

            mark = "✓" if is_c else "✗"
            _txt(d, mark, PAD + 8 + badge_d + 12, oy + (opt_h - _th(f_hdr)) // 2, f_hdr,
                 GR if is_c else RD, op)

            txt_col = WH if is_c else (190, 150, 150)
            opt_txt = str(opt).lstrip("ABCD)").strip().lstrip(") ").strip()
            tx = PAD + 8 + badge_d + 46
            _txt(d, opt_txt[:64], tx, oy + (opt_h - _th(f_opt)) // 2, f_opt, txt_col, op)

        # Analysis lines
        cy = opt_y + len(options[:4]) * (opt_h + 8) + 14
        for i, line in enumerate(analysis_lines[:3]):
            lp = _p(t, 1.50 + i * 0.28, 0.34)
            wl = _wrap(line, f_exp, W - PAD * 2 - 16)
            for wi, txt in enumerate(wl):
                _txt(d, txt, PAD + 14, cy + wi * (_th(f_exp) + 4), f_exp, LG, lp)
            cy += len(wl) * (_th(f_exp) + 4) + 8

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_answer_scene(
    options: list[str],
    correct_option: str,
    explanation: str = "",
    duration: float | None = None,
) -> VideoClip:
    """Correct answer — full-width bars, green glow on correct."""
    f_hdr = _f(24, bold=True)
    f_opt = _f(26)
    f_exp = _f(24)
    f_lbl = _f(19, bold=True)
    opt_h = 72

    correct_idx = max(0, "ABCD".find(correct_option.upper()[:1]))
    exp_lines = _wrap(explanation, f_exp, W - PAD * 2 - 16) if explanation else []
    if duration is None:
        duration = max(6.0, min(5.0 + len(exp_lines) * 0.8, 16.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # Header — full-width green band
        hp = _p(t, 0.10, 0.42)
        _box(d, [(0, 46), (W, 90)], GRD, hp * 0.9)
        header = "✓  DOĞRU CEVAP"
        _txt(d, header, _cx(header, f_hdr), 58, f_hdr, WH, hp)

        # All options — full-width
        for i, opt in enumerate(options[:4]):
            op = _p(t, 0.26 + i * 0.10, 0.38)
            oy = 100 + i * (opt_h + 8)
            is_c = (i == correct_idx)

            bar_col = (20, 80, 38) if is_c else (28, 26, 24)
            _box(d, [(0, oy), (W, oy + opt_h)], bar_col, op * 0.92)

            # Pulse on correct
            if is_c and t > 0.45:
                pulse = 0.07 + 0.055 * abs(float(np.sin(t * 3.0)))
                _box(d, [(0, oy - 3), (W, oy + opt_h + 3)], GR, pulse)

            badge_d = opt_h - 16
            lbl_bg = GR if is_c else DG
            _box(d, [(PAD + 8, oy + 8), (PAD + 8 + badge_d, oy + 8 + badge_d)],
                 lbl_bg, op, radius=badge_d // 2)
            lbl = "ABCD"[i]
            _txt(d, lbl, PAD + 8 + (badge_d - _tw(lbl, f_lbl)) // 2,
                 oy + 8 + (badge_d - _th(f_lbl)) // 2, f_lbl, WH, op)

            prefix = "✓  " if is_c else ""
            txt_col = WH if is_c else MG
            opt_txt = str(opt).lstrip("ABCD)").strip().lstrip(") ").strip()
            tx = PAD + 8 + badge_d + 16
            _txt(d, f"{prefix}{opt_txt}"[:68], tx, oy + (opt_h - _th(f_opt)) // 2, f_opt, txt_col, op)

        # Explanation — full-width card at bottom
        if exp_lines:
            ey = 100 + len(options[:4]) * (opt_h + 8) + 12
            ep = _p(t, 0.90, 0.42)
            exp_h = len(exp_lines) * (_th(f_exp) + 8) + 24
            _box(d, [(0, ey), (W, ey + exp_h)], SURF, ep * 0.88)
            _box(d, [(0, ey), (8, ey + exp_h)], GR, ep * 0.7)
            for i, line in enumerate(exp_lines[:4]):
                _txt(d, line, PAD + 18, ey + 12 + i * (_th(f_exp) + 8), f_exp, LG, ep)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_exam_tip_scene(tip: str, duration: float = 5.5) -> VideoClip:
    """Full-screen pulsing tip — large text, orange header."""
    f_hdr = _f(24, bold=True)
    f_tip = _f(32)
    tip_lines = _wrap(tip, f_tip, W - PAD * 2 - 16)
    tip_h = len(tip_lines) * (_th(f_tip) + 16)

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # Full-width pulsing header
        pulse = 0.85 + 0.10 * abs(float(np.sin(t * 1.6)))
        hp = _p(t, 0.15, 0.45)
        _box(d, [(0, 46), (W, 94)], OG, hp * pulse)
        label = "⚡  SINAV PÜF NOKTASI"
        _txt(d, label, _cx(label, f_hdr), 58, f_hdr, WH, hp)

        # Tip text — centered in remaining space, directly on BG
        ty = 110 + (H - 110 - tip_h) // 2
        for i, line in enumerate(tip_lines):
            lp = _p(t, 0.52 + i * 0.22, 0.36)
            yo = _slide_offset(t, 0.52 + i * 0.22, 0.36, 14)
            _txt(d, line, _cx(line, f_tip), ty + i * (_th(f_tip) + 16) + yo, f_tip, WH, lp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_summary_scene(
    title: str,
    rows: list[dict],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float | None = None,
) -> VideoClip:
    """Full-screen summary table — full-width rows, no card."""
    f_t   = _f(44, bold=True)
    f_lbl = _f(24, bold=True)
    f_val = _f(24)
    row_h = 60
    row_gap = 6
    if duration is None:
        duration = max(5.5, min(3.5 + len(rows) * 0.90, 14.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        tp = _p(t, 0.18, 0.42)
        _txt(d, title[:50], _cx(title[:50], f_t), 58, f_t, WH, tp)
        uw = int((_tw(title[:50], f_t) + 16) * tp)
        ux = _cx(title[:50], f_t) - 8
        _box(d, [(ux, 58 + _th(f_t) + 6), (ux + uw, 58 + _th(f_t) + 9)], OG, 0.9 * tp)

        table_y = 58 + _th(f_t) + 22
        for i, row in enumerate(rows):
            rp = _p(t, 0.44 + i * 0.24, 0.34)
            ry = table_y + i * (row_h + row_gap)
            # Full-width row
            bg = SURF if i % 2 == 0 else SURF2
            _box(d, [(0, ry), (W, ry + row_h)], bg, rp * 0.88)
            border_col = OG if i % 2 == 0 else BL
            _box(d, [(0, ry), (10, ry + row_h)], border_col, rp * 0.8)
            # Label (left ~40% of width)
            _txt(d, str(row.get("label", ""))[:36], PAD + 14, ry + (row_h - _th(f_lbl)) // 2, f_lbl, OG, rp)
            # Value (right 60%)
            _txt(d, str(row.get("value", ""))[:56], W * 2 // 5, ry + (row_h - _th(f_val)) // 2, f_val, WH, rp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_cta_scene(duration: float = 4.5) -> VideoClip:
    f_main = _f(42, bold=True)
    f_url  = _f(30)
    f_sub  = _f(24)
    main_t = "Beğen · Abone Ol · Bildirimi Aç"
    url_t  = "adimmusavir.com"
    sub_t  = "Her gün yeni eğitim içerikleri"

    def frame(t):
        base, ov, d = _frame_start(t)

        # Breathing orange vignette
        glow = 0.04 + 0.022 * abs(float(np.sin(t * 1.7)))
        _box(d, [(0, 0), (W, H)], OG, glow)

        _brand(d, t, 0.0)

        # Full-width center line
        lp = _p(t, 0.08, 0.38)
        _box(d, [(0, H//2 - 1), (W, H//2 + 1)], OG, 0.06 * lp)

        mp = _p(t, 0.24, 0.50)
        _txt(d, main_t, _cx(main_t, f_main), H//2 - 80, f_main, WH, mp)

        up = _p(t, 0.62, 0.40)
        _txt(d, url_t, _cx(url_t, f_url), H//2 + 20, f_url, OG, up)

        sp = _p(t, 0.88, 0.38)
        _txt(d, sub_t, _cx(sub_t, f_sub), H//2 + 74, f_sub, LG, sp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_shorts_scene(
    title: str = "",
    hook: str = "",
    content: str = "",
    duration: float = 4.5,
) -> VideoClip:
    """Shorts/Reels — very large centered text, full canvas."""
    f_hook = _f(60, bold=True)
    f_body = _f(34)
    hook_lines = _wrap(hook or title, f_hook, W - PAD * 2)
    body_lines = _wrap(content, f_body, W - PAD * 2) if content else []

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _box(d, [(0, H - 8), (W, H)], OG, _p(t, 0.08, 0.28))

        # Left accent strip
        _box(d, [(0, 44), (8, H - 8)], OG, 0.55 * _p(t, 0.05, 0.30))

        use_lines = hook_lines if not content else body_lines
        font = f_hook if not content else f_body
        line_h = _th(font) + 18
        block_h = len(use_lines) * line_h
        sy = H // 2 - block_h // 2

        for i, line in enumerate(use_lines):
            lp = _p(t, 0.15 + i * 0.18, 0.36)
            yo = _slide_offset(t, 0.15 + i * 0.18, 0.36, 20)
            _txt(d, line, _cx(line, font), sy + i * line_h + yo, font, WH, lp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


# ══════════════════════════════════════════════════════════════
# DISPATCHER
# ══════════════════════════════════════════════════════════════

def _get_lines(scene: dict) -> list[str]:
    """Normalize scene text fields — priority: display_lines > lines > content > text > narration."""
    dl = scene.get("display_lines")
    if dl and isinstance(dl, list) and dl:
        return [str(x) for x in dl if str(x).strip()]
    li = scene.get("lines")
    if li and isinstance(li, list) and li:
        return [str(x) for x in li if str(x).strip()]
    text = scene.get("content") or scene.get("text", "")
    if text:
        return [str(text)]
    narration = scene.get("narration", "")
    if narration:
        sent = str(narration).split(".")[0][:120]
        return [sent] if sent else [""]
    return [""]


def render_scene(scene: dict, scene_num: int = 1, total_scenes: int = 1) -> VideoClip:
    stype = str(scene.get("type", "content")).lower()
    dur   = scene.get("duration")
    lines = _get_lines(scene)

    if stype == "intro":
        subtitle = lines[1] if len(lines) > 1 else scene.get("subtitle", "")
        return render_intro_scene(scene.get("title", lines[0] if lines else ""), subtitle, dur or 5.0)

    elif stype == "hook":
        return render_hook_scene(lines if lines else [scene.get("title", "")], dur or 4.5)

    elif stype == "definition":
        term = scene.get("title", lines[0] if lines else "")
        def_lines = lines[1:] if len(lines) > 1 else lines
        return render_definition_scene(term, def_lines or lines, scene_num, total_scenes, dur or 6.5)

    elif stype in ("concept", "concept_analysis"):
        return render_concept_scene(scene.get("title", ""), lines, scene_num, total_scenes, dur or 6.5)

    elif stype in ("comparison", "karsilastirma"):
        mid = len(lines) // 2
        left  = lines[:mid] or [""]
        right = lines[mid:] or [""]
        lt = scene.get("left_title",  scene.get("left",  "A"))
        rt = scene.get("right_title", scene.get("right", "B"))
        return render_comparison_scene(lt, left, rt, right, scene_num, total_scenes, dur or 7.0)

    elif stype in ("example", "ornek"):
        scenario = scene.get("scenario", scene.get("title", lines[0] if lines else "Örnek"))
        details  = lines[1:] if len(lines) > 1 else lines
        return render_example_scene(scenario, details, scene_num, total_scenes, dur or 6.5)

    elif stype == "question":
        return render_question_scene(
            scene.get("question_text", lines[0] if lines else ""),
            scene.get("options", []),
            dur,
        )

    elif stype in ("option_analysis", "sik_analizi"):
        return render_option_analysis_scene(
            scene.get("options", []),
            scene.get("correct_option", "A"),
            lines,
            scene_num, total_scenes, dur,
        )

    elif stype == "answer":
        return render_answer_scene(
            scene.get("options", []),
            scene.get("correct_option", "A"),
            scene.get("explanation", ""),
            dur,
        )

    elif stype == "exam_tip":
        tip_text = scene.get("tip", lines[0] if lines else "")
        return render_exam_tip_scene(tip_text, dur or 5.5)

    elif stype == "summary":
        rows = scene.get("rows", [])
        if not rows and lines:
            rows = [
                {"label": l.split(":")[0].strip(), "value": l.split(":", 1)[-1].strip()}
                for l in lines if l and ":" in l
            ]
        return render_summary_scene(scene.get("title", "Özet"), rows, scene_num, total_scenes, dur)

    elif stype == "cta":
        return render_cta_scene(dur or 4.5)

    elif stype == "shorts":
        return render_shorts_scene(scene.get("title", ""), scene.get("hook", ""), scene.get("content", ""), dur or 4.5)

    else:
        return render_content_scene(scene.get("title", ""), lines, scene_num, total_scenes, dur)
