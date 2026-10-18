# Wishiwashi Candyan: o Sweetish Fish do Alex's Caves, a bala de goma em forma de peixe, em 5 sabores (vermelho, verde,
# amarelo, azul e rosa), com os 6 tons de cada bala tirados da textura do próprio Sweetish Fish.
# - Solo: o corpo todo na goma da cor; o azul do original vira a metade escura dos tons e a barriga branca a metade
#   clara, então o desenho do peixe continua. Pontinhos de açúcar (o tom mais claro) espalhados. O corpo é de goma
#   translúcida (camada "candyan", como o Stufful e o Bewear Candyan), só um pouco: BODY_ALPHA. Olhos, boca e as
#   nadadeiras finas (planos) ficam opacos, na textura de base.
# - Modelo próprio do solo (wishiwashi_candyan): através da goma, faces quase no mesmo lugar brigam e piscam. Os
#   olhos (com a pálpebra) saem 0,05 para fora da cabeça, a boca 0,05 para frente, e o tronco fica um pouco mais
#   fino (inflate) para as laterais dele não encostarem nas da cabeça, onde os dois se sobrepõem.
# - Os olhos são opacos: o branco e o preto como no original, e a íris (o losango azul) no tom escuro da goma.
# - Escola (o peixão, só em batalha): na goma da cor, e os pontos que brilham viram confeitos dos 5 sabores. Fica
#   opaca: o peixão é feito de muitos cubos uns dentro dos outros, e através da goma eles apareceriam.
# - Shiny: goma "azedinha", mais clara e coberta de açúcar.
# - Olhos e boca ficam como no original.
# Forma regional Candyan (aspect "candyan"); o sabor é outro aspect (candyan_<cor>):
#   /pokespawn wishiwashi candyan aspect=candyan_red
#
# Uso: python candyan_wishiwashi.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
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
from candyan import bone_colors, box_faces, luma, save_preview  # noqa: E402

SRC = "assets/cobblemon/textures/pokemon/0746_wishiwashi/"
MODELS = "assets/cobblemon/bedrock/pokemon/models/0746_wishiwashi/"
COLORS = ["red", "green", "yellow", "blue", "pink"]
KEEP_BONES = ("eye_left", "eye_right", "eyefish_")  # olhos: o branco e a pupila ficam como no original
SUGAR = 0.06          # parte dos pixels com açúcar
SHINY_SUGAR = 0.22
BODY_ALPHA = 205      # 0-255: o corpo do solo deixa ver um pouco através


def gummy_tones(ac, color):
    """Os tons da bala (do escuro ao claro), tirados da textura do Sweetish Fish."""
    img = Image.open(BytesIO(ac.read(f"assets/alexscaves/textures/entity/sweetish_fish_{color}.png"))).convert("RGBA")
    return sorted({p[:3] for p in img.getdata() if p[3]}, key=lambda c: luma(c + (255,)))


def tone(tones, t):
    """Ponto t (0..1) da escala de tons, misturando os dois vizinhos."""
    t = max(0.0, min(1.0, t)) * (len(tones) - 1)
    i = min(int(t), len(tones) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(tones[i], tones[i + 1]))


def noise(x, y, seed=0):
    """Ruído fixo por pixel (o mesmo a cada vez que o script roda)."""
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFF) / 0xFFFF


EYE_OUT = 0.05     # quanto os olhos saem da cabeça
JAW_OUT = 0.05     # quanto a boca sai da frente da cabeça
TORSO_INFLATE = -0.03


def candyan_model(geo_json):
    """O modelo do solo com as faces que se encostam afastadas (veja o cabeçalho)."""
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    geo["description"]["identifier"] = "geometry.wishiwashi_candyan"
    bones = {b["name"]: b for b in geo["bones"]}

    def shift(bone, dx=0.0, dz=0.0):
        bone["pivot"] = [round(bone["pivot"][0] + dx, 4), bone["pivot"][1], round(bone["pivot"][2] + dz, 4)]
        for c in bone.get("cubes", []):
            c["origin"] = [round(c["origin"][0] + dx, 4), c["origin"][1], round(c["origin"][2] + dz, 4)]
            if "pivot" in c:
                c["pivot"] = [round(c["pivot"][0] + dx, 4), c["pivot"][1], round(c["pivot"][2] + dz, 4)]
        for child in geo["bones"]:
            if child.get("parent") == bone["name"]:
                shift(child, dx, dz)

    shift(bones["eye_left"], dx=EYE_OUT)
    shift(bones["eye_right"], dx=-EYE_OUT)
    shift(bones["jaw"], dz=-JAW_OUT)
    main = max(bones["torso"]["cubes"], key=lambda c: c["size"][0] * c["size"][1] * c["size"][2])
    main["inflate"] = main.get("inflate", 0) + TORSO_INFLATE
    return model


def keep_map(z, model, width, height):
    geo = json.loads(z.read(MODELS + model))["minecraft:geometry"][0]
    names = {b["name"]: b["name"] for b in geo["bones"]}
    owner = bone_colors(geo, width, height, names)
    img = Image.open(BytesIO(z.read(SRC + model.replace(".geo.json", ".png")))).convert("RGBA")
    px = img.load()

    def keep(x, y):
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in px[x, y][:3]))
        if (h > 0.9 or h < 0.06) and s > 0.25:
            return True  # a boca (vermelha)
        if bool(owner[y][x]) and owner[y][x].startswith(KEEP_BONES):
            return True if s < 0.2 else "iris"  # branco e preto dos olhos; o resto do olho é a íris (opaca)
        return False
    flat = [[False] * width for _ in range(height)]
    for bone in geo["bones"]:
        for cube in bone.get("cubes", []):
            size = [round(v) for v in cube["size"]]
            if isinstance(cube.get("uv"), list) and 0 in size:
                for x0, y0, w, h in box_faces(cube["uv"], size):
                    for y in range(max(0, y0), min(height, y0 + h)):
                        for x in range(max(0, x0), min(width, x0 + w)):
                            flat[y][x] = True
    return [[keep(x, y) for x in range(width)] for y in range(height)], flat


def paint(texture, keep, tones, sugar, pale=0.0, flat=None, body_alpha=None):
    """Devolve (base, camada translúcida ou None). Com body_alpha, o corpo vai para a camada com essa opacidade e a
    base fica só com o que é opaco (olhos, boca e os planos de flat)."""
    src = texture.convert("RGBA")
    out = src.copy()
    layer = Image.new("RGBA", src.size, (0, 0, 0, 0)) if body_alpha else None
    sp, op = src.load(), out.load()
    lp = layer.load() if layer else None
    lumas = [luma(sp[x, y]) for y in range(src.height) for x in range(src.width) if sp[x, y][3] and keep[y][x] is False]
    lo, hi = min(lumas), max(lumas)
    if pale:
        tones = [tuple(int(c + (255 - c) * pale) for c in t) for t in tones]
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            if a == 0 or keep[y][x] is True:
                continue
            if keep[y][x] == "iris":
                op[x, y] = tones[0] + (a,)
                continue
            t = (luma(sp[x, y]) - lo) / (hi - lo)
            c = tones[-1] if noise(x, y) < sugar else tone(tones[:-1], t)
            if layer is not None and not flat[y][x]:
                op[x, y] = (0, 0, 0, 0)
                lp[x, y] = c + (body_alpha,)
            else:
                op[x, y] = c + (a,)
    return out, layer


def sprinkles(emissive, all_tones):
    """Os pontos que brilham da forma Escola viram confeitos: cada um com o tom claro de um dos sabores."""
    src = emissive.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, op = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3]:
                tones = all_tones[int(noise(x, y, 7) * len(all_tones)) % len(all_tones)]
                op[x, y] = tones[-2] + (sp[x, y][3],)
    return out


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    solo = Image.open(BytesIO(z.read(SRC + "wishiwashi_solo.png")))
    school = Image.open(BytesIO(z.read(SRC + "wishiwashi_school.png")))
    school_glow = Image.open(BytesIO(z.read(SRC + "wishiwashi_school_emissive.png")))
    keep_solo, flat_solo = keep_map(z, "wishiwashi_solo.geo.json", *solo.size)
    model_path = resources / "assets/ecosystems_hollows/bedrock/pokemon/models/wishiwashi_candyan.geo.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(candyan_model(json.loads(z.read(MODELS + "wishiwashi_solo.geo.json"))), indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    keep_school, _ = keep_map(z, "wishiwashi_school.geo.json", *school.size)
    tones = {c: gummy_tones(ac, c) for c in COLORS}

    out = resources / "assets/ecosystems_hollows/textures/pokemon/wishiwashi"
    out.mkdir(parents=True, exist_ok=True)
    tex = "ecosystems_hollows:textures/pokemon/wishiwashi/"
    sprinkles(school_glow, list(tones.values())).save(out / "wishiwashi_school_candyan_emissive.png")
    # A forma Escola não usa a goma translúcida do solo: a camada dela é vazia.
    Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(out / "wishiwashi_candyan_empty.png")
    previews = {"solo": [], "school": []}
    for c in COLORS:
        for shiny in (False, True):
            suffix = c + ("_shiny" if shiny else "")
            sugar, pale = (SHINY_SUGAR, 0.35) if shiny else (SUGAR, 0.0)
            s, s_layer = paint(solo, keep_solo, tones[c], sugar, pale, flat_solo, BODY_ALPHA)
            k, _ = paint(school, keep_school, tones[c], sugar, pale)
            s.save(out / f"wishiwashi_solo_candyan_{suffix}_base.png")
            s_layer.save(out / f"wishiwashi_solo_candyan_{suffix}.png")
            k.save(out / f"wishiwashi_school_candyan_{suffix}.png")
            previews["solo"].append(Image.alpha_composite(s_layer, s))
            previews["school"].append(k)

    # A ordem importa: as variações que valem juntas se somam em ordem, então as da forma Escola vêm por último.
    def solo_variation(aspects, suffix):
        return {"aspects": aspects, "texture": tex + f"wishiwashi_solo_candyan_{suffix}_base.png",
                "layers": [{"name": "candyan", "translucent": True, "texture": tex + f"wishiwashi_solo_candyan_{suffix}.png"}]}

    glow = [{"name": "emissive", "emissive": True, "texture": tex + "wishiwashi_school_candyan_emissive.png"},
            {"name": "candyan", "translucent": True, "texture": tex + "wishiwashi_candyan_empty.png"}]
    variations = [{**solo_variation(["candyan"], "red"), "model": "ecosystems_hollows:wishiwashi_candyan.geo"}]
    variations += [solo_variation(["candyan", f"candyan_{c}"], c) for c in COLORS]
    variations += [solo_variation(["candyan", "shiny", f"candyan_{c}"], f"{c}_shiny") for c in COLORS]
    # A forma Escola volta para o modelo do Cobblemon (o "candyan" acima trocou o modelo depois do dela).
    variations += [{"aspects": ["candyan", "school-form"], "model": "cobblemon:wishiwashi_school.geo",
                    "texture": tex + "wishiwashi_school_candyan_red.png", "layers": glow}]
    variations += [{"aspects": ["candyan", "school-form", f"candyan_{c}"],
                    "texture": tex + f"wishiwashi_school_candyan_{c}.png", "layers": glow} for c in COLORS]
    variations += [{"aspects": ["candyan", "school-form", "shiny", f"candyan_{c}"],
                    "texture": tex + f"wishiwashi_school_candyan_{c}_shiny.png", "layers": glow} for c in COLORS]
    path = resources / "assets/cobblemon/bedrock/pokemon/resolvers/0746_wishiwashi/2_ecosystems_hollows_candyan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"species": "cobblemon:wishiwashi", "order": 2, "variations": variations}, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    if preview:
        save_preview(preview, "wishiwashi_solo_candyan", solo, previews["solo"])
        save_preview(preview, "wishiwashi_school_candyan", school, previews["school"][::2])


if __name__ == "__main__":
    main()
