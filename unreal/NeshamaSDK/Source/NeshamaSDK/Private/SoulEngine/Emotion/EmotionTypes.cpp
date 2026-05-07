#include "SoulEngine/Emotion/EmotionTypes.h"

float FEmotionState::GetValue(EEmotionType Type) const
{
	switch (Type)
	{
	case EEmotionType::Joy: return Joy;
	case EEmotionType::Sadness: return Sadness;
	case EEmotionType::Anger: return Anger;
	case EEmotionType::Fear: return Fear;
	case EEmotionType::Surprise: return Surprise;
	case EEmotionType::Disgust: return Disgust;
	case EEmotionType::Trust: return Trust;
	case EEmotionType::Anticipation: return Anticipation;
	default: return 0.0f;
	}
}

void FEmotionState::SetValue(EEmotionType Type, float Value)
{
	Value = FMath::Clamp(Value, 0.0f, 1.0f);
	switch (Type)
	{
	case EEmotionType::Joy: Joy = Value; break;
	case EEmotionType::Sadness: Sadness = Value; break;
	case EEmotionType::Anger: Anger = Value; break;
	case EEmotionType::Fear: Fear = Value; break;
	case EEmotionType::Surprise: Surprise = Value; break;
	case EEmotionType::Disgust: Disgust = Value; break;
	case EEmotionType::Trust: Trust = Value; break;
	case EEmotionType::Anticipation: Anticipation = Value; break;
	default: break;
	}
}

void FEmotionState::AdjustValue(EEmotionType Type, float Delta)
{
	SetValue(Type, GetValue(Type) + Delta);
}

void FEmotionState::GetDominant(EEmotionType& OutDominantType, float& OutDominantValue) const
{
	float MaxVal = -1.0f;
	EEmotionType Dom = EEmotionType::Neutral;

	auto Check = [&MaxVal, &Dom](EEmotionType Type, float Val)
	{
		if (Val > MaxVal)
		{
			MaxVal = Val;
			Dom = Type;
		}
	};

	Check(EEmotionType::Joy, Joy);
	Check(EEmotionType::Sadness, Sadness);
	Check(EEmotionType::Anger, Anger);
	Check(EEmotionType::Fear, Fear);
	Check(EEmotionType::Surprise, Surprise);
	Check(EEmotionType::Disgust, Disgust);
	Check(EEmotionType::Trust, Trust);
	Check(EEmotionType::Anticipation, Anticipation);

	OutDominantType = Dom;
	OutDominantValue = MaxVal < 0.0f ? 0.0f : MaxVal;
}

void FEmotionState::Clear()
{
	Joy = Sadness = Anger = Fear = Surprise = Disgust = Trust = Anticipation = 0.0f;
}
