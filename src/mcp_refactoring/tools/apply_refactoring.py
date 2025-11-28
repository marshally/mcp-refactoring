"""Tool for applying refactorings to the codebase."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from mcp_refactoring.adapters import get_adapter
from mcp_refactoring.utils import encode_toon, detect_language


class ApplyRefactoringInput(BaseModel):
    """Input for applying a refactoring."""

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


async def apply_refactoring(params: ApplyRefactoringInput) -> str:
    """Apply a refactoring to the codebase.

    This actually modifies files. Use preview_refactoring first to see
    what changes will be made.

    Args:
        params: Input parameters including refactoring name, target, and options

    Returns:
        TOON-formatted string with results of the applied refactoring
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

    # Execute the refactoring
    result = await adapter.apply_refactoring(
        refactoring=params.refactoring,
        target=params.target,
        params=params.params,
    )

    # Format response
    response: dict[str, Any] = {
        "result": {
            "refactoring": result.refactoring,
            "target": params.target,
            "status": result.status,
            "files_modified": result.files_modified,
        }
    }

    if result.error:
        response["result"]["error"] = result.error

    if result.files:
        response["files"] = [
            {
                "path": f.path,
                "action": f.action,
            }
            for f in result.files
        ]

    return encode_toon(response)
