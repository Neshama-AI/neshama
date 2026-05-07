# Soul Layer - Configuration Loader
"""
Soul Configuration Loader

Features:
- YAML/JSON configuration loading
- Configuration validation
- Configuration merging and override
- Configuration saving
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import yaml
import json
import os


@dataclass
class ModuleConfig:
    """Module configuration."""
    enabled: bool = True
    path: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SoulLoaderConfig:
    """Loader configuration."""
    config_dir: str = "./Neshama/configs"
    default_config_name: str = "default_soul.yaml"
    
    # Loading options
    validate_on_load: bool = True
    merge_with_defaults: bool = True
    allow_missing_modules: bool = True
    
    # Saving options
    auto_save: bool = False
    save_dir: str = "./Neshama/configs"


class SoulLoader:
    """Soul configuration loader."""
    
    def __init__(self, config: SoulLoaderConfig = None):
        self.config = config or SoulLoaderConfig()
        self.loaded_config: Dict[str, Any] = {}
        self.module_configs: Dict[str, Dict] = {}
        self.config_history: List[Dict] = []
    
    def load(
        self,
        config_path: str = None,
        config_data: Dict = None,
    ) -> Dict[str, Any]:
        """Load configuration."""
        if config_path:
            config_data = self._load_from_file(config_path)
        elif config_data is None:
            # Load default configuration
            default_path = os.path.join(
                self.config.config_dir,
                self.config.default_config_name
            )
            if os.path.exists(default_path):
                config_data = self._load_from_file(default_path)
        
        if not config_data:
            return self._get_default_config()
        
        # Validate
        if self.config.validate_on_load:
            config_data = self._validate_config(config_data)
        
        # Merge with defaults
        if self.config.merge_with_defaults:
            config_data = self._merge_with_defaults(config_data)
        
        self.loaded_config = config_data
        self._record_load(config_data)
        
        return config_data
    
    def _load_from_file(self, path: str) -> Dict:
        """Load from file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.json'):
                return json.load(f)
            else:
                return yaml.safe_load(f) or {}
    
    def _validate_config(self, config: Dict) -> Dict:
        """Validate configuration."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["name", "version"]
        for field_name in required_fields:
            if field_name not in config:
                errors.append(f"Missing required field: {field_name}")
        
        # Check version format
        if "version" in config:
            if not self._is_valid_version(config["version"]):
                warnings.append(f"Version format may be invalid: {config['version']}")
        
        # Check module configurations
        if "modules" in config:
            for module_name, module_config in config["modules"].items():
                if isinstance(module_config, dict):
                    if "enabled" not in module_config:
                        warnings.append(f"Module '{module_name}' missing 'enabled' field")
        
        # Check characteristics values
        if "characteristics" in config:
            for char_name, char_config in config["characteristics"].items():
                if isinstance(char_config, dict) and "level" in char_config:
                    level = char_config["level"]
                    if not 0 <= level <= 1:
                        errors.append(f"Characteristic '{char_name}' level must be 0-1, got {level}")
        
        if errors:
            raise ValueError(f"Config validation errors: {', '.join(errors)}")
        
        if warnings:
            print(f"Config warnings: {', '.join(warnings)}")
        
        return config
    
    def _is_valid_version(self, version: str) -> bool:
        """Validate version format."""
        parts = version.split('.')
        if len(parts) < 2:
            return False
        return all(part.isdigit() for part in parts)
    
    def _merge_with_defaults(self, config: Dict) -> Dict:
        """Merge with default configuration."""
        defaults = self._get_default_config()
        
        # Deep merge
        merged = defaults.copy()
        
        for key, value in config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_dicts(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _merge_dicts(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "name": "Neshama Default",
            "version": "1.0.0",
            "description": "Default Soul configuration",
            "identity": {
                "name": "Neshama",
                "tagline": "Your thoughtful AI companion",
                "description": "A friendly and empathetic AI assistant",
            },
            "characteristics": {
                "willpower": {"level": 0.7, "description": "Persistence in difficult tasks"},
                "execution": {"level": 0.8, "description": "Efficiency in action"},
                "empathy": {"level": 0.8, "description": "Understanding emotions"},
                "humor": {"level": 0.5, "description": "Appropriate humor expression"},
                "habits": {"level": 0.6, "description": "Stable behavior patterns"},
            },
            "modules": {
                "emotions": {"enabled": True, "base_tone": "warm"},
                "drives": {"enabled": True, "weights": {}},
                "learning": {"enabled": True, "gepa_enabled": True},
                "creativity": {"enabled": True, "creativity_level": 0.6},
            },
        }
    
    def _record_load(self, config: Dict):
        """Record configuration load history."""
        self.config_history.append({
            "timestamp": datetime.now().isoformat(),
            "name": config.get("name", "Unknown"),
            "version": config.get("version", "Unknown"),
        })
    
    def save(self, config: Dict = None, path: str = None) -> bool:
        """
        Save configuration.
        
        Args:
            config: Configuration to save (uses loaded if None)
            path: Save path
            
        Returns:
            True if successful
        """
        config = config or self.loaded_config
        path = path or os.path.join(
            self.config.save_dir,
            f"{config.get('name', 'soul').lower().replace(' ', '_')}.yaml"
        )
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def get_identity(self) -> Dict[str, str]:
        """Get identity configuration."""
        return self.loaded_config.get("identity", {})
    
    def get_characteristics(self) -> Dict[str, Any]:
        """Get characteristics configuration."""
        return self.loaded_config.get("characteristics", {})
    
    def get_module_config(self, module_name: str) -> Optional[Dict]:
        """Get specific module configuration."""
        return self.loaded_config.get("modules", {}).get(module_name)
    
    def is_module_enabled(self, module_name: str) -> bool:
        """Check if a module is enabled."""
        module_config = self.get_module_config(module_name)
        if not module_config:
            return False
        return module_config.get("enabled", False)
