"""Python backend adapter for molting-cli."""

from __future__ import annotations

import shutil
from typing import Any

from mcp_refactoring.adapters.base import BackendAdapter
from mcp_refactoring.config import get_config
from mcp_refactoring.models import (
    RefactoringCategory,
    RefactoringParam,
    RefactoringSpec,
    PreviewResult,
    RefactoringResult,
    FileChange,
    StructureInfo,
    ClassInfo,
    MethodInfo,
)
from mcp_refactoring.utils import run_command


class PythonAdapter(BackendAdapter):
    """Adapter for the molting-cli Python refactoring tool."""

    def __init__(self, command: str | None = None) -> None:
        """Initialize the adapter.

        Args:
            command: Override for the CLI command (uses config default if None)
        """
        if command is None:
            config = get_config()
            command = config.backends.get("python", {}).command
        self._command = command or "molting"

    @property
    def language(self) -> str:
        return "python"

    @property
    def cli_command(self) -> str:
        return self._command

    def is_available(self) -> bool:
        return shutil.which(self._command) is not None

    def list_refactorings(self) -> list[RefactoringSpec]:
        """Return the catalog of supported Python refactorings."""
        return PYTHON_REFACTORINGS

    def build_command(
        self,
        refactoring: str,
        target: str,
        params: dict[str, Any],
        preview: bool = True,
    ) -> list[str]:
        cmd = [self._command, refactoring, target]

        # Add refactoring-specific params
        for key, value in params.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key.replace('_', '-')}")
            elif isinstance(value, list):
                # Handle list params (e.g., --fields a,b,c)
                cmd.extend([f"--{key.replace('_', '-')}", ",".join(str(v) for v in value)])
            else:
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        if preview:
            cmd.append("--dry-run")

        return cmd

    async def preview_refactoring(
        self,
        refactoring: str,
        target: str,
        params: dict[str, Any],
    ) -> PreviewResult:
        cmd = self.build_command(refactoring, target, params, preview=True)

        result = await run_command(cmd)

        if not result.success:
            return PreviewResult(
                refactoring=refactoring,
                status="error",
                error=result.stderr or f"Command failed with exit code {result.returncode}",
            )

        # Parse the output to extract changes
        # Note: This will need to be updated when molting-cli adds --output=toon
        changes = self._parse_diff_output(result.stdout, target)

        return PreviewResult(
            refactoring=refactoring,
            status="success",
            files_affected=len(changes),
            changes=changes,
        )

    async def apply_refactoring(
        self,
        refactoring: str,
        target: str,
        params: dict[str, Any],
    ) -> RefactoringResult:
        cmd = self.build_command(refactoring, target, params, preview=False)

        result = await run_command(cmd)

        if not result.success:
            return RefactoringResult(
                refactoring=refactoring,
                status="error",
                error=result.stderr or f"Command failed with exit code {result.returncode}",
            )

        # Extract the file path from target
        file_path = target.split("::")[0].split("#")[0]

        return RefactoringResult(
            refactoring=refactoring,
            status="success",
            files_modified=1,
            files=[FileChange(path=file_path, action="modified")],
        )

    async def inspect_structure(
        self,
        path: str,
        depth: str = "class",
    ) -> StructureInfo:
        """Inspect Python code structure using AST.

        Note: This is a basic implementation. A full implementation would
        use molting-cli's inspect command once available.
        """
        # For now, return a basic structure
        # TODO: Implement using molting inspect command or Python AST
        return StructureInfo(
            path=path,
            language="python",
            classes=[],
            methods=[],
            total_lines=0,
        )

    def _parse_diff_output(self, output: str, target: str) -> list[FileChange]:
        """Parse the CLI output to extract file changes.

        Note: This is a placeholder. Once molting-cli supports --output=toon,
        this will parse the TOON output format.
        """
        file_path = target.split("::")[0].split("#")[0]

        # For now, just indicate the file was affected
        if output.strip():
            return [
                FileChange(
                    path=file_path,
                    action="modified",
                    diff=output,
                )
            ]
        return []


# Catalog of Python refactorings supported by molting-cli
PYTHON_REFACTORINGS: list[RefactoringSpec] = [
    # Composing Methods
    RefactoringSpec(
        name="extract-method",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Extract code block into new method",
        params=[
            RefactoringParam(name="target", param_type="string", description="Target with line range (e.g., file.py::Class::method#L10-L15)"),
            RefactoringParam(name="name", param_type="string", description="Name for the new method"),
        ],
    ),
    RefactoringSpec(
        name="extract-function",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Extract code into module-level function",
        params=[
            RefactoringParam(name="target", param_type="string", description="Target with line range"),
            RefactoringParam(name="name", param_type="string", description="Name for the new function"),
        ],
    ),
    RefactoringSpec(
        name="inline-method",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Replace method calls with method body",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to inline (e.g., file.py::Class::method)"),
        ],
    ),
    RefactoringSpec(
        name="inline-temp",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Replace temporary variable with its value",
        params=[
            RefactoringParam(name="target", param_type="string", description="Variable to inline (e.g., file.py::Class::method::var_name)"),
        ],
    ),
    RefactoringSpec(
        name="replace-temp-with-query",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Replace temp variable with method call",
        params=[
            RefactoringParam(name="target", param_type="string", description="Variable to replace"),
            RefactoringParam(name="name", param_type="string", description="Name for the query method"),
        ],
    ),
    RefactoringSpec(
        name="introduce-explaining-variable",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Extract expression into named variable",
        params=[
            RefactoringParam(name="target", param_type="string", description="Target file or method"),
            RefactoringParam(name="expression", param_type="string", description="Expression to extract", required=False),
            RefactoringParam(name="name", param_type="string", description="Name for the new variable"),
            RefactoringParam(name="in_", param_type="string", description="Method to search in", required=False),
            RefactoringParam(name="replace_all", param_type="bool", description="Replace all occurrences", required=False, default=False),
        ],
    ),
    RefactoringSpec(
        name="split-temporary-variable",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Separate variables for different purposes",
        params=[
            RefactoringParam(name="target", param_type="string", description="Variable to split"),
        ],
    ),
    RefactoringSpec(
        name="remove-assignments-to-parameters",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Use temp variable instead of parameter modification",
        params=[
            RefactoringParam(name="target", param_type="string", description="Parameter to protect"),
        ],
    ),
    RefactoringSpec(
        name="replace-method-with-method-object",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Convert method into its own object",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to extract"),
            RefactoringParam(name="name", param_type="string", description="Name for the new class"),
        ],
    ),
    RefactoringSpec(
        name="substitute-algorithm",
        category=RefactoringCategory.COMPOSING_METHODS,
        description="Replace algorithm with clearer implementation",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method containing algorithm"),
        ],
    ),

    # Moving Features Between Objects
    RefactoringSpec(
        name="move-method",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Move method between classes",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to move"),
            RefactoringParam(name="to", param_type="string", description="Destination class name"),
        ],
        multi_file=True,
    ),
    RefactoringSpec(
        name="move-field",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Move field between classes",
        params=[
            RefactoringParam(name="target", param_type="string", description="Field to move"),
            RefactoringParam(name="to", param_type="string", description="Destination class name"),
        ],
        multi_file=True,
    ),
    RefactoringSpec(
        name="extract-class",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Split class into two classes",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class to split"),
            RefactoringParam(name="name", param_type="string", description="Name for new class"),
            RefactoringParam(name="fields", param_type="list", description="Fields to move"),
            RefactoringParam(name="methods", param_type="list", description="Methods to move", required=False),
        ],
    ),
    RefactoringSpec(
        name="inline-class",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Merge class into another class",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class to inline"),
            RefactoringParam(name="into", param_type="string", description="Target class to merge into"),
        ],
    ),
    RefactoringSpec(
        name="hide-delegate",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Create delegating methods to hide delegation",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class with delegate"),
            RefactoringParam(name="delegate", param_type="string", description="Delegate field name"),
        ],
    ),
    RefactoringSpec(
        name="remove-middle-man",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Call delegate directly instead of through wrapper",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class with delegating methods"),
        ],
    ),
    RefactoringSpec(
        name="introduce-foreign-method",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Add method to class you can't modify",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class to extend"),
            RefactoringParam(name="name", param_type="string", description="Name for new method"),
        ],
    ),
    RefactoringSpec(
        name="introduce-local-extension",
        category=RefactoringCategory.MOVING_FEATURES,
        description="Create subclass or wrapper for extensions",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class to extend"),
            RefactoringParam(name="name", param_type="string", description="Name for extension class"),
        ],
    ),

    # Simplifying Conditional Expressions
    RefactoringSpec(
        name="decompose-conditional",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Extract condition and branches into methods",
        params=[
            RefactoringParam(name="target", param_type="string", description="Conditional to decompose"),
        ],
    ),
    RefactoringSpec(
        name="consolidate-conditional-expression",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Combine conditions with same result",
        params=[
            RefactoringParam(name="target", param_type="string", description="Conditionals to consolidate"),
        ],
    ),
    RefactoringSpec(
        name="consolidate-duplicate-conditional-fragments",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Move common code outside conditionals",
        params=[
            RefactoringParam(name="target", param_type="string", description="Conditional with duplicate code"),
        ],
    ),
    RefactoringSpec(
        name="remove-control-flag",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Use break/return instead of control flag",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method with control flag"),
        ],
    ),
    RefactoringSpec(
        name="replace-nested-conditional-with-guard-clauses",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Use guard clauses instead of nested conditionals",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method with nested conditionals"),
        ],
    ),
    RefactoringSpec(
        name="replace-conditional-with-polymorphism",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Use polymorphic dispatch instead of conditionals",
        params=[
            RefactoringParam(name="target", param_type="string", description="Conditional to replace"),
        ],
    ),
    RefactoringSpec(
        name="introduce-null-object",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Replace null checks with null object pattern",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class needing null object"),
            RefactoringParam(name="name", param_type="string", description="Name for null object class"),
        ],
    ),
    RefactoringSpec(
        name="introduce-assertion",
        category=RefactoringCategory.SIMPLIFYING_CONDITIONALS,
        description="Make assumptions explicit with assertions",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method needing assertion"),
        ],
    ),

    # Simplifying Method Calls
    RefactoringSpec(
        name="rename-method",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Rename a method",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to rename"),
            RefactoringParam(name="new_name", param_type="string", description="New method name"),
        ],
    ),
    RefactoringSpec(
        name="add-parameter",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Add a parameter to a method",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to modify"),
            RefactoringParam(name="name", param_type="string", description="Parameter name"),
            RefactoringParam(name="param_type", param_type="string", description="Parameter type", required=False),
            RefactoringParam(name="default", param_type="string", description="Default value", required=False),
        ],
    ),
    RefactoringSpec(
        name="remove-parameter",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Remove a parameter from a method",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to modify"),
            RefactoringParam(name="name", param_type="string", description="Parameter name to remove"),
        ],
    ),
    RefactoringSpec(
        name="separate-query-from-modifier",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Split method into query and modifier",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to split"),
        ],
    ),
    RefactoringSpec(
        name="parameterize-method",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Combine similar methods with parameter",
        params=[
            RefactoringParam(name="target", param_type="string", description="Methods to combine"),
        ],
    ),
    RefactoringSpec(
        name="replace-parameter-with-explicit-methods",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Create separate methods for parameter values",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to split"),
            RefactoringParam(name="parameter", param_type="string", description="Parameter to eliminate"),
        ],
    ),
    RefactoringSpec(
        name="preserve-whole-object",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Pass entire object instead of extracted values",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to modify"),
        ],
    ),
    RefactoringSpec(
        name="replace-parameter-with-method-call",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Call method internally instead of receiving parameter",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to modify"),
            RefactoringParam(name="parameter", param_type="string", description="Parameter to replace"),
        ],
    ),
    RefactoringSpec(
        name="introduce-parameter-object",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Group parameters into object",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method with many parameters"),
            RefactoringParam(name="name", param_type="string", description="Name for parameter object class"),
            RefactoringParam(name="parameters", param_type="list", description="Parameters to group"),
        ],
    ),
    RefactoringSpec(
        name="remove-setting-method",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Remove setter for field set in constructor",
        params=[
            RefactoringParam(name="target", param_type="string", description="Setter to remove"),
        ],
    ),
    RefactoringSpec(
        name="hide-method",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Make method private",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to hide"),
        ],
    ),
    RefactoringSpec(
        name="replace-constructor-with-factory-function",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Use factory function instead of constructor",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class with constructor"),
            RefactoringParam(name="name", param_type="string", description="Factory function name"),
        ],
    ),
    RefactoringSpec(
        name="replace-error-code-with-exception",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Throw exception instead of returning error code",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method returning error code"),
        ],
    ),
    RefactoringSpec(
        name="replace-exception-with-test",
        category=RefactoringCategory.SIMPLIFYING_METHOD_CALLS,
        description="Use conditional check instead of exception",
        params=[
            RefactoringParam(name="target", param_type="string", description="Code with exception to replace"),
        ],
    ),

    # Dealing with Generalization
    RefactoringSpec(
        name="pull-up-field",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Move field to superclass",
        params=[
            RefactoringParam(name="target", param_type="string", description="Field to pull up"),
        ],
    ),
    RefactoringSpec(
        name="pull-up-method",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Move method to superclass",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to pull up"),
        ],
    ),
    RefactoringSpec(
        name="pull-up-constructor-body",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Move constructor logic to superclass",
        params=[
            RefactoringParam(name="target", param_type="string", description="Subclass constructor"),
        ],
    ),
    RefactoringSpec(
        name="push-down-method",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Move method to subclass",
        params=[
            RefactoringParam(name="target", param_type="string", description="Method to push down"),
            RefactoringParam(name="to", param_type="string", description="Target subclass"),
        ],
    ),
    RefactoringSpec(
        name="push-down-field",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Move field to subclass",
        params=[
            RefactoringParam(name="target", param_type="string", description="Field to push down"),
            RefactoringParam(name="to", param_type="string", description="Target subclass"),
        ],
    ),
    RefactoringSpec(
        name="extract-subclass",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Create subclass for subset of features",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class to extract from"),
            RefactoringParam(name="name", param_type="string", description="Name for new subclass"),
        ],
    ),
    RefactoringSpec(
        name="extract-superclass",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Create superclass from common features",
        params=[
            RefactoringParam(name="target", param_type="string", description="Classes to extract from"),
            RefactoringParam(name="name", param_type="string", description="Name for new superclass"),
        ],
    ),
    RefactoringSpec(
        name="extract-interface",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Create interface for common methods",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class to extract from"),
            RefactoringParam(name="name", param_type="string", description="Name for new interface"),
        ],
    ),
    RefactoringSpec(
        name="collapse-hierarchy",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Merge subclass into superclass",
        params=[
            RefactoringParam(name="target", param_type="string", description="Subclass to collapse"),
        ],
    ),
    RefactoringSpec(
        name="form-template-method",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Extract algorithm to superclass with varying steps",
        params=[
            RefactoringParam(name="target", param_type="string", description="Methods to templatize"),
        ],
    ),
    RefactoringSpec(
        name="replace-inheritance-with-delegation",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Use composition instead of inheritance",
        params=[
            RefactoringParam(name="target", param_type="string", description="Subclass to convert"),
        ],
    ),
    RefactoringSpec(
        name="replace-delegation-with-inheritance",
        category=RefactoringCategory.DEALING_WITH_GENERALIZATION,
        description="Use inheritance instead of delegation",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class using delegation"),
        ],
    ),

    # Organizing Data
    RefactoringSpec(
        name="self-encapsulate-field",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Create getter/setter for field access",
        params=[
            RefactoringParam(name="target", param_type="string", description="Field to encapsulate"),
        ],
    ),
    RefactoringSpec(
        name="replace-data-value-with-object",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Convert data item into object",
        params=[
            RefactoringParam(name="target", param_type="string", description="Field to convert"),
            RefactoringParam(name="name", param_type="string", description="Name for new class"),
        ],
    ),
    RefactoringSpec(
        name="change-value-to-reference",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Convert value object to reference",
        params=[
            RefactoringParam(name="target", param_type="string", description="Value class to convert"),
        ],
    ),
    RefactoringSpec(
        name="change-reference-to-value",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Convert reference to value object",
        params=[
            RefactoringParam(name="target", param_type="string", description="Reference class to convert"),
        ],
    ),
    RefactoringSpec(
        name="replace-array-with-object",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Replace array with object",
        params=[
            RefactoringParam(name="target", param_type="string", description="Array to replace"),
            RefactoringParam(name="name", param_type="string", description="Name for new class"),
        ],
    ),
    RefactoringSpec(
        name="duplicate-observed-data",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Copy data to domain object",
        params=[
            RefactoringParam(name="target", param_type="string", description="Data to duplicate"),
        ],
    ),
    RefactoringSpec(
        name="change-unidirectional-to-bidirectional",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Add back pointers to association",
        params=[
            RefactoringParam(name="target", param_type="string", description="Association to modify"),
        ],
    ),
    RefactoringSpec(
        name="change-bidirectional-to-unidirectional",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Remove back pointers from association",
        params=[
            RefactoringParam(name="target", param_type="string", description="Association to modify"),
        ],
    ),
    RefactoringSpec(
        name="replace-magic-number-with-symbolic-constant",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Create named constant for magic number",
        params=[
            RefactoringParam(name="target", param_type="string", description="Location of magic number"),
            RefactoringParam(name="name", param_type="string", description="Name for constant"),
            RefactoringParam(name="value", param_type="string", description="Value to replace"),
        ],
    ),
    RefactoringSpec(
        name="encapsulate-field",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Add getter/setter accessors for public field",
        params=[
            RefactoringParam(name="target", param_type="string", description="Field to encapsulate"),
        ],
    ),
    RefactoringSpec(
        name="encapsulate-collection",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Add proper accessors for collection field",
        params=[
            RefactoringParam(name="target", param_type="string", description="Collection field to encapsulate"),
        ],
    ),
    RefactoringSpec(
        name="replace-type-code-with-class",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Replace type code with class",
        params=[
            RefactoringParam(name="target", param_type="string", description="Type code to replace"),
            RefactoringParam(name="name", param_type="string", description="Name for new class"),
        ],
    ),
    RefactoringSpec(
        name="replace-type-code-with-subclasses",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Use inheritance to replace type code",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class with type code"),
        ],
    ),
    RefactoringSpec(
        name="replace-type-code-with-state-strategy",
        category=RefactoringCategory.ORGANIZING_DATA,
        description="Use State/Strategy pattern for type code",
        params=[
            RefactoringParam(name="target", param_type="string", description="Class with type code"),
        ],
    ),
]
