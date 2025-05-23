"""Prompt management for LLM post-processing configuration."""

import logging
from pathlib import Path
from typing import Dict, Optional, Any

import yaml

from .exceptions import PromptConfigError

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages LLM prompts and application mappings from configuration file."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the prompt manager.
        
        Args:
            config_path: Path to prompts.yaml config file. Defaults to prompts.yaml in project root.
        """
        if config_path is None:
            # Default to prompts.yaml in project root (parent of dictator package)
            config_path = Path(__file__).parent.parent / "prompts.yaml"
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load the prompt configuration from YAML file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Prompt config file not found: {self.config_path}")
                self._load_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
            
            logger.debug(f"Loaded prompt config from {self.config_path}")
            self._validate_config()
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in prompt config: {e}")
            raise PromptConfigError(f"Failed to parse prompt config: {e}")
        except Exception as e:
            logger.error(f"Error loading prompt config: {e}")
            raise PromptConfigError(f"Failed to load prompt config: {e}")
    
    def _load_default_config(self) -> None:
        """Load a minimal default configuration when config file is missing."""
        logger.info("Using default prompt configuration")
        self.config = {
            "prompts": {},
            "applications": {
                "default": {"prompt": None}
            }
        }
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration structure."""
        if not isinstance(self.config, dict):
            raise PromptConfigError("Config must be a dictionary")
        
        if "prompts" not in self.config:
            raise PromptConfigError("Config missing 'prompts' section")
        
        if "applications" not in self.config:
            raise PromptConfigError("Config missing 'applications' section")
        
        # Validate prompts have required template field
        for prompt_name, prompt_config in self.config.get("prompts", {}).items():
            if not isinstance(prompt_config, dict):
                raise PromptConfigError(f"Prompt '{prompt_name}' must be a dictionary")
            
            if "template" not in prompt_config:
                raise PromptConfigError(f"Prompt '{prompt_name}' missing 'template' field")
            
            template = prompt_config["template"]
            if not isinstance(template, str):
                raise PromptConfigError(f"Prompt '{prompt_name}' template must be a string")
            
            if "{transcript}" not in template:
                raise PromptConfigError(f"Prompt '{prompt_name}' template must contain '{{transcript}}' placeholder")
        
        logger.debug("Prompt configuration validation successful")
    
    def get_prompt_for_app(self, app_class: str) -> Optional[str]:
        """Get the prompt template for a given application class.
        
        Args:
            app_class: The window class name from window detection
            
        Returns:
            Prompt template string if found, None if no processing should be done
        """
        if not app_class:
            return None
        
        app_class_lower = app_class.lower()
        
        # Check each application group for pattern matches
        for app_group, config in self.config.get("applications", {}).items():
            if app_group == "default":
                continue
            
            if not isinstance(config, dict):
                continue
            
            patterns = config.get("patterns", [])
            if not isinstance(patterns, list):
                continue
            
            # Check if any pattern matches the app class
            for pattern in patterns:
                if isinstance(pattern, str) and pattern.lower() in app_class_lower:
                    prompt_name = config.get("prompt")
                    if prompt_name and prompt_name in self.config.get("prompts", {}):
                        template = self.config["prompts"][prompt_name]["template"]
                        logger.debug(f"Found prompt '{prompt_name}' for app '{app_class}'")
                        return template
                    elif prompt_name is None:
                        logger.debug(f"App '{app_class}' configured for no processing")
                        return None
                    else:
                        logger.warning(f"App '{app_class}' references unknown prompt '{prompt_name}'")
        
        # No specific match found, check default
        default_config = self.config.get("applications", {}).get("default", {})
        default_prompt = default_config.get("prompt")
        
        if default_prompt and default_prompt in self.config.get("prompts", {}):
            template = self.config["prompts"][default_prompt]["template"]
            logger.debug(f"Using default prompt '{default_prompt}' for app '{app_class}'")
            return template
        
        logger.debug(f"No prompt configured for app '{app_class}', no processing will be done")
        return None
    
    def reload_config(self) -> None:
        """Reload the configuration from file.
        
        Useful for development or when config file is updated at runtime.
        """
        logger.info("Reloading prompt configuration")
        self._load_config()
    
    def list_prompts(self) -> Dict[str, Dict[str, str]]:
        """Get a summary of all available prompts.
        
        Returns:
            Dictionary mapping prompt names to their metadata (name, description)
        """
        prompts = {}
        for prompt_name, prompt_config in self.config.get("prompts", {}).items():
            prompts[prompt_name] = {
                "name": prompt_config.get("name", prompt_name),
                "description": prompt_config.get("description", "No description available")
            }
        return prompts
    
    def list_applications(self) -> Dict[str, Dict[str, Any]]:
        """Get a summary of all application mappings.
        
        Returns:
            Dictionary mapping app groups to their configuration
        """
        return self.config.get("applications", {})