# Tangela e Tangrowth Candyan: o licoroot da Candy Cavity, de alcaçuz.
# - Os cipós azuis viram alcaçuz preto-roxo, com os tons do próprio licoroot do Alex's Caves e uma faixa mais clara em
#   diagonal (o alcaçuz torcido). Mantém a luz e a sombra do original.
# - O vermelho (pés da Tangela, mãos e pés do Tangrowth) vira alcaçuz vermelho, de morango.
# - O escuro de dentro e os olhos ficam como no original.
# - Shiny: invertido, cipós de alcaçuz vermelho e o que era vermelho em alcaçuz preto.
#   /pokespawn tangela candyan
#
# Uso: python candyan_tangela.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
import colorsys
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import luma, save_preview  # noqa: E402

SPECIES = {"tangela": "0114_tangela", "tangrowth": "0465_tangrowth"}
RED_LICORICE = [(92, 6, 22), (150, 12, 34), (205, 28, 48), (240, 66, 80), (255, 130, 140)]
TWIST = 5   # a faixa clara do alcaçuz torcido: uma diagonal a cada TWIST pixels


def licoroot_tones(ac):
    img = Image.open(BytesIO(ac.read("assets/alexscaves/textures/block/licoroot/licoroot_vine.png"))).convert("RGBA")
    tones = sorted({p[:3] for p in img.getdata() if p[3] and p[:3] != (0, 0, 0)}, key=lambda c: luma(c + (255,)))
    return tones + [(150, 60, 175)]  # um brilho no alto, para o alcaçuz não ficar chapado


def tone(tones, t):
    t = max(0.0, min(1.0, t)) * (len(tones) - 1)
    i = min(int(t), len(tones) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(tones[i], tones[i + 1]))


def kind(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s > 0.3 and 0.5 < h < 0.75 and v > 0.2:
        return "vine"
    if s > 0.3 and (h > 0.9 or h < 0.06) and v > 0.25:
        return "red"
    return None


def paint(texture, vine_tones, red_tones):
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()
    ranges = {}
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] and (k := kind(*sp[x, y][:3])):
                l = luma(sp[x, y])
                lo, hi = ranges.get(k, (l, l))
                ranges[k] = (min(lo, l), max(hi, l))
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            k = kind(r, g, b) if a else None
            if not k:
                continue
            lo, hi = ranges[k]
            t = (luma(sp[x, y]) - lo) / (hi - lo) if hi > lo else 0.5
            if (x + y) % TWIST == 0:
                t = min(1.0, t + 0.3)   # a faixa do alcaçuz torcido
            op[x, y] = tone(vine_tones if k == "vine" else red_tones, t) + (a,)
    return out


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    black = licoroot_tones(ac)
    import json
    for species, folder in SPECIES.items():
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{species}.png")))
        normal = paint(texture, black, RED_LICORICE)
        shiny = paint(texture, RED_LICORICE, black)
        out = resources / f"assets/ecosystems_hollows/textures/pokemon/{species}"
        out.mkdir(parents=True, exist_ok=True)
        normal.save(out / f"{species}_candyan.png")
        shiny.save(out / f"{species}_candyan_shiny.png")
        tex = f"ecosystems_hollows:textures/pokemon/{species}/"
        resolver = {"species": f"cobblemon:{species}", "order": 2, "variations": [
            {"aspects": ["candyan"], "texture": tex + f"{species}_candyan.png"},
            {"aspects": ["candyan", "shiny"], "texture": tex + f"{species}_candyan_shiny.png"},
        ]}
        path = resources / f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/2_ecosystems_hollows_candyan.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
        if preview:
            save_preview(preview, f"{species}_candyan", texture, [normal, shiny])


if __name__ == "__main__":
    main()
