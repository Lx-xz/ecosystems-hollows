# Cobblemon Ecosystems: Hollows, Chasms and Cavities — Roadmap

Compat do **Cobblemon Ecosystems** com o **Alex's Caves (Unofficial Port)** do Raguto (NeoForge 1.21.1).
Os animais e criaturas fantasiosas das cavernas dão lugar a Pokémon, alguns com **formas regionais** próprias
de cada bioma (como Alola e Galar). Mobs hostis e habitantes das cavernas continuam, e vão ganhar Pokémon.

Mod id: `ecosystems_hollows` · Depende de: Cobblemon 1.8+, Cobblemon Ecosystems 1.9+, Alex's Caves 2.0+ (e Citadel).

Legenda: `[x]` feito · `[ ]` a fazer · **(decidir)** precisa de decisão

---

## Nomes das formas regionais

Como no jogo original (Alolan, Galarian, Hisuian), o nome vem do lugar:

| Bioma | Forma | Status |
|---|---|---|
| Candy Cavity | **Candyan** | em uso |
| Toxic Caves | (decidir) | |
| Abyssal Chasm | (decidir) | |
| Forlorn Hollows | (decidir) | |
| Primordial Caves | (decidir) | |
| Magnetic Caves | (decidir) | |

As formas são **formas de verdade** do Cobblemon (pasta `species_additions`), com tipos próprios, escolhidas
pela marca (aspect) da região, como a de Alola. Atributos, golpes e habilidades ainda vêm da espécie original.

| Pokémon | Forma Candyan | Original |
|---|---|---|
| Stufful | Fada/Normal, 6 cores de gelatina | Normal/Lutador |
| Bewear | Fada/Lutador, 6 cores de gelatina | Normal/Lutador |
| Orthworm | **Fada/Terra**, chiclete listrado (roxo, laranja, verde-água), **10 segmentos** e escala 1,5 (substitui o Gum Worm) | Aço |

---

## Mobs do Alex's Caves

**Saem** (dinossauros, animais do chasm, animais fantasiosos, chefes por enquanto):

| Bioma | Mob | Pokémon no lugar |
|---|---|---|
| Primordial Caves | Subterranodon, Vallumraptor, Grottoceratops, Tremorsaurus, Relicheirus, Atlatitan, Trilocaris | Pokémon fóssil vivos: Aerodactyl, Tyrunt, Amaura, Shieldon, Cranidos, Archen, Kabuto, Omanyte, Anorith |
| Primordial Caves | Tremorzilla, Luxtructosaurus (chefes) | — (voltar no futuro) |
| Toxic Caves | Raycat, Gammaroach, Radgill | Grimer verde brilhante, Koffing, Trubbish, Croagunk, Skorupi |
| Abyssal Chasm | Lanternfish | Chinchou, Lanturn |
| Abyssal Chasm | Sea Pig | Pyukumuku |
| Abyssal Chasm | Tripodfish, Gossamer Worm | Finneon, Relicanth |
| Abyssal Chasm | Hullbreaker (chefe) | — (voltar no futuro; ideia: Wailord ou Dondozo) |
| Forlorn Hollows | Gloomoth | Venomoth, Dustox |
| Forlorn Hollows | Vesper | Zubat, Noibat |
| Forlorn Hollows | Corrodent | Diglett, Drilbur |
| Candy Cavity | Gummy Bear | **Stufful e Bewear Candyan** |
| Candy Cavity | Candicorn | **Ponyta e Rapidash Candyan**, com base na forma de Galar |
| Candy Cavity | Sweetish Fish | Magikarp Candyan |
| Candy Cavity | Caramel Cube | (decidir) Goomy de caramelo, Eiscue "cubo de açúcar" ou Crustle |
| Candy Cavity | Gum Worm | **Orthworm Candyan** gigante, de chiclete |

**Ficam** (hostis e habitantes): Teletor, Magnetron, Boundroid, Notor, Ferrouslime, Brainiac, Nucleeper,
Deep One, Deep One Knight, Deep One Mage, Underzealot, Watcher, Forsaken, Licowitch, Caniac, Gumbeeper.

**Pokémon extras por bioma** (nascem sem substituir ninguém):
- Magnetic Caves: Magnemite, Nosepass, Klink, Beldum
- Candy Cavity: Swirlix, Milcery, Alcremie

---

## Checklist

### Base
- [x] Projeto NeoForge com Cobblemon, mod base, Alex's Caves e Citadel no jogo de teste
- [x] Remoção pela tag `cobblemon_ecosystems:removed_animals` do mod base (bloqueia em todo lugar e tira dos spawns)
- [ ] README
- [ ] Repositório git

### Candy Cavity
- [x] **Stufful e Bewear Candyan** em 6 cores (vermelho, laranja, amarelo, verde, azul, roxo), translúcidos
- [x] Spawn na Candy Cavity (Stufful comum, Bewear incomum)
- [x] Gummy Bear removido
- [x] Testado no jogo: transparência, cores e spawn funcionam
- [x] Formas regionais de verdade: Stufful Fada/Normal, Bewear Fada/Lutador
- [x] Orthworm Candyan no lugar do Gum Worm (Gum Worm removido): modelo próprio com 10 segmentos, gerado por `tools/orthworm_candyan.py`
- [ ] Testar: tipos na batalha, evolução Stufful → Bewear mantendo a forma e a cor
- [ ] Golpes e habilidades próprios das formas Candyan
- [ ] Nome "Candyan Stufful" na tela (hoje aparece só "Stufful")
- [ ] Ponyta e Rapidash Candyan (base: forma de Galar)
- [ ] Magikarp Candyan no lugar do Sweetish Fish
- [ ] Substituto do Caramel Cube
- [ ] Swirlix, Milcery e Alcremie
- [ ] Remover Candicorn, Sweetish Fish e Caramel Cube

### Outros biomas
- [ ] Primordial Caves: Pokémon fóssil vivos; remover os dinossauros
- [ ] Toxic Caves: Grimer verde que brilha no escuro (camada emissiva) e outros; remover Raycat, Gammaroach, Radgill
- [ ] Abyssal Chasm: Chinchou, Lanturn, Pyukumuku, Finneon, Relicanth; remover os animais do chasm
- [ ] Forlorn Hollows: Venomoth, Dustox, Zubat, Noibat, Diglett, Drilbur; remover Gloomoth, Vesper, Corrodent
- [ ] Magnetic Caves: Magnemite, Nosepass, Klink, Beldum

### Habitantes com Pokémon
- [ ] Deep Ones com Pokémon do abismo
- [ ] Underzealots com Pokémon da Forlorn Hollows
- [ ] Licowitch com Pokémon de doce

### Antes de publicar
- [ ] Confirmar se a licença dos assets do Cobblemon permite texturas derivadas em addons
