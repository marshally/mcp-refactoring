"""Adapter registry for managing language backends."""

from __future__ import annotations

from mcp_refactoring.adapters.base import BackendAdapter
from mcp_refactoring.adapters.python import PythonAdapter
from mcp_refactoring.config import get_config


# Registry of available adapters by language
_ADAPTER_CLASSES: dict[str, type[BackendAdapter]] = {
    "python": PythonAdapter,
}

# Cache of instantiated adapters
_adapters: dict[str, BackendAdapter] = {}


def get_adapter(language: str) -> BackendAdapter | None:
    """Get an adapter for a specific language.

    Args:
        language: Language identifier (e.g., 'python')

    Returns:
        BackendAdapter instance or None if not available
    """
    if language in _adapters:
        return _adapters[language]

    config = get_config()
    backend_config = config.backends.get(language)

    # Check if backend is enabled
    if backend_config is None or not backend_config.enabled:
        return None

    # Check if we have an adapter class for this language
    adapter_class = _ADAPTER_CLASSES.get(language)
    if adapter_class is None:
        return None

    # Create and cache the adapter
    adapter = adapter_class(command=backend_config.command)

    # Check if the backend is actually available
    if not adapter.is_available():
        return None

    _adapters[language] = adapter
    return adapter


def get_available_adapters() -> dict[str, BackendAdapter]:
    """Get all available adapters.

    Returns:
        Dictionary mapping language names to adapter instances
    """
    config = get_config()
    adapters = {}

    for language in _ADAPTER_CLASSES:
        backend_config = config.backends.get(language)
        if backend_config and backend_config.enabled:
            adapter = get_adapter(language)
            if adapter is not None:
                adapters[language] = adapter

    return adapters


def register_adapter(language: str, adapter_class: type[BackendAdapter]) -> None:
    """Register a new adapter class.

    Args:
        language: Language identifier
        adapter_class: Adapter class to register
    """
    _ADAPTER_CLASSES[language] = adapter_class
    # Clear cache for this language
    if language in _adapters:
        del _adapters[language]
