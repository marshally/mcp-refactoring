# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client                              │
│                  (Claude Desktop, VS Code, etc.)                │
└─────────────────────────────────────────────────────────────────┘
                                │
                          stdio transport
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      mcp-refactoring                            │
│                     (Python/FastMCP)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MCP Tools Layer                        │  │
│  │  • list_refactorings    • analyze_code                   │  │
│  │  • preview_refactoring  • apply_refactoring              │  │
│  │  • inspect_structure                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Adapter Layer                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │  │
│  │  │   Python    │ │    Ruby     │ │    Java     │  ...    │  │
│  │  │   Adapter   │ │   Adapter   │ │   Adapter   │         │  │
│  │  │ (hardcoded) │ │  (future)   │ │  (future)   │         │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                    subprocess (CLI invocation)
                                │
                                ▼
                    ┌───────────────────┐
                    │    molting-cli    │
                    │     (Python)      │
                    └───────────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP Transport | stdio only | Local file operations; simplicity |
| Implementation Language | Python | Consistent with molting-cli; FastMCP SDK |
| Backend Communication | Subprocess + TOON output | Language-agnostic; token-efficient |
| Tool Granularity | Introspection + single dispatch | Lean context; LLMs know Fowler catalog |
| Target Syntax | Language-native conventions | Familiar to each ecosystem |
| Safety Default | Dry-run (preview) | Explicit apply required |
| Plugin Discovery | Runtime detection | Check if CLI exists via `shutil.which()` |
| Configuration | TOML + env vars | Standard, overridable |

## Adapter Pattern

Each language backend is wrapped by a hardcoded adapter class:

```python
class BackendAdapter(ABC):
    @property
    def language(self) -> str: ...
    @property
    def cli_command(self) -> str: ...

    def is_available(self) -> bool: ...
    def list_refactorings(self) -> list[RefactoringSpec]: ...
    def build_command(self, refactoring, target, params, preview) -> list[str]: ...
    async def preview_refactoring(self, ...) -> PreviewResult: ...
    async def apply_refactoring(self, ...) -> RefactoringResult: ...
    async def inspect_structure(self, ...) -> StructureInfo: ...
    def supports_analysis(self) -> bool: ...
    async def analyze_code(self, ...) -> AnalysisResult: ...
```

Adding a new language:
1. Create adapter class in `adapters/{lang}.py`
2. Register in `adapters/registry.py`
3. Add config defaults in `config/schema.py`
