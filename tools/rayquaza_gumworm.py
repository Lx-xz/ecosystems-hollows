# Rayquaza Candyan: o Rayquaza repintado como a Gum Worm de chiclete do Alex's Caves (as listras do Orthworm Candyan).
# Só texturas novas para o modelo do próprio Rayquaza, ligadas ao aspect "candyan" (forma regional Candyan):
#   /pokespawn rayquaza candyan
# - Corpo em listras roxo / amarelo / verde-água; a cabeça verde-água e o fim do rabo todo roxo.
# - Boca por dentro roxa com veias rosa (como a da Gum Worm), dentes amarelo-claros.
# - Olhos amarelos, com a pupila num amarelo um pouco mais escuro (quase não aparece).
# - Os 4 chifres verdes; as marcas douradas e as barbatanas vermelhas viram rosa, como as ligações da Gum Worm.
# - Shiny: chiclete pastel (rosa / azul-claro / branco), com as marcas roxas.
# Uso: python rayquaza_gumworm.py <jar do Cobblemon> <pasta resources do mod> [pasta da prévia]
import colorsys
import json
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import bone_colors, luma_ranges, ramp, save_preview, shade_t  # noqa: E402

SRC = "0384_rayquaza"
# Cores da própria Gum Worm do Alex's Caves (texturas gum_worm e gum_worm_segment_0/1/2), com o amarelo mais amarelo.
NORMAL = {
    "stripes": [(173, 50, 244), (255, 214, 50), (24, 229, 181)],  # roxo, amarelo, verde-água
    "head": (21, 243, 184),
    "tail": (173, 50, 244),          # o fim do rabo, todo roxo
    "horn": (70, 215, 80),           # chifres verdes
    "limb": (255, 214, 50),          # braços e mãos
    "accent": (255, 161, 220),       # marcas e barbatanas: rosa das ligações da Gum Worm
    "mouth": (142, 75, 214),         # boca por dentro: roxa...
    "vein": (255, 143, 223),         # ...com veias rosa
    "teeth": (250, 255, 163),
    "eye": (255, 232, 70),
    "pupil": (226, 186, 40),         # um pouco mais escuro que o olho
}
SHINY = {**NORMAL,
         "stripes": [(255, 120, 196), (120, 210, 255), (250, 244, 255)],  # rosa, azul-claro, branco
         "head": (120, 210, 255), "tail": (255, 120, 196), "horn": (250, 244, 255), "limb": (120, 210, 255),
         "accent": (173, 50, 244)}
# Da cabeça para o rabo, alternando as listras como no Orthworm Candyan; o rabo (tail, tail1..4 e os espinhos) é roxo.
CHAIN = ["neck", "neck2", "neck3", "neck4", "torso", "body"] + ["segment"] + [f"segment{i}" for i in range(1, 15)]
MOUTH_BONES = ("muzzle", "jaw", "front_tooth")
EYE_BONES = ("eye_", "pupil_")


def bone_map(geo, width, height):
    """O nome do osso de cada pixel (None onde nenhum cubo usa)."""
    names = {b["name"]: b["name"] for b in geo["bones"]}
    return bone_colors(geo, width, height, names)


def recolor(texture, geo, palette):
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()
    owner = bone_map(geo, src.width, src.height)
    colors = {"head": palette["head"], "muzzle": palette["head"], "jaw": palette["head"], "horn": palette["horn"],
              "arm": palette["limb"], "hand": palette["limb"], "finger": palette["limb"], "tail": palette["tail"]}
    colors.update({bone: palette["stripes"][i % 3] for i, bone in enumerate(CHAIN)})
    body_color = bone_colors(geo, src.width, src.height, colors)

    def kind(x, y):
        r, g, b, a = sp[x, y]
        if a == 0:
            return None
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        bone = owner[y][x] or ""
        if bone.startswith(EYE_BONES):
            return "pupil" if v < 0.35 else "eye"
        red = (h > 0.85 or h < 0.03) and s > 0.4
        if bone.startswith(MOUTH_BONES):
            if red:
                return "mouth"
            if s < 0.15 and v > 0.8:
                return "teeth"
        if red:
            return "accent"
        if 0.1 < h < 0.2 and s > 0.5:
            return "accent_gold"      # marcas douradas
        if 0.3 < h < 0.5 and s > 0.2:
            return "body"
        return None

    ranges = luma_ranges(src, kind)
    for y in range(src.height):
        for x in range(src.width):
            k = kind(x, y)
            if k is None:
                continue
            r, g, b, a = sp[x, y]
            l = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            t = shade_t(ranges, k, l)
            if k == "body":
                color = body_color[y][x] or palette["head"]
            elif k == "accent_gold":
                color = palette["accent"]
            elif k == "mouth":
                # Os tons mais claros do vermelho viram as veias rosa; o resto, o roxo da boca.
                color = palette["vein"] if t > 0.7 else palette["mouth"]
            elif k in ("eye", "pupil", "teeth"):
                color, t = palette[k], 0.7 + 0.3 * t   # claros, sem sombra marrom
            else:
                color = palette[k]
            op[x, y] = ramp(color, t) + (a,)
    return out


def main():
    z = zipfile.ZipFile(sys.argv[1])
    resources = Path(sys.argv[2])
    preview = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{SRC}/rayquaza.png")))
    geo = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{SRC}/rayquaza.geo.json"))["minecraft:geometry"][0]
    normal, shiny = recolor(texture, geo, NORMAL), recolor(texture, geo, SHINY)
    out = resources / "assets/ecosystems_hollows/textures/pokemon/rayquaza"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("rayquaza_gumworm*.png"):
        old.unlink()
    normal.save(out / "rayquaza_candyan.png")
    shiny.save(out / "rayquaza_candyan_shiny.png")
    resolver = {
        "species": "cobblemon:rayquaza",
        "order": 1,
        "variations": [
            {"aspects": ["candyan"], "texture": "ecosystems_hollows:textures/pokemon/rayquaza/rayquaza_candyan.png"},
            {"aspects": ["candyan", "shiny"],
             "texture": "ecosystems_hollows:textures/pokemon/rayquaza/rayquaza_candyan_shiny.png"},
        ],
    }
    res_dir = resources / "assets/cobblemon/bedrock/pokemon/resolvers/0384_rayquaza"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "1_ecosystems_hollows_gumworm.json").unlink(missing_ok=True)
    (res_dir / "1_ecosystems_hollows_candyan.json").write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8")
    if preview:
        save_preview(preview, "rayquaza_candyan", texture, [normal, shiny])


if __name__ == "__main__":
    main()
