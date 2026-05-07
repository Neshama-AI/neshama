#pragma once

#include "CoreMinimal.h"

namespace NeshamaSoul
{
	/**
	 * Math utility functions for the soul engine.
	 * Zero external dependencies, UE5-compatible.
	 */
	namespace SoulMathUtils
	{
		/** Clamp value to [0, 1] range. */
		inline float Clamp01(float Value)
		{
			return FMath::Clamp(Value, 0.0f, 1.0f);
		}

		/** Clamp value to [Min, Max] range. */
		inline float Clamp(float Value, float Min, float Max)
		{
			return FMath::Clamp(Value, Min, Max);
		}

		/**
		 * Exponential decay formula: Value * FMath::Pow(0.5f, DeltaTime / HalfLife)
		 * Matches Python: 0.5 ** (delta_seconds / adjusted_halflife)
		 */
		inline float ExponentialDecay(float CurrentValue, float DeltaTime, float HalfLife)
		{
			if (HalfLife <= 0.0f || DeltaTime <= 0.0f) return CurrentValue;
			float DecayFactor = FMath::Pow(0.5f, DeltaTime / HalfLife);
			return CurrentValue * DecayFactor;
		}

		/** Round to N decimal places. */
		inline float Round(float Value, int32 Digits = 4)
		{
			float Multiplier = FMath::Pow(10.0f, static_cast<float>(Digits));
			return FMath::RoundToFloat(Value * Multiplier) / Multiplier;
		}

		/** Linear interpolation. */
		inline float Lerp(float A, float B, float T)
		{
			return A + (B - A) * Clamp01(T);
		}

		/** Max of two floats. */
		inline float Max(float A, float B) { return FMath::Max(A, B); }

		/** Min of two floats. */
		inline float Min(float A, float B) { return FMath::Min(A, B); }
	}
}
