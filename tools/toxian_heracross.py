# Heracross Toxian: a Gammaroach (a barata radioativa da Toxic Caves) feita do Heracross.
# - Modelo próprio (heracross_toxian): sem o chifre grande, e as antenas sem a bolinha da ponta e bem mais longas
#   (finas, como as de barata). As antenas novas usam um canto vazio da textura (ANTENNA_UV).
# - Carapaça com os tons da textura da própria Gammaroach (oliva, caqui e marrom-escuro), mantendo a luz e a sombra do
#   original, e com as faixas dos segmentos (uma linha mais escura a cada BAND linhas no corpo).
# - Olhos verdes que brilham (camada emissiva), como os da Gammaroach.
# - Asas (camada translúcida do Heracross) em âmbar-oliva translúcido.
# - Shiny: o verde neon pulsando dos Toxian (como o Sharpedo e o Carvanha shiny).
#
# Uso: python toxian_heracross.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
import copy
import json
import math
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import bone_colors, box_faces, luma, save_preview  # noqa: E402

SRC = "assets/cobblemon/textures/pokemon/0214_heracross/"
MODEL = "assets/cobblemon/bedrock/pokemon/models/0214_heracross/heracross_male.geo.json"
HORN_BONES = ("horn", "horn2", "horn3", "horn_tip_left", "horn_tip_right")
ANTENNA_LENGTH = 9        # comprimento novo da segunda parte da antena (era 2)
BAND = 3                  # faixas dos segmentos: uma linha escura a cada BAND linhas
EYE_GLOW = [(0, 150, 0), (0, 223, 0), (0, 255, 0)]
# Shiny: verde neon (os mesmos tons do Sharpedo Toxian shiny).
NEON = [(6, 70, 10), (20, 140, 30), (20, 200, 40), (70, 255, 90), (160, 255, 130)]


def tones_of(ac):
    """Os tons da carapaça da Gammaroach, do escuro ao claro."""
    img = Image.open(BytesIO(ac.read("assets/alexscaves/textures/entity/gammaroach.png"))).convert("RGBA")
    counts = {}
    for p in img.getdata():
        if p[3]:
            counts[p[:3]] = counts.get(p[:3], 0) + 1
    common = [c for c, n in sorted(counts.items(), key=lambda kv: -kv[1]) if n >= 20]
    return sorted(common, key=lambda c: luma(c + (255,)))


def tone(tones, t):
    t = max(0.0, min(1.0, t)) * (len(tones) - 1)
    i = min(int(t), len(tones) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(tones[i], tones[i + 1]))


def free_area(img, owner, size):
    w, h = size
    px = img.load()
    for y in range(img.height - h, -1, -1):
        for x in range(img.width - w, -1, -1):
            if all(px[x + i, y + j][3] == 0 and owner[y + j][x + i] is None for i in range(w) for j in range(h)):
                return x, y
    raise ValueError("sem espaço livre na textura")


def toxian_model(geo_json, antenna_uv):
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    geo["description"]["identifier"] = "geometry.heracross_toxian"
    for bone in geo["bones"]:
        name = bone["name"]
        if name in HORN_BONES:
            bone["cubes"] = []                         # o osso fica (as animações usam), sem os cubos
        elif name in ("antenna_left3", "antenna_right3"):
            bone["cubes"] = []                         # sem a bolinha da ponta
        elif name in ("antenna_left2", "antenna_right2"):
            c = bone["cubes"][0]
            end = c["origin"][2] + c["size"][2]        # a base fica onde estava; a antena cresce para a frente (-z)
            c["size"] = [c["size"][0], 0, ANTENNA_LENGTH]
            c["origin"] = [c["origin"][0], c["origin"][1], end - ANTENNA_LENGTH]
            c["uv"] = list(antenna_uv)
    return model


def recolor(src, owner, tones, wings=False):
    """Carapaça nos tons da Gammaroach (ou neon), com faixas; olhos verdes (na camada que brilha)."""
    src = src.convert("RGBA")
    out = src.copy()
    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, op, gp = src.load(), out.load(), glow.load()
    lumas = [luma(sp[x, y]) for y in range(src.height) for x in range(src.width)
             if sp[x, y][3] and not (owner[y][x] or "").startswith("eye")]
    lo, hi = min(lumas), max(lumas)
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            l = luma(sp[x, y])
            bone = owner[y][x] or ""
            if bone.startswith(("eye", "pupil")) and not wings:
                c = tone(EYE_GLOW, l)
                op[x, y] = c + (a,)
                gp[x, y] = c + (255,)
                continue
            t = (l - lo) / (hi - lo) if hi > lo else 0.5
            if bone in ("torso", "shell_left", "shell_right") and y % BAND == BAND - 1:
                t *= 0.55                                # a linha escura entre os segmentos
            op[x, y] = tone(tones, t) + (a,)
    return out, glow


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    texture = Image.open(BytesIO(z.read(SRC + "heracross.png"))).convert("RGBA")
    wings = Image.open(BytesIO(z.read(SRC + "heracross_transparency.png"))).convert("RGBA")
    geo_json = json.loads(z.read(MODEL))
    geo = geo_json["minecraft:geometry"][0]
    owner = bone_colors(geo, texture.width, texture.height, {b["name"]: b["name"] for b in geo["bones"]})
    tones = tones_of(ac)

    antenna_size = (1, 0, ANTENNA_LENGTH)
    uv_w = 2 * antenna_size[2] + 2 * antenna_size[0]
    uv_h = antenna_size[2] + antenna_size[1]
    antenna_uv = free_area(texture, owner, (uv_w, max(uv_h, 1)))

    out = resources / "assets/ecosystems_hollows/textures/pokemon/heracross"
    out.mkdir(parents=True, exist_ok=True)
    tex = "ecosystems_hollows:textures/pokemon/heracross/"
    results = {}
    for name, palette in (("", tones), ("_shiny", NEON)):
        body, glow = recolor(texture, owner, palette)
        # A antena nova: tons do meio da paleta, com a ponta mais clara.
        p = body.load()
        for x0, y0, w, h in box_faces(list(antenna_uv), list(antenna_size)):
            for j in range(h):
                for i in range(w):
                    p[x0 + i, y0 + j] = tone(palette, 0.25 + 0.5 * ((i + j) % 3) / 2) + (255,)
        wing, _ = recolor(wings, [[None] * wings.width for _ in range(wings.height)], palette[1:], wings=True)
        wp = wing.load()
        for y in range(wing.height):
            for x in range(wing.width):
                r, g, b, a = wp[x, y]
                if a:
                    wp[x, y] = (r, g, b, min(a, 150))  # asa translúcida
        body.save(out / f"heracross_toxian{name}.png")
        glow.save(out / f"heracross_toxian{name}_emissive.png")
        wing.save(out / f"heracross_toxian{name}_wings.png")
        results[name] = (body, glow)

    # Shiny: o corpo pulsa de brilho, como o Sharpedo Toxian shiny.
    frames = []
    shiny = results["_shiny"][0]
    for i in range(8):
        strength = 0.25 + 0.6 * (0.5 - 0.5 * math.cos(2 * math.pi * i / 8))
        frame = results["_shiny"][1].copy()
        fp, sp = frame.load(), shiny.load()
        for y in range(shiny.height):
            for x in range(shiny.width):
                r, g, b, a = sp[x, y]
                if a and g > r and g > b and g > 60 and fp[x, y][3] == 0:
                    fp[x, y] = (r, g, b, int(255 * strength))
        frame.save(out / f"heracross_toxian_shiny_glow_{i}.png")
        frames.append(frame)

    model_path = resources / "assets/ecosystems_hollows/bedrock/pokemon/models/heracross_toxian.geo.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(toxian_model(geo_json, antenna_uv), indent=2) + "\n", encoding="utf-8", newline="\n")

    resolver = {"species": "cobblemon:heracross", "order": 2, "variations": [
        {"aspects": ["toxian"], "model": "ecosystems_hollows:heracross_toxian.geo",
         "texture": tex + "heracross_toxian.png",
         "layers": [{"name": "wings", "translucent": True, "texture": tex + "heracross_toxian_wings.png"},
                    {"name": "emissive", "emissive": True, "texture": tex + "heracross_toxian_emissive.png"}]},
        {"aspects": ["toxian", "shiny"], "texture": tex + "heracross_toxian_shiny.png",
         "layers": [{"name": "wings", "translucent": True, "texture": tex + "heracross_toxian_shiny_wings.png"},
                    {"name": "emissive", "emissive": True, "texture": {
                        "frames": [tex + f"heracross_toxian_shiny_glow_{i}.png" for i in range(8)], "fps": 8, "loop": True}}]},
    ]}
    path = resources / "assets/cobblemon/bedrock/pokemon/resolvers/0214_heracross/2_ecosystems_hollows_toxian.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
    if preview:
        save_preview(preview, "heracross_toxian", texture, [results[""][0], results["_shiny"][0]])


if __name__ == "__main__":
    main()
