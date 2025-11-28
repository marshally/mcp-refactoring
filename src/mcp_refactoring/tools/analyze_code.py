"""Tool for analyzing code for smells and suggesting refactorings."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from mcp_refactoring.adapters import get_adapter
from mcp_refactoring.utils import encode_toon, detect_language


class AnalyzeCodeInput(BaseModel):
    """Input for analyzing code."""

    model_config = ConfigDict(str_strip_whitespace=True)

    path: str = Field(
        ...,
        description="File or directory path to analyze (e.g., 'src/order.py')",
        min_length=1,
    )
    smells: list[str] | None = Field(
        default=None,
        description="Optional list of smell types to check for (e.g., ['long-method', 'large-class'])",
    )


async def analyze_code(params: AnalyzeCodeInput) -> str:
    """Analyze code for smells and suggest refactorings.

    Detects code smells like long methods, large classes, feature envy,
    and suggests appropriate refactorings to address them.

    Note: This feature requires backend support. Returns backend_supported: false
    for backends that don't implement analysis yet.

    Args:
        params: Input parameters including path and optional smell filter

    Returns:
        TOON-formatted string with analysis results
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

    # Check if analysis is supported
    if not adapter.supports_analysis():
        return encode_toon({
            "analysis": {
                "path": params.path,
                "language": language,
                "backend_supported": False,
            },
            "smells": [],
            "note": "Code smell analysis is not yet implemented for this backend. "
                    "This feature will be available in a future release.",
        })

    # Run analysis
    result = await adapter.analyze_code(
        path=params.path,
        smells=params.smells,
    )

    # Format response
    response: dict[str, Any] = {
        "analysis": {
            "path": result.path,
            "language": result.language,
            "backend_supported": result.backend_supported,
        }
    }

    if result.smells:
        response["smells"] = [
            {
                "type": s.smell_type,
                "location": s.location,
                "severity": s.severity.value,
                "suggested_refactoring": s.suggested_refactoring,
                "details": s.details,
            }
            for s in result.smells
        ]
    else:
        response["smells"] = []

    return encode_toon(response)
