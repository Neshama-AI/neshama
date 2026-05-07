using System;

namespace Neshama.SoulEngine.Utils
{
    /// <summary>
    /// Math utility functions for the soul engine.
    /// Zero external dependencies, Unity-compatible.
    /// </summary>
    public static class MathUtils
    {
        /// <summary>
        /// Clamp value to [0, 1] range.
        /// </summary>
        public static float Clamp01(float value)
        {
            if (value < 0f) return 0f;
            if (value > 1f) return 1f;
            return value;
        }

        /// <summary>
        /// Clamp value to [min, max] range.
        /// </summary>
        public static float Clamp(float value, float min, float max)
        {
            if (value < min) return min;
            if (value > max) return max;
            return value;
        }

        /// <summary>
        /// Exponential decay formula: value * pow(0.5, deltaTime / halfLife)
        /// This matches Python: 0.5 ** (delta_seconds / adjusted_halflife)
        /// </summary>
        public static float ExponentialDecay(float currentValue, float deltaTime, float halfLife)
        {
            if (halfLife <= 0f || deltaTime <= 0f) return currentValue;
            float decayFactor = Mathf.Pow(0.5f, deltaTime / halfLife);
            return currentValue * decayFactor;
        }

        /// <summary>
        /// Round to N decimal places.
        /// </summary>
        public static float Round(float value, int digits = 4)
        {
            float multiplier = Mathf.Pow(10f, digits);
            return Mathf.Round(value * multiplier) / multiplier;
        }

        /// <summary>
        /// Linear interpolation.
        /// </summary>
        public static float Lerp(float a, float b, float t)
        {
            return a + (b - a) * Clamp01(t);
        }

        /// <summary>
        /// Max of two floats.
        /// </summary>
        public static float Max(float a, float b) => a > b ? a : b;

        /// <summary>
        /// Min of two floats.
        /// </summary>
        public static float Min(float a, float b) => a < b ? a : b;
    }

    /// <summary>
    /// Minimal Mathf replacement for non-Unity environments (tests).
    /// In Unity, this is not needed as UnityEngine.Mathf exists.
    /// </summary>
    #if !UNITY_ENGINE
    public static class Mathf
    {
        public static float Pow(float x, float y) => (float)Math.Pow(x, y);
        public static float Round(float v) => (float)Math.Round(v);
        public static float Clamp01(float v) => v < 0f ? 0f : (v > 1f ? 1f : v);
    }
    #endif
}
