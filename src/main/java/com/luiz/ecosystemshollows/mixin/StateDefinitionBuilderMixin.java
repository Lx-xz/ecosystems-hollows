package com.luiz.ecosystemshollows.mixin;

import java.util.Arrays;

import com.luiz.ecosystemshollows.LiquidLogging;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.Property;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Todo bloco que aceita água ganha também a marca do líquido de dentro: ácido ou refrigerante (veja LiquidLogging). */
@Mixin(StateDefinition.Builder.class)
public abstract class StateDefinitionBuilderMixin {
    @Shadow @Final private Object owner;

    @ModifyVariable(method = "add", at = @At("HEAD"), argsOnly = true)
    private Property<?>[] ecosystemsHollows$addLiquid(Property<?>[] properties) {
        if (!(owner instanceof Block)) return properties;
        boolean water = false;
        for (Property<?> property : properties) {
            if (property == LiquidLogging.LIQUID) return properties;
            if (property == BlockStateProperties.WATERLOGGED) water = true;
        }
        if (!water) return properties;
        Property<?>[] more = Arrays.copyOf(properties, properties.length + 1);
        more[properties.length] = LiquidLogging.LIQUID;
        return more;
    }
}
