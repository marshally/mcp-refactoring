"""Tool for inspecting code structure."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from mcp_refactoring.adapters import get_adapter
from mcp_refactoring.utils import encode_toon, detect_language


class InspectStructureInput(BaseModel):
    """Input for inspecting code structure."""

    model_config = ConfigDict(str_strip_whitespace=True)

    path: str = Field(
        ...,
        description="File path to inspect (e.g., 'src/order.py')",
        min_length=1,
    )
    depth: str = Field(
        default="class",
        description="Level of detail: 'file', 'class', or 'method'",
    )


async def inspect_structure(params: InspectStructureInput) -> str:
    """Get structural information about code (classes, methods, dependencies).

    Inspects a file to return information about its structure including
    classes, methods, fields, and line numbers.

    Args:
        params: Input parameters including path and depth

    Returns:
        TOON-formatted string with structural information
    """
    # Detect language from path
    language = detect_language(params.path)
    if language is None:
        return encode_toon({
            "status": "error",
            "error": f"Could not detect language from path: {params.path}",
            "hint": "Ensure the path has a recognized file extension (.py, .rb, .java, .go)",
        })

    # Get adapter for the language
    adapter = get_adapter(language)
    if adapter is None:
        return encode_toon({
            "status": "error",
            "error": f"No backend available for language: {language}",
            "hint": f"Install the {language} refactoring backend",
        })

    # Validate depth parameter
    valid_depths = ["file", "class", "method"]
    if params.depth not in valid_depths:
        return encode_toon({
            "status": "error",
            "error": f"Invalid depth: {params.depth}",
            "valid_depths": valid_depths,
        })

    # Get structure
    result = await adapter.inspect_structure(
        path=params.path,
        depth=params.depth,
    )

    # Format response
    response: dict[str, Any] = {
        "structure": {
            "path": result.path,
            "language": result.language,
            "total_lines": result.total_lines,
        }
    }

    if result.classes:
        response["classes"] = [
            {
                "name": c.name,
                "line": c.line,
                "methods": c.methods,
                "fields": c.fields,
            }
            for c in result.classes
        ]

    if result.methods and params.depth == "method":
        response["methods"] = [
            {
                "class": m.class_name or "",
                "name": m.name,
                "line": m.line,
                "params": m.params,
                "lines": m.lines,
            }
            for m in result.methods
        ]

    return encode_toon(response)
