# Carvanha e Sharpedo Toxian (Toxic Caves), no lugar do Radgill do Alex's Caves: corpo marrom-escuro, nadadeiras
# douradas e olhos verdes que brilham no escuro (camada emissiva), com um terceiro olho na testa, como o Radgill.
# - Carvanha: o terceiro olho é pintado no alto da cabeça (os olhos dele já são pintados na textura).
# - Sharpedo: evoluído, tem 4 olhos: os olhos são cubos, e cada lado ganha uma cópia do olho um pouco acima e à
#   frente (modelo próprio, "sharpedo_toxian").
# A sombra é uma rampa por cor (cada cor vai do escuro ao claro), para manter os vários tons do original.
#
# Uso: python toxian_carvanha.py <jar do Cobblemon> <pasta resources do mod> [pasta da prévia]
import colorsys
import copy
import json
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import luma, luma_ranges, ramp, save_preview, shade_t  # noqa: E402

DARK, MID = (58, 42, 36), (92, 70, 56)    # corpo (o marrom-escuro do Radgill)
BELLY = (150, 132, 96)                    # barriga clara, puxada para o oliva
GOLD = (240, 190, 40)                     # nadadeiras
GLOW = (70, 235, 70)                      # olhos e marcas que brilham
PUPIL = (20, 30, 18)


def classify(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.32 and v > 0.6:
        return "light"          # branco, cinza e lilás claros (barriga do Sharpedo, dentes)
    if s < 0.25 and v < 0.25:
        return None             # preto (boca, pupilas): fica
    if 0.1 < h < 0.2 and s > 0.4:
        return "gold"           # amarelo das nadadeiras e da estrela
    if (h > 0.93 or h < 0.05) and s > 0.45:
        return "red"
    if 0.55 < h < 0.72:
        return "blue"
    return None


def recolor(texture, eye_boxes, glow_boxes=()):
    """Devolve (textura, camada emissiva). eye_boxes/glow_boxes: retângulos (x, y, w, h) que viram verde e brilham."""
    src = texture.convert("RGBA")
    out = src.copy()
    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, op, gp = src.load(), out.load(), glow.load()
    in_box = lambda x, y, boxes: any(bx <= x < bx + bw and by <= y < by + bh for bx, by, bw, bh in boxes)
    ranges = luma_ranges(src, lambda x, y: classify(*sp[x, y][:3]))
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            if in_box(x, y, eye_boxes) or in_box(x, y, glow_boxes):
                if classify(r, g, b) is None and luma(sp[x, y]) < 0.25:
                    continue  # pupila
                op[x, y] = GLOW + (a,)
                gp[x, y] = GLOW + (255,)
                continue
            kind = classify(r, g, b)
            if kind is None:
                continue
            color = {"red": DARK, "blue": MID, "gold": GOLD, "light": BELLY}[kind]
            op[x, y] = ramp(color, shade_t(ranges, kind, luma(sp[x, y]))) + (a,)
    return out, glow


def paint_third_eye(img, glow, x0, y0):
    """Olho 3x2 verde com a pupila no meio, pintado na textura (Carvanha)."""
    p, g = img.load(), glow.load()
    for dx in range(3):
        for dy in range(2):
            c = PUPIL if (dx == 1 and dy == 1) else GLOW
            p[x0 + dx, y0 + dy] = c + (255,)
            if c == GLOW:
                g[x0 + dx, y0 + dy] = GLOW + (255,)


# Os olhos novos: um pouco acima e à frente dos originais.
EXTRA_EYE_OFFSET = (0.0, 1.6, -2.4)


def four_eyes_model(geo):
    """Sharpedo: cada olho (osso eye_left/eye_right, um cubo com a pupila) ganha uma cópia ao lado, no mesmo osso pai."""
    geo = copy.deepcopy(geo)
    geo["description"]["identifier"] = "geometry.sharpedo_toxian"
    dx, dy, dz = EXTRA_EYE_OFFSET
    for side in ("left", "right"):
        eye = next(b for b in geo["bones"] if b["name"] == f"eye_{side}")
        moved = lambda c: {**copy.deepcopy(c), "origin": [c["origin"][0] + dx, c["origin"][1] + dy, c["origin"][2] + dz]}
        geo["bones"].append({"name": f"eye_{side}2", "parent": eye["parent"],
                             "pivot": [eye["pivot"][0] + dx, eye["pivot"][1] + dy, eye["pivot"][2] + dz],
                             "cubes": [moved(c) for c in eye["cubes"]]})
    return geo


def main():
    z = zipfile.ZipFile(sys.argv[1])
    resources = Path(sys.argv[2])
    preview = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    tex_dir = resources / "assets/ecosystems_hollows/textures/pokemon"
    res_dir = resources / "assets/cobblemon/bedrock/pokemon/resolvers"

    # Carvanha: os olhos estão nas laterais da cabeça (faces da caixa em uv 0,11, 9x6x7); o terceiro vai no topo
    # do segundo cubo da cabeça (uv 16,34: topo em x 20-28, y 34-37).
    carvanha = Image.open(BytesIO(z.read("assets/cobblemon/textures/pokemon/0318_carvanha/carvanha.png")))
    eyes = [(x, y, 1, 1) for x in range(64) for y in range(64)
            if (lambda p: p[3] and (p[0] > 200 and p[1] < 80 and p[2] < 80))(carvanha.convert("RGBA").getpixel((x, y)))
            and 18 <= y <= 24 and x < 18]  # só os dois olhos (a linha vermelha da boca fica de fora)
    car, car_glow = recolor(carvanha, eyes)
    paint_third_eye(car, car_glow, 23, 35)
    (tex_dir / "carvanha").mkdir(parents=True, exist_ok=True)
    car.save(tex_dir / "carvanha/carvanha_toxian.png")
    car_glow.save(tex_dir / "carvanha/carvanha_toxian_emissive.png")

    # Sharpedo: olhos = cubos dos ossos eye_left/eye_right (uv 96,6 / 26,80 e pupilas); a estrela amarela da testa
    # também brilha (como as guelras do Radgill).
    sharpedo = Image.open(BytesIO(z.read("assets/cobblemon/textures/pokemon/0319_sharpedo/sharpedo.png")))
    eye_boxes = [(96, 6, 8, 4), (26, 80, 8, 4), (98, 65, 4, 2), (6, 98, 4, 2)]
    star = [(x, y, 1, 1) for x in range(128) for y in range(128)
            if (lambda p: p[3] and p[0] > 200 and p[1] > 150 and p[2] < 90)(sharpedo.convert("RGBA").getpixel((x, y)))]
    sha, sha_glow = recolor(sharpedo, eye_boxes, star)
    (tex_dir / "sharpedo").mkdir(parents=True, exist_ok=True)
    sha.save(tex_dir / "sharpedo/sharpedo_toxian.png")
    sha_glow.save(tex_dir / "sharpedo/sharpedo_toxian_emissive.png")

    model = json.loads(z.read("assets/cobblemon/bedrock/pokemon/models/0319_sharpedo/sharpedo.geo.json"))
    model["minecraft:geometry"][0] = four_eyes_model(model["minecraft:geometry"][0])
    model_path = resources / "assets/ecosystems_hollows/bedrock/pokemon/models/sharpedo_toxian.geo.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")

    for species, folder, extra in (("carvanha", "0318_carvanha", {}),
                                   ("sharpedo", "0319_sharpedo", {"model": "ecosystems_hollows:sharpedo_toxian.geo"})):
        resolver = {"species": f"cobblemon:{species}", "order": 1, "variations": [{
            "aspects": ["toxian"], **extra,
            "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_toxian.png",
            "layers": [{"name": "emissive", "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_toxian_emissive.png",
                        "emissive": True}]}]}
        path = res_dir / folder / "1_ecosystems_hollows_toxian.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8")

    if preview:
        save_preview(preview, "carvanha_toxian", carvanha, [car, car_glow])
        save_preview(preview, "sharpedo_toxian", sharpedo, [sha, sha_glow])


if __name__ == "__main__":
    main()
