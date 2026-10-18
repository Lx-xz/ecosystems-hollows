package com.luiz.ecosystemshollows;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.damagesource.DamageTypes;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;

/**
 * Cobblemon Ecosystems: Hollows, Chasms and Cavities. Compat do mod base com o Alex's Caves.
 * Quase tudo é por dados: remoção dos mobs (tag do mod base), spawns dos Pokémon e formas regionais. O código daqui
 * só cuida do que os dados não fazem: os Pokémon que vivem nos líquidos do Alex's Caves nadam neles como na água e não
 * se afogam (veja {@link HomeFluids}): os Toxian (Toxic Caves) no ácido, que também não os machuca nem dá radiação, e
 * o Wishiwashi Candyan (Candy Cavity) no refrigerante roxo. Os blocos com ácido ou refrigerante dentro estão em
 * {@link LiquidLogging}.
 */
@Mod(EcosystemsHollows.MOD_ID)
@EventBusSubscriber(modid = EcosystemsHollows.MOD_ID)
public class EcosystemsHollows {
    public static final String MOD_ID = "ecosystems_hollows";
    private static final ResourceKey<DamageType> ACID =
            ResourceKey.create(Registries.DAMAGE_TYPE, ResourceLocation.fromNamespaceAndPath("alexscaves", "acid"));
    private static final ResourceLocation IRRADIATED = ResourceLocation.fromNamespaceAndPath("alexscaves", "irradiated");

    @SubscribeEvent
    public static void onDamage(LivingIncomingDamageEvent event) {
        // Afogamento dentro do líquido deles (por garantia: para eles o líquido já conta como água), e o ácido.
        String home = HomeFluids.homeOf(event.getEntity());
        if (home == null) return;
        boolean inHome = HomeFluids.is(event.getEntity().level().getFluidState(event.getEntity().blockPosition()), home);
        if ((event.getSource().is(ACID) && home.equals(HomeFluids.ACID)) || (event.getSource().is(DamageTypes.DROWN) && inHome)) {
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onEffect(MobEffectEvent.Applicable event) {
        if (HomeFluids.isToxian(event.getEntity()) && event.getEffectInstance().getEffect().unwrapKey()
                .map(key -> key.location().equals(IRRADIATED)).orElse(false)) {
            event.setResult(MobEffectEvent.Applicable.Result.DO_NOT_APPLY);
        }
    }
}
