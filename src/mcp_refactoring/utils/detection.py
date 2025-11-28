"""Language and file detection utilities."""

from __future__ import annotations

from pathlib import Path

from mcp_refactoring.config import get_config


def get_file_extension(path: str) -> str | None:
    """Get the file extension from a path.

    Args:
        path: File path (may include target specifiers like ::Class::method)

    Returns:
        File extension without the dot, or None if no extension
    """
    # Extract just the file path (before any :: or # target specifiers)
    file_path = path.split("::")[0].split("#")[0]
    p = Path(file_path)

    if p.suffix:
        return p.suffix[1:]  # Remove the leading dot
    return None


def detect_language(path: str) -> str | None:
    """Detect the programming language from a file path.

    Args:
        path: File path (may include target specifiers)

    Returns:
        Language identifier (e.g., 'python', 'ruby') or None if unknown
    """
    ext = get_file_extension(path)
    if ext is None:
        return None

    config = get_config()
    return config.detection.extensions.get(ext)


def get_available_languages() -> list[str]:
    """Get list of languages with enabled backends.

    Returns:
        List of language identifiers with enabled backends
    """
    config = get_config()
    return [
        lang for lang, backend in config.backends.items() if backend.enabled
    ]
