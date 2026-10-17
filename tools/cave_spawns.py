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
            ("zubat", "grounded", "common", "18-30", 8, [d(AC + "guano", 50, "1-2"), d(AC + "vesper_wing", 15)], "Vesper"),
            ("golbat", "grounded", "uncommon", "22-40", 2, [d(AC + "guano", 60, "1-2"), d(AC + "vesper_wing", 30)], "Vesper"),
            ("noibat", "grounded", "uncommon", "18-30", 3, [d(AC + "vesper_wing", 30), d(AC + "guano", 40)], "Vesper"),
            ("diglett", "grounded", "common", "18-30", 6, [d(AC + "corrodent_teeth", 30), d("minecraft:coarse_dirt", 50, "1-2")], "Corrodent"),
            ("dugtrio", "grounded", "rare", "26-45", 1, [d(AC + "corrodent_teeth", 60, "1-2")], "Corrodent"),
            ("drilbur", "grounded", "uncommon", "18-30", 3, [d(AC + "corrodent_teeth", 40)], "Corrodent"),
        ],
    },
    "candy_cavity": {
        "name": "Candy Cavity",
        # Gummy Bear e Gum Worm já saem pelas formas Candyan (arquivos candyan_*.json).
        "removed": ["candicorn", "sweetish_fish", "caramel_cube"],
        "pokemon": [
            # Ponyta e Rapidash Candyan: o de Galar com os sabores dos Candicorns (tools/candyan_ponyta.py).
            *[(f"ponyta galarian aspect=candyan aspect=candyan_{f}", "grounded", "uncommon", "15-30", 1,
               [d(AC + "sweet_puff", 60, "1-2")], "Candicorn") for f in FLAVORS],
            *[(f"rapidash galarian aspect=candyan aspect=candyan_{f}", "grounded", "rare", "40-50", 0.2,
               [d(AC + "sweet_puff", 80, "2-3")], "Candicorn") for f in FLAVORS],
            ("magikarp", "submerged", "common", "5-20", 6,
             [d(AC + "sweetish_fish_" + c, 12) for c in ("red", "green", "yellow", "blue", "pink")], "Sweetish Fish"),
            ("goomy", "grounded", "uncommon", "15-30", 3, [d(AC + "caramel", 60, "1-2")], "Caramel Cube"),
            ("swirlix", "grounded", "uncommon", "15-30", 3, [], "-"),
            ("milcery", "grounded", "rare", "15-30", 2, [], "-"),
        ],
    },
    "magnetic_caves": {
        "name": "Magnetic Caves",
        "removed": [],
        "pokemon": [
            ("magnemite", "grounded", "common", "18-30", 6, [], "-"),
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
            acid = position == "acid"
            spawn = {
                "id": f"ecosystems_hollows-{biome}-{species.replace('aspect=', '').replace(' ', '-')}" + ("-acid" if acid else ""),
                "pokemon": species,
                "type": "pokemon",
                "spawnablePositionType": "submerged" if acid else position,
                "bucket": bucket,
                "level": levels,
                "weight": float(weight),
                "condition": {"canSeeSky": False, "biomes": [AC + biome]},
            }
            if acid:
                spawn["condition"]["fluid"] = AC + "acid"
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
            color = next(a for a in s["pokemon"].split() if a.startswith("aspect=candyan_")).split("_")[-1]
            s["drops"] = drop_table([d(AC + "gelatin_" + GELATIN[color], 70, gelatin_qty)] + extra)
        write(f, spawns)
    f = pool / "candyan_orthworm.json"
    spawns = json.loads(f.read_text(encoding="utf-8"))
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
            where = {"grounded": "chão", "submerged": "água", "acid": "ácido"}[position]
            drop_text = ", ".join(f"{x['item'].split(':')[1]} {x['qty']} ({x['percentage']}%)" for x in drops) or "normais do Cobblemon"
            label = species.split(" form=")[0].split(" aspect=")[0].title() + (" Toxian" if "toxian" in species else "") + (" Candyan " + species.rsplit("candyan_", 1)[1].replace("_", " ") if "candyan_" in species else "")
            lines.append(f"| {label} | {replaces} | {where} | {bucket} | {levels} | {weight} | {drop_text} |")
        lines.append("")
    lines += [
        "## Candyan (já existentes)",
        "",
        "| Pokémon | Substitui | Drops |",
        "|---|---|---|",
        "| Stufful Candyan | Gummy Bear | gelatina da cor 1-2 (70%): vermelho e laranja dão vermelha, roxo dá rosa |",
        "| Bewear Candyan | Gummy Bear | gelatina da cor 2-3 (70%) |",
        "| Orthworm Candyan | Gum Worm | sweet_tooth 1 (50%) |",
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
