# Ponyta e Rapidash Candyan: o Ponyta e o Rapidash de Galar (o unicórnio) com os sabores e os padrões dos
# Candicorns do Alex's Caves. Cada sabor tem cores e padrões próprios por parte do corpo, e o chifre vira uma
# bengala de doce em espiral:
#   milho doce (candy_corn): faixas amarelo/laranja/branco, crina amarela escorrendo calda
#   bengala de hortelã (peppermint): listras diagonais vermelhas e brancas
#   menta com chocolate (mint_chip): verde-menta com gotas de chocolate
#   cereja com gelo (cherry_ice): vermelho com gelo azul escorrendo
#   algodão-doce (cotton_candy): azul com redemoinhos rosa
# A luz e a sombra vêm da textura original, esticadas numa rampa (cada parte vai do escuro ao claro), para não ficar
# lisa. O focinho fica claro e os cascos escuros, como nos Candicorns. No Rapidash saem os tufos longos das patas
# e os dois rabos dos lados (fica só o do meio); a crina continua igual.
# São a forma regional Candyan (aspect "candyan", em data/ecosystems_hollows/species_additions), com o modelo e o
# poser do de Galar; o sabor é a feature "candicorn" (regional_forms.py), sorteada quando nasce:
#   /pokespawn ponyta candyan peppermint shiny
# Shiny: o mesmo sabor coberto de folha de ouro (chifre e cascos dourados) e açúcar cristalizado brilhando na crina e
# no rabo (pontos de brilho, e a crina acende no escuro, numa camada que brilha).
#
# Uso: python candyan_ponyta.py <jar do Cobblemon> <pasta resources do mod> [pasta da prévia]
import json
import math
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candyan import box_faces, luma, luma_ranges, ramp, save_preview, shade_t  # noqa: E402

SPECIES = {"ponyta": ("0077_ponyta", "ponyta_galar"), "rapidash": ("0078_rapidash", "rapidash_galar")}

WHITE, CREAM = (250, 246, 240), (255, 238, 205)
YELLOW, ORANGE, CARAMEL = (255, 206, 60), (246, 134, 36), (196, 104, 34)
RED, DARK_RED = (226, 36, 52), (160, 20, 36)
MINT, DARK_MINT, CHOCO = (120, 226, 170), (46, 168, 110), (96, 56, 34)
ICE, ICE_LIGHT = (130, 200, 245), (210, 238, 255)
PINK, BLUE = (255, 150, 205), (96, 160, 240)
HOOF = (64, 26, 70)  # os cascos roxo-escuros dos Candicorns
GOLD, GOLD_LIGHT = (232, 176, 48), (255, 236, 150)   # shiny: folha de ouro
# O que sai do Rapidash (fica transparente): os tufos longos das patas e os rabos dos lados.
REMOVED = {"rapidash": ("leg_fluff", "tail_left", "tail_right")}


def part_of(bone):
    """Que parte do corpo é o osso (o que não está aqui fica como no original: olhos, pálpebras)."""
    if bone is None or bone.startswith("eye"):
        return None
    if bone.startswith("horn"):
        return "horn"
    if bone.startswith("muzzle"):
        return "muzzle"
    if bone.endswith("3") and bone.startswith("leg_") and not bone.startswith("leg_fluff"):
        return "hoof"
    if bone.startswith("leg_fluff"):
        return "fluff"
    if bone.startswith("leg"):
        return "legs"
    if bone.startswith("hair") or bone.startswith("tail"):
        return "mane"
    return "body"


def noise(x, y, seed=0):
    """Ruído fixo por pixel (0 a 1), para gotas e escorridos."""
    n = math.sin(x * 12.9898 + y * 78.233 + seed * 37.719) * 43758.5453
    return n - math.floor(n)


def stripes(x, y, a, b, width=3):
    return a if ((x + y) // width) % 2 == 0 else b


def drip(fx, fy, fw, fh, x, top, rest, depth=0.35):
    """A parte de cima da face coberta (calda, gelo) escorrendo em pingos de comprimentos diferentes."""
    length = fh * (depth * 0.5 + depth * noise(x, 0, 7))
    return top if fy < max(1, length) else rest


def candy_corn(part, x, y, fx, fy, fw, fh):
    if part == "muzzle":
        return WHITE
    if part == "horn":
        return stripes(x, y, ORANGE, WHITE)
    if part == "mane":
        return drip(fx, fy, fw, fh, x, CARAMEL, YELLOW, 0.3)
    if part in ("legs", "fluff"):  # o doce de milho: amarelo, laranja e a ponta branca
        t = fy / max(1, fh - 1)
        return YELLOW if t < 0.4 else ORANGE if t < 0.8 else WHITE
    return ORANGE


def peppermint(part, x, y, fx, fy, fw, fh):
    if part == "muzzle":
        return WHITE
    if part == "horn":
        return stripes(x, y, RED, WHITE, 2)
    if part == "mane":
        return stripes(x, y, RED, DARK_RED, 4)
    if part == "body":
        return stripes(x, y, RED, WHITE, 4)
    return stripes(x, y, WHITE, RED, 3)


def mint_chip(part, x, y, fx, fy, fw, fh):
    if part == "muzzle":
        return (215, 250, 232)
    if part == "horn":
        return stripes(x, y, MINT, WHITE)
    chip = noise(x, y, 3) < 0.09
    if part == "mane":
        return CHOCO if chip else stripes(x, y, DARK_MINT, MINT, 4)
    return CHOCO if chip else MINT


def cherry_ice(part, x, y, fx, fy, fw, fh):
    if part == "muzzle":
        return ICE_LIGHT
    if part == "horn":
        return stripes(x, y, ICE, ICE_LIGHT)
    if part == "mane":
        return drip(fx, fy, fw, fh, x, ICE_LIGHT, ICE, 0.4)
    if part == "body":
        return drip(fx, fy, fw, fh, x, ICE_LIGHT, RED, 0.2)
    t = fy / max(1, fh - 1)  # pernas vermelhas com a ponta de gelo
    return ICE if t > 0.75 else RED


def cotton_candy(part, x, y, fx, fy, fw, fh):
    if part == "muzzle":
        return (255, 205, 230)
    if part == "horn":
        return stripes(x, y, PINK, BLUE)
    swirl = math.sin((x + 3 * math.sin(y / 2.5)) / 2.2) > 0.2
    if part in ("mane", "fluff"):
        return PINK if swirl else (255, 190, 225)
    if part == "body":
        return PINK if swirl and noise(x // 3, y // 3, 5) < 0.25 else BLUE
    return BLUE


FLAVORS = {"candy_corn": candy_corn, "peppermint": peppermint, "mint_chip": mint_chip,
           "cherry_ice": cherry_ice, "cotton_candy": cotton_candy}


def face_map(geo, width, height):
    """Para cada pixel da textura: (osso, x e y dentro da face, largura e altura da face)."""
    owner = [[None] * width for _ in range(height)]
    for bone in geo["bones"]:
        for cube in bone.get("cubes", []):
            uv = cube.get("uv")
            if not isinstance(uv, list):
                continue
            for x0, y0, w, h in box_faces(uv, [round(v) for v in cube["size"]]):
                for y in range(max(0, y0), min(height, y0 + h)):
                    for x in range(max(0, x0), min(width, x0 + w)):
                        owner[y][x] = (bone["name"], x - x0, y - y0, w, h)
    return owner


def paint(texture, owner, flavor, removed=(), shiny=False):
    src = texture.convert("RGBA")
    out = src.copy()
    sp, op = src.load(), out.load()
    ranges = luma_ranges(src, lambda x, y: owner[y][x] and part_of(owner[y][x][0]))
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] == 0 or owner[y][x] is None:
                continue
            bone, fx, fy, fw, fh = owner[y][x]
            if bone.startswith(removed):
                op[x, y] = (0, 0, 0, 0)
                continue
            part = part_of(bone)
            if part is None:
                continue
            color = HOOF if part == "hoof" else flavor(part, x, y, fx, fy, fw, fh)
            t = shade_t(ranges, part, luma(sp[x, y]))
            if shiny and part == "hoof":
                color = GOLD
            elif shiny and part == "horn":
                color = stripes(x, y, GOLD, GOLD_LIGHT, 2)
            elif shiny and part == "mane" and noise(x, y, 11) < 0.12:
                color, t = WHITE, 1.0          # cristais de açúcar
            op[x, y] = ramp(color, t) + (sp[x, y][3],)
    return out


def glow_layer(img, owner):
    """A crina e o rabo do shiny, numa camada que brilha no escuro (o resto fica vazio)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ip, lp = img.load(), layer.load()
    for y in range(img.height):
        for x in range(img.width):
            if owner[y][x] and part_of(owner[y][x][0]) == "mane" and ip[x, y][3]:
                lp[x, y] = ip[x, y]
    return layer


def main():
    z = zipfile.ZipFile(sys.argv[1])
    resources = Path(sys.argv[2])
    preview = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    for species, (folder, name) in SPECIES.items():
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{name}.png")))
        geo = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{name}.geo.json"))["minecraft:geometry"][0]
        owner = face_map(geo, texture.width, texture.height)
        out = resources / "assets/ecosystems_hollows/textures/pokemon" / species
        out.mkdir(parents=True, exist_ok=True)
        variants = []
        for flavor, fn in FLAVORS.items():
            img = paint(texture, owner, fn, REMOVED.get(species, ()))
            img.save(out / f"{species}_candyan_{flavor}.png")
            shiny = paint(texture, owner, fn, REMOVED.get(species, ()), shiny=True)
            shiny.save(out / f"{species}_candyan_{flavor}_shiny.png")
            glow_layer(shiny, owner).save(out / f"{species}_candyan_{flavor}_shiny_emissive.png")
            variants += [img, shiny]
        # O brilho do Ponyta de Galar (crina lilás e verde) não combina com os doces: camada vazia no lugar.
        Image.new("RGBA", texture.size, (0, 0, 0, 0)).save(out / f"{species}_candyan_emissive.png")

        # O modelo e o poser vêm do resolver do de Galar.
        galar = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/1_{species}_galarian.json"))
        galar = galar["variations"][0]
        resolver = {"species": f"cobblemon:{species}", "order": 2, "variations": [
            {"aspects": ["candyan"], "poser": galar["poser"], "model": galar["model"],
             "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_candyan_peppermint.png",
             "layers": [{"name": "emissive", "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_candyan_emissive.png",
                         "emissive": True}]}] + [
            {"aspects": ["candyan", f"candyan_{flavor}"],
             "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_candyan_{flavor}.png",
             "layers": [{"name": "emissive", "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_candyan_emissive.png",
                         "emissive": True}]}
            for flavor in FLAVORS] + [
            {"aspects": ["candyan", "shiny", f"candyan_{flavor}"],
             "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_candyan_{flavor}_shiny.png",
             "layers": [{"name": "emissive",
                         "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_candyan_{flavor}_shiny_emissive.png",
                         "emissive": True}]}
            for flavor in FLAVORS]}
        path = resources / f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/2_ecosystems_hollows_candyan.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8")
        if preview:
            save_preview(preview, f"{species}_candyan", texture, variants)


if __name__ == "__main__":
    main()
