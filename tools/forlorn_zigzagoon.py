# Zigzagoon e Linoone Forlorn (Forlorn Hollows): o Corrodent do Alex's Caves, um rato-toupeira pelado e espinhento que
# rói pedra. Usam o modelo e o poser dos de Galar (corpo comprido e baixo, de quatro, com o pelo arrepiado nas costas,
# como o do Corrodent); a forma não evolui para o Obstagoon (regional_forms.py).
# - Focinho: um bloco alto e curto de pele pelada, com o desenho do focinho do próprio Corrodent copiado face por face
#   (rugas, tons e marcas dele), e os dois incisivos dele colados e compridos, pendurados na frente. A mandíbula
#   acompanha o focinho e a língua fica toda dentro da boca (saem as presas de Galar e a ponta da língua).
# - Olhos todos vermelhos e sem pálpebras: ele é cego, não pisca.
# - Pelo: o marrom-avermelhado escuro do Corrodent, com o desenho do pelo dele por cima da luz do original.
# - Linoone: espinhos nas costas e no rabo, recortados dos espinhos da própria textura do Corrodent, e patas maiores
#   com três garras em cada pé.
#
# Uso: python forlorn_zigzagoon.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
import colorsys
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
from toxian_sharpedo import noise, texel_positions  # noqa: E402

SPECIES = {"zigzagoon": "0263_zigzagoon", "linoone": "0264_linoone"}
EYE_RED = [(60, 4, 4), (110, 12, 8), (170, 22, 10), (220, 34, 14), (255, 70, 30)]
CLAW = [(40, 28, 26), (66, 48, 42), (104, 80, 68), (150, 124, 106), (190, 166, 146)]
SKIN_BONES = ("jaw", "foot")    # pele rosada pelada (o focinho é cubo novo)
TONGUE_BONES = ("tongue",)
EYE_BONES = ("eye_left", "eye_right")
FUR_TILE = (0, 8, 44, 46)    # o dorso do Corrodent (textura dele, 128 x 128)
FUR = 0.5                    # quanto o desenho do pelo dele pesa sobre a luz do original
# O focinho do Corrodent na textura dele: cubo com UV em (48, 28), 6 x 5 x 10.
CORRODENT_SNOUT = ((48, 28), (6, 5, 10))
# Os espinhos do Corrodent na textura dele: fileira de pontas de 4 de altura (a base embaixo).
CORRODENT_SPIKES = (0, 61, 30, 4)

# Peças novas de cada espécie: (osso, origem, tamanho, tipo[, pivô, rotação]). O tipo diz como pintar.
MODEL = {
    "zigzagoon": {
        "replace": {
            "muzzle": [((-2, 3.1, -14), (4, 3.5, 4), "snout"),
                       ((-1, 0.6, -14.6), (1, 2.5, 0.5), "tooth"),
                       ((0, 0.6, -14.6), (1, 2.5, 0.5), "tooth")],
            "jaw": [((-1.5, 2, -13.5), (3, 1, 4.5), "jaw")],
        },
        "tongue_y": 3.02,
        "drop": [],
        "drop_cubes": {"eye_left": [(1, 1, 0)], "eye_right": [(1, 1, 0)]},
    },
    "linoone": {
        "replace": {
            "muzzle": [((-2, 4.85, -16.5), (4, 3, 4.5), "snout"),
                       ((-1, 1.85, -17), (1, 3, 0.5), "tooth"),
                       ((0, 1.85, -17), (1, 3, 0.5), "tooth")],
            "jaw": [((-1.5, 3.75, -16), (3, 1, 6), "jaw")],
            "teeth": [],
            "tongue_end": [],
            "foot_front_left2": [((0.15, -1, -6.5), (2.5, 1, 2.75), "paw")] + [
                ((x, -1, -8), (0.5, 0.75, 1.5), "claw") for x in (0.35, 1.15, 1.95)],
            "foot_front_right2": [((-2.65, -1, -6.5), (2.5, 1, 2.75), "paw")] + [
                ((x, -1, -8), (0.5, 0.75, 1.5), "claw") for x in (-2.45, -1.65, -0.85)],
        },
        # Garras dos pés de trás: saem as unhas planas e entram três garras na frente de cada pé.
        "add": {
            "foot_back_left": [((x, 0, 2.5), (0.5, 0.5, 1.25), "claw") for x in (1.35, 2.0, 2.65)],
            "foot_back_right": [((x, 0, 2.5), (0.5, 0.5, 1.25), "claw") for x in (-3.15, -2.5, -1.85)],
            # Espinhos nas costas e no rabo, como os do Corrodent: fileiras juntas de placas finas inclinadas para trás,
            # um pouco tortas para os lados (alternando), do pescoço até a ponta do rabo.
            "torso": [((-3, 7.6, z), (6, 4, 0), "spike", (0, 7.6, z), (-50, 0, 12 * (-1) ** i))
                      for i, z in enumerate((-6.5, -5, -3.5, -2, -0.5))],
            "body": [((-3, 7.6, z), (6, 4, 0), "spike", (0, 7.6, z), (-50, 0, 12 * (-1) ** i))
                     for i, z in enumerate((1, 2.5, 4, 5.5, 7))],
            "tail": [((-2, 7.6, z), (4, 3, 0), "spike", (0, 7.6, z), (-55, 0, 10 * (-1) ** i))
                     for i, z in enumerate((9.5, 11, 12.5))],
            "tail2": [((-2, 7.6, z), (4, 3, 0), "spike", (0, 7.6, z), (-55, 0, 10 * (-1) ** i))
                      for i, z in enumerate((14.5, 16, 17.5))],
            "tail3": [((-1.5, 7.6, z), (3, 2, 0), "spike", (0, 7.6, z), (-60, 0, 10 * (-1) ** i))
                      for i, z in enumerate((19.5, 21, 22.5))],
        },
        "tongue_y": 4.77,
        "drop_cubes": {"head": [(1, 2, 0)], "foot_back_left": [(0, 1, 1)], "foot_back_right": [(0, 1, 1)]},
    },
}


def tones(img, test):
    return sorted({p[:3] for p in img.getdata() if p[3] and test(p)}, key=lambda c: luma(c + (255,)))


def pick(ts, t):
    """O tom da paleta mais perto (sem misturar cores: fica pixelado como o resto)."""
    t = max(0.0, min(1.0, t))
    return ts[min(len(ts) - 1, int(t * (len(ts) - 1) + 0.5))]


class Allocator:
    """Reserva retângulos livres da textura (sem pixel e sem cubo) para as peças novas."""

    def __init__(self, texture, owner):
        self.px = texture.load()
        self.w, self.h = texture.size
        self.used = [[owner[y][x] is not None or self.px[x, y][3] > 0 for x in range(self.w)] for y in range(self.h)]
        self.cache = {}

    def box(self, size):
        w, h, d = size
        key = tuple(size)
        if key in self.cache:   # peças iguais dividem a mesma área (os dois dentes, as garras, os espinhos)
            return self.cache[key]
        bw, bh = math.ceil(2 * d + 2 * w), math.ceil(d + h)
        for y in range(self.h - bh, -1, -1):
            for x in range(self.w - bw, -1, -1):
                if not any(self.used[y + j][x + i] for i in range(bw) for j in range(bh)):
                    for j in range(bh):
                        for i in range(bw):
                            self.used[y + j][x + i] = True
                    self.cache[key] = (x, y)
                    return x, y
        raise ValueError("sem espaço livre na textura")


def edit_model(geo_json, species, alloc):
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    geo["description"]["identifier"] = f"geometry.{species}_forlorn"
    spec = MODEL[species]
    kinds = {}

    def cube(origin, size, kind, pivot=None, rotation=None):
        c = {"origin": list(origin), "size": list(size), "uv": list(alloc.box(size))}
        if pivot:
            c["pivot"], c["rotation"] = list(pivot), list(rotation)
        # O dente guarda onde começa (em cima), para clarear da gengiva até a ponta.
        kinds[id(c)] = f"tooth@{origin[1] + size[1]}" if kind == "tooth" else kind
        return c

    for bone in geo["bones"]:
        name = bone["name"]
        if name.startswith("eyelid"):
            bone["cubes"] = []      # cego: sem pálpebra, não pisca
        for size in spec.get("drop_cubes", {}).get(name, []):
            bone["cubes"] = [c for c in bone.get("cubes", []) if c["size"] != list(size)]
        if name in spec["replace"]:
            bone["cubes"] = [cube(*p) for p in spec["replace"][name]]
        if name in spec.get("add", {}):
            bone.setdefault("cubes", []).extend(cube(*p) for p in spec["add"][name])
        if name.startswith(TONGUE_BONES):
            for c in bone.get("cubes", []):
                c["origin"][1] = spec["tongue_y"]   # um tiquinho acima da mandíbula, sem piscar com ela
    return model, kinds


def tone(ts, t):
    """O tom no ponto t de uma rampa (misturando os vizinhos)."""
    t = max(0.0, min(1.0, t)) * (len(ts) - 1)
    i = min(int(t), len(ts) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(ts[i], ts[i + 1]))


def paint(texture, geo, kinds, palettes, fur):
    fl = [luma(p) for p in fur.getdata() if p[3]]
    flo, fhi = min(fl), max(fl)
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()
    positions = texel_positions(geo, src.width, src.height)
    groups = {}
    for (px, py), (bone, pos, key) in positions.items():
        kind = kinds.get(key[1])
        if kind is None:
            if bone.startswith(EYE_BONES):
                h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in sp[px, py][:3]))
                kind = "eye" if s > 0.3 or v > 0.9 else "fur"   # o olho (íris e brilho) fica vermelho; o contorno, pelo
            elif bone.startswith(TONGUE_BONES):
                kind = "tongue"
            elif bone.startswith(SKIN_BONES):
                kind = "skin"
            else:
                kind = "fur"
        groups[(px, py)] = (kind, bone, pos, key)
    ranges = {}
    for (px, py), (kind, *_rest) in groups.items():
        if sp[px, py][3]:
            l = luma(sp[px, py])
            lo, hi = ranges.get(kind, (l, l))
            ranges[kind] = (min(lo, l), max(hi, l))
    shade = {0: 0.12, 1: -0.18, 2: -0.04, 3: 0.0, 4: -0.04, 5: -0.08}
    for (px, py), (kind, bone, (x, y, z), key) in groups.items():
        face = key[2]
        lo, hi = ranges.get(kind, (0, 1))
        t = (luma(sp[px, py]) - lo) / (hi - lo) if sp[px, py][3] and hi > lo else 0.5
        n = noise(px, py, 5)
        if kind == "fur":
            f = fur.getpixel((px % fur.width, py % fur.height))
            f = (luma(f) - flo) / (fhi - flo) if fhi > flo and f[3] else 0.5
            c = tone(palettes["fur"], (1 - FUR) * t + FUR * f)
        elif kind == "eye":
            c = pick(EYE_RED, 0.25 + 0.65 * t)
        elif kind == "tongue":
            c = pick(palettes["skin"], 0.1 + 0.4 * t)
        elif kind in ("skin", "paw"):
            c = pick(palettes["skin"], 0.25 + 0.45 * t + 0.15 * n + shade[face])
        elif kind == "jaw":
            # Em cima é o céu da boca (escuro); fora, a pele do queixo.
            c = pick(palettes["skin"], 0.05 + 0.1 * n) if face == 0 else pick(palettes["skin"], 0.3 + 0.2 * n + shade[face])
        elif kind == "snout":
            continue           # copiado do Corrodent depois (copy_snout)
        elif kind.startswith("tooth"):
            top = float(kind.split("@")[1])
            c = pick(palettes["teeth"], 0.75 - 0.65 * max(0.0, min(1.0, (top - y) / 3)) + 0.1 * n)
        elif kind == "claw":
            c = pick(CLAW, 0.3 + 0.5 * (1 - (z - math.floor(z))) + 0.15 * n)
        else:
            continue
        op[px, py] = c + (255,)
    return out


def copy_snout(img, geo, kinds, corrodent):
    """O focinho: cada face do cubo novo recebe a face correspondente do focinho do Corrodent, esticada."""
    (cu, cv), csize = CORRODENT_SNOUT
    theirs = box_faces((cu, cv), csize)
    p, cp = img.load(), corrodent.load()
    for bone in geo["bones"]:
        for c in bone.get("cubes", []):
            if kinds.get(id(c)) != "snout":
                continue
            ours = box_faces(c["uv"], [math.ceil(v) for v in c["size"]])
            for (x0, y0, w, h), (tx, ty, tw, th) in zip(ours, theirs):
                for j in range(h):
                    for i in range(w):
                        q = cp[tx + int(i * tw / w), ty + int(j * th / h)]
                        if q[3]:
                            p[x0 + i, y0 + j] = q


def paint_spikes(img, geo, kinds, corrodent):
    """Os espinhos: recortes da fileira de pontas do Corrodent (cada tamanho pega um trecho), dos dois lados da placa;
    em volta das pontas fica vazio."""
    sx, sy, sw, sh = CORRODENT_SPIKES
    p, cp = img.load(), corrodent.load()
    done = set()
    for bone in geo["bones"]:
        for c in bone.get("cubes", []):
            if kinds.get(id(c)) != "spike" or tuple(c["uv"]) in done:
                continue
            done.add(tuple(c["uv"]))
            (u, v), (w, h, _d) = c["uv"], c["size"]
            w, h = int(w), int(h)
            start = sx + (len(done) * 7) % (sw - w)
            for side in range(2):
                for i in range(w):
                    col = start + (i if side == 0 else w - 1 - i)
                    for j in range(h):
                        p[u + side * w + i, v + j] = cp[col, sy + sh - h + j]


def clean(model):
    for bone in model["minecraft:geometry"][0]["bones"]:
        if "cubes" in bone and not bone["cubes"]:
            del bone["cubes"]


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    corrodent = Image.open(BytesIO(ac.read("assets/alexscaves/textures/entity/corrodent.png"))).convert("RGBA")
    teeth_item = Image.open(BytesIO(ac.read("assets/alexscaves/textures/item/corrodent_teeth.png"))).convert("RGBA")
    palettes = {
        "fur": tones(corrodent, lambda p: max(p[:3]) < 70 and p[0] > p[2]) + [(96, 70, 62), (124, 98, 88)],
        # Pele: só os rosados do focinho (sem os laranjas dos dentes).
        # (sem os vermelhos saturados demais, para a pele não ficar xadrez)
        "skin": tones(corrodent, lambda p: p[0] > 140 and p[1] < p[0] * 0.75 and p[2] >= p[1] * 0.75
                      and 0.3 <= colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))[1] <= 0.5),
        "teeth": tones(teeth_item, lambda p: p[0] > 180 and p[1] > 110 and p[2] < 140) + [(219, 131, 31)],
    }
    palettes["teeth"].sort(key=lambda c: luma(c + (255,)))
    palettes["skin"] = [(96, 34, 36), (130, 56, 58), (156, 77, 77)] + palettes["skin"]   # o fundo da boca e as rugas mais fundas
    for species, folder in SPECIES.items():
        galar = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/1_{species}_galarian.json"))
        base_variation = galar["variations"][0]
        name = base_variation["texture"].split("/")[-1].removesuffix(".png")
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{name}.png"))).convert("RGBA")
        geo_json = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{name}.geo.json"))
        geo = geo_json["minecraft:geometry"][0]
        owner = bone_colors(geo, texture.width, texture.height, {b["name"]: b["name"] for b in geo["bones"]})
        model, kinds = edit_model(geo_json, species, Allocator(texture, owner))
        new_geo = model["minecraft:geometry"][0]
        painted = paint(texture, new_geo, kinds, palettes, corrodent.crop(FUR_TILE))
        copy_snout(painted, new_geo, kinds, corrodent)
        paint_spikes(painted, new_geo, kinds, corrodent)
        clean(model)
        out = resources / f"assets/ecosystems_hollows/textures/pokemon/{species}"
        out.mkdir(parents=True, exist_ok=True)
        painted.save(out / f"{species}_forlorn.png")
        model_path = resources / f"assets/ecosystems_hollows/bedrock/pokemon/models/{species}_forlorn.geo.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8", newline="\n")
        resolver = {"species": f"cobblemon:{species}", "order": 2, "variations": [
            {"aspects": ["forlorn"], "poser": base_variation["poser"], "model": f"ecosystems_hollows:{species}_forlorn.geo",
             "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_forlorn.png"}]}
        path = resources / f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/2_ecosystems_hollows_forlorn.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
        if preview:
            save_preview(preview, f"{species}_forlorn", texture, [painted])


if __name__ == "__main__":
    main()
