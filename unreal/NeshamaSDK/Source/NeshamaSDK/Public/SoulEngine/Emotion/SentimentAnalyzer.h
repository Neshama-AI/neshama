#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Emotion/EmotionTypes.h"

/**
 * Generates response hints from emotion state.
 * Ported from Python/C# HintGenerator/SentimentAnalyzer.
 */
class NESHAMASDK_API FHintGenerator
{
public:
	/**
	 * Generate a response hint from emotion state and composite emotion.
	 */
	static FResponseHint Generate(
		const TMap<FString, float>& Emotions,
		const FCompositeEmotionResult& Composite);
};
