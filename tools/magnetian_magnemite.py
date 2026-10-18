# Magnemite, Magneton e Magnezone Magnetian (Magnetic Caves): os ímãs da caverna, bem vermelhos e bem azuis.
# - Cada ímã (em U) fica com um polo escarlate e o outro azure, com os tons dos ímãs do Alex's Caves (scarlet_magnet e
#   azure_magnet): a ponta e meia barra de cada cor. Para a divisão ficar limpa, a barra do U vira dois cubos (cada
#   metade com um pedaço próprio da textura, assim como os braços: no original eles dividem pixels com o corpo); o vermelho fica sempre do lado de menor coordenada, então todos os ímãs
#   apontam igual.
# - O corpo e os parafusos ficam no metal escuro da galena da caverna (energized_galena), mantendo a luz e a sombra do
#   original. Olhos e as luzes do Magnezone ficam como no original.
# - Shiny: corpo prateado claro e os ímãs brilhando (camada emissiva).
#   /pokespawn magnemite magnetian
#
# Uso: python magnetian_magnemite.py <jar do Cobblemon> <jar do Alex's Caves> <pasta resources do mod> [pasta da prévia]
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

SPECIES = {"magnemite": "0081_magnemite", "magneton": "0082_magneton", "magnezone": "0462_magnezone"}
KEEP = ("eye", "pupil", "red_light", "magnet_lights")  # ficam como no original
SILVER = 0.55   # shiny: quanto o metal clareia


def palette(ac, path):
    img = Image.open(BytesIO(ac.read(path))).convert("RGBA")
    counts = {}
    for p in img.getdata():
        if p[3]:
            counts[p[:3]] = counts.get(p[:3], 0) + 1
    return sorted((c for c, n in counts.items() if n >= 8 and c != (255, 255, 255) and c != (234, 234, 234)),
                  key=lambda c: luma(c + (255,)))


def tone(tones, t):
    t = max(0.0, min(1.0, t)) * (len(tones) - 1)
    i = min(int(t), len(tones) - 2)
    f = t - i
    return tuple(int(a + (b - a) * f) for a, b in zip(tones[i], tones[i + 1]))


def magnets(geo):
    """Os ímãs em U: (osso, barra, braço vermelho, braço azul, eixo que separa os braços)."""
    found = []
    for bone in geo["bones"]:
        cubes = bone.get("cubes", [])
        if "magnet" not in bone["name"] or "lights" in bone["name"] or len(cubes) != 3:
            continue
        sizes = [tuple(c["size"]) for c in cubes]
        arms = [c for c in cubes if sizes.count(tuple(c["size"])) == 2]
        bar = next(c for c in cubes if c not in arms)
        axis = next(a for a in range(3) if arms[0]["origin"][a] != arms[1]["origin"][a])
        red, blue = sorted(arms, key=lambda c: c["origin"][axis])
        found.append((bone, bar, red, blue, axis))
    return found


def free_areas(img, owner, sizes):
    """Um retângulo livre para cada tamanho; aumenta a textura para baixo se faltar espaço."""
    taken = [[owner[y][x] is not None or img.getpixel((x, y))[3] > 0 for x in range(img.width)] for y in range(img.height)]
    spots = []
    for w, h in sizes:
        spot = None
        for y in range(len(taken) - h, -1, -1):
            for x in range(img.width - w, -1, -1):
                if not any(taken[y + j][x + i] for i in range(w) for j in range(h)):
                    spot = (x, y)
                    break
            if spot:
                break
        if spot is None:
            spot = (0, len(taken))
            taken += [[False] * img.width for _ in range(h)]
        for j in range(h):
            for i in range(w):
                taken[spot[1] + j][spot[0] + i] = True
        spots.append(spot)
    return spots, len(taken)


def build(z, ac, species, folder):
    texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{species}.png"))).convert("RGBA")
    geo_json = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{species}.geo.json"))
    model = copy.deepcopy(geo_json)
    geo = model["minecraft:geometry"][0]
    owner = bone_colors(geo, texture.width, texture.height, {b["name"]: b["name"] for b in geo["bones"]})
    found = magnets(geo)

    # Metade da barra: um cubo novo por cor (todos os ímãs da espécie dividem os dois pedaços de textura).
    _, bar0, _, _, axis0 = found[0]
    half = list(bar0["size"])
    half[axis0] = half[axis0] / 2
    hw, hh, hd = half
    box = (int(2 * hd + 2 * hw), int(hd + hh))
    _, _, arm0, _, _ = found[0]
    aw, ah, ad = [round(v) for v in arm0["size"]]
    arm_box = (2 * ad + 2 * aw, ad + ah)
    (red_uv, blue_uv, red_arm_uv, blue_arm_uv), height = free_areas(texture, owner, [box, box, arm_box, arm_box])
    if height > texture.height:
        grown = Image.new("RGBA", (texture.width, height), (0, 0, 0, 0))
        grown.paste(texture, (0, 0))
        texture = grown
        geo["description"]["texture_height"] = height
        owner += [[None] * texture.width for _ in range(height - len(owner))]
    # Os braços ganham uma cópia da textura deles num pedaço só deles.
    for arm, uv in ((found[0][2], red_arm_uv), (found[0][3], blue_arm_uv)):
        region = texture.crop((arm["uv"][0], arm["uv"][1], arm["uv"][0] + arm_box[0], arm["uv"][1] + arm_box[1]))
        texture.paste(region, uv)
    for bone, bar, red, blue, axis in found:
        red["uv"], blue["uv"] = list(red_arm_uv), list(blue_arm_uv)
        lo = copy.deepcopy(bar)
        hi = copy.deepcopy(bar)
        lo["size"] = half[:]
        hi["size"] = half[:]
        hi["origin"] = list(bar["origin"])
        hi["origin"][axis] = bar["origin"][axis] + half[axis]
        lo["uv"], hi["uv"] = list(red_uv), list(blue_uv)
        bone["cubes"] = [lo, hi, red, blue]
    geo["description"]["identifier"] = f"geometry.{species}_magnetian"

    scarlet = palette(ac, "assets/alexscaves/textures/block/neodymium/scarlet_magnet_0.png")
    azure = palette(ac, "assets/alexscaves/textures/block/neodymium/azure_magnet_0.png")
    # Só os cinzas da galena (o bloco tem veios vermelhos do minério, que não entram no metal).
    galena = [c for c in palette(ac, "assets/alexscaves/textures/block/energized_galena_scarlet.png")
              if max(c) - min(c) < 40] + [(128, 116, 140)]
    pole = {}
    for _, _, red, blue, _ in found:
        for cube, color in ((red, "red"), (blue, "blue")):
            for x0, y0, w, h in box_faces(cube["uv"], [round(v) for v in cube["size"]]):
                for y in range(y0, y0 + h):
                    for x in range(x0, x0 + w):
                        pole[(x, y)] = color
    for uv, color in ((red_uv, "red"), (blue_uv, "blue")):
        for j in range(box[1]):
            for i in range(box[0]):
                pole[(uv[0] + i, uv[1] + j)] = color

    src = texture.load()
    results = {}
    for shiny in (False, True):
        out = texture.copy()
        glow = Image.new("RGBA", texture.size, (0, 0, 0, 0))
        op, gp = out.load(), glow.load()
        metal = [tuple(int(c + (255 - c) * SILVER) for c in t) for t in galena] if shiny else galena
        lumas = [luma(src[x, y]) for y in range(texture.height) for x in range(texture.width)
                 if src[x, y][3] and (x, y) not in pole and not (owner[y][x] or "").startswith(KEEP)]
        lo_l, hi_l = min(lumas), max(lumas)
        for y in range(texture.height):
            for x in range(texture.width):
                bone = owner[y][x] or ""
                if (x, y) in pole:
                    # Pedaços novos (sem pixel no original): luz em faixas, como nos blocos de ímã.
                    l = luma(src[x, y]) if src[x, y][3] else 0.35 + 0.4 * (((x + y) % 4) / 3)
                    tones = scarlet if pole[(x, y)] == "red" else azure
                    c = tone(tones, 0.25 + 0.75 * l)
                    op[x, y] = c + (255,)
                    if shiny:
                        gp[x, y] = c + (200,)
                    continue
                if not src[x, y][3] or bone.startswith(KEEP):
                    continue
                t = (luma(src[x, y]) - lo_l) / (hi_l - lo_l)
                op[x, y] = tone(metal, t) + (src[x, y][3],)
        results[shiny] = (out, glow)
    return texture, model, results


def main():
    z, ac = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2])
    resources = Path(sys.argv[3])
    preview = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    for species, folder in SPECIES.items():
        texture, model, results = build(z, ac, species, folder)
        out = resources / f"assets/ecosystems_hollows/textures/pokemon/{species}"
        out.mkdir(parents=True, exist_ok=True)
        tex = f"ecosystems_hollows:textures/pokemon/{species}/"
        results[False][0].save(out / f"{species}_magnetian.png")
        results[True][0].save(out / f"{species}_magnetian_shiny.png")
        results[True][1].save(out / f"{species}_magnetian_shiny_magnets.png")
        model_path = resources / f"assets/ecosystems_hollows/bedrock/pokemon/models/{species}_magnetian.geo.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8", newline="\n")
        resolver = {"species": f"cobblemon:{species}", "order": 2, "variations": [
            {"aspects": ["magnetian"], "model": f"ecosystems_hollows:{species}_magnetian.geo",
             "texture": tex + f"{species}_magnetian.png"},
            {"aspects": ["magnetian", "shiny"], "texture": tex + f"{species}_magnetian_shiny.png",
             "layers": [{"name": "magnets", "emissive": True, "texture": tex + f"{species}_magnetian_shiny_magnets.png"}]},
        ]}
        path = resources / f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/2_ecosystems_hollows_magnetian.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8", newline="\n")
        if preview:
            save_preview(preview, f"{species}_magnetian", texture, [results[False][0], results[True][0]])
        print(species, "ok", texture.size)


if __name__ == "__main__":
    main()
