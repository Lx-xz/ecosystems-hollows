# Gera os spawns dos Pokémon temáticos de cada caverna do Alex's Caves (data/ecosystems_hollows/spawn_pool_world/caves_*.json),
# a tag dos mobs removidos e o docs/pokemon-das-cavernas.md (para revisar e editar).
#
# Os drops ficam no próprio spawn: só os Pokémon que nascem naquela caverna dão aqueles itens (o mesmo Pokémon nascido
# em outro lugar continua com os drops normais do Cobblemon). Eles repõem os itens que os mobs removidos davam, que o
# Alex's Caves usa nas receitas.
#
# Uso: python cave_spawns.py <pasta resources do mod> <pasta docs>
import json
import sys
from pathlib import Path

AC = "alexscaves:"
FLAVORS = ["candy_corn", "peppermint", "mint_chip", "cherry_ice", "cotton_candy"]
# Sabores dos sorvetes (Vanillite Candyan) e a bola de sorvete que cada um dá (o frostmint dá a de baunilha).
SCOOPS = {"vanilla": "vanilla_ice_cream", "chocolate": "chocolate_ice_cream", "sweetberry": "sweetberry_ice_cream",
          "frostmint": "vanilla_ice_cream"}


def d(item, chance, qty="1"):
    """Um drop: item, chance em % e quantidade ("1" ou "1-2")."""
    return {"item": item, "percentage": chance, "qty": qty}


# Pokémon de cada caverna: (espécie, onde nasce, raridade, níveis, peso, drops, substitui)
CAVES = {
    "primordial_caves": {
        "name": "Primordial Caves",
        "removed": ["subterranodon", "vallumraptor", "grottoceratops", "tremorsaurus", "relicheirus", "atlatitan", "trilocaris"],
        "pokemon": [
            ("aerodactyl", "grounded", "uncommon", "25-40", 4, [d(AC + "dinosaur_chop", 60, "1-2")], "Subterranodon"),
            ("cranidos", "grounded", "common", "18-30", 6, [d(AC + "dinosaur_chop", 60)], "Vallumraptor"),
            ("rampardos", "grounded", "rare", "32-45", 1, [d(AC + "dinosaur_chop", 70, "1-2"), d(AC + "heavy_bone", 30)], "Vallumraptor"),
            ("shieldon", "grounded", "common", "18-30", 6, [d(AC + "dinosaur_chop", 60), d(AC + "tough_hide", 40)], "Grottoceratops"),
            ("bastiodon", "grounded", "rare", "30-45", 1, [d(AC + "dinosaur_chop", 70, "1-2"), d(AC + "tough_hide", 60, "1-2")], "Grottoceratops"),
            ("tyrunt", "grounded", "uncommon", "20-32", 3, [d(AC + "dinosaur_chop", 60, "1-2"), d(AC + "heavy_bone", 40)], "Tremorsaurus"),
            ("tyrantrum", "grounded", "rare", "39-50", 1, [d(AC + "dinosaur_chop", 80, "2-3"), d(AC + "heavy_bone", 60)], "Tremorsaurus"),
            ("archen", "grounded", "uncommon", "20-32", 3, [d("minecraft:feather", 60, "1-2"), d(AC + "dinosaur_chop", 40), d(AC + "heavy_bone", 20)], "Relicheirus"),
            ("archeops", "grounded", "rare", "37-50", 1, [d("minecraft:feather", 70, "1-3"), d(AC + "heavy_bone", 40)], "Relicheirus"),
            ("amaura", "grounded", "uncommon", "20-32", 3, [d(AC + "dinosaur_chop", 60, "1-2"), d(AC + "heavy_bone", 40)], "Atlatitan"),
            ("aurorus", "grounded", "rare", "39-50", 1, [d(AC + "dinosaur_chop", 80, "2-4"), d(AC + "heavy_bone", 60)], "Atlatitan"),
            ("kabuto", "submerged", "common", "15-30", 5, [d(AC + "trilocaris_tail", 60)], "Trilocaris"),
            ("omanyte", "submerged", "common", "15-30", 5, [d(AC + "trilocaris_tail", 60)], "Trilocaris"),
            ("anorith", "submerged", "uncommon", "15-30", 3, [d(AC + "trilocaris_tail", 60)], "Trilocaris"),
        ],
    },
    "toxic_caves": {
        "name": "Toxic Caves",
        "removed": ["raycat", "gammaroach", "radgill"],
        "pokemon": [
            ("grimer", "grounded", "common", "18-30", 8, [d(AC + "toxic_paste", 60, "1-2")], "Gammaroach"),
            ("muk", "grounded", "rare", "38-50", 1, [d(AC + "toxic_paste", 80, "2-3")], "Gammaroach"),
            ("koffing", "grounded", "common", "18-30", 6, [d(AC + "toxic_paste", 50)], "Gammaroach"),
            ("weezing", "grounded", "rare", "35-50", 1, [d(AC + "toxic_paste", 70, "1-2")], "Gammaroach"),
            ("trubbish", "grounded", "common", "18-30", 5, [d("minecraft:bone", 50, "1-2")], "Raycat"),
            ("garbodor", "grounded", "rare", "36-50", 1, [d("minecraft:bone", 60, "1-3"), d(AC + "toxic_paste", 40)], "Raycat"),
            ("croagunk", "grounded", "uncommon", "18-30", 3, [d(AC + "toxic_paste", 40)], "-"),
            ("skorupi", "grounded", "uncommon", "18-30", 3, [d("minecraft:bone", 40)], "-"),
            # Carvanha e Sharpedo Toxian (tools/toxian_carvanha.py): o peixe radioativo de três olhos.
            # Nascem dentro do ácido (e na água); o ácido não machuca os Toxian (EcosystemsHollows).
            ("carvanha form=toxian aspect=toxian", "acid", "common", "18-30", 6, [d(AC + "radgill", 50)], "Radgill"),
            ("sharpedo form=toxian aspect=toxian", "acid", "rare", "30-45", 1, [d(AC + "radgill", 70, "1-2")], "Radgill"),
            ("carvanha form=toxian aspect=toxian", "submerged", "common", "18-30", 3, [d(AC + "radgill", 50)], "Radgill"),
            # Heracross Toxian: a Gammaroach, a barata radioativa (tools/toxian_heracross.py).
            ("heracross form=toxian aspect=toxian", "grounded", "uncommon", "20-40", 3,
             [d(AC + "toxic_paste", 40)], "Gammaroach"),
        ],
    },
    "abyssal_chasm": {
        "name": "Abyssal Chasm",
        "removed": ["lanternfish", "sea_pig", "tripodfish", "gossamer_worm"],
        "pokemon": [
            ("chinchou", "submerged", "common", "20-35", 8, [d(AC + "lanternfish", 40), d(AC + "bioluminesscence", 20)], "Lanternfish"),
            ("lanturn", "submerged", "uncommon", "30-45", 2, [d(AC + "bioluminesscence", 50, "1-2")], "Lanternfish"),
            ("pyukumuku", "submerged", "common", "20-35", 5, [d(AC + "sea_pig", 50)], "Sea Pig"),
            ("finneon", "submerged", "common", "20-35", 5, [d(AC + "tripodfish", 40)], "Tripodfish"),
            ("lumineon", "submerged", "uncommon", "31-45", 1, [d(AC + "tripodfish", 50), d(AC + "bioluminesscence", 30)], "Tripodfish"),
            ("relicanth", "submerged", "rare", "30-45", 2, [d(AC + "bioluminesscence", 60, "1-2")], "Gossamer Worm"),
        ],
    },
    "forlorn_hollows": {
        "name": "Forlorn Hollows",
        "removed": ["gloomoth", "vesper", "corrodent"],
        "pokemon": [
            ("venonat", "grounded", "common", "18-30", 5, [d(AC + "moth_dust", 50)], "Gloomoth"),
            ("venomoth", "grounded", "uncommon", "31-45", 2, [d(AC + "moth_dust", 70, "1-2")], "Gloomoth"),
            ("dustox", "grounded", "uncommon", "20-35", 2, [d(AC + "moth_dust", 60, "1-2")], "Gloomoth"),
            # Noibat Forlorn: o Vesper, morcego cego que caça pelo som (tools/forlorn_noivern.py). O Noivern Forlorn (o
            # Forsaken) não nasce solto: vem do ritual ou da evolução.
            ("noibat form=forlorn aspect=forlorn", "grounded", "common", "18-35", 8,
             [d(AC + "vesper_wing", 30), d(AC + "guano", 50, "1-2")], "Vesper"),
            ("zubat", "grounded", "common", "18-30", 3, [d(AC + "guano", 50, "1-2")], "-"),
            ("golbat", "grounded", "uncommon", "22-40", 1, [d(AC + "guano", 60, "1-2")], "-"),
            # Zigzagoon e Linoone Forlorn: o Corrodent, rato-toupeira pelado e espinhento que rói pedra (tools/forlorn_zigzagoon.py).
            ("zigzagoon form=forlorn aspect=forlorn", "grounded", "common", "15-28", 6,
             [d(AC + "corrodent_teeth", 30), d("minecraft:coarse_dirt", 40, "1-2")], "Corrodent"),
            ("linoone form=forlorn aspect=forlorn", "grounded", "uncommon", "28-45", 2,
             [d(AC + "corrodent_teeth", 60, "1-2")], "Corrodent"),
            ("diglett", "grounded", "common", "18-30", 2, [d("minecraft:coarse_dirt", 50, "1-2")], "-"),
            ("drilbur", "grounded", "uncommon", "18-30", 1, [], "-"),
        ],
    },
    "candy_cavity": {
        "name": "Candy Cavity",
        # Gummy Bear e Gum Worm já saem pelas formas Candyan (arquivos candyan_*.json e o Rayquaza Candyan).
        "removed": ["candicorn", "sweetish_fish", "caramel_cube"],
        "pokemon": [
            # Ponyta e Rapidash Candyan: forma regional (Fada), com os sabores dos Candicorns (tools/candyan_ponyta.py
            # e tools/regional_forms.py).
            *[(f"ponyta form=candyan aspect=candyan candicorn={f}", "grounded", "uncommon", "15-30", 1,
               [d(AC + "sweet_puff", 60, "1-2")], "Candicorn") for f in FLAVORS],
            *[(f"rapidash form=candyan aspect=candyan candicorn={f}", "grounded", "rare", "40-50", 0.2,
               [d(AC + "sweet_puff", 80, "2-3")], "Candicorn") for f in FLAVORS],
            # Rayquaza Candyan: a Gum Worm (Fada/Dragão, tools/rayquaza_gumworm.py). Incapturável por enquanto.
            ("rayquaza form=candyan aspect=candyan uncatchable", "grounded", "ultra-rare", "60-70", 1,
             [d(AC + "sweet_tooth", 100, "2-4")], "Gum Worm"),
            # Wishiwashi Candyan: o Sweetish Fish (tools/candyan_wishiwashi.py); cada cor dá a bala da mesma cor.
            *[(f"wishiwashi form=candyan aspect=candyan sweetish_fish={c}", where, "common", "5-20", 3,
               [d(AC + f"sweetish_fish_{c}", 50, "1-2")], "Sweetish Fish")
              for where in ("submerged", "soda") for c in ("red", "green", "yellow", "blue", "pink")],
            ("goomy", "grounded", "uncommon", "15-30", 3, [d(AC + "caramel", 60, "1-2")], "Caramel Cube"),
            # Tangela Candyan: o licoroot, de alcaçuz (tools/candyan_tangela.py).
            ("tangela form=candyan aspect=candyan", "grounded", "uncommon", "15-30", 3,
             [d(AC + "licoroot_vine", 60, "1-3")], "Licoroot"),
            ("tangrowth form=candyan aspect=candyan", "grounded", "rare", "33-50", 0.5,
             [d(AC + "licoroot_vine", 80, "2-4"), d(AC + "licoroot", 30)], "Licoroot"),
            # Vanillite, Vanillish e Vanilluxe Candyan: os sorvetes, em cada sabor (tools/candyan_vanillite.py).
            *[(f"vanillite form=candyan aspect=candyan ice_cream={f}", "grounded", "common", "12-28", 1.5,
               [d(AC + f"{scoop}_scoop", 50)], "-") for f, scoop in SCOOPS.items()],
            *[(f"vanillish form=candyan aspect=candyan ice_cream={f}", "grounded", "uncommon", "35-45", 0.5,
               [d(AC + f"{scoop}_scoop", 60, "1-2")], "-") for f, scoop in SCOOPS.items()],
            *[(f"vanilluxe form=candyan aspect=candyan ice_cream={f}", "grounded", "rare", "47-55", 0.2,
               [d(AC + f"{scoop}_scoop", 70, "1-3"), d(AC + "sundae", 15)], "-") for f, scoop in SCOOPS.items()],
            ("swirlix", "grounded", "uncommon", "15-30", 3, [], "-"),
            ("milcery", "grounded", "rare", "15-30", 2, [], "-"),
        ],
    },
    "magnetic_caves": {
        "name": "Magnetic Caves",
        "removed": [],
        "pokemon": [
            # Magnemite, Magneton e Magnezone Magnetian: os ímãs da caverna (tools/magnetian_magnemite.py).
            ("magnemite form=magnetian aspect=magnetian", "grounded", "common", "18-30", 6,
             [d(AC + "raw_scarlet_neodymium", 25), d(AC + "raw_azure_neodymium", 25)], "-"),
            ("magneton form=magnetian aspect=magnetian", "grounded", "rare", "30-45", 1,
             [d(AC + "raw_scarlet_neodymium", 40, "1-2"), d(AC + "raw_azure_neodymium", 40, "1-2")], "-"),
            ("nosepass", "grounded", "uncommon", "20-35", 3, [], "-"),
            ("klink", "grounded", "uncommon", "18-30", 3, [], "-"),
            ("beldum", "grounded", "rare", "20-35", 1, [], "-"),
        ],
    },
}

# Drops das formas Candyan (que já existem): a gelatina da cor delas, e o dente-doce do Orthworm.
GELATIN = {"red": "red", "orange": "red", "yellow": "yellow", "green": "green", "blue": "blue", "purple": "pink"}


def drop_table(drops):
    entries = []
    for x in drops:
        e = {"item": x["item"], "percentage": float(x["percentage"])}
        if x["qty"] != "1":
            e["quantityRange"] = x["qty"]
        entries.append(e)
    return {"amount": len(entries), "entries": entries}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    resources, docs = Path(sys.argv[1]), Path(sys.argv[2])
    data = resources / "data"
    removed = []
    for biome, cave in CAVES.items():
        spawns = []
        for species, position, bucket, levels, weight, drops, _ in cave["pokemon"]:
            # Nos lagos de ácido ou de refrigerante: "debaixo d'água" naquele líquido (HomeFluids faz ele contar como água).
            liquid = {"acid": "acid", "soda": "purple_soda"}.get(position)
            spawn = {
                "id": f"ecosystems_hollows-{biome}-{species.replace('aspect=', '').replace(' ', '-')}" + (f"-{position}" if liquid else ""),
                "pokemon": species,
                "type": "pokemon",
                "spawnablePositionType": "submerged" if liquid else position,
                "bucket": bucket,
                "level": levels,
                "weight": float(weight),
                "condition": {"canSeeSky": False, "biomes": [AC + biome]},
            }
            if liquid:
                spawn["condition"]["fluid"] = AC + liquid
            if drops:
                spawn["drops"] = drop_table(drops)
            spawns.append(spawn)
        write(data / "ecosystems_hollows/spawn_pool_world" / f"caves_{biome}.json",
              {"enabled": True, "neededInstalledMods": ["alexscaves"], "neededUninstalledMods": [], "spawns": spawns})
        removed += cave["removed"]

    # Drops das formas Candyan.
    pool = data / "ecosystems_hollows/spawn_pool_world"
    for name, gelatin_qty, extra in (("candyan_stufful", "1-2", []), ("candyan_bewear", "2-3", [])):
        f = pool / f"{name}.json"
        spawns = json.loads(f.read_text(encoding="utf-8"))
        for s in spawns["spawns"]:
            # O sabor é a feature "gummy" (regional_forms.py), não um aspect solto.
            s["pokemon"] = s["pokemon"].replace("aspect=candyan_", "gummy=")
            color = next(a for a in s["pokemon"].split() if a.startswith("gummy=")).split("=")[-1]
            s["drops"] = drop_table([d(AC + "gelatin_" + GELATIN[color], 70, gelatin_qty)] + extra)
        write(f, spawns)
    # Orthworm Candyan: desligado por enquanto (o Rayquaza Candyan é a Gum Worm agora).
    f = pool / "candyan_orthworm.json"
    spawns = json.loads(f.read_text(encoding="utf-8"))
    spawns["enabled"] = False
    for s in spawns["spawns"]:
        s["drops"] = drop_table([d(AC + "sweet_tooth", 50)])
    write(f, spawns)

    # Tag do mod base com os mobs removidos (as formas Candyan já tiram o Gummy Bear e o Gum Worm).
    values = [{"id": AC + m, "required": False} for m in ["gummy_bear", "gum_worm"] + removed]
    write(data / "cobblemon_ecosystems/tags/entity_type/removed_animals.json", {"replace": False, "values": values})

    write_md(docs / "pokemon-das-cavernas.md")


def write_md(path):
    lines = [
        "# Pokémon das cavernas (Alex's Caves)",
        "",
        "Gerado por `tools/cave_spawns.py`. **Edite à vontade** (espécies, raridade, níveis, drops) e me avise: eu passo",
        "as mudanças para o script e para o jogo.",
        "",
        "- Os mobs da coluna \"substitui\" **não nascem mais**; os chefes (Tremorzilla, Luxtructosaurus, Hullbreaker) e os",
        "  habitantes e monstros (Deep Ones, Underzealot, Teletor, Licowitch...) continuam.",
        "- Os **drops só valem para quem nasce naquela caverna**: o mesmo Pokémon nascido em outro lugar dá os drops normais",
        "  do Cobblemon. Eles repõem os itens dos mobs removidos, que o Alex's Caves usa nas receitas.",
        "- Raridade: common, uncommon, rare (do Cobblemon). Peso: quanto aparece dentro da mesma raridade.",
        "- Chance dos drops: cada item é sorteado à parte.",
        "",
    ]
    for biome, cave in CAVES.items():
        lines += [f"## {cave['name']}", ""]
        if cave["removed"]:
            lines += ["Saem: " + ", ".join(m.replace("_", " ").title() for m in cave["removed"]), ""]
        lines += ["| Pokémon | Substitui | Onde | Raridade | Níveis | Peso | Drops |", "|---|---|---|---|---|---|---|"]
        for species, position, bucket, levels, weight, drops, replaces in cave["pokemon"]:
            where = {"grounded": "chão", "submerged": "água", "acid": "ácido", "soda": "refrigerante"}[position]
            drop_text = ", ".join(f"{x['item'].split(':')[1]} {x['qty']} ({x['percentage']}%)" for x in drops) or "normais do Cobblemon"
            label = species.split(" form=")[0].split(" aspect=")[0].title() + (" Toxian" if "toxian" in species else "") + (" Magnetian" if "magnetian" in species else "") + (" Forlorn" if "forlorn" in species else "") + (" Candyan " + species.split()[-1].split("=")[1].replace("_", " ") if "candyan" in species and species.split()[-1].split("=")[0] in ("candicorn", "sweetish_fish", "ice_cream") else " Candyan" if "candyan" in species else "") + (" (incapturável)" if "uncatchable" in species else "")
            lines.append(f"| {label} | {replaces} | {where} | {bucket} | {levels} | {weight} | {drop_text} |")
        lines.append("")
    lines += [
        "## Candyan (já existentes)",
        "",
        "| Pokémon | Substitui | Drops |",
        "|---|---|---|",
        "| Stufful Candyan | Gummy Bear | gelatina da cor 1-2 (70%): vermelho e laranja dão vermelha, roxo dá rosa |",
        "| Bewear Candyan | Gummy Bear | gelatina da cor 2-3 (70%) |",
        "| Orthworm Candyan | Gum Worm | sweet_tooth 1 (50%). **Desligado por enquanto** (a Gum Worm é o Rayquaza Candyan) |",
        "",
        "## A decidir",
        "",
        "- Toxic Caves: o Grimer verde que brilha",
        "- Candy Cavity: o substituto definitivo do Caramel Cube (hoje Goomy dá caramelo)",
        "- Chefes viram Pokémon lendários, com captura diferente (não é só jogar a Pokébola enquanto ele ataca):",
        "  - **Tremorzilla**: o fim da progressão do Primordial Caves, feita com Pokémon",
        "  - **Hullbreaker** (Abyssal Chasm)",
        "  - **Forsaken**, o morcego gigante das Forlorn Hollows",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
