using System.Collections.Generic;

namespace Neshama.SoulEngine.Emotion
{
    /// <summary>
    /// Predefined composite emotion recipes.
    /// Ported from Python COMPOSITE_RECIPES.
    /// </summary>
    public struct CompositeRecipeComponent
    {
        public EmotionType emotion;
        public float weight;

        public CompositeRecipeComponent(EmotionType e, float w)
        {
            emotion = e;
            weight = w;
        }
    }

    public struct CompositeRecipe
    {
        public string name;
        public CompositeRecipeComponent[] components;
    }

    /// <summary>
    /// All predefined composite emotion recipes.
    /// Matches Python COMPOSITE_RECIPES exactly.
    /// </summary>
    public static class CompositeRecipes
    {
        public static readonly CompositeRecipe[] All = new CompositeRecipe[]
        {
            new CompositeRecipe { name = "delight", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Joy, 0.6f),
                new CompositeRecipeComponent(EmotionType.Surprise, 0.4f),
            }},
            new CompositeRecipe { name = "resentment", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Sadness, 0.5f),
                new CompositeRecipeComponent(EmotionType.Anger, 0.5f),
            }},
            new CompositeRecipe { name = "aversion", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Fear, 0.5f),
                new CompositeRecipeComponent(EmotionType.Disgust, 0.5f),
            }},
            new CompositeRecipe { name = "optimism", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Joy, 0.5f),
                new CompositeRecipeComponent(EmotionType.Anticipation, 0.5f),
            }},
            new CompositeRecipe { name = "love", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Trust, 0.5f),
                new CompositeRecipeComponent(EmotionType.Joy, 0.5f),
            }},
            new CompositeRecipe { name = "shock", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Fear, 0.5f),
                new CompositeRecipeComponent(EmotionType.Surprise, 0.5f),
            }},
            new CompositeRecipe { name = "regret", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Sadness, 0.6f),
                new CompositeRecipeComponent(EmotionType.Disgust, 0.4f),
            }},
            new CompositeRecipe { name = "contempt", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Anger, 0.6f),
                new CompositeRecipeComponent(EmotionType.Disgust, 0.4f),
            }},
            new CompositeRecipe { name = "gratitude", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Joy, 0.4f),
                new CompositeRecipeComponent(EmotionType.Trust, 0.6f),
            }},
            new CompositeRecipe { name = "guilt", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Sadness, 0.5f),
                new CompositeRecipeComponent(EmotionType.Fear, 0.5f),
            }},
            new CompositeRecipe { name = "envy", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Anger, 0.4f),
                new CompositeRecipeComponent(EmotionType.Desire, 0.6f),
            }},
            new CompositeRecipe { name = "pride", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Joy, 0.5f),
                new CompositeRecipeComponent(EmotionType.Anger, 0.5f),
            }},
            new CompositeRecipe { name = "anxiety", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Fear, 0.6f),
                new CompositeRecipeComponent(EmotionType.Anticipation, 0.4f),
            }},
            new CompositeRecipe { name = "nostalgia", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Joy, 0.4f),
                new CompositeRecipeComponent(EmotionType.Sadness, 0.6f),
            }},
            new CompositeRecipe { name = "relief", components = new CompositeRecipeComponent[]
            {
                new CompositeRecipeComponent(EmotionType.Joy, 0.5f),
                new CompositeRecipeComponent(EmotionType.Fear, 0.5f),
            }},
        };
    }
}
