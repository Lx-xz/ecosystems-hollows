package com.luiz.ecosystemshollows.mixin;

import com.luiz.ecosystemshollows.HomeFluids;

import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Enquanto um Pokémon que vive num líquido do Alex's Caves está sendo atualizado (Toxian no ácido, Wishiwashi
 * Candyan no refrigerante), um bloco desse líquido responde "sim" para a tag de água: assim a IA, o pathfinding e o
 * movimento do Cobblemon (que olham os blocos pela tag de água) tratam o lago como água. Fora do tick dele, nada muda.
 */
@Mixin(FluidState.class)
public abstract class FluidStateMixin {
    @Inject(method = "is(Lnet/minecraft/tags/TagKey;)Z", at = @At("HEAD"), cancellable = true)
    private void ecosystemsHollows$homeIsWater(TagKey<Fluid> tag, CallbackInfoReturnable<Boolean> cir) {
        if (tag == FluidTags.WATER && HomeFluids.is((FluidState) (Object) this, HomeFluids.ticking())) {
            cir.setReturnValue(true);
        }
    }
}
