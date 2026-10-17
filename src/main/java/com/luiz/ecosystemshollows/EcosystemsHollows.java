package com.luiz.ecosystemshollows;

import com.cobblemon.mod.common.entity.pokemon.PokemonEntity;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageType;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;

/**
 * Cobblemon Ecosystems: Hollows, Chasms and Cavities. Compat do mod base com o Alex's Caves.
 * Quase tudo é por dados: remoção dos mobs (tag do mod base), spawns dos Pokémon e formas regionais. O código daqui
 * só cuida do que os dados não fazem: os Pokémon Toxian (Toxic Caves) não se machucam no ácido nem com a radiação.
 */
@Mod(EcosystemsHollows.MOD_ID)
@EventBusSubscriber(modid = EcosystemsHollows.MOD_ID)
public class EcosystemsHollows {
    public static final String MOD_ID = "ecosystems_hollows";
    private static final ResourceKey<DamageType> ACID =
            ResourceKey.create(Registries.DAMAGE_TYPE, ResourceLocation.fromNamespaceAndPath("alexscaves", "acid"));
    private static final ResourceLocation IRRADIATED = ResourceLocation.fromNamespaceAndPath("alexscaves", "irradiated");

    private static boolean isToxian(Object entity) {
        return entity instanceof PokemonEntity pokemon && pokemon.getAspects().contains("toxian");
    }

    @SubscribeEvent
    public static void onDamage(LivingIncomingDamageEvent event) {
        if (event.getSource().is(ACID) && isToxian(event.getEntity())) event.setCanceled(true);
    }

    @SubscribeEvent
    public static void onEffect(MobEffectEvent.Applicable event) {
        if (isToxian(event.getEntity()) && event.getEffectInstance().getEffect().unwrapKey()
                .map(key -> key.location().equals(IRRADIATED)).orElse(false)) {
            event.setResult(MobEffectEvent.Applicable.Result.DO_NOT_APPLY);
        }
    }
}
