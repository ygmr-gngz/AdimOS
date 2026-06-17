"""
Motion Graphics Engine — professional educational video renderer.
PIL frame-by-frame + moviepy VideoClip.

Scene types:
  intro, hook, definition, concept, content, comparison,
  example, question, option_analysis, answer, exam_tip,
  summary, cta, shorts
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip

W, H, FPS = 1280, 720, 30

# ── Brand palette ─────────────────────────────────────────────
BG    = (16,  15,  14)
SURF  = (34,  31,  28)
SURF2 = (46,  42,  38)
OG    = (249, 115,  22)
OGDK  = (178,  80,  10)
GR    = (34,  197,  94)
GRD   = (21,  128,  61)
RD    = (220,  38,  38)
RDD   = (153,  27,  27)
BL    = (59,  130, 246)
YL    = (234, 179,   8)
WH    = (248, 248, 248)
LG    = (160, 155, 150)
DG    = (65,   60,  55)
MG    = (108, 103,  97)

# ── Pre-computed gradient background ─────────────────────────
_GRAD_BG: Image.Image | None = None

def _get_bg() -> Image.Image:
    global _GRAD_BG
    if _GRAD_BG is None:
        bg = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(bg)
        for y in range(H):
            r = max(8, int(22 - 9 * (y / H)))
            g = max(8, int(20 - 7 * (y / H)))
            b = max(8, int(18 - 5 * (y / H)))
            d.line([(0, y), (W, y)], fill=(r, g, b))
        _GRAD_BG = bg
    return _GRAD_BG.copy()


# ── Easing ────────────────────────────────────────────────────
def _eo(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2

def _p(t: float, start: float, dur: float) -> float:
    return _eo(max(0.0, (t - start) / max(dur, 0.001)))


# ── Font cache ────────────────────────────────────────────────
_FC: dict = {}
_FONT_PATHS = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",              True),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",                   False),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",      True),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",   False),
    ("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",                     True),
    ("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",                     False),
    ("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",                  True),
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",               False),
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


# ── Text helpers ──────────────────────────────────────────────
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
        return 18

def _cx(text: str, font) -> int:
    return max(0, (W - _tw(text, font)) // 2)

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
    return lines or [text[:60]]


# ── Draw primitives ───────────────────────────────────────────
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


# ── Frame boilerplate ─────────────────────────────────────────
def _frame_start(t: float = 0.0):
    base = _get_bg()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # Very subtle breathing top-line accent
    breathe = 0.5 + 0.15 * abs(float(np.sin(t * 0.7)))
    _box(d, [(0, 0), (W, 3)], OG, 0.08 * breathe)
    return base, ov, d

def _composite(base, ov) -> np.ndarray:
    return np.array(Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB"))

def _brand(d, t: float, delay: float = 0.0):
    _txt(d, "Adım Müşavir", 50, 32, _f(18), OG, _p(t, delay, 0.4))

def _progress(d, scene_num: int, total: int):
    if total <= 1:
        return
    bw = int(W * scene_num / max(total, 1))
    _box(d, [(0, H - 4), (bw, H)], OG, 0.45)

def _growing_line(d, x1: int, y: int, x2: int, progress: float, color=OG, alpha: float = 0.75, width: int = 2):
    if progress <= 0:
        return
    end = x1 + int((x2 - x1) * progress)
    _line(d, (x1, y), (end, y), color, alpha, width)


# ══════════════════════════════════════════════════════════════
# SCENE RENDERERS
# ══════════════════════════════════════════════════════════════

def render_intro_scene(title: str, subtitle: str = "", duration: float = 5.0) -> VideoClip:
    f_t = _f(54, bold=True)
    f_s = _f(28)
    t_lines = _wrap(title, f_t, W - 160)
    lh = _th(f_t) + 14

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t, 0.1)

        # Accent bar grows from center
        bp = _p(t, 0.12, 0.55)
        bw = int(520 * bp)
        if bw > 0:
            _box(d, [(W//2 - bw//2, H//2 - 110), (W//2 + bw//2, H//2 - 106)], OG, 0.9)

        # Corner accent brackets
        ca = _p(t, 0.0, 0.35)
        _box(d, [(W - 100, 0), (W, 4)], OG, 0.3 * ca)
        _box(d, [(W - 4, 0), (W, 60)], OG, 0.2 * ca)

        # Title lines slide up + fade
        block_h = len(t_lines) * lh
        for i, line in enumerate(t_lines):
            p = _p(t, 0.32 + i * 0.15, 0.5)
            yo = int(24 * (1 - _eo(max(0.0, (t - 0.32 - i * 0.15) / 0.5))))
            _txt(d, line, _cx(line, f_t), H//2 - block_h//2 + i * lh + yo, f_t, WH, p)

        # Subtitle
        if subtitle:
            sp = _p(t, 0.85, 0.45)
            sl = _wrap(subtitle[:100], f_s, W - 200)
            for i, line in enumerate(sl):
                _txt(d, line, _cx(line, f_s), H//2 + block_h//2 + 38 + i * (_th(f_s) + 8), f_s, LG, sp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_hook_scene(lines: list[str], duration: float = 4.0) -> VideoClip:
    """
    Impact statement — full-width centered text, high contrast.
    Used for opening "hook" and "why this matters" moments.
    """
    f_big = _f(48, bold=True)
    f_sub = _f(28)

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # Side accent bars
        lp = _p(t, 0.1, 0.4)
        _box(d, [(40, 120), (44, H - 120)], OG, 0.25 * lp)
        _box(d, [(W - 44, 120), (W - 40, H - 120)], OG, 0.25 * lp)

        # Split lines: first = big bold hook, rest = sub text
        big_line = lines[0] if lines else ""
        sub_lines = lines[1:] if len(lines) > 1 else []

        # Big hook text — slides from bottom
        bl = _wrap(big_line, f_big, W - 160)
        bh = len(bl) * (_th(f_big) + 12)
        total_h = bh + (len(sub_lines) * (_th(f_sub) + 10) + 20 if sub_lines else 0)
        start_y = H // 2 - total_h // 2

        for i, line in enumerate(bl):
            p = _p(t, 0.18 + i * 0.12, 0.42)
            yo = int(20 * (1 - _eo(max(0.0, (t - 0.18 - i * 0.12) / 0.42))))
            _txt(d, line, _cx(line, f_big), start_y + i * (_th(f_big) + 12) + yo, f_big, WH, p)

        # Sub-lines
        sy = start_y + bh + 22
        for i, line in enumerate(sub_lines[:3]):
            p = _p(t, 0.62 + i * 0.18, 0.38)
            sl = _wrap(line, f_sub, W - 200)
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
    duration: float = 6.0,
) -> VideoClip:
    """
    Term in large orange + definition in highlighted card.
    """
    f_term = _f(46, bold=True)
    f_def  = _f(27)
    f_lbl  = _f(16, bold=True)
    lh = _th(f_def) + 12
    def_h = len(definition_lines) * lh + 36

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # "TANIM" label
        lp = _p(t, 0.1, 0.35)
        _box(d, [(50, 56), (128, 80)], SURF2, lp, radius=4)
        _txt(d, "TANIM", 62, 60, f_lbl, OG, lp)

        # Term — slides from left
        tp = _p(t, 0.2, 0.45)
        xo = int(30 * (1 - _eo(max(0.0, (t - 0.2) / 0.45))))
        _txt(d, term[:60], 50 + xo, 96, f_term, OG, tp)

        # Underline grows
        sep = _p(t, 0.42, 0.35)
        _growing_line(d, 50, 155, min(50 + _tw(term[:60], f_term) + 12, W - 50), sep)

        # Definition card
        cp = _p(t, 0.55, 0.4)
        _box(d, [(50, 172), (W - 50, 172 + def_h)], SURF, cp * 0.95, radius=10)
        # Left accent border on card
        _box(d, [(50, 172), (54, 172 + def_h)], OG, cp * 0.9, radius=2)

        # Definition text lines
        for i, line in enumerate(definition_lines[:6]):
            lp2 = _p(t, 0.72 + i * 0.2, 0.35)
            yo = int(10 * (1 - _eo(max(0.0, (t - 0.72 - i * 0.2) / 0.35))))
            wl = _wrap(line, f_def, W - 155)
            for wi, wline in enumerate(wl):
                _txt(d, wline, 72, 172 + 18 + (i * lh) + (wi * lh) + yo, f_def, WH, lp2)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_concept_scene(
    title: str,
    lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float = 6.0,
) -> VideoClip:
    """
    Numbered concept list — orange numbers, white text.
    """
    f_t   = _f(36, bold=True)
    f_num = _f(30, bold=True)
    f_txt = _f(26)
    lh = _th(f_txt) + 18

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Left stripe
        sp = _p(t, 0.1, 0.4)
        _box(d, [(50, 98), (54, H - 45)], OG, 0.15 * sp)

        # Title
        tp = _p(t, 0.18, 0.42)
        _txt(d, title[:65], 68, 96, f_t, WH, tp)
        _growing_line(d, 68, 143, 68 + min(_tw(title[:65], f_t) + 10, W - 130), _p(t, 0.38, 0.32))

        # Numbered items
        cy = 162
        for i, line in enumerate(lines[:6]):
            ts = 0.55 + i * 0.28
            lp = _p(t, ts, 0.35)
            yo = int(14 * (1 - _eo(max(0.0, (t - ts) / 0.35))))

            # Number badge
            _box(d, [(68, cy + yo), (104, cy + yo + 36)], OG, lp, radius=6)
            _txt(d, str(i + 1), 76, cy + yo + 4, f_num, WH, lp)

            # Line text
            wrapped = _wrap(line, f_txt, W - 175)
            for wi, wl in enumerate(wrapped):
                _txt(d, wl, 118, cy + yo + (4 if wi == 0 else _th(f_txt) + 4), f_txt, WH, lp)
            cy += lh * max(1, len(_wrap(line, f_txt, W - 175))) + 4

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_content_scene(
    title: str,
    lines: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float | None = None,
) -> VideoClip:
    f_t = _f(36, bold=True)
    f_b = _f(26)
    lh = _th(f_b) + 18
    if duration is None:
        duration = max(4.0, min(2.5 + len(lines) * 1.5, 11.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Left orange stripe
        _box(d, [(50, 98), (54, H - 44)], OG, 0.14 * _p(t, 0.08, 0.4))

        # Title slides from left
        tp = _p(t, 0.15, 0.44)
        xo = int(32 * (1 - _eo(max(0.0, (t - 0.15) / 0.44))))
        _txt(d, title[:65], 68 + xo, 96, f_t, WH, tp)

        # Separator under title
        _growing_line(d, 68, 143, 68 + min(_tw(title[:65], f_t) + 10, W - 130), _p(t, 0.36, 0.3))

        # Bullet lines — staggered
        cy = 162
        for i, line in enumerate(lines[:8]):
            ts = 0.55 + i * 0.28
            lp = _p(t, ts, 0.36)
            yo = int(12 * (1 - _eo(max(0.0, (t - ts) / 0.36))))

            # Bullet dot
            if line.strip().startswith("•"):
                line = line.strip()[1:].strip()
                _box(d, [(70, cy + yo + 10), (80, cy + yo + 10 + 10)], OG, lp, radius=5)
                _txt(d, line[:72], 90, cy + yo, f_b, WH, lp)
            else:
                _txt(d, line[:72], 76, cy + yo, f_b, WH, lp)

            wrapped = _wrap(line, f_b, W - 165)
            cx = 90 if line.startswith("•") else 76
            for wi, wl in enumerate(wrapped[1:], 1):
                _txt(d, wl, cx, cy + yo + wi * _th(f_b), f_b, WH, lp)
            cy += lh * max(1, len(_wrap(line, f_b, W - 165))) + 4

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
    """
    Split-screen comparison — left column vs right column.
    """
    f_hdr = _f(26, bold=True)
    f_txt = _f(22)
    lh = _th(f_txt) + 14
    mid = W // 2
    col_w = mid - 80

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # VS badge in center
        vp = _p(t, 0.35, 0.4)
        _box(d, [(mid - 30, H//2 - 30), (mid + 30, H//2 + 30)], SURF2, vp, radius=30)
        _txt(d, "VS", mid - 14, H//2 - 14, f_hdr, OG, vp)

        # Center divider line (grows from center outward)
        dp = _p(t, 0.15, 0.45)
        top_end = H // 2 - int(((H - 160) // 2) * dp)
        bot_end = H // 2 + int(((H - 160) // 2) * dp)
        _line(d, (mid, top_end), (mid, bot_end), DG, 0.4)

        # Left panel — slides from left
        lp = _p(t, 0.12, 0.45)
        xo = int(40 * (1 - _eo(max(0.0, (t - 0.12) / 0.45))))
        _box(d, [(44 + xo, 80), (mid - 14 + xo, H - 60)], SURF, lp * 0.9, radius=8)
        _box(d, [(44 + xo, 80), (48 + xo, H - 60)], BL, lp, radius=4)
        _txt(d, left_title[:28], 60 + xo, 98, f_hdr, BL, lp)
        _growing_line(d, 60 + xo, 132, mid - 24 + xo, _p(t, 0.38, 0.28), BL, 0.6)
        for i, line in enumerate(left_lines[:6]):
            _txt(d, line[:35], 58 + xo, 148 + i * lh, f_txt, WH, _p(t, 0.52 + i * 0.22, 0.32))

        # Right panel — slides from right
        rp = _p(t, 0.22, 0.45)
        xo2 = int(40 * (1 - _eo(max(0.0, (t - 0.22) / 0.45))))
        _box(d, [(mid + 14 - xo2, 80), (W - 44 - xo2, H - 60)], SURF, rp * 0.9, radius=8)
        _box(d, [(W - 48 - xo2, 80), (W - 44 - xo2, H - 60)], OG, rp, radius=4)
        _txt(d, right_title[:28], mid + 26 - xo2, 98, f_hdr, OG, rp)
        _growing_line(d, mid + 26 - xo2, 132, W - 58 - xo2, _p(t, 0.45, 0.28), OG, 0.6)
        for i, line in enumerate(right_lines[:6]):
            _txt(d, line[:35], mid + 24 - xo2, 148 + i * lh, f_txt, WH, _p(t, 0.62 + i * 0.22, 0.32))

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_example_scene(
    scenario: str,
    details: list[str],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float = 6.5,
) -> VideoClip:
    """
    Case study card — realistic example scenario.
    """
    f_lbl = _f(16, bold=True)
    f_scn = _f(28, bold=True)
    f_det = _f(24)
    lh = _th(f_det) + 12

    sc_lines = _wrap(scenario, f_scn, W - 170)
    sc_h = len(sc_lines) * (_th(f_scn) + 8) + 32

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # "ÖRNEK" badge
        bp = _p(t, 0.1, 0.35)
        _box(d, [(50, 54), (140, 78)], YL, bp, radius=5)
        _txt(d, "ÖRNEK", 62, 58, f_lbl, BG, bp)

        # Scenario card slides up
        sp = _p(t, 0.22, 0.45)
        yo = int(20 * (1 - _eo(max(0.0, (t - 0.22) / 0.45))))
        _box(d, [(50, 90 + yo), (W - 50, 90 + sc_h + yo)], SURF2, sp * 0.92, radius=10)
        _box(d, [(50, 90 + yo), (W - 50, 94 + yo)], YL, sp * 0.8)

        for i, line in enumerate(sc_lines):
            _txt(d, line, 68, 90 + 16 + i * (_th(f_scn) + 8) + yo, f_scn, WH, sp)

        # Detail lines
        cy = 90 + sc_h + 16
        for i, line in enumerate(details[:5]):
            ts = 0.65 + i * 0.25
            lp = _p(t, ts, 0.35)
            yo2 = int(10 * (1 - _eo(max(0.0, (t - ts) / 0.35))))
            _box(d, [(68, cy + yo2), (74, cy + yo2 + _th(f_det))], OG, lp, radius=3)
            wrapped = _wrap(line, f_det, W - 160)
            for wi, wl in enumerate(wrapped):
                _txt(d, wl, 84, cy + yo2 + wi * _th(f_det), f_det, WH, lp)
            cy += lh * max(1, len(wrapped)) + 4

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_question_scene(
    question_text: str,
    options: list[str],
    duration: float | None = None,
) -> VideoClip:
    f_ql  = _f(18, bold=True)
    f_q   = _f(26, bold=True)
    f_opt = _f(23)
    f_lbl = _f(19, bold=True)

    q_lines = _wrap(question_text, f_q, W - 175)
    qbox_h  = len(q_lines) * (_th(f_q) + 10) + 34

    if duration is None:
        duration = max(7.0, min(3.5 + len(q_lines) * 1.1 + len(options) * 0.8 + 1.5, 18.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # SORU badge
        bp = _p(t, 0.08, 0.38)
        _box(d, [(50, 46), (140, 74)], OG, bp, radius=6)
        _txt(d, "SORU", 66, 51, f_ql, WH, bp)

        # Question card
        qp = _p(t, 0.26, 0.5)
        qbw = int((W - 100) * qp)
        _box(d, [(50, 86), (50 + qbw, 86 + qbox_h)], SURF, qp * 0.92, radius=8)
        _box(d, [(50, 86), (54, 86 + qbox_h)], OG, qp)

        # Question text
        for i, line in enumerate(q_lines):
            lp = _p(t, 0.5 + i * 0.1, 0.36)
            _txt(d, line, 68, 100 + i * (_th(f_q) + 10), f_q, WH, lp)

        # Options — slide in from right, staggered
        opt_y = 86 + qbox_h + 16
        for i, opt in enumerate(options[:4]):
            ts = 1.1 + i * 0.4
            op = _p(t, ts, 0.36)
            xo = int(50 * (1 - _eo(max(0.0, (t - ts) / 0.36))))

            oy = opt_y + i * 68
            _box(d, [(50 + xo, oy), (W - 50 + xo, oy + 56)], SURF2, op * 0.9, radius=8)

            # Letter badge
            _box(d, [(60 + xo, oy + 8), (94 + xo, oy + 44)], OG, op, radius=18)
            _txt(d, "ABCD"[i], 71 + xo, oy + 12, f_lbl, WH, op)

            # Option text
            opt_txt = _wrap(str(opt), f_opt, W - 210)
            _txt(d, opt_txt[0][:64], 104 + xo, oy + 16, f_opt, WH, op)

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
    """
    Wrong options get X marks + reason; correct option highlighted.
    """
    f_hdr = _f(20, bold=True)
    f_opt = _f(22)
    f_lbl = _f(18, bold=True)
    f_exp = _f(20)

    correct_idx = max(0, "ABCD".find(correct_option.upper()[:1]))
    if duration is None:
        duration = max(8.0, min(5.0 + len(options) * 1.0 + len(analysis_lines) * 0.8, 18.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        # Header
        hp = _p(t, 0.1, 0.4)
        _box(d, [(50, 56), (290, 82)], SURF2, hp, radius=6)
        _txt(d, "ŞIK ANALİZİ", 66, 60, f_hdr, OG, hp)

        # Options with analysis
        opt_y = 100
        for i, opt in enumerate(options[:4]):
            ts = 0.3 + i * 0.32
            op = _p(t, ts, 0.36)
            oy = opt_y + i * 64
            is_c = (i == correct_idx)
            bg = GRD if is_c else (45, 28, 28)
            _box(d, [(50, oy), (W - 50, oy + 52)], bg, op * 0.9, radius=8)

            lbl_col = GR if is_c else RD
            _box(d, [(60, oy + 8), (88, oy + 40)], lbl_col, op, radius=16)
            _txt(d, "ABCD"[i], 69, oy + 11, f_lbl, WH, op)

            mark = "✓" if is_c else "✗"
            mark_col = GR if is_c else RD
            _txt(d, mark, 98, oy + 13, f_hdr, mark_col, op)

            txt_col = WH if is_c else (200, 160, 160)
            _txt(d, str(opt)[:60], 122, oy + 15, f_opt, txt_col, op)

        # Analysis text below
        cy = opt_y + len(options[:4]) * 64 + 12
        for i, line in enumerate(analysis_lines[:3]):
            lp = _p(t, 1.6 + i * 0.3, 0.35)
            wl = _wrap(line, f_exp, W - 130)
            for wi, txt in enumerate(wl):
                _txt(d, txt, 60, cy + wi * (_th(f_exp) + 4), f_exp, LG, lp)
            cy += len(wl) * (_th(f_exp) + 4) + 8

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_answer_scene(
    options: list[str],
    correct_option: str,
    explanation: str = "",
    duration: float | None = None,
) -> VideoClip:
    f_hdr = _f(22, bold=True)
    f_opt = _f(23)
    f_exp = _f(22)
    f_lbl = _f(18, bold=True)

    correct_idx = max(0, "ABCD".find(correct_option.upper()[:1]))
    exp_lines = _wrap(explanation, f_exp, W - 160) if explanation else []
    if duration is None:
        duration = max(5.5, min(4.5 + len(exp_lines) * 0.9, 14.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # Header
        hp = _p(t, 0.1, 0.45)
        _box(d, [(50, 44), (350, 78)], GRD, hp, radius=8)
        _txt(d, "✓  DOĞRU CEVAP", 68, 51, f_hdr, WH, hp)

        # All options
        for i, opt in enumerate(options[:4]):
            op = _p(t, 0.28 + i * 0.1, 0.4)
            oy = 96 + i * 68
            is_c = (i == correct_idx)
            bg = GRD if is_c else (28, 26, 24)
            _box(d, [(50, oy), (W - 50, oy + 56)], bg, op * 0.9, radius=8)

            # Pulse on correct
            if is_c and t > 0.5:
                pulse = 0.08 + 0.06 * abs(float(np.sin(t * 3.2)))
                _box(d, [(44, oy - 4), (W - 44, oy + 60)], GR, pulse, radius=10)

            lbl_col = GR if is_c else DG
            _box(d, [(60, oy + 9), (88, oy + 43)], lbl_col, op, radius=16)
            _txt(d, "ABCD"[i], 69, oy + 13, f_lbl, WH, op)

            prefix = "✓  " if is_c else ""
            txt_col = WH if is_c else MG
            _txt(d, f"{prefix}{str(opt)[:60]}", 100, oy + 15, f_opt, txt_col, op)

        # Explanation
        if exp_lines:
            ey = 96 + len(options[:4]) * 68 + 14
            ep = _p(t, 1.0, 0.45)
            exp_h = len(exp_lines) * (_th(f_exp) + 8) + 24
            _box(d, [(50, ey), (W - 50, ey + exp_h)], SURF, ep * 0.88, radius=8)
            _box(d, [(50, ey), (54, ey + exp_h)], GR, ep * 0.7)
            for i, line in enumerate(exp_lines):
                _txt(d, line, 68, ey + 12 + i * (_th(f_exp) + 8), f_exp, LG, ep)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_exam_tip_scene(tip: str, duration: float = 5.0) -> VideoClip:
    f_hdr = _f(22, bold=True)
    f_tip = _f(26)
    f_lbl = _f(16, bold=True)
    tip_lines = _wrap(tip, f_tip, W - 185)

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)

        # Pulsing header bar
        pulse = 0.88 + 0.07 * abs(float(np.sin(t * 1.8)))
        hp = _p(t, 0.18, 0.48)
        _box(d, [(50, 76), (W - 50, 128)], OG, hp * pulse, radius=8)
        label = "⚡  SINAV PÜF NOKTASI"
        _txt(d, label, _cx(label, f_hdr), 92, f_hdr, WH, hp)

        # Tip text card
        card_h = len(tip_lines) * (_th(f_tip) + 14) + 36
        cp = _p(t, 0.55, 0.4)
        _box(d, [(50, 148), (W - 50, 148 + card_h)], SURF2, cp * 0.9, radius=8)

        cy = 148 + 18
        for i, line in enumerate(tip_lines):
            lp = _p(t, 0.68 + i * 0.25, 0.36)
            yo = int(10 * (1 - _eo(max(0.0, (t - 0.68 - i * 0.25) / 0.36))))
            _txt(d, line, 70, cy + yo, f_tip, WH, lp)
            cy += _th(f_tip) + 14

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_summary_scene(
    title: str,
    rows: list[dict],
    scene_num: int = 1,
    total_scenes: int = 1,
    duration: float | None = None,
) -> VideoClip:
    f_t   = _f(36, bold=True)
    f_lbl = _f(21, bold=True)
    f_val = _f(21)
    row_h, row_gap = 54, 5
    if duration is None:
        duration = max(5.0, min(3.5 + len(rows) * 0.85, 13.0))

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _progress(d, scene_num, total_scenes)

        tp = _p(t, 0.2, 0.45)
        _txt(d, title[:50], _cx(title[:50], f_t), 66, f_t, WH, tp)
        uw = int((_tw(title[:50], f_t) + 16) * tp)
        ux = _cx(title[:50], f_t) - 8
        _box(d, [(ux, 114), (ux + uw, 117)], OG, 0.88 * tp)

        table_y = 132
        for i, row in enumerate(rows):
            rp = _p(t, 0.48 + i * 0.26, 0.34)
            ry = table_y + i * (row_h + row_gap)
            bg = SURF if i % 2 == 0 else SURF2
            _box(d, [(50, ry), (W - 50, ry + row_h)], bg, rp * 0.9, radius=6)
            # Colored left border alternating
            border_col = OG if i % 2 == 0 else BL
            _box(d, [(50, ry), (54, ry + row_h)], border_col, rp * 0.7)
            _txt(d, str(row.get("label", ""))[:36], 68, ry + 15, f_lbl, OG, rp)
            _txt(d, str(row.get("value", ""))[:52], W//2 + 24, ry + 15, f_val, WH, rp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_cta_scene(duration: float = 4.5) -> VideoClip:
    f_main = _f(38, bold=True)
    f_url  = _f(26)
    f_sub  = _f(22)
    main_t = "Beğen · Abone Ol · Bildirimi Aç"
    url_t  = "adimmusavir.com"
    sub_t  = "Her gün yeni içerikler"

    def frame(t):
        base, ov, d = _frame_start(t)

        # Breathing orange vignette
        glow = 0.03 + 0.018 * abs(float(np.sin(t * 1.8)))
        _box(d, [(0, 0), (W, H)], OG, glow)

        _brand(d, t, 0.0)

        # Decorative lines
        lp = _p(t, 0.08, 0.4)
        _box(d, [(0, H//2 - 2), (W, H//2 + 2)], OG, 0.04 * lp)

        mp = _p(t, 0.25, 0.52)
        _txt(d, main_t, _cx(main_t, f_main), H//2 - 72, f_main, WH, mp)

        up = _p(t, 0.65, 0.4)
        _txt(d, url_t, _cx(url_t, f_url), H//2 + 22, f_url, OG, up)

        sp = _p(t, 0.9, 0.4)
        _txt(d, sub_t, _cx(sub_t, f_sub), H//2 + 74, f_sub, LG, sp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_shorts_scene(
    title: str = "",
    hook: str = "",
    content: str = "",
    duration: float = 4.5,
) -> VideoClip:
    f_hook = _f(44, bold=True)
    f_body = _f(28)
    hook_lines = _wrap(hook or title, f_hook, W - 120)
    body_lines = _wrap(content, f_body, W - 120) if content else []

    def frame(t):
        base, ov, d = _frame_start(t)
        _brand(d, t)
        _box(d, [(0, 0), (W, 5)], OG, _p(t, 0.08, 0.32))
        _box(d, [(0, H - 5), (W, H)], OG, _p(t, 0.08, 0.32))

        use_lines = hook_lines if not content else body_lines
        font = f_hook if not content else f_body
        block_h = len(use_lines) * (_th(font) + 14)
        sy = H // 2 - block_h // 2

        for i, line in enumerate(use_lines):
            lp = _p(t, 0.18 + i * 0.2, 0.38)
            yo = int(18 * (1 - _eo(max(0.0, (t - 0.18 - i * 0.2) / 0.38))))
            _txt(d, line, _cx(line, font), sy + i * (_th(font) + 14) + yo, font, WH, lp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


# ══════════════════════════════════════════════════════════════
# DISPATCHER
# ══════════════════════════════════════════════════════════════

def _get_lines(scene: dict) -> list[str]:
    """Normalize scene text — checks display_lines, lines, content, text."""
    dl = scene.get("display_lines")
    if dl and isinstance(dl, list) and dl:
        return [str(x) for x in dl]
    li = scene.get("lines")
    if li and isinstance(li, list) and li:
        return [str(x) for x in li]
    text = scene.get("content") or scene.get("text", "")
    if text:
        return [str(text)]
    narration = scene.get("narration", "")
    if narration:
        # fallback: show first sentence from narration
        sent = str(narration).split(".")[0][:120]
        return [sent] if sent else [""]
    return [""]


def render_scene(scene: dict, scene_num: int = 1, total_scenes: int = 1) -> VideoClip:
    stype = str(scene.get("type", "content")).lower()
    dur   = scene.get("duration")
    lines = _get_lines(scene)

    # ── intro ──────────────────────────────────────────────────
    if stype == "intro":
        subtitle = lines[1] if len(lines) > 1 else scene.get("subtitle", "")
        return render_intro_scene(scene.get("title", lines[0] if lines else ""), subtitle, dur or 5.0)

    # ── hook ───────────────────────────────────────────────────
    elif stype in ("hook",):
        hook_lines = lines if lines else [scene.get("title", "")]
        return render_hook_scene(hook_lines, dur or 4.5)

    # ── definition ─────────────────────────────────────────────
    elif stype in ("definition",):
        term = scene.get("title", lines[0] if lines else "")
        def_lines = lines[1:] if len(lines) > 1 else lines
        return render_definition_scene(term, def_lines or lines, scene_num, total_scenes, dur or 6.5)

    # ── concept ────────────────────────────────────────────────
    elif stype in ("concept", "concept_analysis"):
        return render_concept_scene(scene.get("title", ""), lines, scene_num, total_scenes, dur or 6.5)

    # ── comparison ─────────────────────────────────────────────
    elif stype in ("comparison", "karsilastirma"):
        mid = len(lines) // 2
        left  = lines[:mid] or [""]
        right = lines[mid:] or [""]
        lt = scene.get("left_title",  scene.get("left",  "A"))
        rt = scene.get("right_title", scene.get("right", "B"))
        return render_comparison_scene(lt, left, rt, right, scene_num, total_scenes, dur or 7.0)

    # ── example ────────────────────────────────────────────────
    elif stype in ("example", "ornek"):
        scenario = scene.get("scenario", scene.get("title", lines[0] if lines else "Örnek"))
        details  = lines[1:] if len(lines) > 1 else lines
        return render_example_scene(scenario, details, scene_num, total_scenes, dur or 6.5)

    # ── question ───────────────────────────────────────────────
    elif stype == "question":
        return render_question_scene(
            scene.get("question_text", lines[0] if lines else ""),
            scene.get("options", []),
            dur,
        )

    # ── option analysis ────────────────────────────────────────
    elif stype in ("option_analysis", "sik_analizi"):
        return render_option_analysis_scene(
            scene.get("options", []),
            scene.get("correct_option", "A"),
            lines,
            scene_num, total_scenes, dur,
        )

    # ── answer ─────────────────────────────────────────────────
    elif stype == "answer":
        return render_answer_scene(
            scene.get("options", []),
            scene.get("correct_option", "A"),
            scene.get("explanation", ""),
            dur,
        )

    # ── exam tip ───────────────────────────────────────────────
    elif stype == "exam_tip":
        tip_text = scene.get("tip", lines[0] if lines else "")
        return render_exam_tip_scene(tip_text, dur or 5.5)

    # ── summary ────────────────────────────────────────────────
    elif stype == "summary":
        rows = scene.get("rows", [])
        if not rows and lines:
            rows = [{"label": l.split(":")[0].strip(), "value": l.split(":", 1)[-1].strip()} for l in lines if l]
        return render_summary_scene(scene.get("title", "Özet"), rows, scene_num, total_scenes, dur)

    # ── cta ────────────────────────────────────────────────────
    elif stype == "cta":
        return render_cta_scene(dur or 4.5)

    # ── shorts / hook ──────────────────────────────────────────
    elif stype == "shorts":
        return render_shorts_scene(scene.get("title", ""), scene.get("hook", ""), scene.get("content", ""), dur or 4.5)

    # ── default: content ───────────────────────────────────────
    else:
        return render_content_scene(scene.get("title", ""), lines, scene_num, total_scenes, dur)
