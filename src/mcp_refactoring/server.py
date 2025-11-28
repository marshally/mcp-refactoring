"""MCP server for refactoring operations.

This server exposes Martin Fowler's refactoring catalog to LLMs through
a pluggable, language-agnostic architecture.
"""

from typing import Any, Optional, List

from mcp.server.fastmcp import FastMCP

from mcp_refactoring.tools.list_refactorings import (
    ListRefactoringsInput,
    list_refactorings as _list_refactorings,
)
from mcp_refactoring.tools.preview_refactoring import (
    PreviewRefactoringInput,
    preview_refactoring as _preview_refactoring,
)
from mcp_refactoring.tools.apply_refactoring import (
    ApplyRefactoringInput,
    apply_refactoring as _apply_refactoring,
)
from mcp_refactoring.tools.inspect_structure import (
    InspectStructureInput,
    inspect_structure as _inspect_structure,
)
from mcp_refactoring.tools.analyze_code import (
    AnalyzeCodeInput,
    analyze_code as _analyze_code,
)


# Initialize the MCP server
mcp = FastMCP("refactoring_mcp")


@mcp.tool(
    name="list_refactorings",
    annotations={
        "title": "List Available Refactorings",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def list_refactorings(
    language: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """List available refactorings with their parameter contracts.

    Returns the catalog of available refactorings from all enabled backends,
    optionally filtered by language and/or category.

    Args:
        language: Filter by language (e.g., 'python'). If not specified, returns all.
        category: Filter by Fowler category (e.g., 'composing_methods')

    Returns:
        TOON-formatted string containing refactoring specifications.

    Categories:
        - composing_methods: Extract/inline methods, variables
        - moving_features: Move methods/fields between classes
        - organizing_data: Encapsulation, type codes
        - simplifying_conditionals: Guard clauses, polymorphism
        - simplifying_method_calls: Rename, add/remove parameters
        - dealing_with_generalization: Pull up/push down, inheritance
    """
    params = ListRefactoringsInput(language=language, category=category)
    return await _list_refactorings(params)


@mcp.tool(
    name="preview_refactoring",
    annotations={
        "title": "Preview Refactoring Changes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def preview_refactoring(
    refactoring: str,
    target: str,
    params: Optional[dict] = None,
) -> str:
    """Preview what changes a refactoring would make without applying them.

    This is a dry-run mode that shows the diff of what would change,
    without actually modifying any files. Always preview before applying.

    Args:
        refactoring: Name of the refactoring (e.g., 'extract-method')
        target: Target in language-native format (e.g., 'src/order.py::Order::calculate#L10-L15')
        params: Refactoring-specific parameters (e.g., {'name': 'calculate_tax'})

    Returns:
        TOON-formatted string with preview results including diff.

    Example:
        preview_refactoring(
            refactoring="extract-method",
            target="src/order.py::Order::calculate#L10-L15",
            params={"name": "calculate_tax"}
        )
    """
    input_params = PreviewRefactoringInput(
        refactoring=refactoring,
        target=target,
        params=params or {},
    )
    return await _preview_refactoring(input_params)


@mcp.tool(
    name="apply_refactoring",
    annotations={
        "title": "Apply Refactoring",
        "readOnlyHint": False,
        "destructiveHint": False,  # Reversible via git
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def apply_refactoring(
    refactoring: str,
    target: str,
    params: Optional[dict] = None,
) -> str:
    """Apply a refactoring to the codebase.

    This actually modifies files. Use preview_refactoring first to see
    what changes will be made. Changes can be reverted with git.

    Args:
        refactoring: Name of the refactoring (e.g., 'extract-method')
        target: Target in language-native format (e.g., 'src/order.py::Order::calculate#L10-L15')
        params: Refactoring-specific parameters

    Returns:
        TOON-formatted string with results of the applied refactoring.

    Example:
        apply_refactoring(
            refactoring="rename-method",
            target="src/order.py::Order::calc_total",
            params={"new_name": "calculate_total"}
        )
    """
    input_params = ApplyRefactoringInput(
        refactoring=refactoring,
        target=target,
        params=params or {},
    )
    return await _apply_refactoring(input_params)


@mcp.tool(
    name="inspect_structure",
    annotations={
        "title": "Inspect Code Structure",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def inspect_structure(
    path: str,
    depth: str = "class",
) -> str:
    """Get structural information about code (classes, methods, line numbers).

    Inspects a file to return information about its structure. Use this
    to understand the code before applying refactorings.

    Args:
        path: File path to inspect (e.g., 'src/order.py')
        depth: Level of detail - 'file', 'class', or 'method' (default: 'class')

    Returns:
        TOON-formatted string with structural information.

    Example:
        inspect_structure(path="src/order.py", depth="method")
    """
    input_params = InspectStructureInput(path=path, depth=depth)
    return await _inspect_structure(input_params)


@mcp.tool(
    name="analyze_code",
    annotations={
        "title": "Analyze Code for Smells",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def analyze_code(
    path: str,
    smells: Optional[List[str]] = None,
) -> str:
    """Analyze code for smells and suggest refactorings.

    Detects code smells like long methods, large classes, feature envy,
    and suggests appropriate refactorings to address them.

    Note: This feature requires backend support. Returns backend_supported: false
    for backends that don't implement analysis yet.

    Args:
        path: File or directory path to analyze
        smells: Optional list of smell types to check for
            (e.g., ['long-method', 'large-class', 'feature-envy'])

    Returns:
        TOON-formatted string with analysis results.

    Supported smell types (when backend supports analysis):
        - long-method: Method exceeds line threshold
        - large-class: Class has too many responsibilities
        - feature-envy: Method uses another class's data excessively
        - data-clumps: Same data items appear together repeatedly
        - primitive-obsession: Overuse of primitives instead of objects
        - duplicate-code: Similar code in multiple locations
    """
    input_params = AnalyzeCodeInput(path=path, smells=smells)
    return await _analyze_code(input_params)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
