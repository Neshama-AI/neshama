#include "SoulEngine/Emotion/EmotionTypes.h"

float FSoulEmotionState::GetValue(ESoulEmotionType Type) const
{
	switch (Type)
	{
	case ESoulEmotionType::Joy: return Joy;
	case ESoulEmotionType::Sadness: return Sadness;
	case ESoulEmotionType::Anger: return Anger;
	case ESoulEmotionType::Fear: return Fear;
	case ESoulEmotionType::Surprise: return Surprise;
	case ESoulEmotionType::Disgust: return Disgust;
	case ESoulEmotionType::Trust: return Trust;
	case ESoulEmotionType::Anticipation: return Anticipation;
	default: return 0.0f;
	}
}

void FSoulEmotionState::SetValue(ESoulEmotionType Type, float Value)
{
	Value = FMath::Clamp(Value, 0.0f, 1.0f);
	switch (Type)
	{
	case ESoulEmotionType::Joy: Joy = Value; break;
	case ESoulEmotionType::Sadness: Sadness = Value; break;
	case ESoulEmotionType::Anger: Anger = Value; break;
	case ESoulEmotionType::Fear: Fear = Value; break;
	case ESoulEmotionType::Surprise: Surprise = Value; break;
	case ESoulEmotionType::Disgust: Disgust = Value; break;
	case ESoulEmotionType::Trust: Trust = Value; break;
	case ESoulEmotionType::Anticipation: Anticipation = Value; break;
	default: break;
	}
}

void FSoulEmotionState::AdjustValue(ESoulEmotionType Type, float Delta)
{
	SetValue(Type, GetValue(Type) + Delta);
}

void FSoulEmotionState::GetDominant(ESoulEmotionType& OutDominantType, float& OutDominantValue) const
{
	float MaxVal = -1.0f;
	ESoulEmotionType Dom = ESoulEmotionType::Neutral;

	auto Check = [&MaxVal, &Dom](ESoulEmotionType Type, float Val)
	{
		if (Val > MaxVal)
		{
			MaxVal = Val;
			Dom = Type;
		}
	};

	Check(ESoulEmotionType::Joy, Joy);
	Check(ESoulEmotionType::Sadness, Sadness);
	Check(ESoulEmotionType::Anger, Anger);
	Check(ESoulEmotionType::Fear, Fear);
	Check(ESoulEmotionType::Surprise, Surprise);
	Check(ESoulEmotionType::Disgust, Disgust);
	Check(ESoulEmotionType::Trust, Trust);
	Check(ESoulEmotionType::Anticipation, Anticipation);

	OutDominantType = Dom;
	OutDominantValue = MaxVal < 0.0f ? 0.0f : MaxVal;
}

void FSoulEmotionState::Clear()
{
	Joy = Sadness = Anger = Fear = Surprise = Disgust = Trust = Anticipation = 0.0f;
}
