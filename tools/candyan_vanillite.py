# Vanillite, Vanillish e Vanilluxe Candyan: sorvetes da Candy Cavity, nos sabores dela.
#   baunilha (vanilla), chocolate, sweetberry e frostmint (menta gelada)
# - O creme (lilás-claro no original) vira o sorvete do sabor, com os tons dos blocos de sorvete do Alex's Caves, e
#   ganha confeitos (as cores dos sprinkles de lá) espalhados.
# - O gelo (azul) vira casquinha de wafer, com os tons do wafer_cookie_block e a grade da casquinha.
# - Olhos, boca e o resto do rosto ficam como no original.
# - Shiny: casquinha de chocolate e muito mais confeitos.
# A luz e a sombra vêm do original, esticadas nos tons de cada parte.
#   /pokespawn vanillite candyan aspect=candyan_chocolate
#
# Uso: python candyan_vanillite.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
import colorsys
import json
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import bone_colors, luma, save_preview  # noqa: E402

SPECIES = {"vanillite": "0582_vanillite", "vanillish": "0583_vanillish", "vanilluxe": "0584_vanilluxe"}
FLAVORS = {"vanilla": "vanilla_ice_cream", "chocolate": "chocolate_ice_cream",
           "sweetberry": "sweetberry_ice_cream", "frostmint": "frostmint"}
FACE = ("eye", "pupil", "mouth", "nose", "eyebrow", "eyelid")
SPRINKLES = 0.05          # parte do creme com confeito
SHINY_SPRINKLES = 0.16
GRID = 4                  # a grade da casquinha: uma linha a cada GRID pixels
CHOCOLATE_CONE = [(70, 40, 30), (95, 58, 42), (120, 76, 54), (149, 96, 73), (170, 118, 86)]


def tones(ac, name):
    img = Image.open(BytesIO(ac.read(f"assets/alexscaves/textures/block/{name}.png"))).convert("RGBA")
    return sorted({p[:3] for p in img.getdata() if p[3]}, key=lambda c: luma(c + (255,)))


def sprinkle_colors(ac):
    colors = set()
    for i in range(4):
        img = Image.open(BytesIO(ac.read(f"assets/alexscaves/textures/block/sprinkles_{i}.png"))).convert("RGBA")
        colors |= {p[:3] for p in img.getdata() if p[3] and max(p[:3]) - min(p[:3]) > 80}
    return sorted(colors)


def tone(ts, t):
    t = max(0.0, min(1.0, t)) * (len(ts) - 1)
    i = min(int(t), len(ts) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(ts[i], ts[i + 1]))


def noise(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFF) / 0xFFFF


def kind(px, bone):
    if bone.startswith(FACE):
        return None
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in px[:3]))
    if v < 0.35:
        return None                      # escuros: detalhes do rosto
    if 0.5 < h < 0.72 and s > 0.22:
        return "ice"
    if s < 0.22 and v > 0.6:
        return "cream"
    return None


def paint(texture, owner, cream, cone, sprinkles, amount):
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()
    kinds = {}
    ranges = {}
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] and (k := kind(sp[x, y], owner[y][x] or "")):
                kinds[(x, y)] = k
                l = luma(sp[x, y])
                lo, hi = ranges.get(k, (l, l))
                ranges[k] = (min(lo, l), max(hi, l))
    for (x, y), k in kinds.items():
        lo, hi = ranges[k]
        t = (luma(sp[x, y]) - lo) / (hi - lo) if hi > lo else 0.6
        if k == "cream":
            if noise(x, y) < amount:
                c = sprinkles[int(noise(x, y, 3) * len(sprinkles)) % len(sprinkles)]
            else:
                c = tone(cream, 0.25 + 0.75 * t)
        else:
            if x % GRID == 0 or y % GRID == 0:
                t *= 0.5                 # a linha da grade da casquinha
            c = tone(cone, t)
        op[x, y] = c + (sp[x, y][3],)
    return out


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    wafer = tones(ac, "wafer_cookie_block")
    sprinkles = sprinkle_colors(ac)
    flavor_tones = {f: tones(ac, block) for f, block in FLAVORS.items()}
    for species, folder in SPECIES.items():
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{species}.png")))
        geo = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{species}.geo.json"))["minecraft:geometry"][0]
        owner = bone_colors(geo, texture.width, texture.height, {b["name"]: b["name"] for b in geo["bones"]})
        out = resources / f"assets/ecosystems_hollows/textures/pokemon/{species}"
        out.mkdir(parents=True, exist_ok=True)
        tex = f"ecosystems_hollows:textures/pokemon/{species}/"
        variations = [{"aspects": ["candyan"], "texture": tex + f"{species}_candyan_vanilla.png"}]
        shiny_variations = []
        previews = []
        for flavor, cream in flavor_tones.items():
            normal = paint(texture, owner, cream, wafer, sprinkles, SPRINKLES)
            shiny = paint(texture, owner, cream, CHOCOLATE_CONE, sprinkles, SHINY_SPRINKLES)
            normal.save(out / f"{species}_candyan_{flavor}.png")
            shiny.save(out / f"{species}_candyan_{flavor}_shiny.png")
            previews += [normal, shiny]
            variations.append({"aspects": ["candyan", f"candyan_{flavor}"], "texture": tex + f"{species}_candyan_{flavor}.png"})
            shiny_variations.append({"aspects": ["candyan", "shiny", f"candyan_{flavor}"],
                                     "texture": tex + f"{species}_candyan_{flavor}_shiny.png"})
        resolver = {"species": f"cobblemon:{species}", "order": 2, "variations": variations + shiny_variations}
        path = resources / f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/2_ecosystems_hollows_candyan.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
        if preview:
            save_preview(preview, f"{species}_candyan", texture, previews[::2])


if __name__ == "__main__":
    main()
