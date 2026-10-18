# Gera as formas regionais com tipo, status, habilidades e golpes próprios (data/ecosystems_hollows/species_additions):
#   Ponyta e Rapidash Candyan (Fada pura), Wishiwashi Candyan (Água/Fada), Tangela e Tangrowth Candyan
#   (Planta/Veneno: alcaçuz de licor), Carvanha Toxian (Veneno), Sharpedo Toxian (Veneno/Aço: metal de contenção),
#   Heracross Toxian (Inseto/Veneno), Noibat e Noivern Forlorn (Sombrio/Dragão; o Noivern não voa), Zigzagoon e
#   Linoone Forlorn (Normal/Terra),
#   Magnemite, Magneton e Magnezone Magnetian (Elétrico/Aço), Vanillite, Vanillish e Vanilluxe Candyan (Gelo), e Rayquaza Candyan (Fada/Dragão).
# Os golpes partem da lista do próprio Cobblemon (do de Galar, no caso dos pôneis): os golpes de nível que não
# combinam com a forma são trocados (MOVE_SWAPS), e entram golpes de nível e de TM novos (EXTRA_MOVES).
# A evolução também vai para a mesma forma (Carvanha Toxian -> Sharpedo Toxian, Ponyta Candyan -> Rapidash Candyan).
#
# Uso: python regional_forms.py <jar do Cobblemon> <pasta resources do mod>
import json
import sys
import zipfile
from pathlib import Path

FORMS = {
    "ponyta": {
        "file": "generation1/ponyta.json", "from_form": "Galar", "name": "Candyan", "aspect": "candyan",
        "label": "candyan_form", "types": ("fairy", None),
        # Base 415 (o original tem 410): um pouco mais de ataque especial, com a velocidade do original.
        "stats": {"hp": 50, "attack": 70, "defence": 55, "special_attack": 80, "special_defence": 70, "speed": 90},
        "abilities": ["sweetveil", "runaway", "h:pastelveil"],
        "swaps": {"confusion": "disarmingvoice", "psybeam": "drainingkiss", "healpulse": "sweetkiss",
                  "psychic": "playrough", "healingwish": "moonblast"},
        "extra": ["1:fairywind", "tm:drainingkiss", "tm:moonblast", "tm:mistyterrain", "tm:sweetscent"],
        "evolves_to": "rapidash candyan",
    },
    "rapidash": {
        "file": "generation1/rapidash.json", "from_form": "Galar", "name": "Candyan", "aspect": "candyan",
        "label": "candyan_form", "types": ("fairy", None),
        # Base 525 (o original tem 500).
        "stats": {"hp": 65, "attack": 85, "defence": 70, "special_attack": 105, "special_defence": 90, "speed": 110},
        "abilities": ["sweetveil", "runaway", "h:pastelveil"],
        "swaps": {"confusion": "disarmingvoice", "psybeam": "drainingkiss", "healpulse": "sweetkiss",
                  "psychic": "playrough", "healingwish": "moonblast", "psychocut": "playrough"},
        "extra": ["1:fairywind", "tm:drainingkiss", "tm:moonblast", "tm:mistyterrain", "tm:sweetscent"],
        "pre_evolution": "ponyta candyan",
    },
    "carvanha": {
        "file": "generation3/carvanha.json", "name": "Toxian", "aspect": "toxian", "label": "toxian_form",
        "types": ("poison", None),
        # Base 320 (o original tem 305): menos frágil.
        "stats": {"hp": 45, "attack": 85, "defence": 25, "special_attack": 75, "special_defence": 25, "speed": 65},
        "abilities": ["poisontouch", "h:speedboost"],
        "swaps": {"bite": "poisonfang", "swagger": "acidspray", "assurance": "venoshock"},
        "extra": ["1:acid", "tm:sludgebomb", "tm:sludgewave", "tm:venoshock", "tm:poisonjab", "tm:toxic",
                  "tm:acidspray", "tm:toxicspikes"],
        "evolves_to": "sharpedo toxian",
    },
    "sharpedo": {
        "file": "generation3/sharpedo.json", "name": "Toxian", "aspect": "toxian", "label": "toxian_form",
        "types": ("poison", "steel"),
        # Base 475 (o original tem 460): mais ataque especial (lodo) e um pouco mais de defesa.
        "stats": {"hp": 70, "attack": 115, "defence": 45, "special_attack": 105, "special_defence": 45, "speed": 95},
        "abilities": ["poisontouch", "h:speedboost"],
        "swaps": {"bite": "poisonfang", "swagger": "acidspray", "assurance": "venoshock", "nightslash": "poisonjab"},
        "extra": ["1:acid", "1:poisonjab", "40:sludgebomb", "48:gunkshot", "tm:sludgebomb", "tm:sludgewave",
                  "tm:venoshock", "tm:poisonjab", "tm:gunkshot", "tm:toxic", "tm:acidspray", "tm:toxicspikes"],
        "pre_evolution": "carvanha toxian",
    },
    "wishiwashi": {
        "file": "generation7/wishiwashi.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("water", "fairy"),
        # O Sweetish Fish: os status do solo (a forma Escola, em batalha, continua a do Cobblemon).
        "stats": {"hp": 45, "attack": 20, "defence": 20, "special_attack": 25, "special_defence": 25, "speed": 40},
        "abilities": ["schooling", "h:schooling"],
        "swaps": {},
        "extra": ["1:fairywind", "1:sweetkiss", "12:drainingkiss", "tm:drainingkiss", "tm:dazzlinggleam",
                  "tm:charm", "tm:mistyterrain"],
    },
    "magnemite": {
        "file": "generation1/magnemite.json", "name": "Magnetian", "aspect": "magnetian", "label": "magnetian_form",
        "types": ("electric", "steel"),
        # Os ímãs da Magnetic Caves: mais defesa especial e velocidade, menos ataque especial. Base 325.
        "stats": {"hp": 30, "attack": 35, "defence": 70, "special_attack": 85, "special_defence": 65, "speed": 40},
        "abilities": ["magnetpull", "levitate", "h:analytic"],
        "swaps": {},
        "extra": ["1:magnetrise", "tm:magnetrise", "tm:electroweb", "tm:irondefense", "tm:steelbeam"],
        "evolves_to": "magneton magnetian",
    },
    "magneton": {
        "file": "generation1/magneton.json", "name": "Magnetian", "aspect": "magnetian", "label": "magnetian_form",
        "types": ("electric", "steel"),
        "stats": {"hp": 50, "attack": 60, "defence": 95, "special_attack": 115, "special_defence": 85, "speed": 70},
        "abilities": ["magnetpull", "levitate", "h:analytic"],
        "swaps": {},
        "extra": ["1:magnetrise", "tm:magnetrise", "tm:electroweb", "tm:irondefense", "tm:steelbeam"],
        "evolves_to": "magnezone magnetian",
        "pre_evolution": "magnemite magnetian",
    },
    "magnezone": {
        "file": "generation4/magnezone.json", "name": "Magnetian", "aspect": "magnetian", "label": "magnetian_form",
        "types": ("electric", "steel"),
        "stats": {"hp": 70, "attack": 70, "defence": 115, "special_attack": 130, "special_defence": 100, "speed": 50},
        "abilities": ["magnetpull", "levitate", "h:analytic"],
        "swaps": {},
        "extra": ["1:magnetrise", "tm:magnetrise", "tm:electroweb", "tm:irondefense", "tm:steelbeam"],
        "pre_evolution": "magneton magnetian",
    },
    "tangela": {
        "file": "generation1/tangela.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("grass", "poison"),
        # O licoroot: cipós de alcaçuz de licor (o álcool é o veneno). Base 440 (o original tem 435).
        "stats": {"hp": 65, "attack": 55, "defence": 105, "special_attack": 100, "special_defence": 55, "speed": 60},
        "abilities": ["sweetveil", "leafguard", "h:regenerator"],
        "swaps": {},
        "extra": ["1:acid", "12:venoshock", "tm:sludgebomb", "tm:venoshock", "tm:toxic", "tm:sweetscent"],
        "evolves_to": "tangrowth candyan",
    },
    "tangrowth": {
        "file": "generation4/tangrowth.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("grass", "poison"),
        "stats": {"hp": 100, "attack": 90, "defence": 115, "special_attack": 110, "special_defence": 70, "speed": 50},
        "abilities": ["sweetveil", "leafguard", "h:regenerator"],
        "swaps": {},
        "extra": ["1:acid", "12:venoshock", "tm:sludgebomb", "tm:venoshock", "tm:toxic", "tm:sweetscent",
                  "tm:gunkshot"],
        "pre_evolution": "tangela candyan",
    },
    "vanillite": {
        "file": "generation5/vanillite.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("ice", None),
        # Sorvete de casquinha. Base 310 (o original tem 305).
        "stats": {"hp": 40, "attack": 45, "defence": 50, "special_attack": 65, "special_defence": 70, "speed": 40},
        "abilities": ["icebody", "sweetveil", "h:weakarmor"],
        "swaps": {},
        "extra": ["1:sweetkiss", "1:fairywind", "15:drainingkiss", "tm:drainingkiss", "tm:dazzlinggleam", "tm:mistyterrain", "tm:charm"],
        "evolves_to": "vanillish candyan",
    },
    "vanillish": {
        "file": "generation5/vanillish.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("ice", None),
        "stats": {"hp": 51, "attack": 60, "defence": 65, "special_attack": 80, "special_defence": 85, "speed": 59},
        "abilities": ["icebody", "sweetveil", "h:weakarmor"],
        "swaps": {},
        "extra": ["1:sweetkiss", "1:fairywind", "15:drainingkiss", "tm:drainingkiss", "tm:dazzlinggleam", "tm:mistyterrain", "tm:charm"],
        "evolves_to": "vanilluxe candyan",
        "pre_evolution": "vanillite candyan",
    },
    "vanilluxe": {
        "file": "generation5/vanilluxe.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("ice", None),
        "stats": {"hp": 71, "attack": 85, "defence": 80, "special_attack": 110, "special_defence": 100, "speed": 79},
        "abilities": ["icebody", "sweetveil", "h:weakarmor"],
        "swaps": {},
        "extra": ["1:sweetkiss", "1:fairywind", "15:drainingkiss", "tm:drainingkiss", "tm:dazzlinggleam", "tm:mistyterrain", "tm:charm", "tm:moonblast", "tm:playrough"],
        "pre_evolution": "vanillish candyan",
    },
    "heracross": {
        "file": "generation2/heracross.json", "name": "Toxian", "aspect": "toxian", "label": "toxian_form",
        "types": ("bug", "poison"),
        # A Gammaroach: sem o chifre (Megahorn e Horn Attack viram golpes de veneno e de investida). Base 510.
        "stats": {"hp": 80, "attack": 115, "defence": 85, "special_attack": 50, "special_defence": 100, "speed": 80},
        "abilities": ["poisontouch", "guts", "h:moxie"],
        "swaps": {"hornattack": "poisonjab", "megahorn": "lunge"},
        "extra": ["1:poisonsting", "tm:poisonjab", "tm:gunkshot", "tm:toxic", "tm:venoshock", "tm:sludgebomb",
                  "tm:toxicspikes"],
    },
    "noibat": {
        "file": "generation6/noibat.json", "name": "Forlorn", "aspect": "forlorn", "label": "forlorn_form",
        "types": ("dark", "dragon"),
        # O Vesper: morcego cego que caça pelo som. Base 250 (o original tem 245).
        "stats": {"hp": 40, "attack": 40, "defence": 35, "special_attack": 40, "special_defence": 40, "speed": 55},
        "abilities": ["frisk", "infiltrator", "h:punkrock"],
        "swaps": {"gust": "bite", "wingattack": "crunch", "airslash": "nightslash", "hurricane": "dragonrush"},
        "extra": ["tm:crunch", "tm:knockoff", "tm:suckerpunch"],
        "evolves_to": "noivern forlorn",
    },
    "noivern": {
        "file": "generation6/noivern.json", "name": "Forlorn", "aspect": "forlorn", "label": "forlorn_form",
        "types": ("dark", "dragon"),
        # O Forsaken: não voa, anda de quatro com as asas como patas. Mesmo total (535), mais físico e resistente.
        "stats": {"hp": 95, "attack": 110, "defence": 85, "special_attack": 70, "special_defence": 75, "speed": 100},
        "abilities": ["frisk", "infiltrator", "h:punkrock"],
        "swaps": {"gust": "bite", "wingattack": "crunch", "airslash": "nightslash", "hurricane": "dragonrush",
                  "acrobatics": "crunch", "fly": "dig"},
        "extra": ["tm:crunch", "tm:knockoff", "tm:suckerpunch", "tm:dig", "tm:earthquake"],
        "pre_evolution": "noibat forlorn",
        "behaviour": {"moving": {"fly": {"canFly": False}, "swim": {"avoidsWater": True}}},
    },
    "zigzagoon": {
        "file": "generation3/zigzagoon.json", "name": "Forlorn", "aspect": "forlorn", "label": "forlorn_form",
        "types": ("normal", "ground"),
        # O Corrodent: rato-toupeira pelado e espinhento que rói pedra. Mesmo total do original (240).
        "stats": {"hp": 38, "attack": 45, "defence": 45, "special_attack": 20, "special_defence": 40, "speed": 52},
        "abilities": ["strongjaw", "pickup", "h:sandrush"],
        "swaps": {},
        "extra": ["1:bite", "8:dig", "tm:dig", "tm:crunch", "tm:superfang", "tm:bulldoze"],
        "evolves_to": "linoone forlorn",
    },
    "linoone": {
        "file": "generation3/linoone.json", "name": "Forlorn", "aspect": "forlorn", "label": "forlorn_form",
        "types": ("normal", "ground"),
        # Mesmo total (420): mais ataque e defesa, um pouco menos de velocidade (cava em vez de correr). Não evolui
        # para o Obstagoon.
        "stats": {"hp": 78, "attack": 90, "defence": 75, "special_attack": 30, "special_defence": 55, "speed": 92},
        "abilities": ["strongjaw", "pickup", "h:sandrush"],
        "swaps": {},
        "extra": ["1:bite", "8:dig", "tm:dig", "tm:crunch", "tm:superfang", "tm:bulldoze", "tm:earthquake",
                  "tm:highhorsepower"],
        "pre_evolution": "zigzagoon forlorn",
    },
    "rayquaza": {
        "file": "generation3/rayquaza.json", "name": "Candyan", "aspect": "candyan", "label": "candyan_form",
        "types": ("fairy", "dragon"),
        # A Gum Worm: o mesmo total de lendário (680), mais resistente e menos especial e veloz.
        "stats": {"hp": 120, "attack": 150, "defence": 110, "special_attack": 110, "special_defence": 100, "speed": 90},
        "abilities": ["stickyhold", "h:thickfat"],
        "swaps": {"airslash": "drainingkiss", "hurricane": "moonblast", "fly": "dig", "dragonascent": "playrough"},
        "extra": ["1:sweetkiss", "1:fairywind", "tm:playrough", "tm:moonblast", "tm:dazzlinggleam", "tm:dig",
                  "tm:earthquake", "tm:highhorsepower", "tm:stickyweb", "tm:mistyterrain"],
    },
}


def moves_of(base, form, swaps, extra):
    moves = []
    for move in base:
        how, _, name = move.partition(":")
        moves.append(f"{how}:{swaps.get(name, name)}")
    for move in extra:
        if move not in moves:
            moves.append(move)
    return list(dict.fromkeys(moves))


# Sabores e cores das formas Candyan: uma "feature" de escolha do Cobblemon (como o creme do Alcremie), sorteada quando o
# Pokémon nasce e guardada nele (a marca "candyan_<escolha>" que a textura usa). Não precisa da chave: a palavra solta
# funciona nos comandos (/pokegive vanillite candyan sweetberry shiny), e com a chave também (ice_cream=sweetberry).
CHOICES = {
    "ice_cream": (["vanillite", "vanillish", "vanilluxe"], ["vanilla", "chocolate", "sweetberry", "frostmint"]),
    "candicorn": (["ponyta", "rapidash"], ["candy_corn", "cherry_ice", "cotton_candy", "mint_chip", "peppermint"]),
    "sweetish_fish": (["wishiwashi"], ["red", "green", "yellow", "blue", "pink"]),
    "gummy": (["stufful", "bewear"], ["red", "orange", "yellow", "green", "blue", "purple"]),
}


def write_features(data_dir):
    """Registra cada forma do mod como "feature" do Cobblemon (como ele faz com "galarian"): assim a palavra solta
    funciona nos comandos (/pokespawn zigzagoon forlorn, /pokegive vanillish candyan) e a marca fica guardada no
    Pokémon. As espécies de cada forma vêm de todos os arquivos de species_additions (inclusive os feitos à mão)."""
    species_of = {}
    for f in sorted((data_dir / "species_additions").glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        species = data["target"].split(":")[-1]
        for form in data.get("forms", []):
            for aspect in form.get("aspects", []):
                species_of.setdefault(aspect, []).append(species)
    for aspect, species in species_of.items():
        feature = {"keys": [aspect], "type": "flag", "isAspect": True, "default": False}
        assignment = {"pokemon": sorted(set(species)), "features": [aspect]}
        for folder, content in (("species_features", feature), ("species_feature_assignments", assignment)):
            path = data_dir / folder / f"{aspect}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
        print("feature", aspect, sorted(set(species)))
    for key, (species, choices) in CHOICES.items():
        feature = {"type": "choice", "keys": [key], "needsKey": False, "default": "random", "choices": choices,
                   "isAspect": True, "aspectFormat": "candyan_{{choice}}"}
        assignment = {"pokemon": species, "features": [key]}
        for folder, content in (("species_features", feature), ("species_feature_assignments", assignment)):
            (data_dir / folder / f"{key}.json").write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8",
                                                           newline="\n")
        print("feature", key, species, choices)


def main():
    z = zipfile.ZipFile(sys.argv[1])
    out = Path(sys.argv[2]) / "data/ecosystems_hollows/species_additions"
    out.mkdir(parents=True, exist_ok=True)
    for species, f in FORMS.items():
        data = json.loads(z.read(f"data/cobblemon/species/{f['file']}"))
        base = next((x for x in data.get("forms", []) if x["name"] == f.get("from_form")), data)
        form = {
            "name": f["name"],
            "primaryType": f["types"][0],
            **({"secondaryType": f["types"][1]} if f["types"][1] else {}),
            "aspects": [f["aspect"]],
            "labels": [f["label"], "ecosystems_hollows"],
            "baseStats": f["stats"],
            "abilities": f["abilities"],
            "moves": moves_of(base.get("moves", data["moves"]), f["name"], f["swaps"], f["extra"]),
            "battleOnly": False,
        }
        if "behaviour" in f:
            form["behaviour"] = f["behaviour"]
        if "evolves_to" in f:
            evolutions = []
            for evo in base.get("evolutions", data.get("evolutions", [])):
                evo = dict(evo)
                evo["id"] = f"{species}_{f['evolves_to'].replace(' ', '')}"
                evo["result"] = f["evolves_to"]
                evo["learnableMoves"] = [f["swaps"].get(m, m) for m in evo.get("learnableMoves", [])]
                evolutions.append(evo)
            form["evolutions"] = evolutions
        else:
            form["evolutions"] = []
        if "pre_evolution" in f:
            form["preEvolution"] = f["pre_evolution"]
        path = out / f"{species}_{f['aspect']}.json"
        path.write_text(json.dumps({"target": f"cobblemon:{species}", "forms": [form]}, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        print(path.name, form["primaryType"], form.get("secondaryType", "-"), sum(f["stats"].values()),
              len(form["moves"]), [e["result"] for e in form["evolutions"]])
    write_features(out.parent)


if __name__ == "__main__":
    main()
