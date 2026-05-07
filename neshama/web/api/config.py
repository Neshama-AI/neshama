"""
Config API - Application settings management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException

router = APIRouter()

# Mock configuration data
MOCK_CONFIG = {
    "model": {
        "provider": "openai",
        "model_name": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2048,
        "api_key_configured": True
    },
    "platform": {
        "adapter": "cli",
        "auto_save": True,
        "save_interval": 300
    },
    "appearance": {
        "theme": "dark",
        "accent_color": "#4F46E5",
        "font_size": 14
    },
    "behavior": {
        "stream_responses": True,
        "show_emotions": True,
        "enable_evolution": True,
        "memory_enabled": True
    },
    "debug": {
        "log_level": "info",
        "show_timestamps": True,
        "performance_metrics": False
    }
}


MODEL_PROVIDERS = [
    {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"]},
    {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-opus", "claude-3-sonnet"]},
    {"id": "google", "name": "Google Gemini", "models": ["gemini-pro"]},
    {"id": "mock", "name": "Mock (Demo)", "models": ["mock-model"]}
]


PLATFORM_ADAPTERS = [
    {"id": "cli", "name": "Command Line", "description": "Terminal-based interface"},
    {"id": "web", "name": "Web Panel", "description": "Browser-based Soul Panel"},
    {"id": "api", "name": "API Server", "description": "REST API server"}
]


@router.get("/")
async def get_config():
    """Get current configuration."""
    return {
        "success": True,
        "data": MOCK_CONFIG
    }


@router.put("/")
async def update_config(updates: Dict[str, Any]):
    """Update configuration."""
    global MOCK_CONFIG
    
    # Deep merge updates
    def deep_merge(base: Dict, updates: Dict) -> Dict:
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    MOCK_CONFIG = deep_merge(MOCK_CONFIG, updates)
    
    return {
        "success": True,
        "data": MOCK_CONFIG,
        "message": "Configuration updated"
    }


# 已配置的 API Keys（Mock）
CONFIGURED_API_KEYS = {
    "openai": {"configured": True, "base_url": None},
    "anthropic": {"configured": True, "base_url": None},
    "deepseek": {"configured": True, "base_url": None},
    "dashscope": {"configured": True, "base_url": None},
    "groq": {"configured": True, "base_url": None},
    "google": {"configured": False, "base_url": None},
    "zhipu": {"configured": False, "base_url": None},
}

# 路由策略
ROUTING_STRATEGY = {
    "mode": "manual",  # manual, cheapest, best_quality, by_task
    "coding": {"provider": "anthropic", "model": "claude-sonnet-4"},
    "chat": {"provider": "openai", "model": "gpt-4o"},
    "reasoning": {"provider": "deepseek", "model": "deepseek-r1"},
}

@router.get("/model/providers")
async def get_model_providers():
    """Get available model providers."""
    return {
        "success": True,
        "data": MODEL_PROVIDERS
    }


@router.get("/model/configured")
async def get_configured_providers():
    """Get configured providers with API keys."""
    configured = []
    for provider_id, config in CONFIGURED_API_KEYS.items():
        provider_info = next((p for p in MODEL_PROVIDERS if p["id"] == provider_id), None)
        if provider_info:
            configured.append({
                "id": provider_id,
                "name": provider_info["name"],
                "models": provider_info["models"],
                "configured": config["configured"],
                "base_url": config["base_url"],
            })
    
    return {
        "success": True,
        "data": configured
    }


@router.post("/model/configure")
async def configure_provider(config: Dict[str, Any]):
    """Configure a provider with API key."""
    provider_id = config.get("provider_id")
    api_key = config.get("api_key")
    base_url = config.get("base_url")
    
    if not provider_id or not api_key:
        raise HTTPException(status_code=400, detail="provider_id and api_key are required")
    
    CONFIGURED_API_KEYS[provider_id] = {
        "configured": True,
        "base_url": base_url,
    }
    
    return {
        "success": True,
        "message": f"Provider {provider_id} configured successfully"
    }


@router.delete("/model/configure/{provider_id}")
async def remove_provider_config(provider_id: str):
    """Remove provider configuration."""
    if provider_id in CONFIGURED_API_KEYS:
        CONFIGURED_API_KEYS[provider_id] = {"configured": False, "base_url": None}
    
    return {
        "success": True,
        "message": f"Provider {provider_id} configuration removed"
    }


@router.get("/model/default")
async def get_default_model():
    """Get default provider and model settings."""
    return {
        "success": True,
        "data": {
            "provider": MOCK_CONFIG["model"]["provider"],
            "model": MOCK_CONFIG["model"]["model_name"],
            "temperature": MOCK_CONFIG["model"]["temperature"],
            "max_tokens": MOCK_CONFIG["model"]["max_tokens"],
        }
    }


@router.put("/model/default")
async def set_default_model(config: Dict[str, Any]):
    """Set default provider and model."""
    global MOCK_CONFIG
    
    if "provider" in config:
        MOCK_CONFIG["model"]["provider"] = config["provider"]
    if "model" in config:
        MOCK_CONFIG["model"]["model_name"] = config["model"]
    if "temperature" in config:
        MOCK_CONFIG["model"]["temperature"] = config["temperature"]
    if "max_tokens" in config:
        MOCK_CONFIG["model"]["max_tokens"] = config["max_tokens"]
    
    return {
        "success": True,
        "data": {
            "provider": MOCK_CONFIG["model"]["provider"],
            "model": MOCK_CONFIG["model"]["model_name"],
        },
        "message": "Default model settings updated"
    }


@router.get("/model/routing")
async def get_routing_strategy():
    """Get routing strategy settings."""
    return {
        "success": True,
        "data": ROUTING_STRATEGY
    }


@router.put("/model/routing")
async def set_routing_strategy(config: Dict[str, Any]):
    """Set routing strategy."""
    global ROUTING_STRATEGY
    
    if "mode" in config:
        ROUTING_STRATEGY["mode"] = config["mode"]
    if "coding" in config:
        ROUTING_STRATEGY["coding"] = config["coding"]
    if "chat" in config:
        ROUTING_STRATEGY["chat"] = config["chat"]
    if "reasoning" in config:
        ROUTING_STRATEGY["reasoning"] = config["reasoning"]
    
    return {
        "success": True,
        "data": ROUTING_STRATEGY,
        "message": "Routing strategy updated"
    }


@router.post("/model/test")
async def test_model_connection(config: Dict[str, Any]):
    """Test model connection."""
    provider = config.get("provider", "mock")
    model = config.get("model_name", "mock-model")
    
    # Simulate connection test
    success = provider in [p["id"] for p in MODEL_PROVIDERS]
    
    return {
        "success": success,
        "message": f"Connection test {'successful' if success else 'failed'}",
        "latency_ms": round(50 + hash(provider + model) % 200, 2)
    }


@router.post("/api_key/test")
async def test_api_key(provider: str, api_key: str):
    """Test API key validity."""
    # Simulate API key test
    if len(api_key) < 10:
        return {
            "success": False,
            "message": "API key appears to be invalid"
        }
    
    return {
        "success": True,
        "message": f"API key validated for {provider}",
        "expires": None
    }


@router.get("/export")
async def export_config():
    """Export configuration as JSON."""
    return {
        "success": True,
        "data": MOCK_CONFIG,
        "filename": f"neshama_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    }


@router.post("/import")
async def import_config(config: Dict[str, Any]):
    """Import configuration from JSON."""
    global MOCK_CONFIG
    
    # Validate required sections
    required_sections = ["model", "platform", "appearance", "behavior"]
    for section in required_sections:
        if section not in config:
            raise HTTPException(status_code=400, detail=f"Missing required section: {section}")
    
    MOCK_CONFIG = config
    
    return {
        "success": True,
        "message": "Configuration imported successfully"
    }


@router.post("/reset")
async def reset_config():
    """Reset configuration to defaults."""
    global MOCK_CONFIG
    
    MOCK_CONFIG = {
        "model": {
            "provider": "mock",
            "model_name": "mock-model",
            "temperature": 0.7,
            "max_tokens": 2048,
            "api_key_configured": False
        },
        "platform": {
            "adapter": "cli",
            "auto_save": True,
            "save_interval": 300
        },
        "appearance": {
            "theme": "dark",
            "accent_color": "#4F46E5",
            "font_size": 14
        },
        "behavior": {
            "stream_responses": True,
            "show_emotions": True,
            "enable_evolution": True,
            "memory_enabled": True
        },
        "debug": {
            "log_level": "info",
            "show_timestamps": True,
            "performance_metrics": False
        }
    }
    
    return {
        "success": True,
        "message": "Configuration reset to defaults"
    }
