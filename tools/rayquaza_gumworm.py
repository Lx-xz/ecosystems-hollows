# Teste visual: o Rayquaza repintado como uma "Gum Worm" de chiclete (as mesmas listras do Orthworm Candyan).
# Só uma textura nova para o modelo do próprio Rayquaza, ligada ao aspect "gumworm":
#   /pokespawn rayquaza aspect=gumworm
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
# As cores da própria Gum Worm do Alex's Caves (texturas gum_worm e gum_worm_segment_0/1/2).
PURPLE, ORANGE, TEAL = (173, 50, 244), (248, 199, 75), (24, 229, 181)
HEAD = (21, 243, 184)
PINK = (255, 161, 220)
STRIPES = [PURPLE, ORANGE, TEAL]
# Da cabeça para o rabo, alternando as cores como no Orthworm Candyan.
CHAIN = ["neck", "neck2", "neck3", "neck4", "torso", "body"] + ["segment"] + [f"segment{i}" for i in range(1, 15)] \
    + ["tail", "tail1", "tail2", "tail3", "tail4"]
COLORS = {"head": HEAD, "muzzle": HEAD, "jaw": HEAD, "horn": ORANGE, "arm": ORANGE, "hand": ORANGE, "finger": ORANGE}
COLORS.update({bone: STRIPES[i % 3] for i, bone in enumerate(CHAIN)})


def recolor(texture, owner_color):
    """Cada pixel na cor do seu osso, com a luz e a sombra do original. As marcas amarelas ficam (e brilham, pela
    camada emissiva do próprio Rayquaza); o vermelho das barbatanas vira rosa-chiclete; o resto (olhos, dentes) fica."""
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()

    def kind(x, y):
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in sp[x, y][:3]))
        if (h > 0.85 or h < 0.03) and s > 0.4:
            return "accent"
        return "body" if 0.3 < h < 0.5 and s > 0.2 else None

    ranges = luma_ranges(src, kind)
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            luma = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            if 0.1 < h < 0.2 and s > 0.5:      # marcas amarelas
                continue
            if (h > 0.85 or h < 0.03) and s > 0.4:  # vermelho/carmim das barbatanas e da boca
                color = PINK
            elif 0.3 < h < 0.5 and s > 0.2:     # o verde do corpo
                color = owner_color[y][x] or TEAL
            else:
                continue
            op[x, y] = ramp(color, shade_t(ranges, kind(x, y), luma)) + (a,)
    return out


def main():
    z = zipfile.ZipFile(sys.argv[1])
    resources = Path(sys.argv[2])
    preview = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{SRC}/rayquaza.png")))
    geo = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{SRC}/rayquaza.geo.json"))["minecraft:geometry"][0]
    gum = recolor(texture, bone_colors(geo, texture.width, texture.height, COLORS))
    out = resources / "assets/ecosystems_hollows/textures/pokemon/rayquaza"
    out.mkdir(parents=True, exist_ok=True)
    gum.save(out / "rayquaza_gumworm.png")
    resolver = {
        "species": "cobblemon:rayquaza",
        "order": 1,
        "variations": [{"aspects": ["gumworm"], "texture": "ecosystems_hollows:textures/pokemon/rayquaza/rayquaza_gumworm.png"}],
    }
    path = resources / "assets/cobblemon/bedrock/pokemon/resolvers/0384_rayquaza/1_ecosystems_hollows_gumworm.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8")
    if preview:
        save_preview(preview, "rayquaza_gumworm", texture, [gum])


if __name__ == "__main__":
    main()
