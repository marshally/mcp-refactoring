"""Models for refactoring operations."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RefactoringCategory(str, Enum):
    """Categories of refactorings from Martin Fowler's catalog."""

    COMPOSING_METHODS = "composing_methods"
    MOVING_FEATURES = "moving_features"
    ORGANIZING_DATA = "organizing_data"
    SIMPLIFYING_CONDITIONALS = "simplifying_conditionals"
    SIMPLIFYING_METHOD_CALLS = "simplifying_method_calls"
    DEALING_WITH_GENERALIZATION = "dealing_with_generalization"


class RefactoringParam(BaseModel):
    """Definition of a refactoring parameter."""

    name: str = Field(..., description="Parameter name")
    param_type: str = Field(..., description="Parameter type (string, int, bool, etc.)")
    required: bool = Field(default=True, description="Whether the parameter is required")
    description: str = Field(..., description="Description of the parameter")
    default: Any | None = Field(default=None, description="Default value if not required")


class RefactoringSpec(BaseModel):
    """Specification of a refactoring operation."""

    name: str = Field(..., description="Refactoring name (kebab-case)")
    category: RefactoringCategory = Field(..., description="Fowler category")
    description: str = Field(..., description="Brief description of the refactoring")
    params: list[RefactoringParam] = Field(
        default_factory=list, description="Parameters for this refactoring"
    )
    supports_preview: bool = Field(
        default=True, description="Whether this refactoring supports dry-run preview"
    )
    multi_file: bool = Field(
        default=False, description="Whether this refactoring can affect multiple files"
    )


class FileChange(BaseModel):
    """A change to a single file."""

    path: str = Field(..., description="Path to the file")
    action: str = Field(..., description="Action performed: 'modified', 'created', 'deleted'")
    diff: str | None = Field(default=None, description="Unified diff of the change")


class PreviewResult(BaseModel):
    """Result of previewing a refactoring (dry-run)."""

    refactoring: str = Field(..., description="Name of the refactoring")
    status: str = Field(..., description="Status: 'success' or 'error'")
    files_affected: int = Field(default=0, description="Number of files affected")
    changes: list[FileChange] = Field(default_factory=list, description="List of file changes")
    error: str | None = Field(default=None, description="Error message if status is 'error'")


class RefactoringResult(BaseModel):
    """Result of applying a refactoring."""

    refactoring: str = Field(..., description="Name of the refactoring")
    status: str = Field(..., description="Status: 'success' or 'error'")
    files_modified: int = Field(default=0, description="Number of files modified")
    files: list[FileChange] = Field(default_factory=list, description="List of modified files")
    error: str | None = Field(default=None, description="Error message if status is 'error'")
