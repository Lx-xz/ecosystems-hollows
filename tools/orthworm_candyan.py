# Gera o Orthworm Candyan (de chiclete, no lugar do Gum Worm do Alex's Caves) a partir do Orthworm do Cobblemon:
# - modelo com 11 segmentos no rabo (o original tem 5), com a ponta original no fim;
# - animações com os segmentos novos repetindo a onda dos anteriores;
# - poser apontando para essas animações;
# - textura listrada (roxo, laranja, verde-água), com uma faixa própria para cada segmento novo;
#   placas das pernas na cor das pernas e boca roxa por dentro;
# - shiny: bala de hortelã listrada (vermelho, branco e menta);
# - pose "na areia" (meio enterrado) também nos blocos macios da Candy Cavity.
#
# Uso: python orthworm_candyan.py <jar do Cobblemon> <pasta resources do mod> [pasta da prévia]
import copy
import json
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import colorsys  # noqa: E402

from candyan import bone_colors, box_faces, luma, save_preview, segmented  # noqa: E402

NAME = "orthworm_candyan"
SRC = "0968_orthworm"
# O rabo original tem 5 segmentos: grosso, junta, grosso, junta e a ponta (grossa). Os novos entram antes da
# ponta, alternando grosso e junta; a ponta original vira o último. Para fechar a alternância na ponta, o total
# precisa ser ímpar: 11.
TAIL_SEGMENTS = 11
TIP = f"segment{TAIL_SEGMENTS}"
NEW_SEGMENTS = range(5, TAIL_SEGMENTS)  # 5 a 10; ímpares grossos, pares juntas
# Cada segmento novo ganha uma faixa própria da textura, abaixo da original (uma cópia do layout dela), para
# poder ter a sua cor na listra. A textura cresce para baixo: 64 de altura por faixa.
BAND = 64

PURPLE, ORANGE, TEAL = (164, 70, 224), (246, 170, 58), (82, 214, 176)
EYE, PUPIL = (252, 222, 64), (30, 24, 40)
# Shiny: bala de hortelã listrada (vermelho, branco e menta).
RED, WHITE, MINT = (226, 42, 58), (246, 240, 236), (112, 226, 170)
# Paletas: listras (da cabeça para trás), cabeça, braços e placas das pernas, boca.
PALETTES = {
    "gum": dict(stripes=[PURPLE, ORANGE, TEAL], head=TEAL, arm=ORANGE, mouth=PURPLE),
    "gum_shiny": dict(stripes=[RED, WHITE, MINT], head=MINT, arm=WHITE, mouth=RED),
}
# Da cabeça para trás: o peito começa na primeira cor e as listras seguem alternando.
BODY_CHAIN = ["chest", "top_body3", "top_body2", "top_body"] + [f"segment{i}" for i in range(1, TAIL_SEGMENTS + 1)]


def bone_palette(stripes, head, arm, mouth):
    colors = {"head": head, "jaw": head, "arm": arm, "eyes": EYE, "eye_expression": EYE, "eyelid": head, "pupil": PUPIL}
    colors.update({bone: stripes[i % 3] for i, bone in enumerate(BODY_CHAIN)})
    return colors

# Cada segmento novo copia o movimento de um original: grossos do 3, juntas do 4 ou do 2. Se a animação não
# mexe o primeiro da lista, usa o segundo.
ANIMATION_SOURCE = {n: (["segment3", "segment5"] if n % 2 else ["segment4", "segment2"]) for n in NEW_SEGMENTS}


def extend_model(geo):
    """Coloca os segmentos 5 a 10 entre o 4 e a ponta do rabo; a ponta original (segment5) vira o segment11."""
    geo = copy.deepcopy(geo)
    geo["description"]["identifier"] = f"geometry.{NAME}"
    geo["description"]["texture_height"] = BAND * (1 + len(NEW_SEGMENTS))
    geo["description"]["visible_bounds_width"] = 9  # o corpo ficou bem mais comprido
    bones = {b["name"]: b for b in geo["bones"]}
    joint, thick, tip = bones["segment4"], bones["segment3"], bones["segment5"]

    def shifted(source, name, parent, shift, band):
        bone = {"name": name, "parent": parent,
                "pivot": [source["pivot"][0], source["pivot"][1], source["pivot"][2] + shift], "cubes": []}
        for cube in source["cubes"]:
            new = copy.deepcopy(cube)
            new["origin"] = [cube["origin"][0], cube["origin"][1], cube["origin"][2] + shift]
            if band:
                new["uv"] = [cube["uv"][0], cube["uv"][1] + BAND * band]
            bone["cubes"].append(new)
        return bone

    # Como no original: a parte grossa começa 2 depois do início da junta anterior, e a junta começa 1 antes do
    # fim da parte grossa anterior (elas se sobrepõem).
    joint_start = joint["cubes"][0]["origin"][2]
    thick_end = None
    for band, n in enumerate(NEW_SEGMENTS, start=1):
        if n % 2:  # grosso
            start = joint_start + 2
            thick_end = start + thick["cubes"][0]["size"][2]
            source = thick
        else:  # junta
            start = joint_start = thick_end - 1
            source = joint
        geo["bones"].append(shifted(source, f"segment{n}", f"segment{n - 1}", start - source["cubes"][0]["origin"][2], band))

    # A ponta original vai para o fim, ligada ao último segmento novo, com a textura dela de sempre.
    geo["bones"].remove(tip)
    tip_start = joint_start + 2
    tip_shift = tip_start - tip["cubes"][0]["origin"][2]
    geo["bones"].append(shifted(tip, TIP, f"segment{TAIL_SEGMENTS - 1}", tip_shift, 0))
    # O que estava preso na ponta (os pontos de referência locator_tail e locator_tail_tip) vai junto com ela.
    # O Cobblemon exige que o osso pai venha antes do filho na lista.
    for bone in [b for b in geo["bones"] if b.get("parent") == "segment5" and not b["name"].startswith("segment")]:
        geo["bones"].remove(bone)
        moved = copy.deepcopy(bone)
        moved["parent"] = TIP
        moved["pivot"] = [bone["pivot"][0], bone["pivot"][1], bone["pivot"][2] + tip_shift]
        for cube in moved.get("cubes", []):
            cube["origin"][2] += tip_shift
        for name, locator in moved.get("locators", {}).items():
            if isinstance(locator, list):
                locator[2] += tip_shift
            elif isinstance(locator, dict) and "offset" in locator:
                locator["offset"][2] += tip_shift
        geo["bones"].append(moved)
    return geo


def extend_animations(anim):
    """Renomeia as animações para o grupo novo, leva o movimento da ponta para o segment11 e copia o movimento
    para os segmentos novos."""
    out = {"format_version": anim.get("format_version", "1.8.0"), "animations": {}}
    for name, body in anim["animations"].items():
        body = copy.deepcopy(body)
        bones = body.get("bones", {})
        original = {k: copy.deepcopy(v) for k, v in bones.items()}
        if "segment5" in bones:
            bones[TIP] = bones.pop("segment5")
        for n, sources in ANIMATION_SOURCE.items():
            source = next((s for s in sources if s in original), None)
            if source:
                bones[f"segment{n}"] = copy.deepcopy(original[source])
        out["animations"][name.replace("animation.orthworm.", f"animation.{NAME}.")] = body
    return out


# Blocos macios da Candy Cavity (Alex's Caves): o Orthworm afunda neles como afunda na areia.
SOFT_BLOCKS = ["minecraft:sand", "minecraft:red_sand"] + [f"alexscaves:{b}" for b in (
    "block_of_frosting", "block_of_vanilla_frosting", "block_of_chocolate_frosting", "block_of_chocolate",
    "block_of_frosted_chocolate", "cake_layer", "cookie_block", "vanilla_ice_cream", "chocolate_ice_cream")]


def retarget_poser(poser):
    """O poser do Orthworm, mas tocando as animações do grupo novo."""
    text = json.dumps(poser)
    for call in ("q.bedrock(", "q.bedrock_primary(", "q.bedrock_stateful(", "q.bedrock_quirk("):
        text = text.replace(f"{call}'orthworm'", f"{call}'{NAME}'")
    # A pose "na areia" (corpo meio enterrado) vale também nos blocos macios da Candy Cavity.
    blocks = ", ".join(f"'{b}'" for b in SOFT_BLOCKS)
    text = text.replace("'minecraft:sand', 'minecraft:red_sand'", blocks)
    return json.loads(text)


def bone_map(geo, width, height):
    """Nome do osso de cada pixel da textura (None onde nenhum cubo usa)."""
    owner = [[None] * width for _ in range(height)]
    for bone in geo["bones"]:
        for cube in bone.get("cubes", []):
            uv = cube.get("uv")
            if not isinstance(uv, list):
                continue
            for x0, y0, w, h in box_faces(uv, [round(v) for v in cube["size"]]):
                for y in range(max(0, y0), min(height, y0 + h)):
                    for x in range(max(0, x0), min(width, x0 + w)):
                        owner[y][x] = bone["name"]
    return owner


def recolor_details(original, gum, owner, arm, mouth_color):
    """Detalhes que a pintura por osso apaga:
    - as placas azuis de onde saem as pernas ficam da cor das pernas;
    - a boca por dentro (vermelho escuro e a língua rosada) fica roxa."""
    op, gp = original.load(), gum.load()
    for y in range(original.height):
        for x in range(original.width):
            r, g, b, a = op[x, y]
            if a == 0:
                continue
            h, sat, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            mouth = owner[y][x] in ("head", "jaw") and r > g and (val < 0.4 or (sat < 0.6 and val < 0.82))
            if sat > 0.35 and 0.5 < h < 0.72:
                color = arm
            elif mouth:
                color = mouth_color
            else:
                continue
            k = 0.7 + 0.5 * luma(op[x, y])
            gp[x, y] = tuple(min(255, int(c * k)) for c in color) + (255,)


def main():
    jar, resources = sys.argv[1], Path(sys.argv[2])
    preview_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(jar)
    base = "assets/cobblemon/bedrock/pokemon"
    model = json.loads(z.read(f"{base}/models/{SRC}/orthworm.geo.json"))
    anim = json.loads(z.read(f"{base}/animations/{SRC}/orthworm.animation.json"))
    poser = json.loads(z.read(f"{base}/posers/{SRC}/orthworm.json"))
    texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{SRC}/orthworm.png"))).convert("RGBA")

    model["minecraft:geometry"][0] = extend_model(model["minecraft:geometry"][0])
    out = resources / "assets/ecosystems_hollows/bedrock/pokemon"
    for path, data in ((out / f"models/{NAME}.geo.json", model),
                       (out / f"animations/{NAME}.animation.json", extend_animations(anim)),
                       (out / f"posers/{NAME}.json", retarget_poser(poser))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # Textura mais alta: uma cópia da original por faixa, uma faixa para cada segmento novo.
    bands = 1 + len(NEW_SEGMENTS)
    tall = Image.new("RGBA", (texture.width, BAND * bands), (0, 0, 0, 0))
    for band in range(bands):
        tall.paste(texture, (0, BAND * band))
    geo = model["minecraft:geometry"][0]
    owner = bone_map(geo, tall.width, tall.height)
    tex_dir = resources / "assets/ecosystems_hollows/textures/pokemon/orthworm"
    tex_dir.mkdir(parents=True, exist_ok=True)
    variants = []
    for name, palette in PALETTES.items():
        gum = segmented(tall, bone_colors(geo, tall.width, tall.height, bone_palette(**palette)), solid=(PUPIL,))
        recolor_details(tall, gum, owner, palette["arm"], palette["mouth"])
        gum.save(tex_dir / f"orthworm_candyan_{name}.png")
        variants.append(gum)
    if preview_dir:
        save_preview(preview_dir, "orthworm", tall, variants)


if __name__ == "__main__":
    main()
