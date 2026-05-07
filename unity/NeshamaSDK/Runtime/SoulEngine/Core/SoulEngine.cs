using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Neshama.SoulEngine.Emotion;
using Neshama.SoulEngine.Personality;
using Neshama.SoulEngine.Behavior;
using Neshama.SoulEngine.Memory;
using Neshama.SoulEngine.Social;
using Neshama.SoulEngine.Story;
using Neshama.SoulEngine.Entity;

namespace Neshama.SoulEngine.Core
{
    // ── LLM Provider Interface ───────────────────────────────────────────────────

    /// <summary>
    /// Interface for LLM providers. Dialogue still requires LLM;
    /// all other soul computation is local.
    /// </summary>
    public interface ILLMProvider
    {
        Task<string> GenerateResponse(string systemPrompt, string userMessage);
    }

    /// <summary>
    /// Mock LLM provider for testing. Returns canned responses.
    /// </summary>
    public class MockLLMProvider : ILLMProvider
    {
        public Task<string> GenerateResponse(string systemPrompt, string userMessage)
        {
            return Task.FromResult("[Mock response] I understand how you feel.");
        }
    }

    // ── Event Result ─────────────────────────────────────────────────────────────

    /// <summary>
    /// Result of processing a game event through the SoulEngine.
    /// </summary>
    public struct EventResult
    {
        public GameEventType eventType;
        public EmotionState emotionState;
        public CompositeEmotionResult compositeEmotion;
        public ResponseHint responseHint;
        public BehaviorMapper.BehaviorProfile behaviorProfile;
    }

    // ── SoulEngine ───────────────────────────────────────────────────────────────

    /// <summary>
    /// Main entry point for the Neshama Soul Engine.
    /// Manages all subsystems for a single NPC soul.
    /// 
    /// Usage:
    ///   var engine = new SoulEngine("npc_001", "Tavern Keeper");
    ///   engine.ProcessEvent(GameEventType.PlayerHelped, 0.8f, "player_001");
    ///   var profile = engine.GetBehaviorProfile();
    ///   engine.Tick(Time.deltaTime);
    /// 
    /// Design:
    /// - Pure C#, zero external dependencies (only Unity built-in API)
    /// - All computation on main thread (computation <0.1ms per frame)
    /// - <10ms total processing latency for events
    /// - Data serializable for save/load
    /// </summary>
    public class SoulEngine : IDisposable
    {
        // ── Subsystems ───────────────────────────────────────────────────────────

        private readonly EmotionEngine _emotion;
        private readonly OCEANPersonality _personality;
        private readonly PersonalityEvolver _evolver;
        private readonly BehaviorMapper _behavior;
        private readonly MemorySystem _memory;
        private readonly SocialEngine _social;
        private readonly EntityGraph _graph;
        private readonly StoryTriggerEngine _story;

        // ── Identity ─────────────────────────────────────────────────────────────

        public string NpcId { get; }
        public string NpcName { get; set; }

        // ── Config ───────────────────────────────────────────────────────────────

        private readonly SoulConfig _config;

        // ── State Tracking ───────────────────────────────────────────────────────

        private float _gameTime = 0f;
        private int _totalInteractions = 0;
        private float _lastEvolutionCheck = 0f;

        // ── Accessors ────────────────────────────────────────────────────────────

        public EmotionEngine Emotion => _emotion;
        public OCEANPersonality Personality => _personality;
        public PersonalityEvolver Evolver => _evolver;
        public BehaviorMapper Behavior => _behavior;
        public MemorySystem Memory => _memory;
        public SocialEngine Social => _social;
        public EntityGraph Graph => _graph;
        public StoryTriggerEngine Story => _story;
        public SoulConfig Config => _config;
        public float GameTime => _gameTime;
        public int TotalInteractions => _totalInteractions;

        // ── Constructors ─────────────────────────────────────────────────────────

        public SoulEngine(string npcId, string npcName = null)
            : this(npcId, npcName, new SoulConfig(), new OCEANPersonality()) { }

        public SoulEngine(string npcId, string npcName, SoulConfig config)
            : this(npcId, npcName, config, new OCEANPersonality()) { }

        public SoulEngine(string npcId, string npcName, SoulConfig config, OCEANPersonality personality)
        {
            NpcId = npcId ?? throw new ArgumentNullException(nameof(npcId));
            NpcName = npcName ?? npcId;
            _config = config ?? SoulConfig.Default;
            _personality = personality ?? new OCEANPersonality();

            _emotion = new EmotionEngine(_personality);
            _evolver = new PersonalityEvolver
            {
                maxDeltaPerStep = _config.personalityMaxDeltaPerStep,
                minInteractionsForEvolution = _config.personalityMinInteractionsForEvolution,
            };
            _behavior = new BehaviorMapper(_personality);
            _memory = new MemorySystem
            {
                maxMemoriesPerNpc = _config.maxMemoriesPerNpc,
                relationDecayRate = _config.relationDecayRate,
            };
            _social = new SocialEngine
            {
                minInteractionInterval = _config.minSocialInteractionInterval,
                maxInteractionsPerTick = _config.maxSocialInteractionsPerTick,
            };
            _graph = new EntityGraph();
            _story = new StoryTriggerEngine();
        }

        // ── Core API ─────────────────────────────────────────────────────────────

        /// <summary>
        /// Process a game event through the full pipeline:
        /// Event → Emotion deltas → Emotion update → Composite → Hint → Behavior.
        /// Returns the full result for this tick.
        /// </summary>
        public EventResult ProcessEvent(GameEventType type, float intensity, string sourceId = null)
        {
            _totalInteractions++;
            _evolver.RecordInteraction();

            // Get relationship type from memory system
            string relationshipType = null;
            if (sourceId != null)
            {
                var relation = _memory.GetRelation(sourceId);
                if (relation != null)
                    relationshipType = relation.relationType;
            }

            // Step 1: Process event → emotion deltas → apply
            var deltas = GameEventProcessor.ProcessEvent(type, intensity, _personality, sourceId, relationshipType);
            foreach (var delta in deltas)
            {
                _emotion.AdjustEmotion(delta.emotion, delta.scaledDelta);
            }

            // Step 2: Update memory
            if (sourceId != null)
            {
                var emoDict = _emotion.CurrentEmotions.ToDictionary();
                _memory.OnGameEvent(type, intensity, sourceId, sourceId, emoDict);
            }

            // Step 3: Synthesize composite
            var composite = _emotion.Synthesize();

            // Step 4: Generate hint
            var hint = _emotion.GenerateHint();

            // Step 5: Generate behavior profile
            var profile = _behavior.GenerateBehavior(_emotion.CurrentEmotions.ToDictionary());

            return new EventResult
            {
                eventType = type,
                emotionState = _emotion.CurrentEmotions,
                compositeEmotion = composite,
                responseHint = hint,
                behaviorProfile = profile,
            };
        }

        /// <summary>
        /// Get current behavior profile.
        /// </summary>
        public BehaviorMapper.BehaviorProfile GetBehaviorProfile()
        {
            return _behavior.GenerateBehavior(_emotion.CurrentEmotions.ToDictionary());
        }

        /// <summary>
        /// Get dialogue context for LLM prompt generation.
        /// </summary>
        public DialogueContext GetDialogueContext(string playerId, string playerName = null)
        {
            return _memory.GetDialogueContext(
                NpcId, playerId, playerName,
                _emotion.CurrentEmotions.ToDictionary());
        }

        /// <summary>
        /// Generate LLM dialogue prompt parts.
        /// Returns list of strings to inject into system prompt.
        /// </summary>
        public List<string> GetDialoguePromptParts(string playerId, string playerName = null, int maxMemories = 3)
        {
            var ctx = GetDialogueContext(playerId, playerName);
            return ctx?.ToPromptParts(maxMemories) ?? new List<string>();
        }

        /// <summary>
        /// Chat with the NPC using an LLM provider.
        /// This is the only async method - dialogue requires LLM.
        /// </summary>
        public async Task<string> Chat(string message, ILLMProvider llm)
        {
            if (llm == null) throw new ArgumentNullException(nameof(llm));

            // Build context
            var hint = _emotion.GenerateHint();
            var composite = _emotion.Synthesize();
            var emoDict = _emotion.CurrentEmotions.ToDictionary();

            string systemPrompt = BuildSystemPrompt(hint, composite, emoDict);
            return await llm.GenerateResponse(systemPrompt, message);
        }

        /// <summary>
        /// Tick the engine. Call every frame with Time.deltaTime.
        /// Handles: emotion decay, memory decay, social time, story checks.
        /// </summary>
        public void Tick(float deltaTime)
        {
            _gameTime += deltaTime;

            // Emotion decay
            _emotion.Tick(deltaTime);

            // Memory decay
            _memory.UpdateTime(deltaTime);
            _memory.DecayRelations(deltaTime);

            // Social engine time
            _social.Tick(deltaTime);

            // Story engine time
            _story.Tick(deltaTime);

            // Personality evolution (periodic)
            if (_gameTime - _lastEvolutionCheck >= _config.personalityEvolutionInterval)
            {
                _lastEvolutionCheck = _gameTime;
                _evolver.Evolve(_personality, _emotion.CurrentEmotions);
            }
        }

        // ── Save / Load ──────────────────────────────────────────────────────────

        /// <summary>
        /// Save current state for game save.
        /// </summary>
        public SoulState SaveState()
        {
            return SoulState.Capture(NpcId, NpcName, _emotion, _personality, _memory, _totalInteractions);
        }

        /// <summary>
        /// Load state from game save.
        /// </summary>
        public void LoadState(SoulState state)
        {
            if (state == null) return;

            // Restore emotions
            state.RestoreEmotions(_emotion);

            // Personality is restored via the state
            if (state.personality != null)
            {
                _personality.openness = state.personality.openness;
                _personality.conscientiousness = state.personality.conscientiousness;
                _personality.extraversion = state.personality.extraversion;
                _personality.agreeableness = state.personality.agreeableness;
                _personality.neuroticism = state.personality.neuroticism;
            }

            _totalInteractions = state.totalInteractions;
        }

        // ── System Prompt Builder ────────────────────────────────────────────────

        private string BuildSystemPrompt(ResponseHint hint, CompositeEmotionResult composite,
            Dictionary<string, float> emoDict)
        {
            var parts = new List<string>();

            parts.Add($"你是{NpcName}，一个游戏NPC。");
            parts.Add($"你的情绪状态：{hint.reasoning}");
            parts.Add($"主要情绪：{composite.name}({composite.intensity:F2})");
            parts.Add($"回应风格：{hint.tone}");

            if (emoDict.Count > 0)
            {
                var emoStrs = new List<string>();
                foreach (var kv in emoDict)
                {
                    if (kv.Value > 0.1f) emoStrs.Add($"{kv.Key}={kv.Value:F2}");
                }
                if (emoStrs.Count > 0)
                    parts.Add($"情绪值：{string.Join(", ", emoStrs)}");
            }

            return string.Join("\n", parts);
        }

        // ── IDisposable ──────────────────────────────────────────────────────────

        private bool _disposed;

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;

            _emotion.Clear();
            _memory.Clear();
        }
    }
}
