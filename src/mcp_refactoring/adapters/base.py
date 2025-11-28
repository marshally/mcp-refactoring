"""Abstract base class for language backend adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mcp_refactoring.models import (
    RefactoringSpec,
    PreviewResult,
    RefactoringResult,
    AnalysisResult,
    StructureInfo,
)


class BackendAdapter(ABC):
    """Abstract base for language backend adapters.

    Each adapter wraps a language-specific refactoring CLI tool and provides
    a consistent interface for the MCP server to use.
    """

    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier: 'python', 'ruby', etc."""
        pass

    @property
    @abstractmethod
    def cli_command(self) -> str:
        """CLI executable name or path."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend CLI is installed and accessible.

        Returns:
            True if the backend is available, False otherwise
        """
        pass

    @abstractmethod
    def list_refactorings(self) -> list[RefactoringSpec]:
        """Return available refactorings with their parameter specs.

        Returns:
            List of refactoring specifications
        """
        pass

    @abstractmethod
    def build_command(
        self,
        refactoring: str,
        target: str,
        params: dict[str, Any],
        preview: bool = True,
    ) -> list[str]:
        """Build CLI command args for a refactoring.

        Args:
            refactoring: Name of the refactoring (e.g., 'extract-method')
            target: Target specification in language-native format
            params: Refactoring-specific parameters
            preview: If True, run in preview/dry-run mode

        Returns:
            List of command arguments
        """
        pass

    @abstractmethod
    async def preview_refactoring(
        self,
        refactoring: str,
        target: str,
        params: dict[str, Any],
    ) -> PreviewResult:
        """Preview a refactoring without applying it.

        Args:
            refactoring: Name of the refactoring
            target: Target specification
            params: Refactoring-specific parameters

        Returns:
            PreviewResult with diff and affected files
        """
        pass

    @abstractmethod
    async def apply_refactoring(
        self,
        refactoring: str,
        target: str,
        params: dict[str, Any],
    ) -> RefactoringResult:
        """Apply a refactoring to the codebase.

        Args:
            refactoring: Name of the refactoring
            target: Target specification
            params: Refactoring-specific parameters

        Returns:
            RefactoringResult with modified files
        """
        pass

    @abstractmethod
    async def inspect_structure(
        self,
        path: str,
        depth: str = "class",
    ) -> StructureInfo:
        """Get structural information about code.

        Args:
            path: File path to inspect
            depth: Level of detail: 'file', 'class', or 'method'

        Returns:
            StructureInfo with classes, methods, etc.
        """
        pass

    def supports_analysis(self) -> bool:
        """Whether this backend supports code smell analysis.

        Returns:
            True if analysis is supported, False otherwise
        """
        return False

    async def analyze_code(
        self,
        path: str,
        smells: list[str] | None = None,
    ) -> AnalysisResult:
        """Analyze code for smells and suggest refactorings.

        Args:
            path: File or directory path to analyze
            smells: Optional list of smell types to check for

        Returns:
            AnalysisResult with detected smells

        Raises:
            NotImplementedError: If analysis is not supported
        """
        return AnalysisResult(
            path=path,
            language=self.language,
            backend_supported=False,
            smells=[],
        )
