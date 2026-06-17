"""
Animated scene renderer — PIL frame-by-frame + moviepy VideoClip.
Each render_*() returns a VideoClip with real animations (no static PNGs).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip

W, H, FPS = 1280, 720, 30

# ── Colors ────────────────────────────────────────────────────
BG    = (18,  17,  15)
SURF  = (35,  32,  29)
SURF2 = (52,  48,  44)
OG    = (249, 115,  22)   # orange
GR    = (34,  197,  94)   # green
GRD   = (21,  128,  61)   # dark green
WH    = (248, 248, 248)
LG    = (155, 155, 155)
DG    = (75,   75,  75)

# ── Easing ────────────────────────────────────────────────────
def _eo(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2

def _p(t: float, start: float, dur: float) -> float:
    return _eo(max(0.0, (t - start) / max(dur, 0.001)))

# ── Font loader (cached) ──────────────────────────────────────
_FC: dict = {}
_FONT_SEARCH = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",         True),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",              False),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",     True),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  False),
    ("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",                True),
    ("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",               False),
]

def _f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _FC:
        font = ImageFont.load_default()
        for path, is_bold in _FONT_SEARCH:
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
        b = font.getbbox(text)
        return max(1, b[2] - b[0])
    except Exception:
        return len(text) * 10

def _th(font) -> int:
    try:
        b = font.getbbox("Ag")
        return max(1, b[3] - b[1])
    except Exception:
        return 18

def _cx(text: str, font) -> int:
    return max(0, (W - _tw(text, font)) // 2)

def _wrap(text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = f"{cur} {word}".strip()
        if _tw(test, font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [text[:50]]

# ── Draw helpers (all draw on shared RGBA overlay) ────────────
def _txt(d: ImageDraw.Draw, text: str, x: int, y: int, font, color, alpha: float) -> None:
    if alpha <= 0:
        return
    r, g, b = color
    d.text((x, y), text, font=font, fill=(r, g, b, int(255 * min(alpha, 1.0))))

def _box(d: ImageDraw.Draw, xy, color, alpha: float = 1.0, radius: int = 0) -> None:
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

def _frame_start() -> tuple[Image.Image, Image.Image, ImageDraw.Draw]:
    base = Image.new("RGB",  (W, H), BG)
    ov   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return base, ov, ImageDraw.Draw(ov)

def _composite(base: Image.Image, ov: Image.Image) -> np.ndarray:
    return np.array(Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB"))

def _brand(d, t, delay=0.0):
    _txt(d, "Adım Müşavir", 50, 34, _f(18), OG, _p(t, delay, 0.4))

def _progress_bar(d, scene_num, total):
    bw = int(W * (scene_num / max(total, 1)))
    _box(d, [(0, H - 4), (bw, H)], OG, 0.65)


# ══════════════════════════════════════════════════════════════
# SCENE RENDERERS
# ══════════════════════════════════════════════════════════════

def render_intro_scene(title: str, subtitle: str = "", duration: float = 5.0) -> VideoClip:
    f_t = _f(52, bold=True)
    f_s = _f(28)
    t_lines = _wrap(title, f_t, W - 160)
    lh = _th(f_t) + 14

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t, 0.1)

        # Accent bar grows from center
        bp = _p(t, 0.15, 0.55)
        bw = int(480 * bp)
        if bw > 0:
            _box(d, [(W//2 - bw//2, H//2 - 105), (W//2 + bw//2, H//2 - 101)], OG, 0.85)

        # Title lines slide up + fade in
        block_h = len(t_lines) * lh
        for i, line in enumerate(t_lines):
            p = _p(t, 0.35 + i * 0.15, 0.5)
            yo = int(22 * (1 - _eo(max(0, (t - 0.35 - i*0.15) / 0.5))))
            x = _cx(line, f_t)
            y = H//2 - block_h//2 + i * lh + yo
            _txt(d, line, x, y, f_t, WH, p)

        # Subtitle fades in
        if subtitle:
            sp = _p(t, 0.85, 0.5)
            sl = _wrap(subtitle[:90], f_s, W - 200)
            for i, line in enumerate(sl):
                _txt(d, line, _cx(line, f_s), H//2 + block_h//2 + 35 + i*(_th(f_s)+8), f_s, LG, sp)

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
    if duration is None:
        duration = max(4.0, min(2.5 + len(lines) * 1.6, 11.0))
    lh = _th(f_b) + 16

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t)
        _progress_bar(d, scene_num, total_scenes)

        # Left orange accent stripe
        sp = _p(t, 0.1, 0.4)
        _box(d, [(50, 105), (54, H - 45)], OG, 0.12 * sp)

        # Title slides in from left
        tp = _p(t, 0.15, 0.45)
        xo = int(35 * (1 - _eo(max(0, (t - 0.15) / 0.45))))
        _txt(d, title[:65], 68 + xo, 98, f_t, WH, tp)

        # Separator under title
        sep_p = _p(t, 0.38, 0.3)
        _box(d, [(68, 144), (68 + int((_tw(title[:65], f_t) + 16) * sep_p), 147)], OG, 0.85 * sep_p)

        # Content lines — staggered fade + slide up
        cy = 168
        for i, line in enumerate(lines):
            ts = 0.6 + i * 0.32
            lp = _p(t, ts, 0.38)
            yo = int(14 * (1 - _eo(max(0, (t - ts) / 0.38))))
            wrapped = _wrap(line, f_b, W - 165)
            for wl in wrapped:
                _txt(d, wl, 76, cy + yo, f_b, WH, lp)
                cy += lh
            cy += 6

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_question_scene(
    question_text: str,
    options: list[str],
    duration: float | None = None,
) -> VideoClip:
    f_ql  = _f(20)
    f_q   = _f(28, bold=True)
    f_opt = _f(24)
    f_lbl = _f(20, bold=True)

    q_lines = _wrap(question_text, f_q, W - 180)
    qbox_h  = len(q_lines) * (_th(f_q) + 10) + 32

    if duration is None:
        duration = max(7.0, min(3.0 + len(q_lines) * 1.2 + len(options) * 0.85 + 1.5, 16.0))

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t)

        # "SORU" badge
        bp = _p(t, 0.1, 0.4)
        _box(d, [(50, 48), (138, 78)], OG, bp, radius=6)
        _txt(d, "SORU", 65, 53, f_ql, WH, bp)

        # Question box expands
        qbp = _p(t, 0.28, 0.55)
        qbw = int((W - 100) * qbp)
        _box(d, [(50, 90), (50 + qbw, 90 + qbox_h)], SURF, 0.9 * qbp, radius=8)

        # Question text
        for i, line in enumerate(q_lines):
            lp = _p(t, 0.52 + i * 0.1, 0.38)
            _txt(d, line, 68, 105 + i * (_th(f_q) + 10), f_q, WH, lp)

        # Options — slide from right, staggered
        opt_y = 90 + qbox_h + 18
        opt_bg = [(55, 50, 46), (50, 47, 44), (55, 50, 46), (50, 47, 44)]
        for i, opt in enumerate(options[:4]):
            ts = 1.15 + i * 0.42
            op = _p(t, ts, 0.38)
            xo = int(55 * (1 - _eo(max(0, (t - ts) / 0.38))))
            oy = opt_y + i * 70
            _box(d, [(50 + xo, oy), (W - 50 + xo, oy + 58)], opt_bg[i], op * 0.92, radius=8)
            _box(d, [(60 + xo, oy + 10), (92 + xo, oy + 44)], OG, op, radius=16)
            _txt(d, "ABCD"[i], 70 + xo, oy + 14, f_lbl, WH, op)
            opt_text = _wrap(opt, f_opt, W - 210)
            _txt(d, opt_text[0][:65], 104 + xo, oy + 17, f_opt, WH, op)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_answer_scene(
    options: list[str],
    correct_option: str,
    explanation: str = "",
    duration: float | None = None,
) -> VideoClip:
    f_hdr = _f(22, bold=True)
    f_opt = _f(24)
    f_exp = _f(23)
    f_lbl = _f(20, bold=True)

    correct_idx = max(0, "ABCD".find(correct_option.upper()[:1]))
    exp_lines = _wrap(explanation, f_exp, W - 170) if explanation else []
    if duration is None:
        duration = max(5.5, min(4.5 + len(exp_lines) * 1.0, 13.0))

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t)

        # Header badge
        hp = _p(t, 0.1, 0.45)
        _box(d, [(50, 45), (310, 78)], GRD, hp, radius=8)
        _txt(d, "✓  DOĞRU CEVAP", 68, 52, f_hdr, WH, hp)

        # Options
        for i, opt in enumerate(options[:4]):
            op = _p(t, 0.3 + i * 0.1, 0.42)
            oy = 100 + i * 70
            is_c = (i == correct_idx)
            bg  = GRD if is_c else (28, 26, 24)
            _box(d, [(50, oy), (W - 50, oy + 56)], bg, op * 0.9, radius=8)

            # Pulse glow on correct answer
            if is_c and t > 0.5:
                pulse = 0.10 + 0.06 * abs(float(np.sin(t * 3.0)))
                _box(d, [(44, oy - 4), (W - 44, oy + 60)], GR, pulse, radius=10)

            lbl_color = GR if is_c else DG
            _box(d, [(60, oy + 9), (92, oy + 43)], lbl_color, op, radius=16)
            _txt(d, "ABCD"[i], 70, oy + 13, f_lbl, WH, op)

            txt_color = WH if is_c else DG
            prefix = "✓  " if is_c else ""
            _txt(d, f"{prefix}{opt[:62]}", 104, oy + 16, f_opt, txt_color, op)

        # Explanation box
        if exp_lines:
            ey = 100 + 4 * 70 + 14
            ep = _p(t, 1.0, 0.45)
            exp_h = len(exp_lines) * (_th(f_exp) + 8) + 24
            _box(d, [(50, ey), (W - 50, ey + exp_h)], SURF, ep * 0.85, radius=8)
            for i, line in enumerate(exp_lines):
                _txt(d, line, 68, ey + 12 + i * (_th(f_exp) + 8), f_exp, LG, ep)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_exam_tip_scene(tip: str, duration: float = 5.0) -> VideoClip:
    f_hdr = _f(22, bold=True)
    f_tip = _f(26)
    tip_lines = _wrap(tip, f_tip, W - 190)

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t)

        # Orange header bar
        hp = _p(t, 0.2, 0.5)
        _box(d, [(50, 80), (W - 50, 128)], OG, hp * 0.95, radius=8)
        label = "⚡  SINAV PÜF NOKTASI"
        _txt(d, label, _cx(label, f_hdr), 94, f_hdr, WH, hp)

        # Tip lines — staggered
        cy = 158
        lh = _th(f_tip) + 16
        for i, line in enumerate(tip_lines):
            lp = _p(t, 0.65 + i * 0.28, 0.38)
            yo = int(12 * (1 - _eo(max(0, (t - 0.65 - i * 0.28) / 0.38))))
            _txt(d, line, 76, cy + yo, f_tip, WH, lp)
            cy += lh

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_summary_scene(
    title: str,
    rows: list[dict],
    duration: float | None = None,
) -> VideoClip:
    f_t   = _f(34, bold=True)
    f_lbl = _f(22, bold=True)
    f_val = _f(22)

    if duration is None:
        duration = max(5.0, min(3.0 + len(rows) * 0.9, 12.0))

    row_h, row_gap = 54, 4

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t)

        tp = _p(t, 0.2, 0.45)
        _txt(d, title, _cx(title, f_t), 68, f_t, WH, tp)
        # Underline
        uw = int((_tw(title, f_t) + 16) * tp)
        ux = _cx(title, f_t) - 8
        _box(d, [(ux, 116), (ux + uw, 119)], OG, 0.85 * tp)

        table_y = 132
        for i, row in enumerate(rows):
            rp = _p(t, 0.5 + i * 0.28, 0.35)
            ry = table_y + i * (row_h + row_gap)
            bg = SURF if i % 2 == 0 else SURF2
            _box(d, [(50, ry), (W - 50, ry + row_h)], bg, rp * 0.9, radius=6)
            _txt(d, str(row.get("label", ""))[:38], 68, ry + 15, f_lbl, OG, rp)
            _txt(d, str(row.get("value", ""))[:55], W//2 + 20, ry + 15, f_val, WH, rp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_cta_scene(duration: float = 4.0) -> VideoClip:
    f_main = _f(40, bold=True)
    f_url  = _f(26)
    f_sub  = _f(24)
    main_t = "Beğen  ·  Abone Ol  ·  Kaydet"
    url_t  = "adimmusavir.com"
    sub_t  = "Her gün yeni SMMM içerikleri"

    def frame(t):
        base, ov, d = _frame_start()

        # Pulsing orange glow bg
        glow = 0.04 + 0.02 * abs(float(np.sin(t * 2.0)))
        _box(d, [(0, 0), (W, H)], OG, glow)

        # Brand
        _brand(d, t, 0.0)

        mp = _p(t, 0.25, 0.55)
        _txt(d, main_t, _cx(main_t, f_main), H//2 - 70, f_main, WH, mp)

        up = _p(t, 0.65, 0.4)
        _txt(d, url_t, _cx(url_t, f_url), H//2 + 22, f_url, OG, up)

        sp = _p(t, 0.95, 0.4)
        _txt(d, sub_t, _cx(sub_t, f_sub), H//2 + 72, f_sub, LG, sp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


def render_shorts_scene(
    title: str = "",
    hook: str = "",
    content: str = "",
    duration: float = 4.5,
) -> VideoClip:
    f_hook = _f(42, bold=True)
    f_body = _f(28)
    f_br   = _f(18)
    hook_lines = _wrap(hook or title, f_hook, W - 130)
    body_lines = _wrap(content, f_body, W - 130) if content else []

    def frame(t):
        base, ov, d = _frame_start()
        _brand(d, t)
        _box(d, [(0, 0), (W, 6)],  OG, _p(t, 0.1, 0.35))
        _box(d, [(0, H - 6), (W, H)], OG, _p(t, 0.1, 0.35))

        lines = hook_lines if not content else body_lines
        font  = f_hook if not content else f_body
        block_h = len(lines) * (_th(font) + 12)
        sy = H//2 - block_h//2

        for i, line in enumerate(lines):
            lp = _p(t, 0.2 + i * 0.22, 0.4)
            yo = int(18 * (1 - _eo(max(0, (t - 0.2 - i * 0.22) / 0.4))))
            _txt(d, line, _cx(line, font), sy + i * (_th(font) + 12) + yo, font, WH, lp)

        return _composite(base, ov)

    return VideoClip(frame, duration=duration).set_fps(FPS)


# ══════════════════════════════════════════════════════════════
# DISPATCHER
# ══════════════════════════════════════════════════════════════

def render_scene(scene: dict, scene_num: int = 1, total_scenes: int = 1) -> VideoClip:
    stype = scene.get("type", "content")
    dur   = scene.get("duration")

    if stype == "intro":
        return render_intro_scene(scene.get("title", ""), scene.get("subtitle", ""), dur or 5.0)

    elif stype == "content":
        text  = scene.get("content") or scene.get("text", "")
        lines = scene.get("lines") or ([text] if text else [""])
        return render_content_scene(scene.get("title", ""), lines, scene_num, total_scenes, dur)

    elif stype == "question":
        return render_question_scene(scene.get("question_text", ""), scene.get("options", []), dur)

    elif stype == "answer":
        return render_answer_scene(
            scene.get("options", []),
            scene.get("correct_option", "A"),
            scene.get("explanation", ""),
            dur,
        )
    elif stype == "exam_tip":
        return render_exam_tip_scene(scene.get("tip", ""), dur or 5.0)

    elif stype == "summary":
        return render_summary_scene(scene.get("title", "Özet"), scene.get("rows", []), dur)

    elif stype == "cta":
        return render_cta_scene(dur or 4.0)

    elif stype == "shorts":
        return render_shorts_scene(
            scene.get("title", ""), scene.get("hook", ""), scene.get("content", ""), dur or 4.5
        )
    else:
        text  = scene.get("content") or scene.get("text", "")
        lines = scene.get("lines") or ([text] if text else [""])
        return render_content_scene(scene.get("title", ""), lines, scene_num, total_scenes, dur)
