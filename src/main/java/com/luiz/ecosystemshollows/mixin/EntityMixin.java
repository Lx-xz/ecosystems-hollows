package com.luiz.ecosystemshollows.mixin;

import com.luiz.ecosystemshollows.HomeFluids;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.material.FluidState;
import net.neoforged.neoforge.common.NeoForgeMod;
import net.neoforged.neoforge.fluids.FluidType;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Para os Pokémon que vivem nos líquidos do Alex's Caves (Toxian no ácido, Wishiwashi Candyan no refrigerante), o
 * líquido deles em volta é do tipo água. No NeoForge, tudo o que diz se uma entidade está num
 * fluido (na água, olho na água, altura do fluido, empurrão da correnteza e a física de nado) sai desses dois métodos.
 */
@Mixin(Entity.class)
public abstract class EntityMixin {
    @Redirect(method = {"updateFluidHeightAndDoFluidPushing()V", "updateFluidOnEyes"},
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/material/FluidState;getFluidType()Lnet/neoforged/neoforge/fluids/FluidType;"))
    private FluidType ecosystemsHollows$homeIsWater(FluidState state) {
        if (HomeFluids.actsAsWater((Entity) (Object) this, state)) return NeoForgeMod.WATER_TYPE.value();
        return state.getFluidType();
    }
}
