# Noibat e Noivern Forlorn (Forlorn Hollows): o Vesper e o Forsaken do Alex's Caves.
# - Textura: as cores e o pelo do próprio bicho do Alex's Caves (Vesper no Noibat, Forsaken no Noivern): o corpo no
#   marrom-avermelhado bem escuro, com as mechas do pelo deles por cima da luz do original; o roxo e o verde-água das
#   membranas viram o magenta deles; a gola branca vira pelo.
# - Cegos (caçam pelo som, como o Vesper e o Forsaken; o Noibat e o Noivern já são os Pokémon do ultrassom).
# - Noibat Forlorn (o Vesper): os olhos somem de vez (a bochecha continua no lugar), ganha o nariz em folha do Vesper,
#   maior que a cara (copiado da textura dele), e uma gola de pelos em volta do pescoço.
# - Noivern Forlorn (o Forsaken): não voa e anda de quatro. As animações de chão do próprio Noivern já deitam o corpo
#   e apoiam as asas dobradas como patas dianteiras; o modelo perde as membranas grandes das asas, os ossos das asas
#   engrossam (as patas da frente, com força) e os dedos ganham garras sólidas. O poser próprio troca as poses de voo
#   pelas de chão (e a forma não voa: regional_forms.py).
#
# Uso: python forlorn_noivern.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
import colorsys
import copy
import json
import os
import random
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import bone_colors, luma, save_preview  # noqa: E402
from toxian_carvanha import free_area  # noqa: E402

SPECIES = {"noibat": "0714_noibat", "noivern": "0715_noivern"}
# De onde vêm as cores e o pelo de cada um: (textura do Alex's Caves, pedaço do pelo).
REFERENCE = {"noibat": ("vesper", (0, 13, 52, 26)), "noivern": ("forsaken", (0, 32, 64, 96))}
EYE_BONES = ("eye", "pupil")
FUR = 0.55                   # quanto as mechas do pelo pesam sobre a luz do original

# Noibat: o nariz em folha do Vesper (o pedaço magenta da textura dele) e a gola de pelos.
NOSE_CROP = (66, 62, 73, 73)          # a folha do nariz na textura do Vesper (128 x 128): 7 x 11
NOSE_ORIGIN = (-3.5, 9.4, -3.45)      # na frente da cara, logo acima da boca: sobe além da cara (7 x 5)
COLLAR = 3                            # altura dos pelos da gola

# Noivern: membranas grandes das asas somem (os ossos ficam: as animações usam).
NO_MEMBRANE = ("membrane", "wing_trim", "wing_tip", "wing_end")
THICKER = {"shoulder": 0.6, "arm": 0.9, "elbow": 1.1, "hand": 0.8}   # inflate dos ossos das patas da frente
CLAW = (1, 4, 1)                      # as garras: cubos sólidos na ponta dos dedos


def tones(img, test):
    return sorted({p[:3] for p in img.getdata() if p[3] and test(p)}, key=lambda c: luma(c + (255,)))


def tone(ts, t):
    t = max(0.0, min(1.0, t)) * (len(ts) - 1)
    i = min(int(t), len(ts) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(ts[i], ts[i + 1]))


def kind(p, species=""):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
    if s < 0.25 and v > 0.7:
        return "fluff"
    if species == "noibat" and v > 0.72 and 0.7 < h < 0.95:
        return "fluff"          # a cara lilás clara do Noibat: no Vesper a cara é de pelo
    if s > 0.2 and (0.7 < h < 0.95):
        return "purple"
    if s > 0.2 and (0.4 < h < 0.6):
        return "membrane"
    if s > 0.35 and (h > 0.95 or h < 0.05):
        return "red"
    if s > 0.35 and 0.1 < h < 0.2:
        return "yellow"
    return "body"


def palettes_of(reference):
    body = tones(reference, lambda p: max(p[:3]) < 80 and p[0] >= p[2])
    membrane = tones(reference, lambda p: p[0] > 70 and p[2] > 40 and p[0] > p[1] * 1.6)
    teeth = tones(reference, lambda p: p[0] > 200 and p[1] > 180 and p[2] < 200)
    return {"body": body, "membrane": membrane, "teeth": teeth or [(220, 200, 140), (250, 235, 180)]}


def paint(texture, owner, fur, palettes, species):
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()
    ranges = {}
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3]:
                k = kind(sp[x, y], species)
                l = luma(sp[x, y])
                lo, hi = ranges.get(k, (l, l))
                ranges[k] = (min(lo, l), max(hi, l))
    fw, fh = fur.size
    for y in range(src.height):
        for x in range(src.width):
            if not sp[x, y][3]:
                continue
            bone = owner[y][x] or ""
            if bone.startswith(EYE_BONES):
                if species == "noibat" or bone.startswith(("eyelid", "pupil")):
                    op[x, y] = (0, 0, 0, 0)    # sem olho: o cubo some e a bochecha aparece
                else:
                    op[x, y] = tone(palettes["body"], 0.2) + (sp[x, y][3],)   # pele fechada
                continue
            k = kind(sp[x, y], species)
            if species == "noibat" and k == "purple" and not bone.startswith(("ear", "wing", "finger")):
                k = "body"   # no Vesper só as orelhas e as asas são magenta; cabeça e corpo são de pelo
            lo, hi = ranges.get(k, (0.0, 1.0))
            t = (luma(sp[x, y]) - lo) / (hi - lo) if hi > lo else 0.5
            if k in ("body", "fluff"):
                f = luma(fur.getpixel((x % fw, y % fh)))
                lo_f = min(luma(p) for p in fur.getdata() if p[3])
                hi_f = max(luma(p) for p in fur.getdata() if p[3])
                f = (f - lo_f) / (hi_f - lo_f) if hi_f > lo_f else 0.5
                t = (1 - FUR) * t + FUR * f + (0.15 if k == "fluff" else 0)
                c = tone(palettes["body"], t)
            elif k == "yellow":
                c = tone(palettes["teeth"], 0.5 + 0.5 * t)
            else:
                c = tone(palettes["membrane"], 0.15 + 0.85 * t)
            op[x, y] = c + (sp[x, y][3],)
    return out


def fur_strip(width, height, palette, seed):
    """Uma fileira de pelos para a gola: fios de alturas diferentes, escuros na raiz e mais claros na ponta."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    p = img.load()
    for x in range(width):
        length = rng.randint(max(1, height - 2), height)
        for y in range(height - length, height):
            t = 0.25 + 0.55 * (height - 1 - y) / max(1, height - 1) + 0.15 * rng.random()
            p[x, y] = tone(palette, t) + (255,)
    return img


def plane_uv(img, owner, w, h):
    """Um pedaço livre da textura para um plano w x h (UV de caixa com profundidade 0: frente e costas lado a lado)."""
    return free_area(img, owner, (2 * w, h))


def noibat_model(geo_json, texture, owner, vesper, palettes):
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    geo["description"]["identifier"] = "geometry.noibat_forlorn"
    bones = {b["name"]: b for b in geo["bones"]}
    # Nariz em folha: o pedaço magenta do Vesper, ampliado 1:1, na frente e nas costas de um plano.
    nose = vesper.crop(NOSE_CROP)
    w, h = nose.size
    uv = plane_uv(texture, owner, w, h)
    texture.paste(nose, uv)
    texture.paste(nose.transpose(Image.FLIP_LEFT_RIGHT), (uv[0] + w, uv[1]))
    for y in range(uv[1], uv[1] + h):
        for x in range(uv[0], uv[0] + 2 * w):
            owner[y][x] = "nose"
    ox, oy, oz = NOSE_ORIGIN
    bones["head_angle"]["cubes"].append({"origin": [ox, oy, oz], "size": [w, h, 0], "uv": list(uv)})
    # Gola de pelos: quatro fileiras em volta do pescoço, abertas para fora.
    strip_w = 6
    for i, (side, rot) in enumerate((("front", [-25, 0, 0]), ("back", [25, 0, 0]),
                                     ("left", [0, 0, -25]), ("right", [0, 0, 25]))):
        strip = fur_strip(strip_w, COLLAR, palettes["body"], i)
        uv = plane_uv(texture, owner, strip_w, COLLAR)
        texture.paste(strip, uv)
        texture.paste(strip, (uv[0] + strip_w, uv[1]))
        for y in range(uv[1], uv[1] + COLLAR):
            for x in range(uv[0], uv[0] + 2 * strip_w):
                owner[y][x] = "collar"
        y0 = 8.0
        if side in ("front", "back"):
            z = -1.6 if side == "front" else 2.1
            cube = {"origin": [-strip_w / 2, y0, z], "size": [strip_w, COLLAR, 0], "uv": list(uv),
                    "pivot": [0, y0, z], "rotation": rot}
        else:
            x = 1.85 if side == "left" else -1.85
            cube = {"origin": [x, y0, 0.25 - strip_w / 2], "size": [0, COLLAR, strip_w], "uv": list(uv),
                    "pivot": [x, y0, 0.25], "rotation": rot}
        bones["torso"]["cubes"].append(cube)
    return model


def noivern_model(geo_json, texture, owner, palettes):
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    geo["description"]["identifier"] = "geometry.noivern_forlorn"
    # Garras: um cubo sólido por dedo, pintado do marrom da base ao preto da ponta.
    cw, ch, cd = CLAW
    claw_uv = free_area(texture, owner, (2 * cd + 2 * cw, cd + ch))
    p = texture.load()
    for j in range(cd + ch):
        for i in range(2 * cd + 2 * cw):
            t = j / max(1, cd + ch - 1)
            base = tone(palettes["body"], 0.5)
            p[claw_uv[0] + i, claw_uv[1] + j] = tuple(int(c * (1 - 0.85 * t)) for c in base) + (255,)
    for bone in geo["bones"]:
        name = bone["name"]
        if any(k in name for k in NO_MEMBRANE):
            bone["cubes"] = []
        for prefix, amount in THICKER.items():
            if name.startswith(prefix + "_") and "membrane" not in name:
                for c in bone.get("cubes", []):
                    c["inflate"] = c.get("inflate", 0) + amount
        if name.startswith("finger") and name.endswith("2"):
            # A ponta do dedo vira uma garra: cubo da mesma base do plano, mais longo e grosso.
            old = bone["cubes"][0]
            ox, oy, oz = old["origin"]
            bone["cubes"] = [{"origin": [ox - cw / 2, oy, oz], "size": [cw, ch, cd], "uv": list(claw_uv)}]
    return model


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    refs = {name: Image.open(BytesIO(ac.read(f"assets/alexscaves/textures/entity/{name}.png"))).convert("RGBA")
            for name in ("vesper", "forsaken")}
    for species, folder in SPECIES.items():
        ref_name, fur_tile = REFERENCE[species]
        reference = refs[ref_name]
        palettes = palettes_of(reference)
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{species}.png")))
        geo_json = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{species}.geo.json"))
        geo = geo_json["minecraft:geometry"][0]
        owner = bone_colors(geo, texture.width, texture.height, {b["name"]: b["name"] for b in geo["bones"]})
        painted = paint(texture, owner, reference.crop(fur_tile), palettes, species)
        if species == "noibat":
            model = noibat_model(geo_json, painted, owner, refs["vesper"], palettes)
        else:
            model = noivern_model(geo_json, painted, owner, palettes)
        out = resources / f"assets/ecosystems_hollows/textures/pokemon/{species}"
        out.mkdir(parents=True, exist_ok=True)
        painted.save(out / f"{species}_forlorn.png")
        model_path = resources / f"assets/ecosystems_hollows/bedrock/pokemon/models/{species}_forlorn.geo.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8", newline="\n")
        variation = {"aspects": ["forlorn"], "model": f"ecosystems_hollows:{species}_forlorn.geo",
                     "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_forlorn.png"}
        if species == "noivern":
            variation["poser"] = "ecosystems_hollows:noivern_forlorn"
            poser = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/posers/{folder}/{species}.json"))
            poses = poser["poses"]
            # Sem voo: pairar vira ficar parado no chão; voar e planar viram andar.
            ground = {"HOVER": "standing", "FLY": "walking"}
            for name in ("hover", "fly", "glide"):
                pose = poses.pop(name, None)
                for pose_type in (pose or {}).get("poseTypes", []):
                    target = poses[ground.get(pose_type, "standing")]
                    if pose_type not in target["poseTypes"]:
                        target["poseTypes"].append(pose_type)
            poser_path = resources / "assets/ecosystems_hollows/bedrock/pokemon/posers/noivern_forlorn.json"
            poser_path.parent.mkdir(parents=True, exist_ok=True)
            poser_path.write_text(json.dumps(poser, indent=2) + "\n", encoding="utf-8", newline="\n")
        resolver = {"species": f"cobblemon:{species}", "order": 2, "variations": [variation]}
        path = resources / f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/2_ecosystems_hollows_forlorn.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
        if preview:
            save_preview(preview, f"{species}_forlorn", texture, [painted])


if __name__ == "__main__":
    main()
