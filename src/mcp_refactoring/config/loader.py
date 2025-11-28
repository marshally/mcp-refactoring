"""Configuration loading from files and environment variables."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from mcp_refactoring.config.schema import Config, BackendConfig

# Use tomllib in Python 3.11+, tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# Global config instance
_config: Config | None = None


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    env_path = os.environ.get("MCP_REFACTORING_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".mcp-refactoring" / "config.toml"


def load_config_from_file(config_path: Path) -> dict[str, Any]:
    """Load configuration from a TOML file."""
    if not config_path.exists():
        return {}

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def apply_env_overrides(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides to configuration."""
    # Initialize backends dict if not present
    if "backends" not in config_dict:
        config_dict["backends"] = {}

    # Backend command overrides
    for lang in ["python", "ruby", "java", "go"]:
        env_key = f"MCP_REFACTORING_{lang.upper()}_COMMAND"
        if env_key in os.environ:
            if lang not in config_dict["backends"]:
                config_dict["backends"][lang] = {}
            config_dict["backends"][lang]["command"] = os.environ[env_key]

        # Backend enabled overrides
        env_key = f"MCP_REFACTORING_{lang.upper()}_ENABLED"
        if env_key in os.environ:
            if lang not in config_dict["backends"]:
                config_dict["backends"][lang] = {}
            config_dict["backends"][lang]["enabled"] = os.environ[env_key].lower() in (
                "true",
                "1",
                "yes",
            )

    return config_dict


def load_config(force_reload: bool = False) -> Config:
    """Load and return the configuration.

    Args:
        force_reload: If True, reload config even if already loaded.

    Returns:
        The loaded configuration.
    """
    global _config

    if _config is not None and not force_reload:
        return _config

    config_path = get_config_path()
    config_dict = load_config_from_file(config_path)
    config_dict = apply_env_overrides(config_dict)

    # Build the config, merging with defaults
    backends_dict = config_dict.get("backends", {})
    backends = {}

    # Start with defaults
    default_backends = {
        "python": BackendConfig(enabled=True, command="molting"),
        "ruby": BackendConfig(enabled=False, command="molting-rb"),
        "java": BackendConfig(enabled=False, command="molting-java"),
        "go": BackendConfig(enabled=False, command="molting-go"),
    }

    # Merge user config with defaults
    for lang, default_config in default_backends.items():
        if lang in backends_dict:
            backends[lang] = BackendConfig(
                enabled=backends_dict[lang].get("enabled", default_config.enabled),
                command=backends_dict[lang].get("command", default_config.command),
            )
        else:
            backends[lang] = default_config

    _config = Config(
        backends=backends,
        defaults=config_dict.get("defaults", {}),
        detection=config_dict.get("detection", {}),
    )

    return _config


def get_config() -> Config:
    """Get the current configuration, loading if necessary."""
    return load_config()
