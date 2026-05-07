#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Emotion/EmotionTypes.h"

// Forward declarations
class UOCEANPersonality;

/**
 * Game event processor. Maps game events to emotion deltas.
 * Ported from Python/C# GameEventProcessor.
 *
 * Handles:
 * - Event → emotion delta mapping (15 event types)
 * - Intensity scaling
 * - OCEAN personality modifiers
 * - Grudge factor (hostile relationships reduce positive effects)
 */
class NESHAMASDK_API FGameEventProcessor
{
public:
	/**
	 * Process a game event and return emotion deltas.
	 * Ported from C# GameEventProcessor.ProcessEvent().
	 */
	static TArray<FEmotionDelta> ProcessEvent(
		EGameEventType EventType,
		float Intensity,
		const UOCEANPersonality* Personality,
		const FString& SourceId = TEXT(""),
		const FString& RelationshipType = TEXT(""));

	/**
	 * Process a chain of events, accumulating deltas.
	 * Ported from C# GameEventProcessor.ProcessChain().
	 */
	static FEventChainResult ProcessChain(
		const TArray<FGameEvent>& Events,
		const FString& ChainId,
		const UOCEANPersonality* Personality);
};
