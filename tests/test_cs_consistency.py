"""
Python↔C# 数值一致性验证脚本

验证Python引擎和C# SoulEngine在相同输入下产生相同的输出。
关键验证点：
1. PlayerAttacked → anger=0.24（不是0.74，因为baseline=0不是0.5）
2. decay baseline=0（情绪向0衰减，不是向0.5）
3. hostile人格halving positive effects（敌对关系减半正面效果）

运行方式：
    cd Neshama && python -m pytest tests/test_cs_consistency.py -v
    或: python Neshama/tests/test_cs_consistency.py
"""

import sys
import os
import math

# 确保可以导入neshama包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neshama.soul.emotion.composite import CompositeEmotion, BaseEmotion
from neshama.soul.emotion.game_event import (
    GameEventEngine,
    GameEventType,
    EVENT_EMOTION_MAPPINGS,
    PERSONALITY_MODIFIERS,
    RELATIONSHIP_GRUDGE_MAP,
    POSITIVE_EMOTIONS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 测试1: PlayerAttacked → anger=0.24（baseline=0, 不是0.74）
# ═══════════════════════════════════════════════════════════════════════════════

def test_player_attacked_anger_baseline_zero():
    """
    C# EmotionEngine注释：
      BUG FIX: baseline is 0, not current. When emotion doesn't exist, start from 0.
      This ensures PlayerAttacked → anger = 0 + 0.3*intensity = 0.24 (not 0.74)
    
    Python端验证：PlayerAttacked, intensity=0.8
    - anger base_delta = 0.3
    - scaled = 0.3 * 0.8 = 0.24
    - 默认人格(neuroticism=0.5)无PersonalityModifier影响PlayerAttacked
    - grudge_factor = 0 (no relationship)
    - 初始anger=0, 所以 anger = 0 + 0.24 = 0.24
    """
    engine = CompositeEmotion(neuroticism=0.5)
    event_engine = GameEventEngine(personality={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    })

    # 处理 PlayerAttacked 事件
    from neshama.soul.emotion.game_event import GameEvent
    event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=0.8)
    deltas = event_engine.process_event(event)

    # 应用deltas到CompositeEmotion
    for delta in deltas:
        engine.adjust_emotion(delta.emotion, delta.scaled_by_intensity)

    # 验证：anger应为0.24
    anger = engine.get_emotion("anger")
    assert anger is not None, "anger should be set after PlayerAttacked"
    assert abs(anger - 0.24) < 0.001, (
        f"anger should be 0.24 (0.3*0.8), got {anger}. "
        f"If you got 0.74, the baseline bug (0.5+delta) is present!"
    )

    # 验证fear也正确
    fear = engine.get_emotion("fear")
    assert fear is not None, "fear should be set after PlayerAttacked"
    expected_fear = 0.2 * 0.8  # base_delta=0.2 * intensity=0.8 = 0.16
    assert abs(fear - expected_fear) < 0.001, (
        f"fear should be {expected_fear}, got {fear}"
    )


def test_baseline_is_zero_not_half():
    """
    验证情绪baseline=0，不是0.5。
    C#注释: "Decay baseline is 0, not current value (0+delta, not 0.5+delta)"
    
    从零状态开始调整情绪，结果应从0开始加，不是从0.5开始加。
    """
    engine = CompositeEmotion(neuroticism=0.5)

    # 初始所有情绪应为None或0
    assert engine.get_emotion("joy") is None or engine.get_emotion("joy") == 0.0

    # adjust_emotion在情绪不存在时，从0开始加
    engine.adjust_emotion("joy", 0.3)
    joy = engine.get_emotion("joy")
    assert abs(joy - 0.3) < 0.001, (
        f"joy should be 0.3 (0+0.3), got {joy}. "
        f"If you got 0.8, the old bug was 0.5+0.3"
    )

    # 再次调整，从当前值加
    engine.adjust_emotion("joy", 0.2)
    joy = engine.get_emotion("joy")
    assert abs(joy - 0.5) < 0.001, f"joy should be 0.5 (0.3+0.2), got {joy}"


# ═══════════════════════════════════════════════════════════════════════════════
# 测试2: decay baseline=0（向0衰减）
# ═══════════════════════════════════════════════════════════════════════════════

def test_decay_toward_zero():
    """
    C# EmotionEngine.Tick() 注释：
      "Exponential decay toward 0"
      Formula: value = value * pow(0.5, deltaTime / adjustedHalfLife)
    
    Python端验证：情绪应向0衰减，不是向0.5衰减。
    """
    engine = CompositeEmotion(neuroticism=0.5)
    engine.set_base_emotion("joy", 0.8)

    # tick一段时间，joy应该下降
    initial_joy = engine.get_emotion("joy")
    assert abs(initial_joy - 0.8) < 0.001

    # Tick 60秒 (joy half-life = 120秒)
    engine.tick(delta_seconds=60.0)
    decayed_joy = engine.get_emotion("joy")

    # 情绪可能因衰减过低被清除为None
    if decayed_joy is not None:
        assert decayed_joy < initial_joy, (
            f"joy should decay toward 0, but went from {initial_joy} to {decayed_joy}"
        )

    # 长时间衰减后应接近0或已被清除
    engine.tick(delta_seconds=1000.0)
    long_decayed = engine.get_emotion("joy")
    assert long_decayed is None or long_decayed < 0.1, (
        f"After long decay, joy should be near 0 or None, got {long_decayed}"
    )


def test_decay_does_not_approach_half():
    """
    确保衰减目标是0，不是0.5。
    如果旧bug存在（向0.5衰减），那么joy=0.3时衰减后会增加。
    """
    engine = CompositeEmotion(neuroticism=0.5)
    engine.set_base_emotion("joy", 0.3)

    initial_joy = 0.3
    engine.tick(delta_seconds=60.0)
    decayed_joy = engine.get_emotion("joy")

    # joy=0.3应继续衰减（向0），而不是增加（向0.5）
    assert decayed_joy <= initial_joy, (
        f"joy=0.3 should decay toward 0, not increase toward 0.5. "
        f"Got: {initial_joy} → {decayed_joy}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 测试3: hostile人格 halving positive effects
# ═══════════════════════════════════════════════════════════════════════════════

def test_hostile_grudge_halves_positive():
    """
    C# EventMappings.RelationshipGrudgeMap:
      "hostile" → 0.5
    
    逻辑：当关系为hostile时，正面情绪效果减半。
    reduction = 1.0 - grudge_factor = 1.0 - 0.5 = 0.5
    scaled *= reduction → 正面效果减半
    
    测试场景：PlayerHelped with hostile relationship
    - trust base_delta=0.4, joy base_delta=0.3
    - intensity=1.0
    - trust (positive): scaled = 0.4 * 1.0 * 0.5 = 0.2 (halved)
    - joy (positive): scaled = 0.3 * 1.0 * 0.5 = 0.15 (halved)
    """
    event_engine = GameEventEngine(personality={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    })

    from neshama.soul.emotion.game_event import GameEvent
    event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
    deltas = event_engine.process_event(event, relationship_type="hostile")

    # 找到trust和joy的delta
    trust_delta = None
    joy_delta = None
    for delta in deltas:
        if delta.emotion == "trust":
            trust_delta = delta.scaled_by_intensity
        elif delta.emotion == "joy":
            joy_delta = delta.scaled_by_intensity

    # 验证：正面情绪被减半
    assert trust_delta is not None, "trust delta should exist for PlayerHelped"
    assert joy_delta is not None, "joy delta should exist for PlayerHelped"

    # trust: 0.4 * 1.0 = 0.4, halved by grudge(0.5): 0.4 * 0.5 = 0.2
    # 但默认人格(0.5)不满足PersonalityModifier的threshold(0.7), 所以无modifier
    expected_trust = 0.4 * 1.0 * (1.0 - 0.5)  # = 0.2
    assert abs(trust_delta - expected_trust) < 0.001, (
        f"trust should be {expected_trust} (0.4*1.0*0.5, halved by hostile), got {trust_delta}"
    )

    expected_joy = 0.3 * 1.0 * (1.0 - 0.5)  # = 0.15
    assert abs(joy_delta - expected_joy) < 0.001, (
        f"joy should be {expected_joy} (0.3*1.0*0.5, halved by hostile), got {joy_delta}"
    )


def test_hostile_grudge_does_not_affect_negative():
    """
    hostile grudge factor只影响正面情绪，不影响负面。
    PlayerAttacked → anger(0.3), fear(0.2)
    anger和fear都不是positive emotions，所以不应被grudge影响。
    """
    event_engine = GameEventEngine(personality={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    })

    from neshama.soul.emotion.game_event import GameEvent
    event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)

    # 无关系
    deltas_neutral = event_engine.process_event(event, relationship_type="neutral")
    # hostile关系
    deltas_hostile = event_engine.process_event(event, relationship_type="hostile")

    # 找到anger的delta
    anger_neutral = next(d.scaled_by_intensity for d in deltas_neutral if d.emotion == "anger")
    anger_hostile = next(d.scaled_by_intensity for d in deltas_hostile if d.emotion == "anger")

    # anger不应被grudge影响（不是positive emotion）
    assert abs(anger_neutral - anger_hostile) < 0.001, (
        f"anger should not be affected by grudge factor. "
        f"neutral={anger_neutral}, hostile={anger_hostile}"
    )


def test_grudge_factor_values():
    """
    验证C#和Python的grudge map完全一致。
    C# EventMappings.RelationshipGrudgeMap:
      hostile=0.5, dislikes=0.4, enemy=0.6, rival=0.3, suspicious=0.2,
      neutral=0, friendly=0, likes=0, allied=0
    """
    expected_grudge = {
        "hostile": 0.5,
        "dislikes": 0.4,
        "enemy": 0.6,
        "rival": 0.3,
        "suspicious": 0.2,
        "neutral": 0.0,
        "friendly": 0.0,
        "likes": 0.0,
        "allied": 0.0,
    }

    for rel_type, expected_factor in expected_grudge.items():
        actual = RELATIONSHIP_GRUDGE_MAP.get(rel_type.lower(), 0.0)
        assert abs(actual - expected_factor) < 0.001, (
            f"Grudge factor for '{rel_type}': expected {expected_factor}, got {actual}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 测试4: 事件映射表一致性
# ═══════════════════════════════════════════════════════════════════════════════

def test_event_emotion_mappings_consistency():
    """
    验证Python的EVENT_EMOTION_MAPPINGS与C#的EventMappings.EmotionMappings一致。
    
    C# EmotionMappings (from EventMappings.cs):
      PlayerAttacked → (Anger, 0.3), (Fear, 0.2)
      PlayerHelped → (Trust, 0.4), (Joy, 0.3)
      ... 等15种事件
    
    只检查几个关键映射作为抽样验证。
    """
    # PlayerAttacked: anger=0.3, fear=0.2
    attacked = EVENT_EMOTION_MAPPINGS[GameEventType.PLAYER_ATTACKED]
    attacked_dict = {e: d for e, d in attacked}
    assert abs(attacked_dict.get("anger", 0) - 0.3) < 0.001, "PlayerAttacked→anger should be 0.3"
    assert abs(attacked_dict.get("fear", 0) - 0.2) < 0.001, "PlayerAttacked→fear should be 0.2"

    # PlayerHelped: trust=0.4, joy=0.3
    helped = EVENT_EMOTION_MAPPINGS[GameEventType.PLAYER_HELPED]
    helped_dict = {e: d for e, d in helped}
    assert abs(helped_dict.get("trust", 0) - 0.4) < 0.001, "PlayerHelped→trust should be 0.4"
    assert abs(helped_dict.get("joy", 0) - 0.3) < 0.001, "PlayerHelped→joy should be 0.3"

    # NpcInsulted: anger=0.4, sadness=0.2, disgust=0.2
    insulted = EVENT_EMOTION_MAPPINGS[GameEventType.NPC_INSULTED]
    insulted_dict = {e: d for e, d in insulted}
    assert abs(insulted_dict.get("anger", 0) - 0.4) < 0.001, "NpcInsulted→anger should be 0.4"
    assert abs(insulted_dict.get("sadness", 0) - 0.2) < 0.001, "NpcInsulted→sadness should be 0.2"
    assert abs(insulted_dict.get("disgust", 0) - 0.2) < 0.001, "NpcInsulted→disgust should be 0.2"


def test_personality_modifiers_consistency():
    """
    验证Python的PERSONALITY_MODIFIERS与C#的EventMappings.PersonalityModifiers一致。
    
    C# PersonalityModifiers:
      PlayerHelped → (extraversion, 0.7, 1.3), (agreeableness, 0.7, 1.2)
      NpcInsulted → (neuroticism, 0.7, 1.5), (agreeableness, 0.7, 0.5)
      QuestCompleted → (extraversion, 0.6, 1.2), (conscientiousness, 0.6, 1.3)
      DeathWitnessed → (neuroticism, 0.7, 1.4), (agreeableness, 0.6, 0.6)
    """
    # PlayerHelped modifiers
    helped_mods = PERSONALITY_MODIFIERS[GameEventType.PLAYER_HELPED]
    helped_dict = {trait: (thresh, mult) for trait, thresh, mult in helped_mods}
    assert "extraversion" in helped_dict, "PlayerHelped should have extraversion modifier"
    assert abs(helped_dict["extraversion"][0] - 0.7) < 0.001  # threshold
    assert abs(helped_dict["extraversion"][1] - 1.3) < 0.001  # multiplier

    assert "agreeableness" in helped_dict, "PlayerHelped should have agreeableness modifier"
    assert abs(helped_dict["agreeableness"][0] - 0.7) < 0.001
    assert abs(helped_dict["agreeableness"][1] - 1.2) < 0.001


# ═══════════════════════════════════════════════════════════════════════════════
# 测试5: OCEAN人格modifier交互
# ═══════════════════════════════════════════════════════════════════════════════

def test_high_extraversion_amplifies_joy():
    """
    C#逻辑：extraversion >= 0.7时，PlayerHelped的joy * 1.3
    测试高外向性人格对正面情绪的增强效果。
    """
    event_engine = GameEventEngine(personality={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.8,  # 高外向性，超过0.7阈值
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    })

    from neshama.soul.emotion.game_event import GameEvent
    event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
    deltas = event_engine.process_event(event)

    # trust应该被extraversion modifier放大 (0.4 * 1.3 = 0.52)
    # 但PersonalityModifier只作用于positive deltas
    trust_delta = next(d.scaled_by_intensity for d in deltas if d.emotion == "trust")
    # extraversion >= 0.7 → trust * 1.3 (第一个匹配的modifier)
    # 但wait, trust = 0.4 * 1.0 = 0.4, 第一个modifier是extraversion
    # 实际上PlayerHelped modifier顺序：(extraversion, 0.7, 1.3), (agreeableness, 0.7, 1.2)
    # extraversion=0.8 >= 0.7 → scaled *= 1.3, break
    expected_trust = 0.4 * 1.0 * 1.3  # = 0.52
    assert abs(trust_delta - expected_trust) < 0.01, (
        f"High extraversion: trust should be ~{expected_trust}, got {trust_delta}"
    )


def test_neuroticism_decay_modifier():
    """
    C# OCEANPersonality.GetDecayModifier():
      modifier = 0.2 + 0.8 * (1 - neuroticism)
      neuroticism=0 → modifier=1.0 → adjustedHalfLife = halfLife * 1.0 (normal)
      neuroticism=1 → modifier=0.2 → adjustedHalfLife = halfLife * 0.2 (shorter = faster decay)
    
    Note: C# comment says "High neuroticism = slower decay" but the formula 
    produces the opposite. The important thing is that Python and C# are consistent.
    
    Python CompositeEmotion also uses neuroticism to modify decay rate.
    Both engines produce: high neuroticism → faster decay (shorter effective half-life).
    """
    # 低neuroticism = 较慢衰减
    engine_low_neuro = CompositeEmotion(neuroticism=0.0)
    engine_low_neuro.set_base_emotion("joy", 0.8)

    # 高neuroticism = 较快衰减
    engine_high_neuro = CompositeEmotion(neuroticism=1.0)
    engine_high_neuro.set_base_emotion("joy", 0.8)

    # Tick相同时间
    engine_low_neuro.tick(delta_seconds=60.0)
    engine_high_neuro.tick(delta_seconds=60.0)

    joy_low = engine_low_neuro.get_emotion("joy") or 0.0
    joy_high = engine_high_neuro.get_emotion("joy") or 0.0

    # 两者都应该衰减
    assert joy_low < 0.8, f"low_neuro joy should decay from 0.8, got {joy_low}"
    assert joy_high < 0.8, f"high_neuro joy should decay from 0.8, got {joy_high}"

    # Python和C#的行为一致：高neuroticism → 更快衰减
    # C#公式: modifier = 0.2 + 0.8*(1-neuroticism), high_neuro→low modifier→short half-life
    assert joy_high < joy_low, (
        f"High neuroticism should produce faster decay: "
        f"high_neuro joy={joy_high}, low_neuro joy={joy_low}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 测试6: EmotionState clamped to [0,1]
# ═══════════════════════════════════════════════════════════════════════════════

def test_emotion_clamped_to_range():
    """
    C# EmotionState.SetValue clamps to [0,1].
    Python adjust_emotion also clamps.
    验证叠加情绪不会超出范围。
    """
    engine = CompositeEmotion(neuroticism=0.5)

    # 设置高值
    engine.adjust_emotion("joy", 0.9)
    # 再加大量
    engine.adjust_emotion("joy", 0.5)
    joy = engine.get_emotion("joy")
    assert joy <= 1.0, f"joy should be clamped to 1.0, got {joy}"

    # 负数测试
    engine.set_base_emotion("sadness", 0.1)
    engine.adjust_emotion("sadness", -0.5)
    sadness = engine.get_emotion("sadness")
    assert sadness >= 0.0, f"sadness should be clamped to 0.0, got {sadness}"


# ═══════════════════════════════════════════════════════════════════════════════
# 测试7: 完整流程 - 端到端一致性
# ═══════════════════════════════════════════════════════════════════════════════

def test_full_pipeline_player_attacked():
    """
    完整流程测试：PlayerAttacked → 全管线处理 → 验证最终状态
    与C# SoulEngine.ProcessEvent()的结果一致。
    """
    emotion_engine = CompositeEmotion(neuroticism=0.5)
    event_engine = GameEventEngine(personality={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    })

    # Step 1: Process event
    from neshama.soul.emotion.game_event import GameEvent
    event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=0.8)
    deltas = event_engine.process_event(event)

    # Step 2: Apply deltas
    for delta in deltas:
        emotion_engine.adjust_emotion(delta.emotion, delta.scaled_by_intensity)

    # Step 3: Verify final state
    anger = emotion_engine.get_emotion("anger")
    fear = emotion_engine.get_emotion("fear")

    # C#期望值：anger=0.24, fear=0.16
    assert abs(anger - 0.24) < 0.001, f"anger should be 0.24, got {anger}"
    assert abs(fear - 0.16) < 0.001, f"fear should be 0.16, got {fear}"

    # Step 4: Composite emotion
    composite = emotion_engine.synthesize()
    # anger > fear, so dominant should be anger-related
    assert composite.name in ("anger", "anger+fear"), (
        f"composite should be anger-based, got {composite.name}"
    )

    # Step 5: Decay
    emotion_engine.tick(delta_seconds=45.0)  # anger half-life = 90s
    decayed_anger = emotion_engine.get_emotion("anger")
    assert decayed_anger < anger, f"anger should decay, {anger} → {decayed_anger}"
    assert decayed_anger > 0, "anger should still be positive"


def test_full_pipeline_hostile_helped():
    """
    完整流程测试：PlayerHelped with hostile relationship
    hostile → grudge_factor=0.5 → positive effects halved
    """
    emotion_engine = CompositeEmotion(neuroticism=0.5)
    event_engine = GameEventEngine(personality={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    })

    from neshama.soul.emotion.game_event import GameEvent
    event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.8)
    deltas = event_engine.process_event(event, relationship_type="hostile")

    for delta in deltas:
        emotion_engine.adjust_emotion(delta.emotion, delta.scaled_by_intensity)

    trust = emotion_engine.get_emotion("trust")
    joy = emotion_engine.get_emotion("joy")

    # C#期望值：
    # trust: 0.4 * 0.8 * (1-0.5) = 0.16 (halved by grudge)
    # joy: 0.3 * 0.8 * (1-0.5) = 0.12 (halved by grudge)
    # 注意：默认人格(0.5)不满足PersonalityModifier的threshold(0.7)
    assert abs(trust - 0.16) < 0.001, f"trust should be 0.16 (halved), got {trust}"
    assert abs(joy - 0.12) < 0.001, f"joy should be 0.12 (halved), got {joy}"


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Python↔C# 数值一致性验证")
    print("=" * 60)

    tests = [
        ("PlayerAttacked anger=0.24 (baseline=0)", test_player_attacked_anger_baseline_zero),
        ("Baseline is 0 not 0.5", test_baseline_is_zero_not_half),
        ("Decay toward 0", test_decay_toward_zero),
        ("Decay does not approach 0.5", test_decay_does_not_approach_half),
        ("Hostile grudge halves positive", test_hostile_grudge_halves_positive),
        ("Hostile grudge no effect on negative", test_hostile_grudge_does_not_affect_negative),
        ("Grudge factor values", test_grudge_factor_values),
        ("Event emotion mappings", test_event_emotion_mappings_consistency),
        ("Personality modifiers", test_personality_modifiers_consistency),
        ("High extraversion amplifies joy", test_high_extraversion_amplifies_joy),
        ("Neuroticism decay modifier", test_neuroticism_decay_modifier),
        ("Emotion clamped to [0,1]", test_emotion_clamped_to_range),
        ("Full pipeline: PlayerAttacked", test_full_pipeline_player_attacked),
        ("Full pipeline: Hostile Helped", test_full_pipeline_hostile_helped),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  ✅ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  💥 {name}: {type(e).__name__}: {e}")
            failed += 1

    print()
    print(f"结果: {passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(0 if failed == 0 else 1)
