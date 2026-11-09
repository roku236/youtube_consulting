"""9:16 promo renderer: PIL frames piped to ffmpeg.
usage: python render.py timeline.json out.mp4 [--preview t1,t2,...]
"""
import json, math, subprocess, sys, os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(ROOT)
IMG = os.path.join(SP, "dl", "img")
GEN = os.path.join(ROOT, "gen")

F_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
F_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
F_MED = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
F_SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
JP = 0  # ttc index: 0 = JP

CREAM = (250, 242, 228)
INK = (24, 18, 14)
RED = (226, 64, 43)
YEL = (255, 201, 60)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_cubic(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ease_out_back(x, s=1.6):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

def ease_in_out(x):
    x = clamp(x); return 3 * x * x - 2 * x * x * x

def prog(t, start, dur):
    return clamp((t - start) / dur)


# ---------- assets ----------
@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size, index=JP)

@lru_cache(None)
def load(path):
    im = Image.open(path).convert("RGB")
    return im

def src(name):
    if name.startswith("gen:"):
        return os.path.join(GEN, name[4:] + ".jpg")
    return os.path.join(IMG, name + ".jpg")

@lru_cache(None)
def bg_base(name):
    """blurred, darkened cover-fit background at 1.15x frame size"""
    im = load(src(name))
    bw, bh = int(W * 1.15), int(H * 1.15)
    sc = max(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.BICUBIC)
    l = (im.width - bw) // 2; t = (im.height - bh) // 2
    im = im.crop((l, t, l + bw, t + bh))
    im = im.filter(ImageFilter.GaussianBlur(38))
    im = ImageEnhance.Brightness(im).enhance(0.42)
    im = ImageEnhance.Color(im).enhance(1.15)
    return im

@lru_cache(None)
def vignette():
    v = Image.new("L", (W // 4, H // 4), 0)
    d = ImageDraw.Draw(v)
    for i in range(60):
        a = int(255 * (i / 60) ** 1.8)
        d.ellipse((-W // 8 + i * 2, -H // 8 + i * 3, W // 4 + W // 8 - i * 2, H // 4 + H // 8 - i * 3), fill=a)
    v = v.filter(ImageFilter.GaussianBlur(20)).resize((W, H), Image.BICUBIC)
    return v  # 255 = keep, 0 = darken

@lru_cache(None)
def card_src(name, w, h):
    """image fitted to exactly w x h (aspect kept by caller), slightly oversized for ken burns"""
    im = load(src(name))
    return im

def rounded_mask(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=255)
    return m.resize((w, h), Image.LANCZOS)

@lru_cache(None)
def mask_c(w, h, r):
    return rounded_mask(w, h, r)

@lru_cache(None)
def shadow_c(w, h, r, blur):
    pad = blur * 3
    s = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    ImageDraw.Draw(s).rounded_rectangle((pad, pad + blur // 2, pad + w, pad + h + blur // 2), r, fill=170)
    return s.filter(ImageFilter.GaussianBlur(blur)), pad


def card_frame(name, w, kb, focus=(0.5, 0.5)):
    """returns card image (w x h) with ken-burns zoom kb (1.0..)"""
    im = load(src(name))
    h = round(w * im.height / im.width)
    # source crop for zoom
    cw, ch = im.width / kb, im.height / kb
    fx, fy = focus
    l = (im.width - cw) * fx; t = (im.height - ch) * fy
    out = im.resize((w, h), Image.LANCZOS, box=(l, t, l + cw, t + ch))
    return out


def paste_card(canvas, name, cx, cy, w, t_in, t, kb, alpha=1.0, r=30, focus=(0.5, 0.5), rise=70, scale_from=0.94, border=True):
    p = ease_out_cubic(prog(t, t_in, 0.45))
    if p <= 0: return None
    im = card_frame(name, w, kb, focus)
    h = im.height
    s = scale_from + (1 - scale_from) * p
    if abs(s - 1) > 1e-3:
        im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.BICUBIC)
    ww, hh = im.size
    x = round(cx - ww / 2); y = round(cy - hh / 2 + (1 - p) * rise)
    a = p * alpha
    sh, pad = shadow_c(ww, hh, r, 26)
    canvas.paste(INK, (x - pad, y - pad), sh.point(lambda v: int(v * a)))
    if border:
        bm = mask_c(ww + 8, hh + 8, r + 4).point(lambda v: int(v * a * 0.9))
        canvas.paste(CREAM, (x - 4, y - 4), bm)
    m = mask_c(ww, hh, r)
    if a < 1: m = m.point(lambda v: int(v * a))
    canvas.paste(im, (x, y), m)
    return (x, y, ww, hh)


# ---------- text ----------
def text_size(txt, f, tracking=0):
    w = 0
    for ch in txt:
        w += f.getlength(ch) + tracking
    return w - tracking if txt else 0

def draw_text_layer(txt, f, fill, tracking=0, stroke=0, stroke_fill=None):
    asc, desc = f.getmetrics()
    tw = int(math.ceil(text_size(txt, f, tracking))) + stroke * 2 + 4
    th = asc + desc + stroke * 2 + 4
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = stroke + 2
    for ch in txt:
        d.text((x, stroke + 2), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(ch) + tracking
    return layer

@lru_cache(None)
def text_img(txt, fpath, size, fill, tracking=0, shadow=True):
    f = font(fpath, size)
    layer = draw_text_layer(txt, f, fill + (255,), tracking)
    if not shadow:
        return layer
    pad = max(8, size // 6)
    out = Image.new("RGBA", (layer.width + pad * 2, layer.height + pad * 2), (0, 0, 0, 0))
    a = layer.split()[3]
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh_a = Image.new("L", out.size, 0); sh_a.paste(a, (pad, pad + max(2, size // 28)))
    sh_a = sh_a.filter(ImageFilter.GaussianBlur(max(3, size // 14))).point(lambda v: int(v * 0.75))
    sh.putalpha(sh_a)
    out = Image.alpha_composite(sh, out)
    out.alpha_composite(layer, (pad, pad))
    out.info["pad"] = pad
    return out

def place_text(canvas, txt, fpath, size, fill, x, y, t, t_in, anchor="c", tracking=0, dur=0.42, mode="rise", alpha=1.0):
    """mode rise: masked slide-up reveal. pop: scale with overshoot."""
    im = text_img(txt, fpath, size, fill, tracking)
    pad = im.info.get("pad", 0)
    p = prog(t, t_in, dur)
    if p <= 0: return
    w, h = im.size
    if anchor == "c": x0 = x - w / 2
    elif anchor == "l": x0 = x - pad
    else: x0 = x - w + pad
    y0 = y - pad
    if mode == "rise":
        e = ease_out_cubic(p)
        off = (1 - e) * h * 0.85
        # clip to the text box so it rises from an invisible baseline
        crop_h = h
        piece = im.crop((0, 0, w, crop_h))
        clip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        clip.alpha_composite(piece, (0, int(off)))
        a = clip.split()[3].point(lambda v: int(v * min(1, e * 1.4) * alpha))
        clip.putalpha(a)
        canvas.alpha_composite(clip, (int(x0), int(y0)))
    elif mode == "pop":
        e = ease_out_back(p, 1.9)
        s = 0.55 + 0.45 * e
        nw, nh = max(1, int(w * s)), max(1, int(h * s))
        r = im.resize((nw, nh), Image.BICUBIC)
        a = r.split()[3].point(lambda v: int(v * min(1, p * 2.5) * alpha)); r.putalpha(a)
        cx = x0 + w / 2; cy = y0 + h / 2
        canvas.alpha_composite(r, (int(cx - nw / 2), int(cy - nh / 2)))
    else:  # fade
        e = ease_out_cubic(p)
        r = im.copy(); a = r.split()[3].point(lambda v: int(v * e * alpha)); r.putalpha(a)
        canvas.alpha_composite(r, (int(x0), int(y0 + (1 - e) * 16)))


def chip(canvas, txt, x, y, t, t_in, size=46, fg=CREAM, bg=RED, anchor="c", padx=26, pady=10, fpath=F_BOLD, alpha=1.0):
    f = font(fpath, size)
    tw = text_size(txt, f, 2)
    asc, desc = f.getmetrics()
    bw = int(tw + padx * 2); bh = int(size * 1.0 + pady * 2)
    p = ease_out_cubic(prog(t, t_in, 0.38))
    if p <= 0: return
    if anchor == "c": x0 = x - bw / 2
    elif anchor == "l": x0 = x
    else: x0 = x - bw
    # wipe from left
    vis = int(bw * p)
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), bh // 2 if bh < 80 else 18, fill=bg + (255,))
    tl = draw_text_layer(txt, f, fg + (255,), 2)
    # vertically center using the font's em box
    ty = (bh - (asc + desc)) // 2 - 2
    layer.alpha_composite(tl, (padx - 2, max(0, ty)))
    m = Image.new("L", (bw, bh), 0); ImageDraw.Draw(m).rectangle((0, 0, vis, bh), fill=255)
    a = ImageChops.multiply(layer.split()[3], m).point(lambda v: int(v * alpha))
    layer.putalpha(a)
    canvas.alpha_composite(layer, (int(x0), int(y)))
    return bw, bh


def rule(canvas, x, y, w, t, t_in, color=CREAM, thick=4, alpha=1.0, anchor="c"):
    p = ease_out_cubic(prog(t, t_in, 0.5))
    if p <= 0: return
    ww = int(w * p)
    x0 = x - ww / 2 if anchor == "c" else x
    d = ImageDraw.Draw(canvas)
    d.rectangle((x0, y, x0 + ww, y + thick), fill=color + (int(255 * alpha),))


# ---------- scenes ----------
def scene_intro(c, t, d, q):  # interior
    kb = 1.0 + 0.07 * ease_in_out(t / d)
    chip(c, "横浜駅前の大衆酒場", W / 2, 330, t, q["a"], size=50)
    paste_card(c, "01_owner", W / 2, 1060, 960, 0.0, t, kb)
    place_text(c, "西口商店", F_SERIF, 210, CREAM, W / 2, 420, t, q["name"], tracking=10, mode="pop", dur=0.5)
    place_text(c, "もつ鍋 × 食べ飲み放題", F_BOLD, 50, CREAM, W / 2, 1378, t, q["name"] + 0.25, tracking=4)
    place_text(c, "【旧店名】横浜大衆酒場 いちばん", F_MED, 32, (210, 198, 180), W / 2, 1452, t, q["name"] + 0.4, tracking=2, mode="fade")


def scene_price(c, t, d, q):  # 198 yen
    kb = 1.0 + 0.07 * ease_in_out(t / d)
    chip(c, "19時までのご来店で", W / 2, 250, t, q["a"], size=50)
    place_text(c, "生ビールも ハイボールも", F_BLACK, 76, CREAM, W / 2, 345, t, q["h"], tracking=2)
    p_in = q["p"]
    big = text_img("198", F_BLACK, 320, YEL, -8)
    yen = text_img("円", F_BLACK, 130, YEL, 0)
    total = big.width + yen.width - big.info["pad"] * 2 - yen.info["pad"] * 2 + 6
    x0 = W / 2 - total / 2
    place_text(c, "198", F_BLACK, 320, YEL, x0, 440, t, p_in, anchor="l", tracking=-8, mode="pop", dur=0.5)
    place_text(c, "円", F_BLACK, 130, YEL, x0 + big.width - big.info["pad"] * 2 + 6, 622, t, p_in + 0.1, anchor="l", mode="pop", dur=0.45)
    paste_card(c, "02_owner", W / 2, 1120, 920, 0.0, t, kb)
    place_text(c, "生ビール・サワー・カクテル・ハイボール・ソフトドリンク", F_MED, 32, (225, 212, 194), W / 2, 1400, t, q["h"] + 0.3, mode="fade")
    place_text(c, "※19時までのご来店で全品198円", F_MED, 30, (200, 186, 168), W / 2, 1448, t, q["h"] + 0.4, mode="fade")


def scene_menu(c, t, d, q):  # motsunabe + korean
    kb = 1.0 + 0.06 * ease_in_out(t / d)
    t_sub = q["sub"]
    chip(c, "名物", W / 2, 210, t, q["a"], size=46)
    place_text(c, "もつ鍋", F_BLACK, 168, CREAM, W / 2, 280, t, q["a"] + 0.1, tracking=8)
    paste_card(c, "10_owner", W / 2, 790, 960, 0.0, t, kb, focus=(0.6, 0.5))
    place_text(c, "チヂミ・キムチも大人気！", F_BLACK, 64, YEL, W / 2, 1090, t, t_sub - 0.05, tracking=2)
    z = 1.0 + 0.05 * prog(t, t_sub, 3)
    r1 = paste_card(c, "gen:23", 290, 1365, 450, t_sub + 0.0, t, z, r=24, rise=90)
    r2 = paste_card(c, "gen:24", 790, 1365, 450, t_sub + 0.12, t, z, r=24, rise=90)
    if r1: chip(c, "チヂミ", r1[0] + 18, r1[1] + r1[3] - 74, t, t_sub + 0.3, size=34, bg=INK, anchor="l", padx=18, pady=8)
    if r2: chip(c, "キムチ", r2[0] + 18, r2[1] + r2[3] - 74, t, t_sub + 0.4, size=34, bg=INK, anchor="l", padx=18, pady=8)


def scene_party(c, t, d, q):  # tabe-nomi-houdai
    kb = 1.0 + 0.07 * ease_in_out(t / d)
    place_text(c, "食べ飲み放題", F_BLACK, 150, CREAM, W / 2, 250, t, q["a"], tracking=4)
    rule(c, W / 2, 470, 520, t, q["a"] + 0.3, color=RED, thick=8)
    place_text(c, "宴会もおまかせ！", F_BLACK, 76, YEL, W / 2, 505, t, q["e"], tracking=3)
    paste_card(c, "14_owner", W / 2, 940, 960, 0.0, t, kb)
    z = 1.0 + 0.05 * prog(t, q["e"], 3)
    paste_card(c, "08_owner", 300, 1345, 420, q["e"] - 0.1, t, z, r=24, rise=90)
    paste_card(c, "gen:28", 780, 1345, 420, q["e"] + 0.02, t, z, r=24, rise=90)


def scene_end(c, t, d, q):
    kb = 1.0 + 0.06 * ease_in_out(t / d)
    t_end = q["info"]
    place_text(c, "今夜は西口商店で", F_BOLD, 58, CREAM, W / 2, 205, t, q["a"], tracking=3)
    place_text(c, "かんぱーい！", F_BLACK, 150, YEL, W / 2, 283, t, q["k"], tracking=2, mode="pop", dur=0.5)
    paste_card(c, "gen:22", W / 2, 915, 600, 0.0, t, kb, focus=(0.5, 0.45))
    y0 = 1352
    rule(c, W / 2, y0, 760, t, t_end, color=(250, 242, 228), thick=2, alpha=0.6)
    place_text(c, "西口商店 横浜駅前店", F_SERIF, 66, CREAM, W / 2, y0 + 22, t, t_end + 0.1, tracking=4)
    place_text(c, "最寄り駅：平沼橋駅　｜　予算 ¥3,000〜¥3,999", F_MED, 34, (230, 218, 200), W / 2, y0 + 128, t, t_end + 0.25, mode="fade")
    place_text(c, "※価格・内容は変更になる場合があります", F_MED, 26, (190, 176, 160), W / 2, y0 + 186, t, t_end + 0.35, mode="fade")


SCENES = dict(intro=scene_intro, price=scene_price, menu=scene_menu, party=scene_party, end=scene_end)


# ---------- compositor ----------
def make_frame(tl, t):
    scenes = tl["scenes"]
    idx = 0
    for i, s in enumerate(scenes):
        if t >= s["start"]: idx = i
    s = scenes[idx]
    lt = t - s["start"]
    d = s["end"] - s["start"]
    # background (crossfade with previous scene for XF seconds)
    XF = 0.22
    def bg_for(sc, tt):
        b = bg_base(sc["bg"])
        z = 1.0 + 0.05 * (tt / (sc["end"] - sc["start"]))
        bw, bh = b.size
        cw, ch = bw / z / 1.0, bh / z / 1.0
        cw, ch = W * (bw / W) / z, H * (bh / H) / z
        l = (bw - cw) / 2; tp = (bh - ch) / 2
        return b.resize((W, H), Image.BILINEAR, box=(l, tp, l + cw, tp + ch))
    bg = bg_for(s, lt)
    if idx > 0 and lt < XF:
        prev = scenes[idx - 1]
        bg = Image.blend(bg_for(prev, t - prev["start"]), bg, ease_in_out(lt / XF))
    dark = Image.new("RGB", (W, H), (10, 7, 5))
    bg = Image.composite(bg, dark, vignette())
    canvas = bg.convert("RGBA")
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENES[s["kind"]](fg, lt, d, s["q"])
    dy = s.get("dy", 0)
    if dy:
        fg = fg.transform(fg.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy), Image.BILINEAR)
    # scene exit: quick fade+lift of foreground in the last 0.16s (not for final scene)
    EX = 0.16
    if idx < len(scenes) - 1 and d - lt < EX:
        e = ease_in_out((EX - (d - lt)) / EX)
        a = fg.split()[3].point(lambda v: int(v * (1 - e)))
        fg.putalpha(a)
        fg = fg.transform(fg.size, Image.AFFINE, (1, 0, 0, 0, 1, 40 * e), Image.BILINEAR)
    canvas.alpha_composite(fg)
    # global fade-in from black at very start
    if t < 0.12:
        canvas = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), canvas, t / 0.12)
    return canvas.convert("RGB")


def main():
    tl = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == "--preview":
        ts = [float(x) for x in sys.argv[4].split(",")]
        for t in ts:
            make_frame(tl, t).save(f"{out}_{t:05.2f}.jpg", quality=88)
        return
    dur = tl["duration"]
    n = int(round(dur * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", tl["audio"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(make_frame(tl, i / FPS).tobytes())
        if i % 60 == 0: print("frame", i, "/", n, flush=True)
    p.stdin.close(); p.wait()
    print("done", out)


if __name__ == "__main__":
    main()
