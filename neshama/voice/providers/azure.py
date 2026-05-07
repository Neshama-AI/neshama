# Azure Speech Provider
"""
Azure Cognitive Services Speech TTS/STT Adapter

API Endpoints:
- TTS: POST https://{region}.api.cognitive.microsoft.com/cognitiveservices/v1
- STT: POST https://{region}.api.cognitive.microsoft.com/speech/recognition/conversation/cognitiveservices/v1

Pricing:
- Standard: $1/million characters
- Neural HD: $16/million characters
"""

import os
from typing import Dict, List, Optional, AsyncIterator
import logging

from ..base import (
    VoiceProvider,
    VoiceInfo,
    ProviderInfo,
    TTSOptions,
    STTOptions,
    TTSResult,
    STTResult,
    EmotionStyle,
    VoiceError,
    AuthenticationError,
    RateLimitError,
    TextTooLongError,
)

logger = logging.getLogger(__name__)

# Default API endpoint
DEFAULT_API_URL = "https://{region}.api.cognitive.microsoft.com"

# Azure Speech synthesis voices (sample)
AZURE_VOICES = [
    # English voices
    VoiceInfo(voice_id="en-US-JennyNeural", name="Jenny", language="en-US", gender="female", style="friendly", provider="azure"),
    VoiceInfo(voice_id="en-US-GuyNeural", name="Guy", language="en-US", gender="male", style="professional", provider="azure"),
    VoiceInfo(voice_id="en-US-AriaNeural", name="Aria", language="en-US", gender="female", style="natural", provider="azure"),
    VoiceInfo(voice_id="en-US-JasonNeural", name="Jason", language="en-US", gender="male", style="dramatic", provider="azure"),
    VoiceInfo(voice_id="en-US-NancyNeural", name="Nancy", language="en-US", gender="female", style="cheerful", provider="azure"),
    VoiceInfo(voice_id="en-GB-SoniaNeural", name="Sonia", language="en-GB", gender="female", style="british", provider="azure"),
    VoiceInfo(voice_id="en-GB-RyanNeural", name="Ryan", language="en-GB", gender="male", style="british", provider="azure"),
    # Chinese voices
    VoiceInfo(voice_id="zh-CN-XiaoxiaoNeural", name="Xiaoxiao", language="zh-CN", gender="female", style="natural", provider="azure"),
    VoiceInfo(voice_id="zh-CN-YunxiNeural", name="Yunxi", language="zh-CN", gender="male", style="dramatic", provider="azure"),
    VoiceInfo(voice_id="zh-TW-HsiaoChenNeural", name="HsiaoChen", language="zh-TW", gender="female", style="natural", provider="azure"),
    # Japanese voices
    VoiceInfo(voice_id="ja-JP-NanamiNeural", name="Nanami", language="ja-JP", gender="female", style="natural", provider="azure"),
    VoiceInfo(voice_id="ja-JP-KeitaNeural", name="Keita", language="ja-JP", gender="male", style="professional", provider="azure"),
    # Spanish voices
    VoiceInfo(voice_id="es-ES-ElviraNeural", name="Elvira", language="es-ES", gender="female", style="natural", provider="azure"),
    VoiceInfo(voice_id="es-MX-DaliaNeural", name="Dalia", language="es-MX", gender="female", style="friendly", provider="azure"),
    # French voices
    VoiceInfo(voice_id="fr-FR-DeniseNeural", name="Denise", language="fr-FR", gender="female", style="natural", provider="azure"),
    VoiceInfo(voice_id="fr-FR-HenriNeural", name="Henri", language="fr-FR", gender="male", style="professional", provider="azure"),
    # German voices
    VoiceInfo(voice_id="de-DE-KatjaNeural", name="Katja", language="de-DE", gender="female", style="natural", provider="azure"),
    VoiceInfo(voice_id="de-DE-ConradNeural", name="Conrad", language="de-DE", gender="male", style="professional", provider="azure"),
    # Korean voices
    VoiceInfo(voice_id="ko-KR-SunHiNeural", name="SunHi", language="ko-KR", gender="female", style="cheerful", provider="azure"),
    VoiceInfo(voice_id="ko-KR-InJoonNeural", name="InJoon", language="ko-KR", gender="male", style="professional", provider="azure"),
]

# Emotion to SSML style mapping
AZURE_EMOTION_MAP: Dict[EmotionStyle, str] = {
    EmotionStyle.JOY: "cheerful",
    EmotionStyle.ANGER: "angry",
    EmotionStyle.SADNESS: "sad",
    EmotionStyle.FEAR: "terrified",
    EmotionStyle.TRUST: "friendly",
    EmotionStyle.SURPRISE: "surprised",
    EmotionStyle.DISGUST: "unfriendly",
    EmotionStyle.ANTICIPATION: "hopeful",
    EmotionStyle.NEUTRAL: "general",
}


class AzureSpeechProvider(VoiceProvider):
    """
    Azure Cognitive Services Speech provider.
    
    Supports:
    - TTS with SSML emotion tags
    - STT with real-time transcription
    - 400+ Neural voices
    - Streaming synthesis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Azure Speech provider.
        
        Config options:
        - subscription_key: Azure subscription key
        - region: Azure region (e.g., eastus, westus2)
        - voice_name: Default voice name
        """
        super().__init__(config)
        self.subscription_key = self.config.get("subscription_key") or os.getenv("AZURE_SPEECH_KEY")
        self.region = self.config.get("region") or os.getenv("AZURE_SPEECH_REGION", "eastus")
        self.voice_name = self.config.get("voice_name", "en-US-JennyNeural")
        
        # Build API URL
        self.api_url = self.config.get("api_url") or DEFAULT_API_URL
        self.api_url = self.api_url.format(region=self.region)
        
        if not self.subscription_key:
            logger.warning("Azure Speech subscription key not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers."""
        return {
            "Ocp-Apim-Subscription-Key": self.subscription_key or "",
            "Content-Type": "application/json",
        }
    
    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="azure",
            supported_languages=[
                "en-US", "en-GB", "en-AU", "en-IN", "en-CA",
                "zh-CN", "zh-TW", "zh-HK",
                "ja-JP", "ko-KR",
                "es-ES", "es-MX", "es-US",
                "fr-FR", "fr-CA",
                "de-DE", "it-IT", "pt-BR", "pt-PT",
                "ru-RU", "ar-SA", "nl-NL", "pl-PL", "sv-SE", "tr-TR",
            ],
            max_text_length=10000,
            supports_emotion=True,
            supports_streaming=True,
            pricing={
                "tts_per_char": 0.000001,  # $1/million chars
                "stt_per_second": 0.001,
            },
            provider_type="cloud",
        )
    
    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available voices.
        """
        if not language:
            return AZURE_VOICES
        
        lang_prefix = language.split("-")[0]
        return [v for v in AZURE_VOICES if v.language.startswith(lang_prefix)]
    
    def _build_ssml(
        self,
        text: str,
        voice_id: str,
        emotion: Optional[EmotionStyle] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
    ) -> str:
        """Build SSML document with emotion."""
        # Convert speed/float to SSML rate
        if speed < 0.8:
            rate = "slow"
        elif speed > 1.2:
            rate = "fast"
        else:
            rate = "medium"
        
        # Convert pitch to SSML pitch
        pitch_str = f"{int((pitch - 1) * 50)}Hz"
        
        # Build voice element
        voice_elem = f'<voice name="{voice_id}">'
        
        # Add emotion tag if specified
        if emotion:
            style = AZURE_EMOTION_MAP.get(emotion, "general")
            voice_elem = f'<mstts:express-as style="{style}">{voice_elem}'
        
        ssml = f'''<?xml version="1.0" encoding="UTF-8"?>
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
       xmlns:mstts="http://schemas.microsoft.com/2003/10/mstts/synthesis"
       xml:lang="en-US">
    <prosody rate="{rate}" pitch="{pitch_str}">
        {voice_elem}
        {text}
        </voice>
        {'</mstts:express-as>' if emotion else ''}
    </prosody>
</speak>'''
        
        return ssml
    
    async def text_to_speech(
        self,
        text: str,
        options: TTSOptions,
    ) -> TTSResult:
        """
        Convert text to speech using Azure Speech API.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            TTSResult with audio data
        """
        if not self.subscription_key:
            raise AuthenticationError("Azure Speech subscription key not configured", provider="azure")
        
        if len(text) > self.get_provider_info().max_text_length:
            raise TextTooLongError(
                f"Text length {len(text)} exceeds maximum",
                provider="azure"
            )
        
        # Build SSML
        ssml = self._build_ssml(
            text,
            options.voice_id,
            options.emotion,
            options.speed,
            options.pitch,
        )
        
        import aiohttp
        
        url = f"{self.api_url}/cognitiveservices/v1"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Ocp-Apim-Subscription-Key": self.subscription_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                    "User-Agent": "Neshama/1.0",
                }
                
                async with session.post(
                    url,
                    data=ssml.encode("utf-8"),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid Azure Speech key", provider="azure")
                    elif response.status == 429:
                        raise RateLimitError("Azure Speech rate limit exceeded", provider="azure")
                    elif response.status != 200:
                        text_err = await response.text()
                        raise VoiceError(
                            f"Azure Speech API error: {response.status} - {text_err}",
                            provider="azure"
                        )
                    
                    audio_data = await response.read()
                    
                    return TTSResult(
                        audio_data=audio_data,
                        duration_seconds=len(audio_data) / 48000,  # 24kHz
                        format="mp3",
                        voice_id=options.voice_id,
                        provider="azure",
                    )
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="azure")
    
    async def text_to_speech_stream(
        self,
        text: str,
        options: TTSOptions,
    ) -> AsyncIterator[bytes]:
        """
        Convert text to speech with streaming audio chunks.
        """
        if not self.subscription_key:
            raise AuthenticationError("Azure Speech subscription key not configured", provider="azure")
        
        ssml = self._build_ssml(
            text,
            options.voice_id,
            options.emotion,
            options.speed,
            options.pitch,
        )
        
        import aiohttp
        
        url = f"{self.api_url}/cognitiveservices/v1"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Ocp-Apim-Subscription-Key": self.subscription_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                    "User-Agent": "Neshama/1.0",
                }
                
                async with session.post(
                    url,
                    data=ssml.encode("utf-8"),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        text_err = await response.text()
                        raise VoiceError(
                            f"Azure Speech streaming error: {response.status}",
                            provider="azure"
                        )
                    
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            yield chunk
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="azure")
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        options: STTOptions,
    ) -> STTResult:
        """
        Convert speech to text using Azure Speech API.
        
        Args:
            audio_data: Audio data to transcribe
            options: STT options
            
        Returns:
            STTResult with transcribed text
        """
        if not self.subscription_key:
            raise AuthenticationError("Azure Speech subscription key not configured", provider="azure")
        
        import aiohttp
        
        url = f"{self.api_url}/speech/recognition/conversation/cognitiveservices/v1?language={options.language or 'en-US'}"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Ocp-Apim-Subscription-Key": self.subscription_key,
                    "Content-Type": "audio/wav",
                }
                
                async with session.post(
                    url,
                    data=audio_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        text_err = await response.text()
                        raise VoiceError(
                            f"Azure Speech STT error: {response.status} - {text_err}",
                            provider="azure"
                        )
                    
                    result = await response.json()
                    
                    return STTResult(
                        text=result.get("DisplayText", ""),
                        confidence=result.get("Confidence", 0.95),
                        language=options.language,
                        provider="azure",
                    )
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="azure")
