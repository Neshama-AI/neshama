#include "SoulEngine/Emotion/CompositeEmotion.h"

const TArray<FCompositeRecipe>& FCompositeRecipes::GetAll()
{
	static TArray<FCompositeRecipe> Recipes;
	if (Recipes.Num() > 0) return Recipes;

	// delight = Joy(0.6) + Surprise(0.4)
	{
		FCompositeRecipe R;
		R.Name = TEXT("delight");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.6f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Surprise, 0.4f));
		Recipes.Add(R);
	}
	// resentment = Sadness(0.5) + Anger(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("resentment");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Sadness, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anger, 0.5f));
		Recipes.Add(R);
	}
	// aversion = Fear(0.5) + Disgust(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("aversion");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Fear, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Disgust, 0.5f));
		Recipes.Add(R);
	}
	// optimism = Joy(0.5) + Anticipation(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("optimism");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anticipation, 0.5f));
		Recipes.Add(R);
	}
	// love = Trust(0.5) + Joy(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("love");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Trust, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.5f));
		Recipes.Add(R);
	}
	// shock = Fear(0.5) + Surprise(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("shock");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Fear, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Surprise, 0.5f));
		Recipes.Add(R);
	}
	// regret = Sadness(0.6) + Disgust(0.4)
	{
		FCompositeRecipe R;
		R.Name = TEXT("regret");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Sadness, 0.6f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Disgust, 0.4f));
		Recipes.Add(R);
	}
	// contempt = Anger(0.6) + Disgust(0.4)
	{
		FCompositeRecipe R;
		R.Name = TEXT("contempt");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anger, 0.6f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Disgust, 0.4f));
		Recipes.Add(R);
	}
	// gratitude = Joy(0.4) + Trust(0.6)
	{
		FCompositeRecipe R;
		R.Name = TEXT("gratitude");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.4f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Trust, 0.6f));
		Recipes.Add(R);
	}
	// guilt = Sadness(0.5) + Fear(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("guilt");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Sadness, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Fear, 0.5f));
		Recipes.Add(R);
	}
	// envy = Anger(0.4) + Desire(0.6) — Desire not in base emotions; using Anticipation as proxy
	{
		FCompositeRecipe R;
		R.Name = TEXT("envy");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anger, 0.4f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anticipation, 0.6f));
		Recipes.Add(R);
	}
	// pride = Joy(0.5) + Anger(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("pride");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anger, 0.5f));
		Recipes.Add(R);
	}
	// anxiety = Fear(0.6) + Anticipation(0.4)
	{
		FCompositeRecipe R;
		R.Name = TEXT("anxiety");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Fear, 0.6f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Anticipation, 0.4f));
		Recipes.Add(R);
	}
	// nostalgia = Joy(0.4) + Sadness(0.6)
	{
		FCompositeRecipe R;
		R.Name = TEXT("nostalgia");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.4f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Sadness, 0.6f));
		Recipes.Add(R);
	}
	// relief = Joy(0.5) + Fear(0.5)
	{
		FCompositeRecipe R;
		R.Name = TEXT("relief");
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Joy, 0.5f));
		R.Components.Add(FCompositeRecipeComponent(EEmotionType::Fear, 0.5f));
		Recipes.Add(R);
	}

	return Recipes;
}
