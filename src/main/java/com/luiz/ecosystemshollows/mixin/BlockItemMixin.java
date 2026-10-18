package com.luiz.ecosystemshollows.mixin;

import com.luiz.ecosystemshollows.LiquidLogging;

import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Bloco colocado numa fonte de ácido ou de refrigerante já nasce com o líquido dentro, como o vanilla faz com a água:
 * na hora de escolher o estado do bloco, pelo fluido que está no lugar.
 */
@Mixin(BlockItem.class)
public abstract class BlockItemMixin {
    @Inject(method = "getPlacementState", at = @At("RETURN"), cancellable = true)
    private void ecosystemsHollows$liquidOnPlace(BlockPlaceContext context, CallbackInfoReturnable<BlockState> cir) {
        BlockState state = cir.getReturnValue();
        if (state == null) return;
        BlockState filled = LiquidLogging.withLiquidAt(state, context.getLevel().getFluidState(context.getClickedPos()));
        if (filled != state) cir.setReturnValue(filled);
    }
}
