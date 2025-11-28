"""Tool for previewing refactorings without applying them."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from mcp_refactoring.adapters import get_adapter
from mcp_refactoring.utils import encode_toon, detect_language


class PreviewRefactoringInput(BaseModel):
    """Input for previewing a refactoring."""

    model_config = ConfigDict(str_strip_whitespace=True)

    refactoring: str = Field(
        ...,
        description="Name of the refactoring (e.g., 'extract-method')",
        min_length=1,
    )
    target: str = Field(
        ...,
        description="Target specification in language-native format (e.g., 'src/order.py::Order::calculate#L10-L15')",
        min_length=1,
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Refactoring-specific parameters (e.g., {'name': 'calculate_tax'})",
    )


async def preview_refactoring(params: PreviewRefactoringInput) -> str:
    """Preview what changes a refactoring would make without applying them.

    This is a dry-run mode that shows the diff of what would change,
    without actually modifying any files.

    Args:
        params: Input parameters including refactoring name, target, and options

    Returns:
        TOON-formatted string with preview results including diff
    """
    # Detect language from target path
    language = detect_language(params.target)
    if language is None:
        return encode_toon({
            "status": "error",
            "error": f"Could not detect language from target: {params.target}",
            "hint": "Ensure the target path has a recognized file extension (.py, .rb, .java, .go)",
        })

    # Get adapter for the language
    adapter = get_adapter(language)
    if adapter is None:
        return encode_toon({
            "status": "error",
            "error": f"No backend available for language: {language}",
            "hint": f"Install the {language} refactoring backend",
        })

    # Verify the refactoring is supported
    supported_names = {spec.name for spec in adapter.list_refactorings()}
    if params.refactoring not in supported_names:
        return encode_toon({
            "status": "error",
            "error": f"Unknown refactoring: {params.refactoring}",
            "hint": "Use list_refactorings to see available refactorings",
            "available": sorted(supported_names),
        })

    # Execute preview
    result = await adapter.preview_refactoring(
        refactoring=params.refactoring,
        target=params.target,
        params=params.params,
    )

    # Format response
    response: dict[str, Any] = {
        "preview": {
            "refactoring": result.refactoring,
            "target": params.target,
            "status": result.status,
            "files_affected": result.files_affected,
        }
    }

    if result.error:
        response["preview"]["error"] = result.error

    if result.changes:
        response["changes"] = [
            {
                "file": change.path,
                "action": change.action,
                "diff": change.diff or "",
            }
            for change in result.changes
        ]

    return encode_toon(response)
