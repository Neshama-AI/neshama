# Web API - Voice API Router
"""
Voice API - Endpoints for TTS/STT services.

Provides voice endpoints for:
- Text-to-Speech (TTS)
- Speech-to-Text (STT)
- Provider management
- NPC voice binding
"""

from typing import Dict, Any, Optional, List
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response, StreamingResponse

from neshama.voice import VoiceManager, get_voice_manager, EmotionStyle
from neshama.voice.base import TTSResult, STTResult
from neshama.soul.npc_manager import get_npc_manager

router = APIRouter()
logger = logging.getLogger(__name__)


# ── TTS Endpoints ──────────────────────────────────────────────────────────────

@router.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    npc_id: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    voice_id: Optional[str] = Form(None),
    language: str = Form("en"),
    emotion: Optional[str] = Form(None),
    stream: bool = Form(False),
):
    """
    Convert text to speech.
    
    Args:
        text: Text to synthesize
        npc_id: NPC ID for voice binding
        provider: Specific provider to use
        voice_id: Specific voice ID
        language: Language code
        emotion: Emotion style (joy/anger/sadness/fear/trust/surprise/disgust/anticipation/neutral)
        stream: Whether to stream audio chunks
        
    Returns:
        Audio file (mp3/wav) or streaming chunks
    """
    manager = get_voice_manager()
    
    # Parse emotion
    emotion_style = None
    if emotion:
        try:
            emotion_style = EmotionStyle(emotion)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid emotion: {emotion}. Valid values: {[e.value for e in EmotionStyle]}"
            )
    
    # Get NPC voice config if npc_id is provided
    if npc_id and not voice_id and not provider:
        npc_config = manager.get_npc_voice(npc_id)
        if npc_config:
            provider = npc_config.provider_name
            voice_id = npc_config.voice_id
            language = npc_config.language
            if npc_config.emotion and not emotion_style:
                try:
                    emotion_style = EmotionStyle(npc_config.emotion)
                except ValueError:
                    pass
    
    try:
        if stream:
            # Return streaming response
            async def stream_generator():
                stream_result = await manager.tts(
                    text=text,
                    npc_id=npc_id,
                    provider_name=provider,
                    voice_id=voice_id,
                    language=language,
                    emotion=emotion_style,
                    stream=True,
                )
                
                # Handle both AsyncIterator and regular iterator
                if hasattr(stream_result, "__anext__"):
                    async for chunk in stream_result:
                        yield chunk
                else:
                    for chunk in stream_result:
                        yield chunk
            
            return StreamingResponse(
                stream_generator(),
                media_type="audio/mpeg",
                headers={
                    "Transfer-Encoding": "chunked",
                    "X-Content-Type-Options": "nosniff",
                }
            )
        else:
            # Return full audio
            result = await manager.tts(
                text=text,
                npc_id=npc_id,
                provider_name=provider,
                voice_id=voice_id,
                language=language,
                emotion=emotion_style,
                stream=False,
            )
            
            return Response(
                content=result.audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename=speech.mp3",
                    "X-Audio-Duration": str(result.duration_seconds),
                    "X-Audio-Provider": result.provider,
                }
            )
            
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── STT Endpoints ─────────────────────────────────────────────────────────────

@router.post("/stt")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    language: str = Form("en"),
    provider: Optional[str] = Form(None),
    max_duration: int = Form(60),
):
    """
    Convert speech audio to text.
    
    Args:
        audio_file: Audio file (mp3/wav/ogg)
        language: Language code
        provider: Specific provider to use
        max_duration: Maximum audio duration in seconds
        
    Returns:
        Transcribed text with confidence
    """
    manager = get_voice_manager()
    
    # Read audio data
    audio_data = await audio_file.read()
    
    # Check file size
    if len(audio_data) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="Audio file too large (max 50MB)")
    
    try:
        result = await manager.stt(
            audio_data=audio_data,
            language=language,
            provider_name=provider,
            max_duration=max_duration,
        )
        
        return {
            "success": True,
            "data": {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "provider": result.provider,
                "duration_seconds": result.duration_seconds,
            }
        }
        
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Provider Endpoints ────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers():
    """
    List all available voice providers.
    
    Returns:
        List of providers with their capabilities
    """
    manager = get_voice_manager()
    providers = manager.list_providers()
    
    return {
        "success": True,
        "data": {
            "providers": [p.to_dict() for p in providers],
            "count": len(providers),
        }
    }


@router.get("/voices/{provider}")
async def list_provider_voices(
    provider: str,
    language: Optional[str] = None,
):
    """
    List voices for a specific provider.
    
    Args:
        provider: Provider name
        language: Optional language filter
        
    Returns:
        List of available voices
    """
    manager = get_voice_manager()
    
    # Get provider
    voice_provider = manager.get_provider(provider)
    if not voice_provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
    
    voices = voice_provider.list_voices(language)
    
    return {
        "success": True,
        "data": {
            "provider": provider,
            "language": language,
            "voices": [v.to_dict() for v in voices],
            "count": len(voices),
        }
    }


# ── NPC Voice Binding Endpoints ───────────────────────────────────────────────

@router.post("/npc/{npc_id}/voice")
async def set_npc_voice(
    npc_id: str,
    voice_id: str = Form(...),
    provider: str = Form(...),
    language: str = Form("en"),
    emotion: Optional[str] = Form(None),
    speed: float = Form(1.0),
    pitch: float = Form(1.0),
):
    """
    Set voice configuration for an NPC.
    
    Args:
        npc_id: NPC identifier
        voice_id: Voice ID to use
        provider: Provider name
        language: Language code
        emotion: Default emotion style
        speed: Speech speed
        pitch: Speech pitch
        
    Returns:
        Voice configuration
    """
    manager = get_voice_manager()
    
    # Validate provider exists
    if not manager.get_provider(provider):
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
    
    # Validate voice exists
    voice_provider = manager.get_provider(provider)
    voices = voice_provider.list_voices()
    if not any(v.voice_id == voice_id for v in voices):
        raise HTTPException(status_code=400, detail=f"Voice {voice_id} not found in provider {provider}")
    
    # Set NPC voice
    manager.set_npc_voice(
        npc_id=npc_id,
        voice_id=voice_id,
        provider_name=provider,
        language=language,
        emotion=emotion,
        speed=speed,
        pitch=pitch,
    )
    
    config = manager.get_npc_voice(npc_id)
    
    return {
        "success": True,
        "data": config.to_dict(),
    }


@router.get("/npc/{npc_id}/voice")
async def get_npc_voice(npc_id: str):
    """
    Get voice configuration for an NPC.
    
    Args:
        npc_id: NPC identifier
        
    Returns:
        Voice configuration or null
    """
    manager = get_voice_manager()
    config = manager.get_npc_voice(npc_id)
    
    if not config:
        return {
            "success": True,
            "data": None,
        }
    
    return {
        "success": True,
        "data": config.to_dict(),
    }


@router.delete("/npc/{npc_id}/voice")
async def delete_npc_voice(npc_id: str):
    """
    Remove voice configuration for an NPC.
    
    Args:
        npc_id: NPC identifier
        
    Returns:
        Success status
    """
    manager = get_voice_manager()
    removed = manager.remove_npc_voice(npc_id)
    
    return {
        "success": removed,
        "message": "Voice configuration removed" if removed else "No voice configuration found",
    }


# ── TTS Cache Endpoints ───────────────────────────────────────────────────────

@router.delete("/cache")
async def clear_cache():
    """
    Clear the TTS cache.
    
    Returns:
        Success status
    """
    manager = get_voice_manager()
    manager.clear_cache()
    
    return {
        "success": True,
        "message": "Cache cleared",
    }
