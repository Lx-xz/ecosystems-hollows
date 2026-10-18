package com.luiz.ecosystemshollows;

import com.cobblemon.mod.common.entity.pokemon.PokemonEntity;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.material.FluidState;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * Os líquidos do Alex's Caves contam como água para os Pokémon que vivem neles, para eles nadarem exatamente como na
 * água: com a IA, o pathfinding, o movimento, as poses e as animações de nado do próprio Cobblemon.
 * <ul>
 *   <li>Os Toxian (Toxic Caves) vivem no ácido.</li>
 *   <li>O Wishiwashi Candyan (o Sweetish Fish da Candy Cavity) vive no refrigerante roxo.</li>
 * </ul>
 * Como funciona:
 * <ul>
 *   <li>Na entidade ({@code mixin/EntityMixin}): o líquido dela em volta é do tipo água, então ela está "na água",
 *   com o olho na água e com a física de nado, nos dois lados (servidor e cliente).</li>
 *   <li>Nos blocos ({@code mixin/FluidStateMixin}): enquanto um desses Pokémon está sendo atualizado (o tick dele,
 *   onde rodam a IA e o pathfinding do Cobblemon), um bloco do líquido dele responde "sim" para a tag de água. Fora do
 *   tick dele, o líquido continua o mesmo para todo o resto do jogo.</li>
 * </ul>
 */
@EventBusSubscriber(modid = EcosystemsHollows.MOD_ID)
public final class HomeFluids {
    public static final String ACID = "acid";
    public static final String SODA = "purple_soda";

    /** O líquido do Pokémon que está no tick agora nesta thread (null: nenhum). */
    private static final ThreadLocal<String> TICKING = new ThreadLocal<>();

    private HomeFluids() {
    }

    /** O líquido em que o Pokémon vive (ACID, SODA), ou null. */
    public static String homeOf(Object entity) {
        if (!(entity instanceof PokemonEntity pokemon)) return null;
        var aspects = pokemon.getAspects();
        if (aspects.contains("toxian")) return ACID;
        if (aspects.contains("candyan") && pokemon.getPokemon().getSpecies().getResourceIdentifier().getPath().equals("wishiwashi")) {
            return SODA;
        }
        return null;
    }

    public static boolean isToxian(Object entity) {
        return ACID.equals(homeOf(entity));
    }

    /** Se o fluido é o líquido (ACID ou SODA) do Alex's Caves, parado ou correndo. */
    public static boolean is(FluidState state, String liquid) {
        if (liquid == null || state.isEmpty()) return false;
        ResourceLocation id = BuiltInRegistries.FLUID.getKey(state.getType());
        return id.getNamespace().equals("alexscaves") && id.getPath().startsWith(liquid);
    }

    public static boolean isAcid(FluidState state) {
        return is(state, ACID);
    }

    /** O líquido do Pokémon que está no tick agora (null: não é um desses). */
    public static String ticking() {
        return TICKING.get();
    }

    // Marca o começo e o fim do tick de cada entidade. Todo começo de tick redefine a marca, então ela não fica
    // ligada por engano se um tick for interrompido.
    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void onTickStart(EntityTickEvent.Pre event) {
        TICKING.set(homeOf(event.getEntity()));
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onTickEnd(EntityTickEvent.Post event) {
        TICKING.remove();
    }

    /** Se o fluido é o líquido em que a entidade vive (para ela, ele vira água). */
    public static boolean actsAsWater(Entity entity, FluidState state) {
        return is(state, homeOf(entity));
    }
}
