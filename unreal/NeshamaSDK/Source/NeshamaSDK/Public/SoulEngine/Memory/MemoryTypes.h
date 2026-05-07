#pragma once

#include "CoreMinimal.h"
#include "MemoryTypes.generated.h"

/**
 * Memory layer types (simplified from Python 3-layer system).
 */
UENUM(BlueprintType)
enum class EMemoryLayer : uint8
{
	L0_Raw UMETA(DisplayName = "Raw"),
	L1_Summary UMETA(DisplayName = "Summary")
};

/**
 * Memory importance levels.
 */
UENUM(BlueprintType)
enum class EMemoryImportance : uint8
{
	Low UMETA(DisplayName = "Low"),
	Medium UMETA(DisplayName = "Medium"),
	High UMETA(DisplayName = "High"),
	Critical UMETA(DisplayName = "Critical")
};
