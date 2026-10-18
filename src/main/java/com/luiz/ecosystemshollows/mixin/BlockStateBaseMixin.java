package com.luiz.ecosystemshollows.mixin;

import com.luiz.ecosystemshollows.LiquidLogging;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Bloco com líquido dentro (ácido, refrigerante): o fluido dele é esse líquido (o jogo guarda o fluido de cada estado
 * de bloco nesse cache, então o líquido aparece, escorre e faz o efeito dele pelas regras normais), e ao mudar de forma
 * ele agenda o líquido para escorrer, como os blocos com água fazem.
 */
@Mixin(BlockBehaviour.BlockStateBase.class)
public abstract class BlockStateBaseMixin {
    @Shadow private FluidState fluidState;

    @Shadow protected abstract BlockState asState();

    @Inject(method = "initCache", at = @At("TAIL"))
    private void ecosystemsHollows$liquidFluid(CallbackInfo ci) {
        FluidState liquid = LiquidLogging.fluidOf(asState());
        if (liquid != null) fluidState = liquid;
    }

    @Inject(method = "updateShape", at = @At("RETURN"))
    private void ecosystemsHollows$liquidFlows(Direction direction, BlockState neighbor, LevelAccessor level, BlockPos pos,
                                             BlockPos neighborPos, CallbackInfoReturnable<BlockState> cir) {
        LiquidLogging.scheduleFlow(level, pos, cir.getReturnValue());
    }
}
