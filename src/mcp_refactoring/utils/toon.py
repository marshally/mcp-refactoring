"""TOON (Token-Oriented Object Notation) encoder.

TOON is a compact, LLM-friendly format that combines YAML-style indentation
with CSV-style tabular layout for uniform arrays.

See: https://github.com/toon-format/toon
"""

from __future__ import annotations

from typing import Any


class ToonEncoder:
    """Encoder for TOON format."""

    def __init__(self, indent: int = 2) -> None:
        """Initialize the encoder.

        Args:
            indent: Number of spaces for indentation (default: 2)
        """
        self.indent = indent

    def encode(self, data: dict[str, Any]) -> str:
        """Encode a dictionary to TOON format.

        Args:
            data: Dictionary to encode

        Returns:
            TOON-formatted string
        """
        lines: list[str] = []
        self._encode_dict(data, lines, 0)
        return "\n".join(lines)

    def _encode_dict(
        self, data: dict[str, Any], lines: list[str], depth: int
    ) -> None:
        """Encode a dictionary."""
        prefix = " " * (depth * self.indent)

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                self._encode_dict(value, lines, depth + 1)
            elif isinstance(value, list):
                self._encode_list(key, value, lines, prefix)
            else:
                lines.append(f"{prefix}{key}: {self._format_value(value)}")

    def _encode_list(
        self, key: str, items: list[Any], lines: list[str], prefix: str
    ) -> None:
        """Encode a list, using tabular format for uniform object arrays."""
        if not items:
            lines.append(f"{prefix}{key}[0]{{}}:")
            return

        # Check if all items are dicts with the same keys (uniform array)
        if all(isinstance(item, dict) for item in items):
            first_keys = set(items[0].keys()) if items else set()
            if all(set(item.keys()) == first_keys for item in items):
                # Uniform object array - use tabular format
                self._encode_tabular(key, items, lines, prefix)
                return

        # Non-uniform or primitive list
        lines.append(f"{prefix}{key}[{len(items)}]:")
        for item in items:
            if isinstance(item, dict):
                lines.append(f"{prefix}  -")
                self._encode_dict(item, lines, len(prefix) // self.indent + 2)
            else:
                lines.append(f"{prefix}  - {self._format_value(item)}")

    def _encode_tabular(
        self, key: str, items: list[dict[str, Any]], lines: list[str], prefix: str
    ) -> None:
        """Encode a uniform object array in tabular format."""
        if not items:
            return

        # Get field names from first item
        fields = list(items[0].keys())
        fields_str = ",".join(fields)

        # Header line: key[N]{field1,field2,...}:
        lines.append(f"{prefix}{key}[{len(items)}]{{{fields_str}}}:")

        # Data rows
        for item in items:
            values = [self._format_tabular_value(item.get(f, "")) for f in fields]
            lines.append(f"{prefix}  {','.join(values)}")

    def _format_value(self, value: Any) -> str:
        """Format a scalar value for TOON."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            # Quote strings with special characters
            if any(c in value for c in [",", ":", "\n", '"', "'"]):
                return f'"{self._escape_string(value)}"'
            return value
        return str(value)

    def _format_tabular_value(self, value: Any) -> str:
        """Format a value for tabular (CSV-style) format."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            # Quote strings with commas or special characters
            if any(c in value for c in [",", "\n", '"']):
                return f'"{self._escape_string(value)}"'
            return value
        return str(value)

    def _escape_string(self, s: str) -> str:
        """Escape special characters in a string."""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def encode_toon(data: dict[str, Any]) -> str:
    """Convenience function to encode data to TOON format.

    Args:
        data: Dictionary to encode

    Returns:
        TOON-formatted string
    """
    encoder = ToonEncoder()
    return encoder.encode(data)
