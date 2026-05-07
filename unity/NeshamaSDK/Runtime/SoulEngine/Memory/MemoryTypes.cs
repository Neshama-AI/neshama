using System;

namespace Neshama.SoulEngine.Memory
{
    /// <summary>
    /// Memory layer types (simplified from Python 3-layer system).
    /// L0: Raw/original memories
    /// L1: Summarized/compressed memories
    /// </summary>
    public enum MemoryLayer
    {
        L0_Raw = 0,
        L1_Summary = 1
    }

    /// <summary>
    /// Memory importance levels.
    /// </summary>
    public enum MemoryImportance
    {
        Low = 0,
        Medium = 1,
        High = 2,
        Critical = 3
    }
}
