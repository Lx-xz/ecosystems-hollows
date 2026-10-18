package com.luiz.ecosystemshollows;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/**
 * Blocos com os líquidos do Alex's Caves dentro ("acidlogged", "sodalogged"), como a água faz com os blocos
 * "waterlogged" e como o próprio Alex's Caves faz com o bastão de urânio. Todo bloco que aceita água ganha também a
 * marca {@link #LIQUID} (nenhum, ácido ou refrigerante roxo; {@code mixin/StateDefinitionBuilderMixin}); com ela, o
 * fluido do bloco é aquele líquido ({@code mixin/BlockStateBaseMixin}), então ele aparece dentro do bloco, escorre
 * para os lados, faz o efeito dele em quem entra e fica no lugar quando o bloco quebra, tudo pelas regras normais de
 * fluido do jogo.
 * <ul>
 *   <li>Balde do líquido num bloco que aceita água: o bloco fica com o líquido dentro. Balde vazio nele: tira.</li>
 *   <li>Colocar um bloco que aceita água dentro de uma fonte do líquido: ele já nasce com o líquido dentro
 *   ({@code mixin/BlockItemMixin}).</li>
 * </ul>
 */
@EventBusSubscriber(modid = EcosystemsHollows.MOD_ID)
public final class LiquidLogging {
    /** O líquido de dentro do bloco. */
    public enum Liquid implements StringRepresentable {
        NONE("none", null),
        ACID("acid", "acid"),
        PURPLE_SODA("purple_soda", "purple_soda");

        private final String name;
        private final ResourceLocation fluid, bucket;

        Liquid(String name, String fluid) {
            this.name = name;
            this.fluid = fluid == null ? null : ResourceLocation.fromNamespaceAndPath("alexscaves", fluid);
            this.bucket = fluid == null ? null : ResourceLocation.fromNamespaceAndPath("alexscaves", fluid + "_bucket");
        }

        @Override
        public String getSerializedName() {
            return name;
        }

        /** A fonte do líquido, ou vazio se ele não existe (sem o Alex's Caves). */
        public Fluid fluid() {
            return fluid == null ? Fluids.EMPTY : BuiltInRegistries.FLUID.get(fluid);
        }

        public Item bucket() {
            return bucket == null ? Items.AIR : BuiltInRegistries.ITEM.get(bucket);
        }
    }

    public static final EnumProperty<Liquid> LIQUID = EnumProperty.create("liquid", Liquid.class);

    private LiquidLogging() {
    }

    public static Liquid liquidOf(BlockState state) {
        return state.hasProperty(LIQUID) ? state.getValue(LIQUID) : Liquid.NONE;
    }

    /** O fluido de um bloco com líquido dentro (null: o bloco não tem, fica o fluido normal dele). */
    public static FluidState fluidOf(BlockState state) {
        Fluid fluid = liquidOf(state).fluid();
        return fluid != Fluids.EMPTY ? fluid.defaultFluidState() : null;
    }

    /** Agenda a atualização do líquido no bloco, para ele escorrer para os vizinhos. */
    public static void scheduleFlow(LevelAccessor level, BlockPos pos, BlockState state) {
        Fluid fluid = liquidOf(state).fluid();
        if (fluid != Fluids.EMPTY) level.scheduleTick(pos, fluid, fluid.getTickDelay(level));
    }

    private static boolean canHold(BlockState state) {
        return state.hasProperty(LIQUID) && state.getValue(LIQUID) == Liquid.NONE
                && !(state.hasProperty(BlockStateProperties.WATERLOGGED) && state.getValue(BlockStateProperties.WATERLOGGED));
    }

    private static Liquid ofBucket(ItemStack stack) {
        for (Liquid liquid : Liquid.values()) {
            if (liquid != Liquid.NONE && stack.is(liquid.bucket())) return liquid;
        }
        return Liquid.NONE;
    }

    @SubscribeEvent
    public static void onBucket(PlayerInteractEvent.RightClickBlock event) {
        Level level = event.getLevel();
        BlockPos pos = event.getPos();
        BlockState state = level.getBlockState(pos);
        Player player = event.getEntity();
        ItemStack stack = event.getItemStack();
        Liquid poured = ofBucket(stack);
        Liquid inside = liquidOf(state);
        if (poured != Liquid.NONE && canHold(state)) {
            // Balde do líquido: o bloco fica com ele dentro.
            if (!level.isClientSide()) {
                BlockState filled = state.setValue(LIQUID, poured);
                level.setBlock(pos, filled, 3);
                scheduleFlow(level, pos, filled);
                level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 1f, 1f);
                if (!player.getAbilities().instabuild) player.setItemInHand(event.getHand(), new ItemStack(Items.BUCKET));
            }
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.sidedSuccess(level.isClientSide()));
        } else if (stack.is(Items.BUCKET) && inside != Liquid.NONE) {
            // Balde vazio: tira o líquido do bloco.
            if (!level.isClientSide()) {
                level.setBlock(pos, state.setValue(LIQUID, Liquid.NONE), 3);
                level.playSound(null, pos, SoundEvents.BUCKET_FILL, SoundSource.BLOCKS, 1f, 1f);
                ItemStack filled = new ItemStack(inside.bucket());
                player.setItemInHand(event.getHand(), ItemUtils.createFilledResult(stack, player, filled));
            }
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.sidedSuccess(level.isClientSide()));
        }
    }

    /** O estado com o líquido dentro, se o fluido do lugar for uma fonte de um dos líquidos (senão, o mesmo estado). */
    public static BlockState withLiquidAt(BlockState state, FluidState fluid) {
        if (!fluid.isSource() || !canHold(state)) return state;
        for (Liquid liquid : Liquid.values()) {
            if (liquid != Liquid.NONE && liquid.fluid() != Fluids.EMPTY && fluid.getType() == liquid.fluid()) {
                return state.setValue(LIQUID, liquid);
            }
        }
        return state;
    }
}
