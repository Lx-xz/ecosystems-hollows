package com.luiz.ecosystemshollows.mixin;

import com.luiz.ecosystemshollows.LiquidLogging;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/**
 * O estado padrão dos blocos nasce sem líquido dentro: os blocos não conhecem a marca nova (garantia, caso o
 * estado padrão de algum bloco não seja o primeiro).
 */
@Mixin(Block.class)
public abstract class BlockMixin {
    @ModifyVariable(method = "registerDefaultState", at = @At("HEAD"), argsOnly = true)
    private BlockState ecosystemsHollows$noLiquidByDefault(BlockState state) {
        return state.hasProperty(LiquidLogging.LIQUID) ? state.setValue(LiquidLogging.LIQUID, LiquidLogging.Liquid.NONE) : state;
    }
}
