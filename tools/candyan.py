# Gera as texturas "Candyan" (de gelatina e de chiclete) a partir das texturas originais do Cobblemon.
#
# Uso: python candyan.py <jar do Cobblemon> <pasta de saída> [pasta da prévia]
#
# O modelo 3D (.geo.json) de cada Pokémon diz o que é cada parte da textura:
# - rosto (olhos, boca, focinho): opaco e com cor firme, para continuar bem visível;
# - planos finos (orelhas, tufos): opacos e sem suavização;
# - o resto do corpo: translúcido, com a sombra suavizada para não ficar manchado.
#
# Para os translúcidos saem duas texturas por cor:
# - <espécie>_candyan_<cor>_base.png: só as partes opacas (rosto e planos). Vai como textura base, que o jogo
#   desenha com profundidade. Na camada translúcida, os planos "piscavam": frente e verso ficam no mesmo
#   lugar e o jogo alternava entre os dois.
# - <espécie>_candyan_<cor>.png: só o corpo translúcido, na camada por cima.
# Os planos não usam a sombra suavizada: a média com os vizinhos deixava a frente e o verso com cores
# diferentes, e aí a alternância aparecia como listras.
import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

GUMMY_COLORS = {
    "red": (232, 40, 56),
    "orange": (248, 132, 32),
    "yellow": (250, 214, 48),
    "green": (72, 204, 80),
    "blue": (56, 128, 236),
    "purple": (156, 72, 216),
}
# Shiny: cada cor puxa para a vizinha mais clara (azul -> ciano, vermelho -> magenta, verde -> menta...).
# Laranja e amarelo não têm uma vizinha óbvia: viram pêssego e limão.
GUMMY_SHINY = {
    "red": (236, 48, 168),      # magenta
    "orange": (255, 146, 120),  # pêssego
    "yellow": (214, 240, 72),   # limão
    "green": (110, 236, 176),   # menta
    "blue": (48, 214, 236),     # ciano
    "purple": (206, 150, 250),  # lilás
}
# espécie: (pasta no Cobblemon, cores, translúcido?, cubos extras do rosto pelo UV)
POKEMON = {
    "stufful": ("0759_stufful", GUMMY_COLORS, True, []),
    # O focinho do Bewear é um cubo dentro do osso "head", com UV em (0, 63).
    "bewear": ("0760_bewear", GUMMY_COLORS, True, [(0, 63)]),
}

# Peças que somem na forma Candyan (ficam transparentes): a etiqueta de pelúcia embaixo do rabo do Stufful faz
# sentido num bicho de pelúcia, não numa bala de goma.
HIDDEN_BONES = {"stufful": ("tag",)}

# Cubos que encostam numa face do corpo translúcido: a face de trás deles fica no mesmo plano da face do corpo e,
# vista através da gelatina, as duas brigam (listras piscando). A face de trás precisa entrar um pouco no corpo.
# O Cobblemon só aceita UV de caixa, e mudar o tamanho do cubo para um valor quebrado desalinharia a textura.
# Então o cubo cresce com "inflate" (a textura estica junto, sem desalinhar) e é empurrado para dentro na mesma
# medida: a frente fica onde estava e só a face de trás entra no corpo.
# Gera um modelo próprio "<espécie>_candyan" com a correção.
# espécie: [(osso, UV do cubo, quanto a face de trás entra no corpo)]
OVERLAP_FIXES = {
    # Focinho do Bewear: a face de trás ficava em z = -8, igual à frente da cabeça.
    "bewear": [("head", (0, 63), 0.25)],
}

# Pokémon de chiclete listrados, pintados osso por osso (veja bone_colors). O Orthworm tem modelo próprio
# e é gerado por orthworm_candyan.py.
SEGMENTED = {}
# Ossos do rosto (eyelid fica de fora: é a pálpebra, aparece só quando pisca).
FACE_BONES = ("eye", "mouth", "jaw", "nose", "muzzle", "snout")
BODY_ALPHA = 165   # 0-255: quanto do corpo aparece (o resto deixa ver através)

BODY, FLAT, FACE = 0, 1, 2


def luma(rgb):
    r, g, b = rgb[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def box_faces(uv, size):
    """Retângulos (x, y, largura, altura) das 6 faces de um cubo com UV de caixa (Bedrock)."""
    u, v = uv
    w, h, d = size
    faces = [(u + d, v, w, d), (u + d + w, v, w, d),                  # cima, baixo
             (u, v + d, d, h), (u + d, v + d, w, h),                  # leste, norte (frente)
             (u + d + w, v + d, d, h), (u + 2 * d + w, v + d, w, h)]  # oeste, sul
    return [f for f in faces if f[2] > 0 and f[3] > 0]


def region_map(geo, width, height, extra_face_uvs):
    """Para cada pixel da textura: corpo, plano fino ou rosto."""
    regions = [[BODY] * width for _ in range(height)]
    for bone in geo["bones"]:
        name = bone["name"]
        face_bone = any(k in name for k in FACE_BONES) and "eyelid" not in name
        for cube in bone.get("cubes", []):
            uv, size = cube.get("uv"), [round(s) for s in cube["size"]]
            if not isinstance(uv, list):
                continue  # UV por face: não usado nesses modelos
            flat = 0 in size
            # Planos dentro da cabeça (como o focinho do Stufful) também são rosto.
            is_face = face_bone or tuple(uv) in extra_face_uvs or (flat and name == "head")
            if not (flat or is_face):
                continue
            kind = FACE if is_face else FLAT
            for x0, y0, w, h in box_faces(uv, size):
                for y in range(max(0, y0), min(height, y0 + h)):
                    for x in range(max(0, x0), min(width, x0 + w)):
                        regions[y][x] = max(regions[y][x], kind)
    return regions


def smoothed_luma(src):
    """Brilho de cada pixel pela média com os vizinhos (tira o "ruído" do pelo que virava mancha)."""
    sp = src.load()
    out = {}
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] == 0:
                continue
            vals = [luma(sp[nx, ny]) for nx in range(max(0, x - 1), min(src.width, x + 2))
                    for ny in range(max(0, y - 1), min(src.height, y + 2)) if sp[nx, ny][3] > 0]
            out[(x, y)] = sum(vals) / len(vals)
    return out


def face_positions(geo, width, height):
    """Para cada pixel da textura: (x e y dentro da face, largura e altura da face, canto da face na textura)."""
    pos = {}
    for bone in geo["bones"]:
        for cube in bone.get("cubes", []):
            uv = cube.get("uv")
            if not isinstance(uv, list):
                continue
            for x0, y0, w, h in box_faces(uv, [round(v) for v in cube["size"]]):
                for y in range(max(0, y0), min(height, y0 + h)):
                    for x in range(max(0, x0), min(width, x0 + w)):
                        pos[(x, y)] = (x - x0, y - y0, w, h, x0, y0)
    return pos


def noise(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFF) / 0xFFFF


def gummy_tones(color):
    """Os tons da bala, do fundo escuro ao brilho, como nos Gummy Bears do Alex's Caves."""
    return [tuple(int(c * k) for c in color) for k in (0.5, 0.66, 0.82)] + [tuple(color)] + [
        tuple(int(c + (255 - c) * k) for c in color) for k in (0.28, 0.55, 0.8)]


def gummy_pixel(tones, l, face):
    """Tom e transparência de um pixel de bala de goma, no desenho dos Gummy Bears do Alex's Caves: cada face com a
    borda mais clara e mais firme, o miolo manchado de bolhas mais escuras e mais densas, e alguns pontos de brilho;
    tudo por cima da luz e da sombra do original (l, de 0 a 1)."""
    fx, fy, fw, fh, x0, y0 = face
    v = 0.3 + 0.35 * l + 0.08 * (noise(fx + x0, fy + y0, 1) - 0.5)
    alpha = BODY_ALPHA
    # A borda tem falhas (nem todo pixel dela clareia), para não virar uma moldura lisa.
    rim = fw >= 3 and fh >= 3 and (fx in (0, fw - 1) or fy in (0, fh - 1)) and noise(fx + x0, fy + y0, 4) < 0.8
    if rim:
        v, alpha = max(v + 0.12, 0.5), 205
    elif noise((fx + x0) // 2, (fy + y0) // 2, 2) < 0.32:
        v, alpha = v - 0.2, 185          # bolha mais escura dentro da bala
    elif noise(fx + x0, fy + y0, 3) < 0.025:
        v, alpha = 0.85, 225             # ponto de brilho
    t = max(0.0, min(1.0, v))
    return tones[min(len(tones) - 1, int(t * (len(tones) - 1) + 0.5))], alpha


def candy(texture, color, translucent, regions, faces=None):
    """Devolve (base, camada). Para os opacos (chiclete), a camada é None e tudo vai na base."""
    src = texture.convert("RGBA")
    base = Image.new("RGBA", src.size, (0, 0, 0, 0))
    layer = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, bp, lp = src.load(), base.load(), layer.load()
    smooth = smoothed_luma(src)
    tones = gummy_tones(color)
    body = [l for (x, y), l in smooth.items() if regions[y][x] != FACE]
    lo, hi = (min(body), max(body)) if body else (0.0, 1.0)
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] == 0:
                continue
            region = regions[y][x]
            if region == FACE:
                # Rosto: cores firmes e opacas. Escuro vira quase preto; claro vira quase branco.
                l = luma(sp[x, y])
                if l < 0.35:
                    rgb = tuple(int(c * 0.18) for c in color)
                elif l > 0.7:
                    rgb = tuple(int(c + (255 - c) * 0.8) for c in color)
                else:
                    rgb = tuple(int(c * 0.85) for c in color)
                bp[x, y] = rgb + (255,)
                continue
            # Corpo e planos: a luz do original (esticada de 0 a 1) com o desenho da bala por cima.
            l = luma(sp[x, y]) if region == FLAT else smooth[(x, y)]
            l = (l - lo) / (hi - lo) if hi > lo else 0.5
            face = (faces or {}).get((x, y), (0, 0, 1, 1, x, y))
            rgb, alpha = gummy_pixel(tones, l, face)
            if not translucent or region == FLAT:
                bp[x, y] = rgb + (255,)
            else:
                lp[x, y] = rgb + (alpha,)
    return base, (layer if translucent else None)


def bone_colors(geo, width, height, colors):
    """Cor de cada pixel pelo osso a que ele pertence: nome exato, ou senão o começo do nome ("arm" pega
    "arm_front_left"). O nome exato vem antes para "segment1" não pintar o "segment10"."""
    pixel_color = [[None] * width for _ in range(height)]
    for bone in geo["bones"]:
        color = colors.get(bone["name"]) or next((c for key, c in colors.items() if bone["name"].startswith(key)), None)
        if color is None:
            continue
        for cube in bone.get("cubes", []):
            uv = cube.get("uv")
            if not isinstance(uv, list):
                continue
            for x0, y0, w, h in box_faces(uv, [round(v) for v in cube["size"]]):
                for y in range(max(0, y0), min(height, y0 + h)):
                    for x in range(max(0, x0), min(width, x0 + w)):
                        pixel_color[y][x] = color
    return pixel_color


def segmented(texture, pixel_color, solid=()):
    """Pinta cada pixel com a cor do seu osso, mantendo a luz e a sombra do original. Opaco.
    Cores em solid ficam chapadas, sem sombra (ex.: pupila)."""
    src = texture.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, op = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            color = pixel_color[y][x]
            if sp[x, y][3] == 0 or color is None:
                continue
            if color in solid:
                op[x, y] = color + (255,)
                continue
            l = luma(sp[x, y])
            k = 0.7 + 0.5 * l
            op[x, y] = tuple(min(255, int(c * k)) for c in color) + (255,)
    return out


def main():
    jar, out_dir = sys.argv[1], Path(sys.argv[2])
    preview_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(jar)
    out_dir.mkdir(parents=True, exist_ok=True)
    models_dir = out_dir.parents[1] / "bedrock/pokemon/models"
    for species, fixes in OVERLAP_FIXES.items():
        folder = POKEMON[species][0]
        model = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{species}.geo.json"))
        geo = model["minecraft:geometry"][0]
        geo["description"]["identifier"] = f"geometry.{species}_candyan"
        for bone_name, uv, depth in fixes:
            bone = next(b for b in geo["bones"] if b["name"] == bone_name)
            cube = next(c for c in bone["cubes"] if tuple(c.get("uv", ())) == uv)
            # inflate cresce metade da medida para cada lado; o empurrão compensa o lado da frente.
            cube["inflate"] = cube.get("inflate", 0) + depth / 2
            cube["origin"][2] += depth / 2
        models_dir.mkdir(parents=True, exist_ok=True)
        (models_dir / f"{species}_candyan.geo.json").write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")

    for species, (folder, colors, translucent, extra_face_uvs) in POKEMON.items():
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{species}.png")))
        geo = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{species}.geo.json"))["minecraft:geometry"][0]
        regions = region_map(geo, texture.width, texture.height, [tuple(uv) for uv in extra_face_uvs])
        faces = face_positions(geo, texture.width, texture.height)
        hidden = bone_colors(geo, texture.width, texture.height, {b: True for b in HIDDEN_BONES.get(species, ())})
        (out_dir / species).mkdir(exist_ok=True)
        variants = []
        shiny = {f"{name}_shiny": GUMMY_SHINY[name] for name in colors if colors is GUMMY_COLORS}
        for name, color in {**colors, **shiny}.items():
            base, layer = candy(texture, color, translucent, regions, faces)
            for img in (base, layer):
                if img is not None:
                    px = img.load()
                    for y in range(img.height):
                        for x in range(img.width):
                            if hidden[y][x]:
                                px[x, y] = (0, 0, 0, 0)
            if layer is None:
                base.save(out_dir / species / f"{species}_candyan_{name}.png")
                variants.append(base)
            else:
                base.save(out_dir / species / f"{species}_candyan_{name}_base.png")
                layer.save(out_dir / species / f"{species}_candyan_{name}.png")
                variants.append(Image.alpha_composite(layer, base))
        if preview_dir:
            save_preview(preview_dir, species, texture, variants)

    for species, (folder, name, colors) in SEGMENTED.items():
        texture = Image.open(BytesIO(z.read(f"assets/cobblemon/textures/pokemon/{folder}/{species}.png")))
        geo = json.loads(z.read(f"assets/cobblemon/bedrock/pokemon/models/{folder}/{species}.geo.json"))["minecraft:geometry"][0]
        img = segmented(texture, bone_colors(geo, texture.width, texture.height, colors))
        (out_dir / species).mkdir(exist_ok=True)
        img.save(out_dir / species / f"{species}_candyan_{name}.png")
        if preview_dir:
            save_preview(preview_dir, species, texture, [img])


def save_preview(preview_dir, species, texture, variants):
    """Prévia: original + variações lado a lado, ampliadas, sobre um fundo xadrez."""
    preview_dir.mkdir(parents=True, exist_ok=True)
    w, h = texture.size
    scale = max(1, 256 // w)
    sheet = Image.new("RGBA", (w * scale * (len(variants) + 1), h * scale), (0, 0, 0, 0))
    checker = Image.new("RGBA", sheet.size, (200, 200, 200, 255))
    cp = checker.load()
    for yy in range(sheet.height):
        for xx in range(sheet.width):
            if (xx // 8 + yy // 8) % 2:
                cp[xx, yy] = (150, 150, 150, 255)
    for i, img in enumerate([texture.convert("RGBA")] + variants):
        sheet.paste(img.resize((w * scale, h * scale), Image.NEAREST), (i * w * scale, 0))
    Image.alpha_composite(checker, sheet).save(preview_dir / f"{species}_preview.png")


if __name__ == "__main__":
    main()


# ----- Sombra em rampa (para as texturas novas não ficarem "lisas") -----

def ramp(color, t):
    """A cor no ponto t (0 = sombra, 1 = luz) de uma rampa que vai de uma versão escura a uma clara da cor."""
    t = max(0.0, min(1.0, t))
    dark = tuple(c * 0.58 for c in color)
    light = tuple(c + (255 - c) * 0.25 for c in color)
    return tuple(int(d + (l - d) * t) for d, l in zip(dark, light))


def luma_ranges(texture, key_of):
    """Para cada grupo de pixels (key_of(x, y) -> chave ou None): o menor e o maior brilho do original. Assim cada
    grupo usa a rampa inteira, do escuro ao claro, mesmo que o original seja quase de uma cor só."""
    src = texture.convert("RGBA")
    sp = src.load()
    ranges = {}
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] == 0:
                continue
            key = key_of(x, y)
            if key is None:
                continue
            l = luma(sp[x, y])
            lo, hi = ranges.get(key, (l, l))
            ranges[key] = (min(lo, l), max(hi, l))
    return ranges


def shade_t(ranges, key, l):
    """O brilho l do pixel, de 0 a 1 dentro do seu grupo (meio-termo se o grupo tem um brilho só)."""
    lo, hi = ranges.get(key, (0.0, 1.0))
    return 0.6 if hi - lo < 0.02 else (l - lo) / (hi - lo)
