package com.luiz.ecosystemshollows;

import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import com.cobblemon.mod.common.api.pokemon.feature.ChoiceSpeciesFeatureProvider;
import com.cobblemon.mod.common.api.pokemon.feature.SpeciesFeatureProvider;
import com.cobblemon.mod.common.api.pokemon.feature.SpeciesFeatures;
import com.cobblemon.mod.common.api.properties.CustomPokemonProperty;
import com.cobblemon.mod.common.api.properties.CustomPokemonPropertyType;
import com.cobblemon.mod.common.pokemon.Pokemon;

import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.OnDatapackSyncEvent;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;

/**
 * As escolhas das features (cores e sabores das formas Candyan) como palavras soltas nos comandos e nos spawns:
 * "/pokespawn bewear candyan purple", "/pokegive vanillite candyan sweetberry".
 * <p>
 * O Cobblemon separa uma palavra sem "=" como chave sem valor ("purple" vira chave "purple", valor nenhum). As flags
 * ("candyan", "galarian") funcionam porque a palavra é a chave delas; já uma escolha sem chave ("needsKey": false)
 * recebe o valor, que é nenhum, e nunca a palavra: a escolha não pega e fica o sorteio. Aqui cada palavra de escolha
 * vira uma chave própria: "purple" vale a escolha "purple" em todas as features da espécie que a têm (a cor do Bewear,
 * a do Sweetish Fish, a flor do Flabébé...). As palavras saem das features carregadas e são atualizadas a cada recarga
 * dos dados; uma palavra que já é chave de outra coisa fica de fora.
 */
@EventBusSubscriber(modid = EcosystemsHollows.MOD_ID)
public final class SharedWords implements CustomPokemonPropertyType<SharedWords.Choice> {
    private final String word;

    private SharedWords(String word) {
        this.word = word;
    }

    @SubscribeEvent
    public static void onServerStart(ServerAboutToStartEvent event) {
        refresh();
    }

    @SubscribeEvent
    public static void onDataReload(OnDatapackSyncEvent event) {
        refresh();
    }

    /** Registra uma chave para cada escolha de feature que pode vir sem chave e ainda não tem uma. */
    public static synchronized void refresh() {
        List<CustomPokemonPropertyType<?>> properties = CustomPokemonProperty.Companion.getProperties();
        Set<String> taken = new HashSet<>();
        for (CustomPokemonPropertyType<?> type : properties) {
            for (String key : type.getKeys()) taken.add(key.toLowerCase(Locale.ROOT));
        }
        for (SpeciesFeatureProvider<?> provider : SpeciesFeatures.getFeatures()) {
            if (!(provider instanceof ChoiceSpeciesFeatureProvider choice) || choice.getNeedsKey()) continue;
            for (String value : choice.getChoices()) {
                String word = value.toLowerCase(Locale.ROOT);
                if (taken.add(word)) properties.add(new SharedWords(word));
            }
        }
    }

    @Override
    public Iterable<String> getKeys() {
        return List.of(word);
    }

    @Override
    public boolean getNeedsKey() {
        return true;
    }

    @Override
    public Choice fromString(String value) {
        // Só a palavra solta ("purple"); com valor ("purple=x") não é uma escolha.
        return value == null || value.isEmpty() ? new Choice(word) : null;
    }

    @Override
    public Collection<String> examples() {
        return List.of();
    }

    /** A escolha, em toda feature da espécie que a tem. */
    public record Choice(String word) implements CustomPokemonProperty {
        @Override
        public String asString() {
            return word;
        }

        @Override
        public void apply(Pokemon pokemon) {
            for (SpeciesFeatureProvider<?> provider : SpeciesFeatures.getFeaturesFor(pokemon.getSpecies())) {
                if (provider instanceof ChoiceSpeciesFeatureProvider choice && choice.getChoices().contains(word)) {
                    choice.fromString(word).apply(pokemon);
                }
            }
        }

        @Override
        public boolean matches(Pokemon pokemon) {
            for (SpeciesFeatureProvider<?> provider : SpeciesFeatures.getFeaturesFor(pokemon.getSpecies())) {
                if (provider instanceof ChoiceSpeciesFeatureProvider choice && choice.getChoices().contains(word)
                        && choice.fromString(word).matches(pokemon)) {
                    return true;
                }
            }
            return false;
        }
    }
}
