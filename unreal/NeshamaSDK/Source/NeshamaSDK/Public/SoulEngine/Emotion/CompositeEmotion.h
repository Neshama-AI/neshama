#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Emotion/EmotionTypes.h"
#include "CompositeEmotion.generated.h"

/**
 * A single component of a composite emotion recipe.
 */
USTRUCT(BlueprintType)
struct FCompositeRecipeComponent
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EEmotionType Emotion = EEmotionType::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Weight = 0.0f;

	FCompositeRecipeComponent() = default;
	FCompositeRecipeComponent(EEmotionType InEmotion, float InWeight)
		: Emotion(InEmotion), Weight(InWeight) {}
};

/**
 * A composite emotion recipe (e.g., "love" = trust + joy).
 */
USTRUCT(BlueprintType)
struct FCompositeRecipe
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FCompositeRecipeComponent> Components;
};

/**
 * All predefined composite emotion recipes.
 * Matches Python/C# COMPOSITE_RECIPES exactly (15 recipes).
 */
class NESHAMASDK_API FCompositeRecipes
{
public:
	/** Get all 15 predefined composite recipes. */
	static const TArray<FCompositeRecipe>& GetAll();
};
