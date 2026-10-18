package com.luiz.ecosystemshollows;

import net.minecraft.client.renderer.ItemBlockRenderTypes;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLLoadCompleteEvent;

/**
 * Ácido translúcido, para dar para fazer aquários dos Toxian: o Alex's Caves desenha o ácido na camada "cutout" (que
 * não aceita transparência); aqui ele passa para a translúcida, a mesma da água. As texturas do ácido do nosso mod
 * (tools/acid_translucent.py) são as dele, um pouco transparentes. Roda depois do Alex's Caves (no fim do carregamento).
 */
@EventBusSubscriber(modid = EcosystemsHollows.MOD_ID, value = Dist.CLIENT)
public final class AcidRender {
    private AcidRender() {
    }

    @SubscribeEvent
    public static void onLoadComplete(FMLLoadCompleteEvent event) {
        event.enqueueWork(() -> {
            for (String id : new String[]{"acid", "acid_flowing"}) {
                var fluid = BuiltInRegistries.FLUID.get(ResourceLocation.fromNamespaceAndPath("alexscaves", id));
                if (fluid != Fluids.EMPTY) ItemBlockRenderTypes.setRenderLayer(fluid, RenderType.translucent());
            }
        });
    }
}
