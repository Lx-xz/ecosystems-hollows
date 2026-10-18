# Sharpedo Toxian: um tubarão de metal de contenção e resíduo nuclear da Toxic Caves (o Carvanha continua o Radgill).
# Copia o desenho dos próprios blocos do Alex's Caves, não só as cores: cada parte usa a textura do bloco (repetida a
# cada 16 pixels), com a luz e a sombra do Sharpedo original por cima.
# - Corpo: metal escuro em painéis (scrap_metal e metal_barrel), com o recorte e os rebites deles.
# - Barriga: listras de perigo amarelas e pretas desenhadas do zero, que seguem o corpo (pela posição de cada pixel no
#   modelo: chevrons apontando para a frente embaixo, diagonais nas laterais), com as cores do hazmat_block.
# - Nadadeira de baixo: toda amarela (o amarelo do waste_drum).
# - No topo do focinho, no lugar do X: o símbolo de radiação, em amarelo.
# - Grade das guelras e a borda da boca: o cinza da peça do reator (nuclear_furnace_component).
# - Propulsores do rabo (a estrela amarela e as bordas dela): o verde do urânio, brilhando (camada emissiva).
# - Boca por dentro: com os tons do propulsor, brilhando: a garganta mais escura, manchas e bolhas pixel a pixel.
# - Faces de barriga são barriga inteira: os contornos escuros e os buracos do original nelas viram listras também.
# - Dentes: metal claro. Olhos: verdes com a pupila branca, brilhando no escuro (shiny: azul e branco). Os 4 olhos continuam
#   (modelo próprio, com as funções de toxian_carvanha.py).
# - Shiny: um barril velho. O metal enferrujado (rusty_barrel), e a pintura de aviso (símbolo, listras e nadadeira
#   de baixo) em amarelo de tinta velha sobre marrom quase preto. O brilho é o azul da radiação de Cherenkov (o
#   brilho de verdade dos reatores), no lugar do verde.
#
# Uso: python toxian_sharpedo.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
import colorsys
import json
import math
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import luma, save_preview  # noqa: E402
from toxian_carvanha import (EXTRA_EYE_UV_SIZE, bone_map, classify, four_eyes_model, free_area,  # noqa: E402
                             paint_extra_eye, ramp)

BLOCKS = "assets/alexscaves/textures/block/"
EYEBALLS, PUPILS = [(96, 6, 8, 4), (26, 80, 8, 4)], [(98, 65, 4, 2), (6, 98, 4, 2)]
# Cada parte do Sharpedo: (bloco normal, bloco do shiny). O desenho vem do bloco; a luz, do Sharpedo.
PARTS = {
    "body": ("scrap_metal_plate", "rusty_scrap_metal_plate"),
    "body_light": ("metal_barrel", "rusty_barrel"),
    "gray": ("nuclear_furnace_component", "rusty_scrap_metal_0"),
    "outline": ("scrap_metal_0", "rusty_scrap_metal_1"),
    "belly": ("hazmat_block", "hazmat_block"),          # no shiny, as listras viram ferrugem (RUST_STRIPES)
    "fin": ("waste_drum", "rusty_barrel_top"),
    "teeth": ("metal_barrel_top", "rusty_barrel_bottom"),
    "glow": ("uranium_rod", "uranium_rod"),
    "mouth": ("unrefined_waste", "unrefined_waste"),
}
LIGHT = 0.45     # quanto a luz do Sharpedo original pesa sobre o desenho do bloco
STRIPE = 2.0     # largura das listras de perigo (em pixels do corpo)
# O símbolo de radiação vai no topo do focinho, onde ficava o X: face de cima do cubo da cabeça em uv (34, 50),
# 11 x 9 (os arcos do X no cubo da frente viram metal).
SYMBOL = (43, 50, 11, 9)
# Shiny: tinta amarela desbotada, marrom bem escuro no lugar do preto, e o azul de Cherenkov (do fundo ao claro).
FADED_YELLOW = [(196, 158, 52), (216, 180, 66), (232, 200, 88), (242, 218, 120)]
DARK_RUST = [(22, 14, 10), (32, 20, 14), (44, 26, 18)]
CHERENKOV = [(8, 18, 64), (14, 40, 120), (24, 80, 200), (50, 140, 255), (120, 200, 255), (200, 236, 255)]
# A boca por dentro do shiny: o fundo azul-marinho bem escuro, com o brilho azul só nas bolhas.
# Olhos (brilham): verde com a pupila branca; no shiny, azul Cherenkov e branco.
EYE_GREEN, EYE_BLUE, PUPIL_WHITE = (60, 236, 70), (60, 160, 255), (240, 255, 244)
CHERENKOV_MOUTH = [(4, 8, 28), (6, 14, 48), (10, 26, 84), (16, 50, 140), (30, 100, 220), (80, 170, 255)]


def block(ac, name):
    return Image.open(BytesIO(ac.read(BLOCKS + name + ".png"))).convert("RGBA").crop((0, 0, 16, 16))


def green_only(img):
    """Do bastão de urânio, só o verde (o encaixe de metal fica de fora)."""
    pixels = [p for p in img.getdata() if p[3] and p[1] > p[0] + 40]
    return sorted({p[:3] for p in pixels}, key=lambda c: luma(c + (255,)))


def texel_positions(geo, width, height):
    """A posição no corpo (x, y, z, com y para cima) de cada pixel da textura, pela caixa de cada cubo (UV de caixa,
    como o Minecraft monta: ModelPart.Cube). Ignora as rotações dos ossos: serve para desenhar padrões que seguem o
    corpo e passam de uma face para a outra sem quebrar."""
    pos = {}
    for bone in geo["bones"]:
        for cube in bone.get("cubes", []):
            uv = cube.get("uv")
            if not isinstance(uv, list):
                continue
            (ox, oy, oz), (w, h, d) = cube["origin"], cube["size"]
            x0, x1, y0, y1, z0, z1 = ox, ox + w, -(oy + h), -oy, oz, oz + d   # espaço do Java: y para baixo
            if cube.get("mirror", bone.get("mirror", False)):
                x0, x1 = x1, x0
            v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                 (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
            u, vv = uv
            U = [u, u + d, u + d + w, u + d + 2 * w, u + 2 * d + w, u + 2 * d + 2 * w]
            V = [vv, vv + d, vv + d + h]
            faces = [([5, 4, 0, 1], U[1], V[0], U[2], V[1]), ([2, 3, 7, 6], U[2], V[1], U[3], V[0]),
                     ([0, 4, 7, 3], U[0], V[1], U[1], V[2]), ([1, 0, 3, 2], U[1], V[1], U[2], V[2]),
                     ([5, 1, 2, 6], U[2], V[1], U[4], V[2]), ([4, 5, 6, 7], U[4], V[1], U[5], V[2])]
            for face, (ids, u1, v1, u2, v2) in enumerate(faces):
                if u1 == u2 or v1 == v2:
                    continue
                q = [v[i] for i in ids]   # nos cantos (u2,v1), (u1,v1), (u1,v2), (u2,v2)
                for py in range(int(min(v1, v2)), int(max(v1, v2))):
                    for px in range(int(min(u1, u2)), int(max(u1, u2))):
                        if not (0 <= px < width and 0 <= py < height):
                            continue
                        a, b = (px + 0.5 - u1) / (u2 - u1), (py + 0.5 - v1) / (v2 - v1)
                        top = [q[1][k] + (q[0][k] - q[1][k]) * a for k in range(3)]
                        bottom = [q[2][k] + (q[3][k] - q[2][k]) * a for k in range(3)]
                        x, y, z = [top[k] + (bottom[k] - top[k]) * b for k in range(3)]
                        pos[(px, py)] = (bone["name"], (x, -y, z), (bone["name"], id(cube), face))
    return pos


def tones_where(img, test):
    return sorted({p[:3] for p in img.getdata() if p[3] and test(p)}, key=lambda c: luma(c + (255,)))


def pick(tones, t):
    t = max(0.0, min(1.0, t))
    return tones[min(len(tones) - 1, int(t * (len(tones) - 1) + 0.5))]


def hazard(x, y, z):
    """Listras de perigo que seguem o corpo: chevrons apontando para a frente na barriga, diagonais nas laterais."""
    return int((z * 0.7 - y * 0.7 + abs(x) * 0.6) // STRIPE) % 2 == 1


def radiation(w, h):
    """O símbolo de radiação (três pás e o miolo) num retângulo w x h: os pixels pintados."""
    cx, cy, inner, outer, hole = (w - 1) / 2, (h - 1) / 2, 2.1, min(w, h) / 2 - 0.1, 1.2
    pixels = set()
    for py in range(h):
        for px in range(w):
            hits = 0
            for sy in range(4):
                for sx in range(4):
                    dx, dy = px + (sx + 0.5) / 4 - 0.5 - cx, py + (sy + 0.5) / 4 - 0.5 - cy
                    r = math.hypot(dx, dy)
                    ang = math.degrees(math.atan2(dy, dx)) % 360
                    blade = any(abs((ang - c + 180) % 360 - 180) <= 30 for c in (90, 210, 330))
                    hits += r <= hole or (inner <= r <= outer and blade)
            if hits >= 8:
                pixels.add((px, py))
    return pixels


def paint(texture, owner, positions, blocks, colors):
    src = texture.convert("RGBA")
    out = src.copy()
    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, op, gp = src.load(), out.load(), glow.load()
    in_box = lambda x, y, boxes: any(bx <= x < bx + bw and by <= y < by + bh for bx, by, bw, bh in boxes)

    def warm(p):
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
        return 0.03 < h < 0.2 and s > 0.35 and v > 0.3

    def kind_of(x, y):
        p = sp[x, y]
        bone = owner[y][x] or ""
        if warm(p):
            # As marcas amarelas (e as bordas alaranjadas delas): no rabo são os propulsores, que brilham; no resto
            # (o X da cabeça) viram metal.
            return "glow" if bone == "tail" else "body"
        if bone == "fin_bottom":
            return "fin_bottom"
        return classify(*p[:3])

    kinds = {(x, y): kind_of(x, y) for y in range(src.height) for x in range(src.width) if sp[x, y][3]}
    faces = {}
    for xy, (_, _, face) in positions.items():
        faces.setdefault(face, []).append(xy)
    filled = set()
    for pixels in faces.values():
        solid = [xy for xy in pixels if xy in kinds]
        belly = sum(1 for xy in solid if kinds[xy] == "belly")
        if solid and belly / len(solid) >= 0.5:
            for xy in pixels:
                if kinds.get(xy) not in ("mouth", "teeth"):
                    if xy not in kinds:
                        filled.add(xy)   # buraco (transparente) no meio da barriga
                    kinds[xy] = "belly"
    ranges = {}
    for (x, y), k in kinds.items():
        if k:
            l = luma(sp[x, y])
            lo, hi = ranges.get(k, (l, l))
            ranges[k] = (min(lo, l), max(hi, l))

    def t_of(x, y, k):
        if sp[x, y][3] == 0 or (k == "belly" and classify(*sp[x, y][:3]) != "belly"):
            return 0.5   # pixel que não era barriga (contorno, buraco): tom do meio
        lo, hi = ranges.get(k, (0.0, 1.0))
        return (luma(sp[x, y]) - lo) / (hi - lo) if hi > lo else 0.6

    for (x, y), k in kinds.items():
        a = 255 if (x, y) in filled else sp[x, y][3]
        # Olhos que brilham: verde com a pupila branca (shiny: azul e branco).
        if in_box(x, y, PUPILS):
            op[x, y], gp[x, y] = colors["pupil"] + (a,), colors["pupil"] + (255,)
            continue
        if in_box(x, y, EYEBALLS):
            c = ramp(colors["eye"], 0.75 + 0.25 * luma(sp[x, y]))
            op[x, y], gp[x, y] = c + (a,), c + (255,)
            continue
        if k is None:
            continue
        t = t_of(x, y, k)
        if k == "glow":
            c = pick(colors["glow"], 0.35 + 0.65 * t)
            op[x, y], gp[x, y] = c + (a,), c + (255,)
        elif k == "mouth":
            # Boca por dentro: resíduo verde borbulhando (o desenho do unrefined_waste), do fundo escuro ao claro.
            # Os tons do propulsor: a sombra do original (fundo da garganta mais escuro), manchas escuras e bolhas
            # claras espalhadas pixel a pixel.
            n = noise(x, y, 11)
            level = 0.2 + 0.55 * t + (0.35 if n < 0.12 else -0.2 if n > 0.86 else 0.12 * (noise(x, y, 12) - 0.5))
            c = pick(colors["glow"], level)
            op[x, y], gp[x, y] = c + (a,), c + (255,)
        elif k in ("belly", "fin_bottom"):
            where = positions.get((x, y))
            stripe = k == "belly" and where is not None and hazard(*where[1])
            tones = colors["black"] if stripe else colors["yellow"]
            op[x, y] = pick(tones, 0.2 + 0.8 * t) + (a,)
        else:
            pattern = blocks[k if k in blocks else "body"].getpixel((x % 16, y % 16))
            shade = 1 - LIGHT + LIGHT * (0.6 + 0.8 * t)   # 0,55..1,25: o escuro escurece, o claro clareia
            op[x, y] = tuple(max(0, min(255, int(c * shade))) for c in pattern[:3]) + (a,)
    return out, glow


def noise(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFF) / 0xFFFF


def paint_symbol(img, x0, y0, w, h, tones):
    """O símbolo de radiação pintado com relevo: tons claros na borda de cima e da esquerda, escuros na de baixo e da
    direita, e o meio variando um pouco, como tinta em chapa de metal."""
    p = img.load()
    shape = radiation(w, h)
    for dx, dy in shape:
        lit = ((dx, dy - 1) not in shape) + ((dx - 1, dy) not in shape)
        shade = ((dx, dy + 1) not in shape) + ((dx + 1, dy) not in shape)
        t = 0.55 + 0.22 * lit - 0.25 * shade + 0.12 * (noise(x0 + dx, y0 + dy, 9) - 0.5)
        p[x0 + dx, y0 + dy] = pick(tones, t) + (255,)


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    sharpedo = Image.open(BytesIO(z.read("assets/cobblemon/textures/pokemon/0319_sharpedo/sharpedo.png")))
    geo_json = json.loads(z.read("assets/cobblemon/bedrock/pokemon/models/0319_sharpedo/sharpedo.geo.json"))
    owner = bone_map(geo_json["minecraft:geometry"][0], sharpedo.width, sharpedo.height)
    greens = sorted(set(green_only(block(ac, "uranium_rod")) + green_only(block(ac, "unrefined_waste"))),
                    key=lambda c: luma(c + (255,)))
    eye_uv = free_area(sharpedo, owner, EXTRA_EYE_UV_SIZE)
    positions = texel_positions(geo_json["minecraft:geometry"][0], sharpedo.width, sharpedo.height)
    hazmat, drum, rust = block(ac, "hazmat_block"), block(ac, "waste_drum"), block(ac, "rusty_barrel")
    rust_tones = tones_where(rust, lambda p: True)
    waste_greens = tones_where(block(ac, "unrefined_waste"), lambda p: p[1] > p[0] + 30)
    yellow = sorted(set(tones_where(drum, lambda p: p[0] > 150 and p[1] > 100 and p[2] < 90)
                        + tones_where(hazmat, lambda p: p[0] > 150 and p[2] < 90)), key=lambda c: luma(c + (255,)))
    black = tones_where(hazmat, lambda p: max(p[:3]) < 90)
    mouth = [(6, 46, 14), (10, 80, 20)] + waste_greens
    palettes = {
        False: {"glow": greens, "mouth": mouth, "yellow": yellow, "black": black, "eye": EYE_GREEN, "pupil": PUPIL_WHITE},
        True: {"glow": CHERENKOV[1:], "mouth": CHERENKOV_MOUTH, "yellow": FADED_YELLOW, "black": DARK_RUST,
               "eye": EYE_BLUE, "pupil": PUPIL_WHITE},
    }

    tex_dir = resources / "assets/ecosystems_hollows/textures/pokemon/sharpedo"
    tex_dir.mkdir(parents=True, exist_ok=True)
    for old in tex_dir.glob("sharpedo_toxian*.png"):
        old.unlink()
    results = {}
    for shiny in (False, True):
        blocks = {k: block(ac, names[1] if shiny else names[0]) for k, names in PARTS.items()}
        blocks["waste"] = block(ac, "unrefined_waste")
        tex, glow = paint(sharpedo, owner, positions, blocks, palettes[shiny])
        paint_symbol(tex, *SYMBOL, palettes[shiny]["yellow"])
        paint_extra_eye(tex, eye_uv, palettes[shiny]["eye"], glow)
        name = "sharpedo_toxian" + ("_shiny" if shiny else "")
        tex.save(tex_dir / f"{name}.png")
        glow.save(tex_dir / f"{name}_emissive.png")
        results[shiny] = tex

    model = json.loads(json.dumps(geo_json))
    model["minecraft:geometry"][0] = four_eyes_model(model["minecraft:geometry"][0], eye_uv)
    model_path = resources / "assets/ecosystems_hollows/bedrock/pokemon/models/sharpedo_toxian.geo.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8", newline="\n")

    tex = "ecosystems_hollows:textures/pokemon/sharpedo/"
    resolver = {"species": "cobblemon:sharpedo", "order": 1, "variations": [
        {"aspects": ["toxian"], "model": "ecosystems_hollows:sharpedo_toxian.geo", "texture": tex + "sharpedo_toxian.png",
         "layers": [{"name": "emissive", "emissive": True, "texture": tex + "sharpedo_toxian_emissive.png"}]},
        {"aspects": ["toxian", "shiny"], "texture": tex + "sharpedo_toxian_shiny.png",
         "layers": [{"name": "emissive", "emissive": True, "texture": tex + "sharpedo_toxian_shiny_emissive.png"}]},
    ]}
    path = resources / "assets/cobblemon/bedrock/pokemon/resolvers/0319_sharpedo/1_ecosystems_hollows_toxian.json"
    path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
    if preview:
        save_preview(preview, "sharpedo_toxian", sharpedo, [results[False], results[True]])


if __name__ == "__main__":
    main()
