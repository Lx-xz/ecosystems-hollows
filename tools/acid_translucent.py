# Ácido translúcido (para aquários de Toxian): cópias das texturas do ácido do Alex's Caves, com a mesma arte e a mesma
# animação, só que um pouco transparentes (ALPHA). Ficam em assets/alexscaves/... do nosso mod, por cima das do Alex's
# Caves (os arquivos dele não mudam). O AcidRender.java passa o ácido para a camada translúcida, que respeita isso.
#
# Uso: python acid_translucent.py <jar do Alex's Caves> <pasta resources do mod>
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

ALPHA = 185   # 0-255: quanto o ácido esconde o que está atrás (a água do Minecraft fica perto de 180)
FILES = ["acid_still", "acid_flowing"]


def main():
    ac = zipfile.ZipFile(sys.argv[1])
    out = Path(sys.argv[2]) / "assets/alexscaves/textures/block"
    out.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        path = f"assets/alexscaves/textures/block/{name}.png"
        img = Image.open(BytesIO(ac.read(path))).convert("RGBA")
        img.putalpha(Image.new("L", img.size, ALPHA))
        img.save(out / f"{name}.png")
        # A animação vem do .mcmeta do mesmo pacote que a textura: vai junto.
        (out / f"{name}.png.mcmeta").write_bytes(ac.read(path + ".mcmeta"))


if __name__ == "__main__":
    main()
