# Gera o Orthworm Candyan (de chiclete, no lugar do Gum Worm do Alex's Caves) a partir do Orthworm do Cobblemon:
# - modelo com 10 segmentos no rabo (o original tem 5);
# - animações com os segmentos novos repetindo a onda dos anteriores;
# - poser apontando para essas animações;
# - textura listrada (roxo, laranja, verde-água), com uma faixa própria para cada segmento novo.
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
from candyan import bone_colors, save_preview, segmented  # noqa: E402

NAME = "orthworm_candyan"
SRC = "0968_orthworm"
TAIL_SEGMENTS = 10
# Cada segmento novo ganha uma faixa própria da textura, abaixo da original (uma cópia do layout dela), para
# poder ter a sua cor na listra. A textura cresce para baixo: 64 de altura por faixa.
BAND = 64

PURPLE, ORANGE, TEAL = (164, 70, 224), (246, 170, 58), (82, 214, 176)
EYE, PUPIL = (252, 222, 64), (30, 24, 40)
STRIPES = [PURPLE, ORANGE, TEAL]
# Da cabeça para trás: o peito começa roxo e as listras seguem alternando.
BODY_CHAIN = ["chest", "top_body3", "top_body2", "top_body"] + [f"segment{i}" for i in range(1, TAIL_SEGMENTS + 1)]
COLORS = {"head": TEAL, "jaw": TEAL, "arm": ORANGE, "eyes": EYE, "eye_expression": EYE, "eyelid": TEAL, "pupil": PUPIL}
COLORS.update({bone: STRIPES[i % 3] for i, bone in enumerate(BODY_CHAIN)})

# Cada segmento novo copia o movimento de um original: juntas finas (2, 4) e partes grossas (3, 5). Se a
# animação não mexe o primeiro da lista, usa o segundo.
ANIMATION_SOURCE = {
    6: ["segment2", "segment4"], 7: ["segment3", "segment5"], 8: ["segment4", "segment2"],
    9: ["segment5", "segment3"], 10: ["segment2", "segment4"],
}
NEW_SEGMENTS = range(6, TAIL_SEGMENTS + 1)


def extend_model(geo):
    """Acrescenta os segmentos 6 a 10 depois do 5, alternando junta e parte grossa, como no original."""
    geo = copy.deepcopy(geo)
    geo["description"]["identifier"] = f"geometry.{NAME}"
    geo["description"]["texture_height"] = BAND * (1 + len(NEW_SEGMENTS))
    geo["description"]["visible_bounds_width"] = 9  # o corpo ficou bem mais comprido
    bones = {b["name"]: b for b in geo["bones"]}
    joint, thick = bones["segment4"], bones["segment3"]
    # Como no original: a junta começa 1 antes do fim da parte grossa anterior (elas se sobrepõem),
    # e a parte grossa seguinte começa 2 depois do início da junta.
    last = bones["segment5"]["cubes"][0]
    thick_end = last["origin"][2] + last["size"][2]
    joint_start = None
    for band, n in enumerate(NEW_SEGMENTS, start=1):
        is_joint = n % 2 == 0
        source = joint if is_joint else thick
        if is_joint:
            start = joint_start = thick_end - 1
        else:
            start = joint_start + 2
            thick_end = start + source["cubes"][0]["size"][2]
        # Desloca o osso inteiro (pivô e cubos) igual, mantendo a forma do segmento copiado.
        shift = start - source["cubes"][0]["origin"][2]
        bone = {"name": f"segment{n}", "parent": f"segment{n - 1}",
                "pivot": [source["pivot"][0], source["pivot"][1], source["pivot"][2] + shift], "cubes": []}
        for cube in source["cubes"]:
            new = copy.deepcopy(cube)
            new["origin"] = [cube["origin"][0], cube["origin"][1], cube["origin"][2] + shift]
            new["uv"] = [cube["uv"][0], cube["uv"][1] + BAND * band]
            bone["cubes"].append(new)
        geo["bones"].append(bone)
    return geo


def extend_animations(anim):
    """Renomeia as animações para o grupo novo e copia o movimento para os segmentos novos."""
    out = {"format_version": anim.get("format_version", "1.8.0"), "animations": {}}
    for name, body in anim["animations"].items():
        body = copy.deepcopy(body)
        bones = body.get("bones", {})
        for n, sources in ANIMATION_SOURCE.items():
            source = next((s for s in sources if s in bones), None)
            if source:
                bones[f"segment{n}"] = copy.deepcopy(bones[source])
        out["animations"][name.replace("animation.orthworm.", f"animation.{NAME}.")] = body
    return out


def retarget_poser(poser):
    """O poser do Orthworm, mas tocando as animações do grupo novo."""
    text = json.dumps(poser)
    for call in ("q.bedrock(", "q.bedrock_primary(", "q.bedrock_stateful(", "q.bedrock_quirk("):
        text = text.replace(f"{call}'orthworm'", f"{call}'{NAME}'")
    return json.loads(text)


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
    gum = segmented(tall, bone_colors(geo, tall.width, tall.height, COLORS), solid=(PUPIL,))
    tex_dir = resources / "assets/ecosystems_hollows/textures/pokemon/orthworm"
    tex_dir.mkdir(parents=True, exist_ok=True)
    gum.save(tex_dir / "orthworm_candyan_gum.png")
    if preview_dir:
        save_preview(preview_dir, "orthworm", tall, [gum])


if __name__ == "__main__":
    main()
