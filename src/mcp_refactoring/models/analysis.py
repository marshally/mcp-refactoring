"""Models for code analysis operations."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SmellSeverity(str, Enum):
    """Severity level of a code smell."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CodeSmell(BaseModel):
    """A detected code smell."""

    smell_type: str = Field(..., description="Type of smell (e.g., 'long-method', 'feature-envy')")
    location: str = Field(..., description="Location in target syntax (e.g., 'Order::calculate')")
    severity: SmellSeverity = Field(..., description="Severity level")
    suggested_refactoring: str = Field(
        ..., description="Suggested refactoring to address this smell"
    )
    details: str = Field(..., description="Human-readable details about the smell")


class AnalysisResult(BaseModel):
    """Result of analyzing code for smells."""

    path: str = Field(..., description="Path that was analyzed")
    language: str = Field(..., description="Detected language")
    backend_supported: bool = Field(
        ..., description="Whether the backend supports analysis"
    )
    smells: list[CodeSmell] = Field(default_factory=list, description="Detected code smells")


class MethodInfo(BaseModel):
    """Information about a method or function."""

    name: str = Field(..., description="Method name")
    class_name: str | None = Field(default=None, description="Containing class name, if any")
    line: int = Field(..., description="Starting line number")
    end_line: int | None = Field(default=None, description="Ending line number")
    params: int = Field(default=0, description="Number of parameters")
    lines: int = Field(default=0, description="Number of lines in the method")


class ClassInfo(BaseModel):
    """Information about a class."""

    name: str = Field(..., description="Class name")
    line: int = Field(..., description="Starting line number")
    end_line: int | None = Field(default=None, description="Ending line number")
    methods: int = Field(default=0, description="Number of methods")
    fields: int = Field(default=0, description="Number of fields/attributes")


class StructureInfo(BaseModel):
    """Structural information about code."""

    path: str = Field(..., description="Path that was inspected")
    language: str = Field(..., description="Detected language")
    classes: list[ClassInfo] = Field(default_factory=list, description="Classes in the file")
    methods: list[MethodInfo] = Field(default_factory=list, description="Methods/functions")
    total_lines: int = Field(default=0, description="Total lines in the file")
