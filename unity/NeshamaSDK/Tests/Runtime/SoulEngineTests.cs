using System;
using System.Collections.Generic;
using Neshama.SoulEngine.Emotion;
using Neshama.SoulEngine.Personality;
using Neshama.SoulEngine.Behavior;
using Neshama.SoulEngine.Memory;
using Neshama.SoulEngine.Social;
using Neshama.SoulEngine.Story;
using Neshama.SoulEngine.Entity;
using SoulEngineClass = Neshama.SoulEngine.Core.SoulEngine;

namespace Neshama.SoulEngine.Tests
{
    /// <summary>
    /// Runtime tests for the SoulEngine.
    /// Validates numerical correctness against Python version.
    /// 
    /// Key validations:
    /// - Attack event → anger = 0.24 (NOT 0.74, BUG FIX)
    /// - Emotion decay toward 0 (baseline=0, not current)
    /// - Hostile relationship reduces positive emotion effects by grudge factor
    /// - Memory correctly saves and queries
    /// </summary>
    public static class SoulEngineTests
    {
        private static int _passed;
        private static int _failed;
        private static List<string> _failures = new List<string>();

        public static void RunAll()
        {
            _passed = 0;
            _failed = 0;
            _failures.Clear();

            TestAttackEventAngerValue();
            TestEmotionDecayTowardZero();
            TestGrudgeFactorReducesPositiveEmotions();
            TestCompositeEmotionDelight();
            TestCompositeEmotionGratitude();
            TestOCEANDecayModifier();
            TestBehaviorProfileDialogueStyle();
            TestBehaviorProfileShopPrice();
            TestMemorySystemAddAndQuery();
            TestMemoryDialogueContext();
            TestSocialEngineInteraction();
            TestEntityGraph();
            TestStoryTriggerEmotionThreshold();
            TestStoryTriggerTimeBased();
            TestPersonalityEvolution();
            TestSaveLoadState();
            TestSoulEngineTick();

            Console.WriteLine($"=== SoulEngine Tests: {_passed} passed, {_failed} failed ===");
            if (_failures.Count > 0)
            {
                Console.WriteLine("FAILURES:");
                foreach (var f in _failures) Console.WriteLine("  " + f);
            }
        }

        // ── Helper ───────────────────────────────────────────────────────────────

        private static void Assert(bool condition, string message)
        {
            if (condition) { _passed++; }
            else { _failed++; _failures.Add(message); }
        }

        private static void AssertApprox(float actual, float expected, float tolerance, string message)
        {
            bool pass = Math.Abs(actual - expected) <= tolerance;
            if (!pass) message += $" (expected={expected:F4}, actual={actual:F4}, diff={Math.Abs(actual - expected):F6})";
            Assert(pass, message);
        }

        // ── P0: Emotion Engine Tests ─────────────────────────────────────────────

        /// <summary>
        /// BUG FIX TEST: Attack event should produce anger=0.24, NOT 0.74.
        /// Python had a bug where baseline was 0.5 instead of 0.
        /// With intensity=0.8: anger_delta = 0.3 * 0.8 = 0.24
        /// anger = 0 + 0.24 = 0.24 (correct)
        /// NOT: 0.5 + 0.24 = 0.74 (old bug)
        /// </summary>
        static void TestAttackEventAngerValue()
        {
            var engine = new EmotionEngine(new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.5f));
            engine.ProcessEvent(GameEventType.PlayerAttacked, 0.8f);

            float anger = engine.GetEmotionValue(EmotionType.Anger);
            AssertApprox(anger, 0.24f, 0.001f, "Attack event anger should be 0.24 (not 0.74)");

            float fear = engine.GetEmotionValue(EmotionType.Fear);
            AssertApprox(fear, 0.16f, 0.001f, "Attack event fear should be 0.16 (0.2*0.8)");
        }

        /// <summary>
        /// Emotion decay should move toward 0, not toward some other baseline.
        /// After tick, emotions should decrease.
        /// </summary>
        static void TestEmotionDecayTowardZero()
        {
            var engine = new EmotionEngine(new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.5f));
            engine.SetEmotion(EmotionType.Joy, 0.8f);

            // Decay for 10 seconds (half-life of joy = 120s)
            engine.Tick(10f);

            float joy = engine.GetEmotionValue(EmotionType.Joy);
            // Expected: 0.8 * pow(0.5, 10/120) = 0.8 * 0.5^(0.0833) ≈ 0.8 * 0.9439 ≈ 0.7551
            Assert(joy < 0.8f, "Emotion should decay over time");
            Assert(joy > 0.5f, "Emotion should not decay too fast");
            AssertApprox(joy, 0.7551f, 0.01f, "Emotion decay should follow exponential formula");
        }

        /// <summary>
        /// Hostile relationship reduces positive emotion effects by grudge factor.
        /// hostile grudge = 0.5, so positive emotions are reduced by factor (1-0.5) = 0.5
        /// PlayerHelped: trust base=0.4, joy base=0.3
        /// With hostile relation: trust = 0.4*0.8*0.5 = 0.16, joy = 0.3*0.8*0.5 = 0.12
        /// </summary>
        static void TestGrudgeFactorReducesPositiveEmotions()
        {
            var personality = new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.5f);
            var deltas = GameEventProcessor.ProcessEvent(
                GameEventType.PlayerHelped, 0.8f, personality,
                relationshipType: "hostile");

            float trustDelta = 0f, joyDelta = 0f;
            foreach (var d in deltas)
            {
                if (d.emotion == EmotionType.Trust) trustDelta = d.scaledDelta;
                if (d.emotion == EmotionType.Joy) joyDelta = d.scaledDelta;
            }

            // Without grudge: trust = 0.4*0.8 = 0.32, joy = 0.3*0.8 = 0.24
            // With hostile grudge (0.5): trust = 0.32*0.5 = 0.16, joy = 0.24*0.5 = 0.12
            AssertApprox(trustDelta, 0.16f, 0.01f, "Hostile grudge should halve trust delta");
            AssertApprox(joyDelta, 0.12f, 0.01f, "Hostile grudge should halve joy delta");
        }

        /// <summary>
        /// Joy + Surprise → Delight composite emotion.
        /// </summary>
        static void TestCompositeEmotionDelight()
        {
            var engine = new EmotionEngine(new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.5f));
            engine.SetEmotion(EmotionType.Joy, 0.8f);
            engine.SetEmotion(EmotionType.Surprise, 0.6f);

            var result = engine.Synthesize();
            Assert(result.name == "delight", $"Composite should be 'delight', got '{result.name}'");
            Assert(result.intensity > 0f, "Delight intensity should be > 0");
        }

        /// <summary>
        /// Joy + Trust → Gratitude composite emotion.
        /// </summary>
        static void TestCompositeEmotionGratitude()
        {
            var engine = new EmotionEngine(new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.5f));
            engine.SetEmotion(EmotionType.Joy, 0.6f);
            engine.SetEmotion(EmotionType.Trust, 0.8f);

            var result = engine.Synthesize();
            Assert(result.name == "gratitude", $"Composite should be 'gratitude', got '{result.name}'");
        }

        /// <summary>
        /// OCEAN neuroticism affects decay speed.
        /// High neuroticism = slower decay.
        /// </summary>
        static void TestOCEANDecayModifier()
        {
            var lowNeuroticism = new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.0f);
            var highNeuroticism = new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 1.0f);

            float modLow = lowNeuroticism.GetDecayModifier();
            float modHigh = highNeuroticism.GetDecayModifier();

            AssertApprox(modLow, 1.0f, 0.01f, "Low neuroticism decay modifier should be ~1.0");
            AssertApprox(modHigh, 0.2f, 0.01f, "High neuroticism decay modifier should be ~0.2");
            Assert(modHigh < modLow, "High neuroticism should decay slower");
        }

        // ── P2: Behavior Tests ───────────────────────────────────────────────────

        static void TestBehaviorProfileDialogueStyle()
        {
            var mapper = new BehaviorMapper(new OCEANPersonality());
            var emotions = new Dictionary<string, float> { { "anger", 0.7f } };

            var profile = mapper.GenerateBehavior(emotions);
            Assert(profile.dialogueStyle == DialogueStyle.Aggressive,
                "High anger should produce aggressive dialogue style");
        }

        static void TestBehaviorProfileShopPrice()
        {
            var mapper = new BehaviorMapper(new OCEANPersonality());
            var emotions = new Dictionary<string, float> { { "joy", 0.8f }, { "trust", 0.7f } };

            var profile = mapper.GenerateBehavior(emotions);
            Assert(profile.shopPriceMultiplier < 1.0f,
                "High joy+trust should give discount (multiplier < 1.0)");
        }

        // ── P3: Memory Tests ─────────────────────────────────────────────────────

        static void TestMemorySystemAddAndQuery()
        {
            var memory = new MemorySystem();
            memory.OnGameEvent(GameEventType.PlayerHelped, 1.0f, "player_001", "Hero");

            var relation = memory.GetRelation("player_001");
            Assert(relation != null, "Relation should exist after game event");
            Assert(relation.relationType == "ally", "Relation type should be 'ally' after help");

            var mems = memory.GetEntityMemories("player_001");
            Assert(mems.Count == 1, "Should have 1 memory entry");
        }

        static void TestMemoryDialogueContext()
        {
            var memory = new MemorySystem();
            memory.OnGameEvent(GameEventType.PlayerHelped, 1.0f, "player_001", "Hero");

            var ctx = memory.GetDialogueContext("npc_001", "player_001", "Hero");
            Assert(ctx != null, "Dialogue context should exist");
            Assert(ctx.playerName == "Hero", "Player name should be set");

            var parts = ctx.ToPromptParts();
            Assert(parts.Count > 0, "Should have prompt parts");
        }

        // ── P4: Social Engine Tests ──────────────────────────────────────────────

        static void TestSocialEngineInteraction()
        {
            var social = new SocialEngine();
            social.RegisterNPC("alice", new OCEANPersonality(0.5f, 0.5f, 0.7f, 0.8f, 0.3f));
            social.RegisterNPC("bob", new OCEANPersonality(0.5f, 0.5f, 0.4f, 0.5f, 0.4f));

            var evt = social.InitiateInteraction("alice", "bob");
            Assert(evt != null, "Social event should be created");
            Assert(evt.success, "Social event should succeed (first interaction)");

            var relation = social.GetRelation("alice", "bob");
            Assert(relation != null, "Relation should exist after interaction");
        }

        // ── P5: Entity Graph Tests ───────────────────────────────────────────────

        static void TestEntityGraph()
        {
            var graph = new EntityGraph();
            var alice = graph.AddEntity("Alice", EntityType.Person, description: "AI researcher");
            var paris = graph.AddEntity("Paris", EntityType.Place, description: "City");

            graph.AddRelation(alice.id, paris.id, RelationType.LocatedAt, weight: 0.9f);

            var edges = graph.GetEdgesFrom(alice.id);
            Assert(edges.Count == 1, "Alice should have 1 outgoing edge");
            Assert(edges[0].relationType == RelationType.LocatedAt, "Edge type should be LocatedAt");

            var paths = graph.FindPaths(alice.id, paris.id, maxDepth: 3);
            Assert(paths.Count >= 1, "Should find a path from Alice to Paris");
        }

        // ── P6: Story Trigger Tests ──────────────────────────────────────────────

        static void TestStoryTriggerEmotionThreshold()
        {
            var engine = new StoryTriggerEngine();
            engine.RegisterTrigger(new StoryTrigger
            {
                triggerId = "rage_lockdown",
                name = "NPC暴怒封锁",
                conditions = new List<TriggerCondition>
                {
                    new TriggerCondition
                    {
                        conditionType = TriggerConditionType.EmotionThreshold,
                        npcId = "npc_001",
                        emotion = "anger",
                        threshold = 0.8f,
                    }
                },
                effects = new List<StoryEffect>
                {
                    new StoryEffect
                    {
                        effectType = StoryEffectType.TriggerWorldEvent,
                        target = "area_lockdown",
                    }
                },
            });

            // Below threshold
            var emotions = new Dictionary<string, Dictionary<string, float>>
            {
                { "npc_001", new Dictionary<string, float> { { "anger", 0.5f } } }
            };
            var results = engine.CheckTriggers(emotions);
            Assert(results.Count == 0, "Should not trigger below threshold");

            // Above threshold
            emotions["npc_001"]["anger"] = 0.9f;
            results = engine.CheckTriggers(emotions);
            Assert(results.Count == 1, "Should trigger above threshold");
            Assert(results[0].triggerId == "rage_lockdown", "Should fire rage_lockdown trigger");
        }

        static void TestStoryTriggerTimeBased()
        {
            var engine = new StoryTriggerEngine();

            engine.RegisterTrigger(new StoryTrigger
            {
                triggerId = "sustained_fear",
                name = "持续恐惧",
                conditions = new List<TriggerCondition>
                {
                    new TriggerCondition
                    {
                        conditionType = TriggerConditionType.TimeBased,
                        npcId = "npc_001",
                        emotion = "fear",
                        threshold = 0.5f,
                        durationSeconds = 30f,
                    }
                },
                effects = new List<StoryEffect>(),
                cooldown = 999f,
            });

            // Start: fear above threshold
            var emotions = new Dictionary<string, Dictionary<string, float>>
            {
                { "npc_001", new Dictionary<string, float> { { "fear", 0.7f } } }
            };

            engine.Tick(1f);
            var results = engine.CheckTriggers(emotions);
            Assert(results.Count == 0, "Should not trigger immediately");

            // After 30 seconds
            engine.Tick(30f);
            results = engine.CheckTriggers(emotions);
            Assert(results.Count == 1, "Should trigger after sustained duration");
        }

        // ── Personality Evolution ────────────────────────────────────────────────

        static void TestPersonalityEvolution()
        {
            var personality = new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, 0.5f);
            var evolver = new PersonalityEvolver
            {
                minInteractionsForEvolution = 1, // Low threshold for test
                emotionalInfluenceStrength = 0.05f,
            };

            // Record enough interactions
            for (int i = 0; i < 10; i++) evolver.RecordInteraction();

            // High joy/trust should increase extraversion
            var emo = new EmotionState { joy = 0.9f, trust = 0.8f };
            float before = personality.extraversion;
            evolver.Evolve(personality, emo);
            Assert(personality.extraversion > before, "High joy+trust should increase extraversion");
        }

        // ── Save/Load ────────────────────────────────────────────────────────────

        static void TestSaveLoadState()
        {
            var soul = new SoulEngineClass("npc_001", "Tavern Keeper");
            soul.ProcessEvent(GameEventType.PlayerHelped, 1.0f, "player_001");

            var saved = soul.SaveState();
            Assert(saved.joy > 0f, "Joy should be > 0 after help event");
            Assert(saved.trust > 0f, "Trust should be > 0 after help event");

            // Load into new engine
            var soul2 = new SoulEngineClass("npc_001", "Tavern Keeper");
            soul2.LoadState(saved);
            AssertApprox(soul2.Emotion.GetEmotionValue(EmotionType.Joy), saved.joy, 0.001f,
                "Loaded joy should match saved");
            AssertApprox(soul2.Emotion.GetEmotionValue(EmotionType.Trust), saved.trust, 0.001f,
                "Loaded trust should match saved");
        }

        // ── Tick Test ────────────────────────────────────────────────────────────

        static void TestSoulEngineTick()
        {
            var soul = new SoulEngineClass("npc_001", "Test");
            soul.ProcessEvent(GameEventType.PlayerHelped, 1.0f, "player_001");

            float joyBefore = soul.Emotion.GetEmotionValue(EmotionType.Joy);
            soul.Tick(10f);
            float joyAfter = soul.Emotion.GetEmotionValue(EmotionType.Joy);

            Assert(joyAfter < joyBefore, "Emotion should decay after tick");
            Assert(soul.GameTime > 0f, "Game time should advance");
        }
    }
}
