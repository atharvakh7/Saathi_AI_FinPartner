"""Draw placeholder mascot poses for Saathi (spec §4.2): a young man in a teal hoodie.

    python scripts/make_mascot.py      -> assets/mascot/{wave,point_up,shield,listening,speaking,thumbs_up,thinking}.png

Flat vector-style art drawn at 4x and downscaled for smooth edges. Replace with designed artwork
any time; file names and the 512x512 transparent canvas are the contract.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "mascot"
S = 4                      # supersampling factor
W = H = 512 * S

TEAL = (14, 93, 102, 255)        # color.primary
TEAL_LIGHT = (27, 163, 156, 255)  # color.primaryLight
TEAL_DARK = (9, 66, 73, 255)
SKIN = (198, 139, 89, 255)
SKIN_SHADE = (176, 118, 72, 255)
HAIR = (38, 30, 28, 255)
WHITE = (255, 255, 255, 255)
INK = (20, 35, 43, 255)          # color.text
CHEEK = (226, 120, 100, 110)
GOLD = (232, 160, 32, 255)       # color.warning
PANTS = (52, 72, 86, 255)


def p(x, y):
    return (x * S, y * S)


def box(x0, y0, x1, y1):
    return [x0 * S, y0 * S, x1 * S, y1 * S]


def limb(d, a, b, width, fill):
    """Thick rounded segment from a to b (sleeve / arm)."""
    d.line([p(*a), p(*b)], fill=fill, width=width * S)
    r = width / 2
    for (x, y) in (a, b):
        d.ellipse(box(x - r, y - r, x + r, y + r), fill=fill)


def hand(d, c, r=17):
    x, y = c
    d.ellipse(box(x - r, y - r, x + r, y + r), fill=SKIN)


def body(d):
    # legs
    d.rounded_rectangle(box(196, 410, 246, 500), radius=20 * S, fill=PANTS)
    d.rounded_rectangle(box(266, 410, 316, 500), radius=20 * S, fill=PANTS)
    d.rounded_rectangle(box(184, 486, 250, 506), radius=10 * S, fill=INK)
    d.rounded_rectangle(box(262, 486, 328, 506), radius=10 * S, fill=INK)
    # hoodie torso
    d.rounded_rectangle(box(166, 262, 346, 432), radius=46 * S, fill=TEAL)
    # pocket + zip line + strings
    d.rounded_rectangle(box(206, 360, 306, 410), radius=18 * S, fill=TEAL_DARK)
    d.line([p(256, 282), p(256, 360)], fill=TEAL_DARK, width=4 * S)
    d.line([p(236, 276), p(232, 318)], fill=WHITE, width=4 * S)
    d.line([p(276, 276), p(280, 318)], fill=WHITE, width=4 * S)
    # hood behind neck
    d.ellipse(box(196, 238, 316, 292), fill=TEAL_LIGHT)
    d.ellipse(box(222, 248, 290, 282), fill=SKIN_SHADE)


def head(d, mouth="smile", eyes="open", look=0):
    # ears
    d.ellipse(box(158, 150, 186, 196), fill=SKIN)
    d.ellipse(box(326, 150, 354, 196), fill=SKIN)
    # face
    d.ellipse(box(170, 84, 342, 256), fill=SKIN)
    # hair: cap of hair + side fringe
    d.chord(box(164, 66, 348, 210), start=180, end=360, fill=HAIR)
    d.pieslice(box(168, 76, 270, 170), start=150, end=330, fill=HAIR)
    d.ellipse(box(250, 78, 340, 132), fill=HAIR)
    # eyes
    ex = look * 4
    for cx in (222, 290):
        if eyes == "closed":
            d.arc(box(cx - 13, 166, cx + 13, 186), start=200, end=340, fill=INK, width=5 * S)
        else:
            d.ellipse(box(cx - 11 + ex, 160, cx + 11 + ex, 186), fill=INK)
            d.ellipse(box(cx - 4 + ex, 164, cx + 3 + ex, 171), fill=WHITE)
    # brows
    d.line([p(208, 146), p(234, 142)], fill=HAIR, width=5 * S)
    d.line([p(278, 142), p(304, 146)], fill=HAIR, width=5 * S)
    # cheeks
    d.ellipse(box(192, 192, 216, 206), fill=CHEEK)
    d.ellipse(box(296, 192, 320, 206), fill=CHEEK)
    # mouth
    if mouth == "smile":
        d.arc(box(226, 190, 286, 228), start=20, end=160, fill=INK, width=6 * S)
    elif mouth == "open":
        d.chord(box(230, 198, 282, 236), start=0, end=180, fill=INK)
        d.chord(box(240, 216, 272, 234), start=0, end=180, fill=(226, 108, 108, 255))
    elif mouth == "hmm":
        d.line([p(238, 214), p(276, 208)], fill=INK, width=6 * S)


def shoulder_arm_down(d, side):
    """Relaxed arm hanging by the body. side: -1 left, +1 right."""
    sx = 256 + side * 82
    limb(d, (sx, 292), (sx + side * 14, 392), 38, TEAL)
    hand(d, (sx + side * 14, 404))


def make(pose: str) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # soft floor shadow
    d.ellipse(box(150, 488, 362, 512), fill=(20, 35, 43, 28))

    if pose == "wave":
        body(d)
        shoulder_arm_down(d, -1)
        limb(d, (338, 292), (396, 214), 38, TEAL)
        hand(d, (408, 196), 20)
        for i, ang in enumerate((-40, -15, 10)):  # motion marks
            a = math.radians(ang)
            x0, y0 = 438 + 6 * math.cos(a), 170 + 26 * math.sin(a) + i * 4
            d.arc(box(x0 - 18, y0 - 18, x0 + 18, y0 + 18), start=300, end=360, fill=TEAL_LIGHT, width=5 * S)
        head(d, "smile")
    elif pose == "point_up":
        body(d)
        shoulder_arm_down(d, -1)
        limb(d, (338, 292), (380, 196), 38, TEAL)
        hand(d, (386, 182), 18)
        d.rounded_rectangle(box(380, 116, 394, 176), radius=7 * S, fill=SKIN)  # index finger
        d.ellipse(box(404, 92, 424, 112), fill=GOLD)  # idea spark
        head(d, "open", look=1)
    elif pose == "shield":
        body(d)
        shoulder_arm_down(d, 1)
        limb(d, (174, 292), (150, 340), 38, TEAL)
        # shield held in front-left
        cx, top = 138, 286
        shield = [p(cx - 64, top), p(cx + 64, top), p(cx + 64, top + 70), p(cx, top + 140), p(cx - 64, top + 70)]
        d.polygon(shield, fill=TEAL_LIGHT, outline=WHITE, width=6 * S)
        d.line([p(cx - 28, top + 62), p(cx - 6, top + 88), p(cx + 32, top + 40)], fill=WHITE, width=12 * S, joint="curve")
        head(d, "smile")
    elif pose == "listening":
        body(d)
        shoulder_arm_down(d, -1)
        limb(d, (338, 292), (352, 196), 38, TEAL)
        hand(d, (346, 176), 19)  # hand cupped at ear
        for i, r in enumerate((26, 44, 62)):
            d.arc(box(372 - r, 172 - r, 372 + r, 172 + r), start=300, end=60, fill=TEAL_LIGHT, width=(6 - i) * S)
        head(d, "smile", look=1)
    elif pose == "speaking":
        body(d)
        shoulder_arm_down(d, -1)
        limb(d, (338, 292), (384, 300), 38, TEAL)
        hand(d, (398, 296), 18)  # open palm explaining
        d.rounded_rectangle(box(372, 70, 488, 140), radius=26 * S, fill=WHITE, outline=TEAL_LIGHT, width=5 * S)
        d.polygon([p(392, 134), p(380, 160), p(414, 138)], fill=WHITE)
        for i, x in enumerate((404, 430, 456)):
            d.ellipse(box(x - 7, 98, x + 7, 112), fill=TEAL)
        head(d, "open")
    elif pose == "thumbs_up":
        body(d)
        shoulder_arm_down(d, -1)
        limb(d, (338, 292), (378, 250), 38, TEAL)
        d.rounded_rectangle(box(366, 216, 410, 262), radius=14 * S, fill=SKIN)  # fist
        d.rounded_rectangle(box(374, 176, 394, 226), radius=10 * S, fill=SKIN)  # thumb
        for ang in (-60, -25, 10):
            a = math.radians(ang)
            d.line([p(430 + 14 * math.cos(a), 200 + 14 * math.sin(a)),
                    p(430 + 40 * math.cos(a), 200 + 40 * math.sin(a))], fill=GOLD, width=6 * S)
        head(d, "smile", eyes="closed")
    elif pose == "thinking":
        body(d)
        shoulder_arm_down(d, -1)
        limb(d, (338, 292), (300, 250), 38, TEAL)
        hand(d, (290, 236), 18)  # hand at chin
        for i, (x, y, r) in enumerate(((356, 104, 8), (380, 78, 12), (418, 50, 18))):
            d.ellipse(box(x - r, y - r, x + r, y + r), fill=TEAL_LIGHT)
        head(d, "hmm", look=1)
    else:
        raise ValueError(pose)
    return img.resize((512, 512), Image.LANCZOS)


POSES = ("wave", "point_up", "shield", "listening", "speaking", "thumbs_up", "thinking")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for pose in POSES:
        make(pose).save(OUT / f"{pose}.png", optimize=True)
    # App icon / splash: the waving mascot on the brand tint.
    icon = Image.new("RGBA", (1024, 1024), (227, 244, 245, 255))
    face = make("wave").resize((880, 880), Image.LANCZOS)
    icon.alpha_composite(face, (72, 96))
    icon.save(OUT.parent / "icon.png", optimize=True)
    fg = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    fg.alpha_composite(make("wave").resize((640, 640), Image.LANCZOS), (192, 200))  # adaptive-icon safe zone
    fg.save(OUT.parent / "android-icon-foreground.png", optimize=True)
    make("wave").resize((400, 400), Image.LANCZOS).save(OUT.parent / "splash-icon.png", optimize=True)
    print("wrote", ", ".join(POSES), "+ icon, adaptive foreground, splash")
