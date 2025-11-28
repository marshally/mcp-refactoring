"""Tool for listing available refactorings."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from mcp_refactoring.adapters import get_adapter, get_available_adapters
from mcp_refactoring.models import RefactoringCategory
from mcp_refactoring.utils import encode_toon


class ListRefactoringsInput(BaseModel):
    """Input for listing refactorings."""

    model_config = ConfigDict(str_strip_whitespace=True)

    language: str | None = Field(
        default=None,
        description="Filter by language (e.g., 'python'). If not specified, returns all.",
    )
    category: str | None = Field(
        default=None,
        description="Filter by Fowler category (e.g., 'composing_methods')",
    )


async def list_refactorings(params: ListRefactoringsInput) -> str:
    """List available refactorings with their parameter contracts.

    Returns the catalog of available refactorings from all enabled backends,
    optionally filtered by language and/or category.

    Args:
        params: Input parameters for filtering

    Returns:
        TOON-formatted string with refactoring specifications
    """
    # Get adapters based on language filter
    if params.language:
        adapter = get_adapter(params.language)
        if adapter is None:
            return encode_toon({
                "error": f"Language '{params.language}' not available",
                "available_languages": list(get_available_adapters().keys()),
            })
        adapters = {params.language: adapter}
    else:
        adapters = get_available_adapters()

    if not adapters:
        return encode_toon({
            "error": "No language backends available",
            "hint": "Install molting-cli for Python support: pip install molting-cli",
        })

    # Collect refactorings from all adapters
    all_refactorings: list[dict[str, Any]] = []

    for language, adapter in adapters.items():
        for spec in adapter.list_refactorings():
            # Apply category filter
            if params.category:
                try:
                    filter_category = RefactoringCategory(params.category)
                    if spec.category != filter_category:
                        continue
                except ValueError:
                    return encode_toon({
                        "error": f"Invalid category: '{params.category}'",
                        "valid_categories": [c.value for c in RefactoringCategory],
                    })

            # Format parameters as comma-separated string
            param_names = ",".join(p.name for p in spec.params if p.required)
            optional_params = [p.name for p in spec.params if not p.required]
            if optional_params:
                param_names += f" [optional: {','.join(optional_params)}]"

            all_refactorings.append({
                "name": spec.name,
                "language": language,
                "category": spec.category.value,
                "params": param_names,
                "description": spec.description,
            })

    # Build response
    response: dict[str, Any] = {
        "total": len(all_refactorings),
        "languages": list(adapters.keys()),
    }

    if params.category:
        response["filtered_by_category"] = params.category

    response["refactorings"] = all_refactorings

    return encode_toon(response)
