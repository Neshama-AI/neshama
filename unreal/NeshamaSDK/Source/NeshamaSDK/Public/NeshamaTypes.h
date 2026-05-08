// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - 类型定义头文件
// 包含所有枚举、USTRUCT结构体、数据类型定义

#pragma once

#include "CoreMinimal.h"
#include "NeshamaTypes.generated.h"

// ============================================================================
// 枚举定义
// ============================================================================

/**
 * 游戏事件类型枚举
 * 与后端 game_event.py 中的事件类型完全对齐
 * 用于描述游戏中发生的各类事件，NPC会根据事件类型调整情绪和行为
 */
UENUM(BlueprintType)
enum class EGameEventType : uint8
{
	/** 玩家进入NPC视野范围 */
	PlayerEntered		UMETA(DisplayName = "Player Entered"),
	
	/** 玩家离开NPC视野范围 */
	PlayerLeft			UMETA(DisplayName = "Player Left"),
	
	/** 玩家攻击了NPC */
	PlayerAttacked		UMETA(DisplayName = "Player Attacked"),
	
	/** NPC被治愈 */
	NPCHealed			UMETA(DisplayName = "NPC Healed"),
	
	/** NPC受到伤害 */
	NPCDamaged			UMETA(DisplayName = "NPC Damaged"),
	
	/** NPC被赞美 */
	NPCComplimented		UMETA(DisplayName = "NPC Complimented"),
	
	/** NPC被侮辱 */
	NPCInsulted			UMETA(DisplayName = "NPC Insulted"),
	
	/** NPC收到礼物 */
	GiftGiven			UMETA(DisplayName = "Gift Given"),
	
	/** 玩家帮助了NPC */
	NPCHelped			UMETA(DisplayName = "NPC Helped"),
	
	/** 玩家与NPC交易 */
	TradeCompleted		UMETA(DisplayName = "Trade Completed"),
	
	/** NPC目睹战斗开始 */
	CombatStarted		UMETA(DisplayName = "Combat Started"),
	
	/** NPC目睹战斗结束 */
	CombatEnded			UMETA(DisplayName = "Combat Ended"),
	
	/** 玩家完成了NPC的任务 */
	QuestCompleted		UMETA(DisplayName = "Quest Completed"),
	
	/** 玩家接受了NPC的任务 */
	QuestAccepted		UMETA(DisplayName = "Quest Accepted"),
	
	/** 玩家任务失败 */
	QuestFailed			UMETA(DisplayName = "Quest Failed")
};

/**
 * 九种基础情绪类型枚举
 * 对应后端的九种基础情绪
 */
UENUM(BlueprintType)
enum class EEmotionType : uint8
{
	/** 喜悦 - 开心、愉快的情绪 */
	Joy			UMETA(DisplayName = "Joy"),
	
	/** 悲伤 - 难过、沮丧的情绪 */
	Sadness		UMETA(DisplayName = "Sadness"),
	
	/** 愤怒 - 生气、不满的情绪 */
	Anger		UMETA(DisplayName = "Anger"),
	
	/** 恐惧 - 害怕、担心的情绪 */
	Fear		UMETA(DisplayName = "Fear"),
	
	/** 惊讶 - 意外、震惊的情绪 */
	Surprise	UMETA(DisplayName = "Surprise"),
	
	/** 厌恶 - 反感、讨厌的情绪 */
	Disgust		UMETA(DisplayName = "Disgust"),
	
	/** 信任 - 相信、依赖的情绪 */
	Trust		UMETA(DisplayName = "Trust"),
	
	/** 期待 - 希望、盼望的情绪 */
	Anticipation UMETA(DisplayName = "Anticipation"),
	
	/** 羞愧 - 尴尬、自责的情绪 */
	Shame		UMETA(DisplayName = "Shame"),
	
	/** 中性 - 无明显情绪 */
	Neutral		UMETA(DisplayName = "Neutral", Hidden)
};

/**
 * 行为修改类型枚举
 * 用于描述NPC行为的变化
 */
UENUM(BlueprintType)
enum class EBehaviorType : uint8
{
	/** 对话风格改变（如变得冷淡、热情等） */
	DialogueStyleChange		UMETA(DisplayName = "Dialogue Style Change"),
	
	/** 任务可用性改变（如锁定/解锁任务） */
	QuestAvailabilityChange UMETA(DisplayName = "Quest Availability Change"),
	
	/** 商店价格调整 */
	ShopPriceModifier		UMETA(DisplayName = "Shop Price Modifier"),
	
	/** 移动速度改变 */
	MovementSpeedChange		UMETA(DisplayName = "Movement Speed Change"),
	
	/** AI行为模式改变 */
	AIBehaviorChange		UMETA(DisplayName = "AI Behavior Change")
};

/**
 * 连接状态枚举
 */
UENUM(BlueprintType)
enum class ENeshamaConnectionState : uint8
{
	/** 未连接 */
	Disconnected	UMETA(DisplayName = "Disconnected"),
	
	/** 正在连接 */
	Connecting		UMETA(DisplayName = "Connecting"),
	
	/** 已连接 */
	Connected		UMETA(DisplayName = "Connected"),
	
	/** 连接错误 */
	Error			UMETA(DisplayName = "Error")
};

// ============================================================================
// 结构体定义 (USTRUCT)
// ============================================================================

/**
 * 情绪状态结构体
 * 包含九种基础情绪的强度值、主导情绪和复合情绪
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FEmotionState : public FTableRowBase
{
	GENERATED_BODY()

	/** 九种基础情绪的强度值，范围0-1 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Emotion")
	TMap<FString, float> Emotions;

	/** 主导情绪类型（如"anger"、"joy"等） */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Emotion")
	FString Dominant;

	/** 复合情绪描述（如"resentment"、"satisfaction"等） */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Emotion")
	FString Composite;

	/** 默认构造函数 */
	FEmotionState()
		: Dominant(TEXT("joy"))
		, Composite(TEXT("neutral"))
	{
		// 初始化所有情绪为0
		Emotions.Add(TEXT("joy"), 0.0f);
		Emotions.Add(TEXT("sadness"), 0.0f);
		Emotions.Add(TEXT("anger"), 0.0f);
		Emotions.Add(TEXT("fear"), 0.0f);
		Emotions.Add(TEXT("surprise"), 0.0f);
		Emotions.Add(TEXT("disgust"), 0.0f);
		Emotions.Add(TEXT("trust"), 0.0f);
		Emotions.Add(TEXT("anticipation"), 0.0f);
		Emotions.Add(TEXT("shame"), 0.0f);
	}

	/**
	 * 获取指定情绪的强度值
	 * @param EmotionType 情绪类型名称
	 * @return 情绪强度值，0-1范围
	 */
	float GetEmotionValue(const FString& EmotionType) const
	{
		if (const float* Value = Emotions.Find(EmotionType))
		{
			return *Value;
		}
		return 0.0f;
	}

	/** 获取喜悦情绪强度 */
	float GetJoy() const { return GetEmotionValue(TEXT("joy")); }
	
	/** 获取悲伤情绪强度 */
	float GetSadness() const { return GetEmotionValue(TEXT("sadness")); }
	
	/** 获取愤怒情绪强度 */
	float GetAnger() const { return GetEmotionValue(TEXT("anger")); }
	
	/** 获取恐惧情绪强度 */
	float GetFear() const { return GetEmotionValue(TEXT("fear")); }
	
	/** 获取惊讶情绪强度 */
	float GetSurprise() const { return GetEmotionValue(TEXT("surprise")); }
	
	/** 获取厌恶情绪强度 */
	float GetDisgust() const { return GetEmotionValue(TEXT("disgust")); }
	
	/** 获取信任情绪强度 */
	float GetTrust() const { return GetEmotionValue(TEXT("trust")); }
	
	/** 获取期待情绪强度 */
	float GetAnticipation() const { return GetEmotionValue(TEXT("anticipation")); }
	
	/** 获取羞愧情绪强度 */
	float GetShame() const { return GetEmotionValue(TEXT("shame")); }

	/**
	 * 获取主导情绪对应的EEmotionType枚举
	 */
	EEmotionType GetDominantEmotionType() const
	{
		if (Dominant.IsEmpty()) return EEmotionType::Joy;
		
		static const TMap<FString, EEmotionType> EmotionMap = {
			{TEXT("joy"), EEmotionType::Joy},
			{TEXT("sadness"), EEmotionType::Sadness},
			{TEXT("anger"), EEmotionType::Anger},
			{TEXT("fear"), EEmotionType::Fear},
			{TEXT("surprise"), EEmotionType::Surprise},
			{TEXT("disgust"), EEmotionType::Disgust},
			{TEXT("trust"), EEmotionType::Trust},
			{TEXT("anticipation"), EEmotionType::Anticipation},
			{TEXT("shame"), EEmotionType::Shame}
		};

		if (const EEmotionType* Type = EmotionMap.Find(Dominant))
		{
			return *Type;
		}
		return EEmotionType::Joy;
	}

	/**
	 * 判断当前情绪是否积极（喜悦或信任为主导）
	 */
	bool IsPositive() const
	{
		return Dominant == TEXT("joy") || Dominant == TEXT("trust");
	}

	/**
	 * 判断当前情绪是否消极（愤怒、悲伤、恐惧为主导）
	 */
	bool IsNegative() const
	{
		return Dominant == TEXT("anger") || Dominant == TEXT("sadness") || Dominant == TEXT("fear");
	}
};

/**
 * 游戏事件结构体
 * 描述游戏中发生的单个事件
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FGameEvent : public FTableRowBase
{
	GENERATED_BODY()

	/** 事件类型 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Event")
	FString EventType;

	/** 事件强度 (0-1) */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Event", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Intensity;

	/** 事件上下文数据 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Event")
	TMap<FString, FString> Context;

	/** 事件时间戳 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Event")
	int64 Timestamp;

	/** 默认构造函数 */
	FGameEvent()
		: EventType(TEXT("player_entered"))
		, Intensity(1.0f)
		, Timestamp(0)
	{
	}

	/**
	 * 创建游戏事件
	 * @param InEventType 事件类型枚举
	 * @param InIntensity 事件强度
	 * @param InContext 上下文数据
	 */
	FGameEvent(EGameEventType InEventType, float InIntensity = 1.0f)
		: Intensity(InIntensity)
		, Timestamp(FDateTime::Now().ToUnixTimestamp())
	{
		EventType = StaticEnum<EGameEventType>()->GetNameStringByValue(static_cast<uint64>(InEventType));
		// 移除前缀 "EGameEventType::"
		EventType = EventType.Replace(TEXT("EGameEventType::"), TEXT(""));
		// 转换为小写
		EventType = EventType.ToLower();
	}

	/**
	 * 创建带上下文的事件
	 */
	FGameEvent(EGameEventType InEventType, float InIntensity, const TMap<FString, FString>& InContext)
		: FGameEvent(InEventType, InIntensity)
	{
		Context = InContext;
	}
};

/**
 * 行为建议结构体
 * 描述NPC应该采取的行为修改
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FBehaviorHint : public FTableRowBase
{
	GENERATED_BODY()

	/** 行为类型 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Behavior")
	FString Type;

	/** 行为值 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Behavior")
	FString Value;

	/** 行为强度/优先级 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Behavior", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Strength;

	/** 默认构造函数 */
	FBehaviorHint()
		: Type(TEXT("dialogue_style_change"))
		, Value(TEXT("neutral"))
		, Strength(0.5f)
	{
	}

	/** 判断是否为对话风格改变 */
	bool IsDialogueStyleChange() const
	{
		return Type == TEXT("dialogue_style_change");
	}

	/** 获取对话风格 */
	FString GetDialogueStyle() const
	{
		return IsDialogueStyleChange() ? Value : TEXT("");
	}

	/** 判断是否为任务可用性改变 */
	bool IsQuestAvailabilityChange() const
	{
		return Type == TEXT("quest_availability_change");
	}

	/** 获取任务是否被锁定 */
	bool IsQuestLocked() const
	{
		return IsQuestAvailabilityChange() && Value == TEXT("locked");
	}

	/** 获取任务是否被解锁 */
	bool IsQuestUnlocked() const
	{
		return IsQuestAvailabilityChange() && Value == TEXT("unlocked");
	}

	/** 获取行为类型枚举 */
	EBehaviorType GetBehaviorType() const
	{
		if (Type == TEXT("dialogue_style_change")) return EBehaviorType::DialogueStyleChange;
		if (Type == TEXT("quest_availability_change")) return EBehaviorType::QuestAvailabilityChange;
		if (Type == TEXT("shop_price_modifier")) return EBehaviorType::ShopPriceModifier;
		if (Type == TEXT("movement_speed_change")) return EBehaviorType::MovementSpeedChange;
		if (Type == TEXT("ai_behavior_change")) return EBehaviorType::AIBehaviorChange;
		return EBehaviorType::DialogueStyleChange;
	}
};

/**
 * 对话消息结构体
 * 用于描述玩家发送的消息和NPC的回复
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FChatMessage : public FTableRowBase
{
	GENERATED_BODY()

	/** 消息内容 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	FString Message;

	/** 发送者ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	FString SenderId;

	/** 接收者ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	FString ReceiverId;

	/** 消息发送时间戳 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	int64 Timestamp;

	/** 消息类型（player/npc/system） */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	FString MessageType;

	/** 默认构造函数 */
	FChatMessage()
		: Timestamp(0)
		, MessageType(TEXT("player"))
	{
	}
};

/**
 * NPC档案结构体
 * 描述NPC的基本信息和状态
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FNPCProfile : public FTableRowBase
{
	GENERATED_BODY()

	/** NPC唯一标识符 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	FString NpcId;

	/** NPC名称 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	FString Name;

	/** NPC预设模板 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	FString Preset;

	/** NPC描述 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	FString Description;

	/** 性格特征 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	TArray<FString> PersonalityTraits;

	/** 创建时间 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	int64 CreatedAt;

	/** 最后活动时间 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|NPC")
	int64 LastActiveAt;

	/** 默认构造函数 */
	FNPCProfile()
		: CreatedAt(0)
		, LastActiveAt(0)
	{
	}
};

/**
 * 关系节点结构体
 * 用于关系图谱中的单个节点
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FRelationNode : public FTableRowBase
{
	GENERATED_BODY()

	/** 实体ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation")
	FString EntityId;

	/** 实体名称 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation")
	FString EntityName;

	/** 实体类型 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation")
	FString EntityType;

	/** 关系紧密度 (0-1) */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Affinity;

	/** 默认构造函数 */
	FRelationNode()
		: EntityType(TEXT("player"))
		, Affinity(0.0f)
	{
	}
};

/**
 * 关系图谱结构体
 * 描述NPC与所有相关实体的关系网络
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FRelationGraph : public FTableRowBase
{
	GENERATED_BODY()

	/** NPC ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation")
	FString NpcId;

	/** 关系节点列表 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation")
	TArray<FRelationNode> Relations;

	/** 最后更新时间 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Relation")
	int64 UpdatedAt;

	/** 默认构造函数 */
	FRelationGraph()
		: UpdatedAt(0)
	{
	}

	/**
	 * 获取与指定实体的关系紧密度
	 */
	float GetAffinity(const FString& EntityId) const
	{
		for (const FRelationNode& Node : Relations)
		{
			if (Node.EntityId == EntityId)
			{
				return Node.Affinity;
			}
		}
		return 0.0f;
	}
};

/**
 * 记忆条目结构体
 * 描述NPC的单个记忆
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FMemoryEntry : public FTableRowBase
{
	GENERATED_BODY()

	/** 记忆ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString MemoryId;

	/** 记忆内容 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString Content;

	/** 相关实体 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString RelatedEntity;

	/** 记忆类型 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString MemoryType;

	/** 情感权重 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory", meta = (ClampMin = "-1.0", ClampMax = "1.0"))
	float EmotionalWeight;

	/** 创建时间 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	int64 CreatedAt;

	/** 重要度 (0-1) */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Importance;

	/** 默认构造函数 */
	FMemoryEntry()
		: EmotionalWeight(0.0f)
		, CreatedAt(0)
		, Importance(0.5f)
	{
	}
};

// ============================================================================
// 响应结构体定义
// ============================================================================

/**
 * 创建NPC响应
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FCreateNPCResponse : public FTableRowBase
{
	GENERATED_BODY()

	/** 创建的NPC ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString NpcId;

	/** NPC档案 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FNPCProfile Profile;

	/** 是否成功 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	bool Success;

	/** 错误信息 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString Error;

	/** 默认构造函数 */
	FCreateNPCResponse()
		: Success(false)
	{
	}
};

/**
 * 事件响应
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FEventResponse : public FTableRowBase
{
	GENERATED_BODY()

	/** 事件是否被处理 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	bool Handled;

	/** 响应提示 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString Tone;

	/** 紧迫度 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString Urgency;

	/** 建议动作列表 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	TArray<FString> SuggestedActions;

	/** 更新后的情绪状态 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FEmotionState EmotionState;

	/** 行为建议列表 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	TArray<FBehaviorHint> BehaviorHints;

	/** 默认构造函数 */
	FEventResponse()
		: Handled(false)
		, Tone(TEXT("neutral"))
		, Urgency(TEXT("low"))
	{
	}
};

/**
 * 行为响应
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FBehaviorResponse : public FTableRowBase
{
	GENERATED_BODY()

	/** 行为修改列表 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	TArray<FBehaviorHint> Modifiers;

	/** 默认构造函数 */
	FBehaviorResponse()
	{
	}
};

/**
 * 对话请求
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FChatRequest : public FTableRowBase
{
	GENERATED_BODY()

	/** 消息内容 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	FString Message;

	/** 玩家ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Chat")
	FString PlayerId;

	/** 默认构造函数 */
	FChatRequest()
	{
	}

	/** 构造函数 */
	FChatRequest(const FString& InMessage, const FString& InPlayerId)
		: Message(InMessage)
		, PlayerId(InPlayerId)
	{
	}
};

/**
 * 对话响应
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FChatResponse : public FTableRowBase
{
	GENERATED_BODY()

	/** 回复内容 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString Content;

	/** 发送者ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString SenderId;

	/** 接收者ID */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FString ReceiverId;

	/** 回复后的情绪状态 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	FEmotionState EmotionAfter;

	/** 时间戳 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	int64 Timestamp;

	/** 默认构造函数 */
	FChatResponse()
		: Timestamp(0)
	{
	}
};

/**
 * 记忆响应
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FRememberRequest : public FTableRowBase
{
	GENERATED_BODY()

	/** 实体类型 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString EntityType;

	/** 实体名称 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString EntityName;

	/** 关系类型 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString Relation;

	/** 备注 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Memory")
	FString Note;

	/** 默认构造函数 */
	FRememberRequest()
	{
	}

	/** 构造函数 */
	FRememberRequest(const FString& InEntityType, const FString& InEntityName, 
		const FString& InRelation = TEXT(""), const FString& InNote = TEXT(""))
		: EntityType(InEntityType)
		, EntityName(InEntityName)
		, Relation(InRelation)
		, Note(InNote)
	{
	}
};

/**
 * 记忆列表响应
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FMemoryListResponse : public FTableRowBase
{
	GENERATED_BODY()

	/** 记忆列表 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	TArray<FMemoryEntry> Memories;

	/** 总数 */
	UPROPERTY(BlueprintReadWrite, Category = "Neshama|Response")
	int32 Total;

	/** 默认构造函数 */
	FMemoryListResponse()
		: Total(0)
	{
	}
};

// ============================================================================
// Blueprint 委托定义
// ============================================================================

/**
 * 连接状态变化委托
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnConnectionStateChanged, bool, bIsConnected);

/**
 * 情绪变化委托
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEmotionChanged, FEmotionState, NewEmotion);

/**
 * 行为变化委托
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnBehaviorChanged, FString, BehaviorType, FString, Value);

/**
 * 对话响应委托
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnChatResponse, FChatResponse, Response);

/**
 * 错误回调委托
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnError, FString, ErrorMessage);

/**
 * 日志回调委托
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLog, FString, LogMessage);
