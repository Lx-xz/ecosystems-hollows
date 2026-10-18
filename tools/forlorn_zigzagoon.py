# Zigzagoon e Linoone Forlorn (Forlorn Hollows): o Corrodent do Alex's Caves, um rato-toupeira pelado e espinhento que
# rói pedra. Usam o modelo e o poser dos de Galar (corpo comprido e baixo, de quatro, com o pelo arrepiado nas costas,
# como o do Corrodent); a forma não evolui para o Obstagoon (regional_forms.py).
# - As peças do Corrodent vêm do próprio modelo dele (CorrodentModel do Alex's Caves): cada cubo novo copia, face por
#   face, a face equivalente da caixa dele na textura dele (CORRODENT). Ao diminuir, cada pixel é a média dos que
#   caem nele, presa à paleta daquela face (sem tons inventados nem manchas):
#   - Focinho: o focinho pelado dele (pele pálida com rugas, o céu da boca vermelho embaixo), com a mandíbula dele.
#   - Dentes: o plano dos incisivos dele, pendurado na frente do focinho, com a raiz dentro dele.
#   - Linoone: a crista de espinhos das costas dele (uma crista fina, com as laterais recortadas em pontas) no lombo
#     e no rabo, e o pelo do corpo e do rabo dele no corpo e no rabo.
# - Olhos todos vermelhos e sem pálpebras: ele é cego, não pisca. A língua fica toda dentro da boca.
#   - Pelo: todo cubo de pelo (corpo, cabeça, orelhas, pernas, tufos de Galar) recebe o pelo do Corrodent: o do peito
#     na frente, o do quadril atrás e o do rabo no rabo. Os tufos e planos de Galar guardam o recorte deles (as pontas
#     vazadas continuam vazadas).
# - Patas e pés: pele rosada lisa (a luz do original, sem ruído) e garras claras; o Linoone tem patas maiores com três
#   garras em cada pé.
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
CLAW = [(120, 100, 90), (168, 148, 134), (212, 198, 184), (240, 232, 220)]   # garras claras, como as dele
SKIN_BONES = ("jaw", "foot")    # pele rosada pelada (o focinho é cubo novo)
TONGUE_BONES = ("tongue",)
EYE_BONES = ("eye_left", "eye_right")
FUR_TILE = (0, 8, 44, 46)    # o dorso do Corrodent (textura dele, 128 x 128)
FUR = 0.5                    # quanto o desenho do pelo dele pesa sobre a luz do original
# As caixas do modelo do Corrodent (CorrodentModel): UV na textura dele (128 x 128) e tamanho.
CORRODENT = {
    "snout": ((48, 28), (6, 5, 10)),
    "jaw": ((53, 43), (6, 3, 9)),
    "teeth": ((30, 7), (4, 7, 0)),
    "hips": ((0, 0), (8, 9, 14)),
    "chest": ((0, 23), (8, 9, 14)),
    "ridge_hips": ((30, 32), (2, 5, 14)),    # a crista de espinhos das costas (laterais recortadas em pontas)
    "ridge_chest": ((0, 46), (2, 5, 14)),
    "tail": ((70, 8), (4, 5, 14)),
}

# Peças novas de cada espécie: (osso, origem, tamanho, tipo[, pivô, rotação]). O tipo diz como pintar.
MODEL = {
    "zigzagoon": {
        "replace": {
            "muzzle": [((-2, 3.1, -15), (4, 4, 5), "copy:snout"),
                       ((-1, 0.6, -15.01), (2, 3, 0), "copy:teeth")],
            "jaw": [((-1.5, 2, -14), (3, 1, 5), "copy:jaw")],
        },
        "tongue_y": 3.02,
        "drop_cubes": {"eye_left": [(1, 1, 0)], "eye_right": [(1, 1, 0)]},
    },
    "linoone": {
        "replace": {
            "muzzle": [((-2, 4.85, -18), (4, 3, 6), "copy:snout"),
                       ((-1, 1.35, -18.01), (2, 4, 0), "copy:teeth")],
            "jaw": [((-1.5, 3.75, -17), (3, 1, 7), "copy:jaw")],
            "teeth": [],
            "tongue_end": [],
            "foot_front_left2": [((0.15, -1, -6.5), (2.5, 1, 2.75), "paw")] + [
                ((x, -1, -7.5), (0.5, 0.5, 1), "claw") for x in (0.35, 1.15, 1.95)],
            "foot_front_right2": [((-2.65, -1, -6.5), (2.5, 1, 2.75), "paw")] + [
                ((x, -1, -7.5), (0.5, 0.5, 1), "claw") for x in (-2.45, -1.65, -0.85)],
        },
        "add": {
            # Garras dos pés de trás: saem as unhas planas e entram três garras na frente de cada pé.
            "foot_back_left": [((x, 0, 2.75), (0.5, 0.5, 1), "claw") for x in (1.35, 2.0, 2.65)],
            "foot_back_right": [((x, 0, 2.75), (0.5, 0.5, 1), "claw") for x in (-3.15, -2.5, -1.85)],
            # A crista de espinhos do Corrodent, do pescoço à ponta do rabo (a base meio afundada no corpo).
            "torso": [((-1, 7.25, -7), (2, 5, 8), "copy:ridge_chest")],
            "body": [((-1, 7.25, 1), (2, 5, 8), "copy:ridge_hips")],
            "tail": [((-1, 7.25, 9), (2, 4, 5), "copy:ridge_hips")],
            "tail2": [((-1, 7.25, 14), (2, 3, 5), "copy:ridge_chest")],
            "tail3": [((-0.5, 7.5, 19), (1, 2, 5), "copy:ridge_chest")],
        },
        # Cubos de Galar que ganham o pelo do Corrodent (pelo tamanho do cubo).
        "transplant": {"torso": {(5, 5, 8): "chest"}, "body": {(7, 5, 8): "hips"}, "tail": {(8, 2, 5): "tail"},
                       "tail2": {(8, 1, 5): "tail"}, "tail3": {(7, 0, 5): "tail"}},
        "tongue_y": 4.77,
        # Saem: a placa de Galar em cima do lombo (a crista entra no lugar), a placa da cara e as unhas planas.
        "drop_cubes": {"torso": [(2, 0, 8)], "head": [(1, 2, 0)], "foot_back_left": [(0, 1, 1)],
                       "foot_back_right": [(0, 1, 1)]},
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

    def box(self, size, kind=""):
        w, h, d = size
        key = (tuple(size), kind)
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


HIPS_BONES = ("butt", "body", "leg_back", "body_ruff3", "bodyruff5", "bodyruff6", "bodyruff9")
NOT_FUR = ("eye_left", "eye_right", "eyelid", "tongue", "jaw", "muzzle", "teeth", "foot", "zigzagoon", "linoone")


def fur_source(bone):
    """De que parte do Corrodent vem o pelo do osso (None: não é pelo)."""
    if bone.startswith(NOT_FUR):
        return None
    if bone.startswith("tail"):
        return "tail"
    return "hips" if bone.startswith(HIPS_BONES) else "chest"


def edit_model(geo_json, species, alloc):
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    geo["description"]["identifier"] = f"geometry.{species}_forlorn"
    spec = MODEL[species]
    kinds = {}

    def cube(origin, size, kind, pivot=None, rotation=None):
        c = {"origin": list(origin), "size": list(size), "uv": list(alloc.box(size, kind))}
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
        for c in bone.get("cubes", []):
            part = spec.get("transplant", {}).get(name, {}).get(tuple(c["size"]))
            if part and id(c) not in kinds:
                kinds[id(c)] = "copy:" + part
        source = fur_source(name)
        for c in bone.get("cubes", []):
            if source and id(c) not in kinds:
                kinds[id(c)] = "fur:" + source
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
        if kind and kind.startswith("fur:"):
            kind = None   # pinta como pelo por baixo; o pelo do Corrodent vem por cima (copy_parts)
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
        new_cube = not kinds.get(key[1], "fur:").startswith("fur:")   # cubo novo (pintado inteiro)
        if sp[px, py][3] == 0 and not new_cube:
            continue   # o vazio do original fica vazio (as pontas dos tufos de pelo de Galar)
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
            # Pele lisa, como os pés do Corrodent: um tom por face, só com a sombra do lado (os poucos tons de luz do
            # original, ampliados, viravam blocos).
            c = pick(palettes["skin"], 0.62 + shade[face])
        elif kind == "jaw":
            # Em cima é o céu da boca (escuro); fora, a pele do queixo.
            c = pick(palettes["skin"], 0.05 + 0.1 * n) if face == 0 else pick(palettes["skin"], 0.3 + 0.2 * n + shade[face])
        elif kind == "snout":
            continue           # copiado do Corrodent depois (copy_snout)
        elif kind.startswith("tooth"):
            top = float(kind.split("@")[1])
            c = pick(palettes["teeth"], 0.75 - 0.65 * max(0.0, min(1.0, (top - y) / 3)) + 0.1 * n)
        elif kind == "claw":
            c = pick(CLAW, 0.35 + 0.6 * (1 - (z - math.floor(z))))   # mais clara na ponta
        else:
            continue
        op[px, py] = c + (255 if new_cube else sp[px, py][3],)
    return out


def fit_face(src, w, h, crisp):
    """Uma face do Corrodent no tamanho da nossa: ampliada pixel a pixel; diminuída pela média de cada bloco, presa
    à paleta da própria face (crisp: diminuída pixel a pixel, para as pontas recortadas não borrarem)."""
    if w >= src.width and h >= src.height or crisp:
        return src.resize((w, h), Image.NEAREST)
    small = src.resize((w, h), Image.BOX)
    palette = list({q[:3] for q in src.getdata() if q[3]})
    out = small.copy()
    po, ps = out.load(), small.load()
    alpha = src.resize((w, h), Image.NEAREST).load()
    for y in range(h):
        for x in range(w):
            q = ps[x, y]
            if not alpha[x, y][3] or not palette:
                po[x, y] = (0, 0, 0, 0)
                continue
            po[x, y] = min(palette, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, q[:3]))) + (255,)
    return out


# A textura sai com o dobro da resolução (cada unidade do modelo vira 2 x 2 pixels; o modelo continua declarando 64,
# e o Cobblemon mede o UV por ele). O Corrodent tem 1 pixel por unidade: as peças dele entram ampliadas, sem média.
SCALE = 2


def all_faces(uv, size):
    """As 6 faces de um cubo (cima, baixo, leste, frente, oeste, costas), inclusive as de tamanho zero (planos)."""
    u, v = uv
    w, h, d = size
    return [(u + d, v, w, d), (u + d + w, v, w, d), (u, v + d, d, h), (u + d, v + d, w, h),
            (u + d + w, v + d, d, h), (u + 2 * d + w, v + d, w, h)]


def copy_parts(img, geo, kinds, corrodent):
    """Os cubos "copy:<peça>" e "fur:<peça>": cada face recebe a face equivalente da caixa do Corrodent (CORRODENT).
    "fur" é um cubo de Galar que ganha o pelo dele: fica o recorte do original (o vazio continua vazio)."""
    for bone in geo["bones"]:
        for c in bone.get("cubes", []):
            kind = kinds.get(id(c), "")
            if not kind.startswith(("copy:", "fur:")):
                continue
            part = kind.split(":")[1]
            masked = kind.startswith("fur:")
            (cu, cv), csize = CORRODENT[part]
            theirs = all_faces((cu, cv), csize)
            ours = all_faces(c["uv"], [math.ceil(v) for v in c["size"]])
            for (x0, y0, w, h), (tx, ty, tw, th) in zip(ours, theirs):
                if w <= 0 or h <= 0 or tw <= 0 or th <= 0:
                    continue
                x0, y0, w, h = SCALE * x0, SCALE * y0, SCALE * w, SCALE * h
                face = fit_face(corrodent.crop((tx, ty, tx + tw, ty + th)), w, h, part.startswith("ridge"))
                if masked:
                    fp, ip = face.load(), img.load()
                    for j in range(h):
                        for i in range(w):
                            if 0 <= x0 + i < img.width and 0 <= y0 + j < img.height and ip[x0 + i, y0 + j][3] \
                                    and fp[i, j][3]:
                                ip[x0 + i, y0 + j] = fp[i, j]
                else:
                    img.paste(face, (x0, y0))


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
        painted = painted.resize((painted.width * SCALE, painted.height * SCALE), Image.NEAREST)
        copy_parts(painted, new_geo, kinds, corrodent)
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
            save_preview(preview, f"{species}_forlorn", texture.resize(painted.size, Image.NEAREST), [painted])


if __name__ == "__main__":
    main()
