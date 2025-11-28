"""Configuration schema definitions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BackendConfig(BaseModel):
    """Configuration for a language backend."""

    enabled: bool = Field(default=True, description="Whether this backend is enabled")
    command: str = Field(..., description="CLI command or path to the backend executable")


class DefaultsConfig(BaseModel):
    """Default settings for the MCP server."""

    preview_by_default: bool = Field(
        default=True, description="Always preview unless --apply is specified"
    )
    output_format: str = Field(default="toon", description="Default output format")


class DetectionConfig(BaseModel):
    """File detection configuration."""

    extensions: dict[str, str] = Field(
        default_factory=lambda: {
            "py": "python",
            "pyi": "python",
            "rb": "ruby",
            "java": "java",
            "go": "go",
        },
        description="Map file extensions to languages",
    )


class Config(BaseModel):
    """Main configuration for the MCP server."""

    backends: dict[str, BackendConfig] = Field(
        default_factory=lambda: {
            "python": BackendConfig(enabled=True, command="molting"),
            "ruby": BackendConfig(enabled=False, command="molting-rb"),
            "java": BackendConfig(enabled=False, command="molting-java"),
            "go": BackendConfig(enabled=False, command="molting-go"),
        },
        description="Backend configurations by language",
    )
    defaults: DefaultsConfig = Field(
        default_factory=DefaultsConfig, description="Default settings"
    )
    detection: DetectionConfig = Field(
        default_factory=DetectionConfig, description="File detection settings"
    )
