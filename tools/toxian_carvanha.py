# Carvanha e Sharpedo Toxian (Toxic Caves), no lugar do Radgill do Alex's Caves, com as cores dele: corpo marrom bem
# escuro, nadadeiras oliva (marrom-amarelado-esverdeado), dentes creme, olhos amarelos e laranja com pupila preta, e a
# boca por dentro verde que brilha no escuro (camada emissiva), como a do Radgill.
# - Carvanha: tem um terceiro olho, pintado na testa, entre os dois. Os olhos brilham no escuro (no shiny ficam acesos
#   enquanto o corpo pulsa).
# - Sharpedo: agora tem visual próprio (metal de contenção e resíduo nuclear: toxian_sharpedo.py); daqui saem as
#   funções dos 4 olhos. Evoluído, tem 4 olhos: os olhos são cubos dentro da "grade" das guelras, e cada lado ganha uma cópia do
#   olho logo atrás, dentro da mesma grade (modelo próprio, "sharpedo_toxian").
# Shiny: verde neon (contornos, cinzas e o preto de dentro também), com o corpo pulsando de brilho (camada emissiva
# animada).
# As marcas amarelas do Sharpedo (a estrela da testa e os "propulsores" do rabo) viram marcas verdes que brilham.
# Cores claras amareladas (dentes, olhos) usam só a metade clara da rampa, para a sombra não virar marrom.
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
from candyan import box_faces, luma, luma_ranges, ramp, save_preview, shade_t  # noqa: E402

# Cores tiradas da textura do Radgill.
BODY, BODY_LIGHT = (48, 36, 32), (62, 46, 41)   # marrom-escuro
BELLY = (88, 70, 54)                            # a barriga clara do Sharpedo, num marrom um pouco mais claro
FIN = (90, 77, 8)                               # nadadeiras: oliva
TEETH = (255, 250, 185)                         # dentes: creme
EYE, IRIS = (232, 228, 0), (222, 143, 0)        # olhos: amarelo e laranja
GLOW = (0, 223, 0)                              # boca por dentro e marcas: verde que brilha
PUPIL = (12, 8, 6)
# glow: marcas que brilham; mouth: a boca por dentro (mais escura, também brilha); outline: contornos escuros
# (None = ficam como no original).
NORMAL = {"body": BODY, "body_light": BODY_LIGHT, "gray": BODY_LIGHT, "belly": BELLY, "fin": FIN, "teeth": TEETH,
          "glow": GLOW, "mouth": (0, 150, 10), "outline": None}
SHINY = {"body": (20, 200, 40), "body_light": (70, 255, 90), "gray": (70, 255, 90), "belly": (160, 255, 130),
         "fin": (150, 255, 40), "teeth": TEETH, "glow": (120, 255, 70), "mouth": (120, 255, 40), "outline": (6, 70, 10)}


def classify(r, g, b):
    """Que parte é o pixel do original (None: fica como está, ex. o preto da boca e das pupilas)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    red = h > 0.93 or h < 0.05
    if v > 0.9 and s < 0.12 and b <= r + 4:
        return "teeth"          # branco puro: dentes (e o branco dos olhos, tratado à parte); o lilás é barriga
    if red and s > 0.25 and (v <= 0.55 or s < 0.6):
        return "mouth"          # vermelho-escuro e rosado: a boca por dentro
    if s < 0.32 and v > 0.6:
        return "belly"          # cinza e lilás claros (barriga do Sharpedo)
    if s < 0.35 and v < 0.25:
        return "outline"        # contornos escuros (e o preto de dentro da boca)
    if s < 0.25 and v <= 0.6:
        return "gray"           # cinzas
    if 0.02 < h < 0.2 and s > 0.4:
        return "fin"            # amarelo e laranja das nadadeiras (e as bordas delas)
    if red and s > 0.45:
        return "body"
    if 0.55 < h < 0.72:
        return "body_light"
    return None


def eye_color(r, g, b):
    """Dentro dos olhos: branco vira amarelo, vermelho vira laranja; o preto (pupila) fica."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if v > 0.75 and s < 0.25:
        return EYE
    if (h > 0.93 or h < 0.05) and s > 0.4:
        return (234, 181, 0)  # a íris também amarela, um pouco mais escura
    return None


def recolor(texture, eye_boxes, glow_boxes=(), eyeball_boxes=(), pupil_boxes=(), palette=NORMAL):
    """Devolve (textura, camada emissiva).
    eye_boxes: olhos pintados (branco vira amarelo, vermelho vira laranja); eyeball_boxes/pupil_boxes: olhos em cubo
    (a moldura fica amarela e a pupila preta, como no Radgill); glow_boxes: marcas que brilham."""
    src = texture.convert("RGBA")
    out = src.copy()
    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, op, gp = src.load(), out.load(), glow.load()
    in_box = lambda x, y, boxes: any(bx <= x < bx + bw and by <= y < by + bh for bx, by, bw, bh in boxes)
    ranges = luma_ranges(src, lambda x, y: "glow" if in_box(x, y, glow_boxes) else classify(*sp[x, y][:3]))
    colors = palette
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            l = luma(sp[x, y])
            if in_box(x, y, pupil_boxes):
                op[x, y] = PUPIL + (a,)
                continue
            if in_box(x, y, eyeball_boxes):
                op[x, y] = ramp(EYE, 0.75 + 0.25 * l) + (a,)
                gp[x, y] = op[x, y][:3] + (255,)   # os olhos brilham
                continue
            if in_box(x, y, eye_boxes):
                color = eye_color(r, g, b)
                if color:
                    op[x, y] = ramp(color, 0.75 + 0.25 * l) + (a,)
                    gp[x, y] = op[x, y][:3] + (255,)
                    continue
                if l < 0.3:
                    continue  # o contorno e a pupila do olho ficam escuros
            kind = classify(r, g, b)
            if in_box(x, y, glow_boxes) or kind == "mouth":
                key = "glow" if in_box(x, y, glow_boxes) else "mouth"
                c = ramp(palette[key], shade_t(ranges, key, l) * (1.0 if key == "glow" else 0.85))
                op[x, y] = c + (a,)
                gp[x, y] = c + (255,)
                continue
            if kind is None or colors.get(kind) is None:
                continue
            t = shade_t(ranges, kind, l)
            op[x, y] = ramp(colors[kind], 0.6 + 0.4 * t if kind == "teeth" else t) + (a,)
    return out, glow


def bone_map(geo, width, height):
    """O osso de cada pixel da textura."""
    owner = [[None] * width for _ in range(height)]
    for bone in geo["bones"]:
        for cube in bone.get("cubes", []):
            if isinstance(cube.get("uv"), list):
                for x0, y0, w, h in box_faces(cube["uv"], [round(v) for v in cube["size"]]):
                    for y in range(max(0, y0), min(height, y0 + h)):
                        for x in range(max(0, x0), min(width, x0 + w)):
                            owner[y][x] = bone["name"]
    return owner


def pulse_frames(texture, palette, count=8):
    """Camada emissiva animada: o corpo inteiro acende e apaga devagar (o brilho vai de fraco a forte e volta)."""
    import math
    src = texture.convert("RGBA")
    frames = []
    for i in range(count):
        strength = 0.25 + 0.6 * (0.5 - 0.5 * math.cos(2 * math.pi * i / count))
        frame = Image.new("RGBA", src.size, (0, 0, 0, 0))
        sp, fp = src.load(), frame.load()
        for y in range(src.height):
            for x in range(src.width):
                r, g, b, a = sp[x, y]
                if a and g > r and g > b and g > 60:  # só o verde (corpo, nadadeiras, boca)
                    fp[x, y] = (r, g, b, int(255 * strength))
        frames.append(frame)
    return frames


def paint_third_eye(img, x0, y0, glow=None):
    """Olho 3x2 amarelo, com a íris laranja e a pupila preta, pintado na textura (Carvanha); o amarelo e a íris
    também na camada que brilha, se vier."""
    p = img.load()
    g = glow.load() if glow else None
    rows = [[EYE, EYE, EYE], [IRIS, PUPIL, IRIS]]
    for dy, row in enumerate(rows):
        for dx, c in enumerate(row):
            p[x0 + dx, y0 + dy] = c + (255,)
            if g and c != PUPIL:
                g[x0 + dx, y0 + dy] = c + (255,)


# O olho novo de cada lado: logo atrás do original (z), dentro da grade das guelras. O cubo amarelo é mais curto só
# no x (1,5 em vez de 2: o lado que vai do escuro de dentro até as barras), com a face de fora logo antes das barras
# (|x| = 8,45); a pupila fica do tamanho original, no meio dele.
# O cubo amarelo do original é "do avesso" (tamanho 2 com inflate -2: dá para ver a pupila lá dentro); o novo também:
# tamanho 2,5 com inflate -2 = 1,5 visível no x. Como 2,5 não cabe na UV do original, ele usa um canto vazio da
# textura, pintado de amarelo (EXTRA_EYE_UV).
EXTRA_EYE_DZ = 2.6
EXTRA_EYE_WIDTH = 1.5
EXTRA_EYE_OUTER = 8.45
EXTRA_EYE_UV_SIZE = (10, 5)  # caixa 2,5 x 2 x 2 arredondada para cima: (2d + 2w) x (d + h)


def free_area(texture, owner, size):
    """Um retângulo da textura sem pixel nenhum e sem cubo usando."""
    w, h = size
    px = texture.convert("RGBA").load()
    for y in range(texture.height - h, -1, -1):
        for x in range(texture.width - w, -1, -1):
            if all(px[x + i, y + j][3] == 0 and owner[y + j][x + i] is None for i in range(w) for j in range(h)):
                return x, y
    raise ValueError("sem espaço livre na textura")


def paint_extra_eye(img, uv, color=EYE, glow=None):
    """Pinta com os tons do olho (amarelo, ou a cor dada) a área do cubo do olho novo; também na camada que brilha,
    se vier."""
    p = img.load()
    g = glow.load() if glow else None
    for j in range(EXTRA_EYE_UV_SIZE[1]):
        for i in range(EXTRA_EYE_UV_SIZE[0]):
            p[uv[0] + i, uv[1] + j] = ramp(color, 0.8 + 0.2 * ((i + j) % 2)) + (255,)
            if g:
                g[uv[0] + i, uv[1] + j] = p[uv[0] + i, uv[1] + j]


def four_eyes_model(geo, uv):
    """Sharpedo: cada olho (osso eye_left/eye_right, um cubo com a pupila) ganha uma cópia ao lado, no mesmo osso pai."""
    geo = copy.deepcopy(geo)
    geo["description"]["identifier"] = "geometry.sharpedo_toxian"
    for side, sign in (("left", 1), ("right", -1)):
        eye = next(b for b in geo["bones"] if b["name"] == f"eye_{side}")
        main, pupil = sorted(eye["cubes"], key=lambda c: -c["size"][0])
        # Cubo amarelo: visível de 6,95 a 8,45 no x (espelhado no direito); y e z como o original, só mais para trás.
        inflate = main.get("inflate", 0)
        size_x = -2 * inflate - EXTRA_EYE_WIDTH if inflate < 0 else EXTRA_EYE_WIDTH  # do avesso: |tamanho + 2*inflate|
        center = (EXTRA_EYE_OUTER - EXTRA_EYE_WIDTH / 2) * sign
        new_main = {**copy.deepcopy(main), "origin": [round(center - size_x / 2, 4), main["origin"][1],
                                                      round(main["origin"][2] + EXTRA_EYE_DZ, 4)],
                    "size": [size_x, main["size"][1], main["size"][2]], "uv": list(uv)}
        # Pupila: mesmo tamanho, no mesmo lugar relativo (centrada no x do cubo amarelo).
        dx = center - (main["origin"][0] + main["size"][0] / 2)
        new_pupil = {**copy.deepcopy(pupil), "origin": [round(pupil["origin"][0] + dx, 4), pupil["origin"][1],
                                                       round(pupil["origin"][2] + EXTRA_EYE_DZ, 4)]}
        geo["bones"].append({"name": f"eye_{side}2", "parent": eye["parent"],
                             "pivot": [round(eye["pivot"][0] + dx, 4), eye["pivot"][1],
                                       round(eye["pivot"][2] + EXTRA_EYE_DZ, 4)],
                             "cubes": [new_main, new_pupil]})
    return geo


def main():
    z = zipfile.ZipFile(sys.argv[1])
    resources = Path(sys.argv[2])
    preview = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    tex_dir = resources / "assets/ecosystems_hollows/textures/pokemon"
    res_dir = resources / "assets/cobblemon/bedrock/pokemon/resolvers"

    # Carvanha: os olhos são pintados na frente da cabeça (cubo em uv 0,11, 9x6x7: frente em x 7-15, y 18-23), um
    # de cada lado; o terceiro vai na testa, no meio, acima deles.
    carvanha = Image.open(BytesIO(z.read("assets/cobblemon/textures/pokemon/0318_carvanha/carvanha.png")))
    eyes = [(1, 19, 22, 5)]  # os dois olhos, de ponta a ponta
    car, car_glow = recolor(carvanha, eyes)
    car_s, car_s_glow = recolor(carvanha, eyes, palette=SHINY)
    paint_third_eye(car, 10, 18, car_glow)
    paint_third_eye(car_s, 10, 18, car_s_glow)
    # No shiny o corpo pulsa (acende e apaga); os olhos ficam sempre acesos por cima.
    eyes_glow = Image.new("RGBA", carvanha.size, (0, 0, 0, 0))
    for box in eyes + [(10, 18, 3, 2)]:
        crop = (box[0], box[1], box[0] + box[2], box[1] + box[3])
        eyes_glow.paste(car_s_glow.crop(crop), crop[:2])
    car_s_frames = [Image.alpha_composite(f, eyes_glow) for f in pulse_frames(car_s, SHINY)]
    (tex_dir / "carvanha").mkdir(parents=True, exist_ok=True)
    car.save(tex_dir / "carvanha/carvanha_toxian.png")
    car_glow.save(tex_dir / "carvanha/carvanha_toxian_emissive.png")
    car_s.save(tex_dir / "carvanha/carvanha_toxian_shiny.png")
    for i, frame in enumerate(car_s_frames):
        frame.save(tex_dir / f"carvanha/carvanha_toxian_shiny_glow_{i}.png")

    # O Sharpedo Toxian tem script próprio (toxian_sharpedo.py), que usa as funções dos olhos daqui.
    for species, folder, extra in (("carvanha", "0318_carvanha", {}),):
        resolver = {"species": f"cobblemon:{species}", "order": 1, "variations": [{
            "aspects": ["toxian"], **extra,
            "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_toxian.png",
            "layers": [{"name": "emissive", "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_toxian_emissive.png",
                        "emissive": True}]},
            {"aspects": ["toxian", "shiny"],
             "texture": f"ecosystems_hollows:textures/pokemon/{species}/{species}_toxian_shiny.png",
             "layers": [{"name": "emissive", "emissive": True, "texture": {
                 "frames": [f"ecosystems_hollows:textures/pokemon/{species}/{species}_toxian_shiny_glow_{i}.png"
                            for i in range(8)], "fps": 8, "loop": True}}]}]}
        path = res_dir / folder / "1_ecosystems_hollows_toxian.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(resolver, indent=2) + "\n", encoding="utf-8")

    if preview:
        save_preview(preview, "carvanha_toxian", carvanha, [car, car_s])


if __name__ == "__main__":
    main()
