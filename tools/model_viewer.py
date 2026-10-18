# Gera a Pokédex do mod: uma página com um visualizador 3D de todas as nossas formas e variações (docs/index.html,
# para o GitHub Pages). Para cada variação dos nossos resolvers, junta o modelo, a textura e as camadas como o
# Cobblemon faria (somando as variações do Cobblemon e as nossas, em ordem), e o original para comparar. Com a ficha
# de cada uma: número da Pokédex, tipos, status e habilidades (das formas em species_additions, ou da espécie), com os
# nomes da tradução do Cobblemon. Tudo vai embutido no HTML (modelos e texturas).
#
# O mesmo script serve aos três mods (base, Hollows e Untamed): --forms diz quais aspects são as formas do mod.
#
# Uso: python model_viewer.py <jar do Cobblemon> <pasta resources do mod> <arquivo .html> --title "Hollows"
#          --forms '{"candyan": "Candyan", "toxian": "Toxian"}' [--subtitle "..."] [--repo https://github.com/...]
#          [--fragment miolo.html]
import argparse
import base64
import json
import zipfile
from pathlib import Path

NAMES = {
    "shiny": "Shiny", "school-form": "Escola",
    "candy_corn": "Milho doce", "peppermint": "Hortelã", "mint_chip": "Menta com chocolate",
    "cherry_ice": "Cereja com gelo", "cotton_candy": "Algodão-doce",
    "red": "Vermelho", "orange": "Laranja", "yellow": "Amarelo", "green": "Verde", "blue": "Azul",
    "purple": "Roxo", "pink": "Rosa",
    "vanilla": "Baunilha", "chocolate": "Chocolate", "sweetberry": "Sweetberry", "frostmint": "Frostmint",
}
STATS = ["hp", "attack", "defence", "special_attack", "special_defence", "speed"]


class Assets:
    def __init__(self, jar, resources):
        self.jar, self.res = zipfile.ZipFile(jar), Path(resources)
        self.names = self.jar.namelist()
        self.lang = json.loads(self.jar.read("assets/cobblemon/lang/pt_br.json"))
        self.lang_en = json.loads(self.jar.read("assets/cobblemon/lang/en_us.json"))

    def t(self, key, fallback):
        return self.lang.get(key) or self.lang_en.get(key) or fallback

    def read(self, ns, path):
        ours = self.res / "assets" / ns / path
        if ours.exists():
            return ours.read_bytes()
        return self.jar.read(f"assets/{ns}/{path}")

    def model(self, ident):
        ns, name = ident.split(":")
        name = name.removesuffix(".geo") + ".geo.json"
        ours = list((self.res / "assets" / ns / "bedrock/pokemon/models").rglob(name))
        if ours:
            return json.loads(ours[0].read_text(encoding="utf-8"))
        path = next(n for n in self.names if n.startswith(f"assets/{ns}/bedrock/pokemon/models/") and n.endswith("/" + name))
        return json.loads(self.jar.read(path))

    def resolvers(self, folder):
        found = []
        prefix = f"assets/cobblemon/bedrock/pokemon/resolvers/{folder}/"
        for n in self.names:
            if n.startswith(prefix) and n.endswith(".json"):
                found.append(json.loads(self.jar.read(n)))
        for f in sorted((self.res / "assets/cobblemon/bedrock/pokemon/resolvers" / folder).glob("*.json")):
            found.append(json.loads(f.read_text(encoding="utf-8")))
        return sorted(found, key=lambda r: r.get("order", 0))

    def species(self, name):
        path = next((n for n in self.names if n.startswith("data/cobblemon/species/") and n.endswith(f"/{name}.json")), None)
        return json.loads(self.jar.read(path)) if path else {}

    def form_data(self, species, aspect):
        """A forma do nosso mod (species_additions) com esse aspect, ou None."""
        for f in (self.res / "data").glob("*/species_additions/*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("target", "").split(":")[-1] != species:
                continue
            for form in data.get("forms", []):
                if aspect in form.get("aspects", []):
                    return form
        return None


def fold(resolvers, aspects):
    """O que o Cobblemon mostra para esses aspects: as variações que valem, somadas em ordem."""
    state = {"model": None, "texture": None, "layers": {}}
    for r in resolvers:
        for v in r["variations"]:
            if set(v.get("aspects", [])) <= set(aspects):
                for key in ("model", "texture"):
                    if key in v:
                        state[key] = v[key]
                for layer in v.get("layers", []):
                    state["layers"][layer["name"]] = layer
    return state


def frames(texture):
    if isinstance(texture, dict):
        return texture["frames"], texture.get("fps", 8)
    return [texture], 0


def slim(geo):
    g = geo["minecraft:geometry"][0]
    d = g["description"]
    keep = ("name", "parent", "pivot", "rotation", "cubes", "mirror")
    return {"w": d.get("texture_width", 64), "h": d.get("texture_height", 64),
            "bones": [{k: b[k] for k in keep if k in b} for b in g["bones"]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar")
    ap.add_argument("resources")
    ap.add_argument("out")
    ap.add_argument("--title", required=True, help="nome do mod na Pokédex (ex.: Hollows)")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--forms", required=True, help="JSON {aspect: nome da forma}")
    ap.add_argument("--repo", default="")
    ap.add_argument("--fragment", default="", help="também grava só o miolo da página (sem <html>), para o Artifact")
    args = ap.parse_args()
    forms = json.loads(args.forms)
    assets = Assets(args.jar, args.resources)
    textures, models, groups = {}, {}, []

    def is_ours(a):
        return a in forms or any(a.startswith(f + "_") for f in forms)

    def label(aspects):
        parts = []
        for a in aspects:
            if a in forms:
                continue
            for f in forms:
                a = a.removeprefix(f + "_")
            parts.append(NAMES.get(a, a.replace("_", " ").capitalize()))
        return " · ".join(parts) or "Normal"

    def tex(ident):
        if ident not in textures:
            ns, path = ident.split(":")
            textures[ident] = "data:image/png;base64," + base64.b64encode(assets.read(ns, path)).decode()
        return ident

    def entry(resolvers, aspects, name):
        state = fold(resolvers, aspects)
        if not state["model"] or not state["texture"]:
            return None
        if state["model"] not in models:
            models[state["model"]] = slim(assets.model(state["model"]))
        layers = []
        for layer_name, layer in state["layers"].items():
            if layer_name == "alpha_eyes":
                continue
            layer_frames, fps = frames(layer["texture"])
            layers.append({"name": layer_name, "frames": [tex(f) for f in layer_frames], "fps": fps,
                           "emissive": layer.get("emissive") in (True, "true"),
                           "translucent": layer.get("translucent") in (True, "true")})
        return {"name": name, "aspects": aspects, "model": state["model"], "texture": tex(frames(state["texture"])[0][0]),
                "layers": layers}

    root = assets.res / "assets/cobblemon/bedrock/pokemon/resolvers"
    for folder in sorted(p.name for p in root.iterdir() if p.is_dir()):
        resolvers = assets.resolvers(folder)
        dex, species = folder.split("_", 1)
        base = assets.species(species)
        ours = [v for f in sorted((root / folder).glob("*.json"))
                for v in json.loads(f.read_text(encoding="utf-8"))["variations"]]
        by_form = {}
        for v in ours:
            aspects = v.get("aspects", [])
            form = next((a for a in aspects if a in forms), None)
            if form:
                by_form.setdefault(form, []).append(aspects)
        for form, aspect_sets in by_form.items():
            entries, originals = [], []
            for aspects in aspect_sets:
                plain = [a for a in aspects if not is_ours(a)]
                if plain not in originals and "shiny" not in plain:
                    originals.append(plain)
            for plain in originals:
                e = entry(resolvers, plain, "Original" + (" · " + label(plain) if plain else ""))
                if e:
                    e["original"] = True
                    entries.append(e)
            # Variações que dão o mesmo resultado: fica a mais específica (ex.: "candyan" sozinho = hortelã).
            best = {}
            for aspects in aspect_sets:
                e = entry(resolvers, aspects, label(aspects))
                if e:
                    key = (e["model"], e["texture"], json.dumps(e["layers"]))
                    if key not in best or len(aspects) > len(best[key]["aspects"]):
                        best[key] = e
            entries += sorted(best.values(), key=lambda e: [i for i, a in enumerate(aspect_sets) if a == e["aspects"]][0])
            data = assets.form_data(species, form) or {}
            source = data if "primaryType" in data else base
            types = [source.get("primaryType"), source.get("secondaryType")]
            stats = data.get("baseStats") or base.get("baseStats", {})
            abilities = data.get("abilities") or base.get("abilities", [])
            groups.append({
                "dex": int(dex), "id": species, "form": forms[form], "formAspect": form, "regional": bool(data),
                "species": assets.t(f"cobblemon.species.{species}.name", species.capitalize()),
                "types": [{"id": t, "name": assets.t(f"cobblemon.type.{t}", t)} for t in types if t],
                "stats": [{"id": s, "name": assets.t(f"cobblemon.stat.{s}.name", s), "value": stats.get(s, 0)} for s in STATS],
                "abilities": [{"name": assets.t(f"cobblemon.ability.{a.removeprefix('h:')}", a.removeprefix("h:")),
                               "hidden": a.startswith("h:")} for a in abilities],
                "entries": entries,
            })
    groups.sort(key=lambda g: (g["dex"], g["form"]))
    data = json.dumps({"title": args.title, "subtitle": args.subtitle, "repo": args.repo, "groups": groups,
                       "models": models, "textures": textures}, separators=(",", ":"), ensure_ascii=False)
    template = (Path(__file__).parent / "model_viewer.html").read_text(encoding="utf-8")
    page = template.replace("/*DATA*/null", data).replace("{{TITLE}}", args.title)
    # Documento completo, para o GitHub Pages (o template é só o miolo da página).
    html = ("<!doctype html>\n<html lang=\"pt-BR\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            "</head>\n<body>\n" + page + "\n</body>\n</html>\n")
    if args.fragment:
        Path(args.fragment).write_text(page, encoding="utf-8", newline="\n")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    count = sum(len(g["entries"]) for g in groups)
    print(f"{out}: {len(groups)} formas, {count} variações, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
