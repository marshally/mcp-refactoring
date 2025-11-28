# mcp-refactoring Technical Specification

## Overview

An MCP (Model Context Protocol) server that exposes Martin Fowler's refactoring catalog to LLMs through a pluggable, language-agnostic architecture. The server delegates actual refactoring operations to language-specific backend CLIs (starting with `molting-cli` for Python).

---

## Architecture

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
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                Configuration Layer                        │  │
│  │  • ~/.mcp-refactoring/config.toml                        │  │
│  │  • Environment variable overrides                         │  │
│  │  • Runtime backend detection                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                    subprocess (CLI invocation)
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │  molting-cli  │   │  (ruby-cli)   │   │  (java-cli)   │
    │    Python     │   │    Future     │   │    Future     │
    └───────────────┘   └───────────────┘   └───────────────┘
```

---

## Core Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP Transport | stdio only | Local file operations; simplicity |
| Implementation Language | Python | Consistent with molting-cli; FastMCP SDK |
| Backend Communication | Subprocess + TOON output | Language-agnostic; token-efficient |
| Tool Granularity | Introspection + single dispatch | Lean context; LLMs know Fowler catalog |
| Target Syntax | Language-native conventions | Familiar to each ecosystem |
| Safety Default | Dry-run (preview) | Explicit `--apply` required |
| Analysis | Backend-side (stubbed initially) | Leverages AST knowledge |
| Package Distribution | PyPI, uvx/pipx optimized | Modern isolated installation |
| License | MIT | Permissive, widely compatible |

---

## MCP Tools

### 1. `list_refactorings`

Returns available refactorings with their parameter contracts.

**Parameters:**
```yaml
language: string (optional)  # Filter by language: "python", "ruby", etc.
category: string (optional)  # Filter by Fowler category
```

**Returns (TOON format):**
```
refactorings[N]{name,category,params,description}:
  extract-method,composing_methods,"target,name",Extract code block into new method
  rename-method,simplifying_method_calls,"target,new_name",Rename a method
  move-method,moving_features,"target,to_class",Move method to another class
  ...
```

**Annotations:**
- `readOnlyHint: true`
- `idempotentHint: true`

---

### 2. `preview_refactoring`

Shows what changes a refactoring would make without applying them.

**Parameters:**
```yaml
refactoring: string (required)  # e.g., "extract-method"
target: string (required)       # Language-native target spec
params: object (required)       # Refactoring-specific parameters
```

**Returns (TOON format):**
```
preview:
  refactoring: extract-method
  status: success
  files_affected: 1
changes[1]{file,action,diff}:
  src/order.py,modified,"@@ -10,5 +10,10 @@\n-    total = price * qty\n+    total = self.calculate_total(price, qty)\n..."
```

**Annotations:**
- `readOnlyHint: true`
- `idempotentHint: true`

---

### 3. `apply_refactoring`

Applies a refactoring to the codebase.

**Parameters:**
```yaml
refactoring: string (required)  # e.g., "extract-method"
target: string (required)       # Language-native target spec
params: object (required)       # Refactoring-specific parameters
```

**Returns (TOON format):**
```
result:
  refactoring: extract-method
  status: success
  files_modified: 1
files[1]{path,action}:
  src/order.py,modified
```

**Annotations:**
- `readOnlyHint: false`
- `destructiveHint: false` (reversible via git)
- `idempotentHint: false`

---

### 4. `inspect_structure`

Returns structural information about code (classes, methods, dependencies).

**Parameters:**
```yaml
path: string (required)        # File or directory path
depth: string (optional)       # "file", "class", "method" (default: "class")
```

**Returns (TOON format):**
```
structure:
  path: src/order.py
  language: python
classes[2]{name,line,methods,fields}:
  Order,5,3,2
  OrderItem,45,2,3
methods[5]{class,name,line,params,lines}:
  Order,__init__,6,2,8
  Order,calculate_total,15,0,12
  Order,apply_discount,28,1,6
  ...
```

**Annotations:**
- `readOnlyHint: true`
- `idempotentHint: true`

---

### 5. `analyze_code`

Detects code smells and suggests refactorings.

**Parameters:**
```yaml
path: string (required)        # File or directory path
smells: array (optional)       # Filter: ["long-method", "large-class", ...]
```

**Returns (TOON format):**
```
analysis:
  path: src/order.py
  language: python
  backend_supported: true  # false if backend doesn't have analyze command
smells[N]{type,location,severity,suggested_refactoring,details}:
  long-method,Order::calculate_total,high,extract-method,"45 lines (threshold: 20)"
  feature-envy,Order::format_address,medium,move-method,"Accesses Customer 8 times"
  ...
```

**Annotations:**
- `readOnlyHint: true`
- `idempotentHint: true`

**Note:** Returns `backend_supported: false` with empty smells array for backends that don't implement analysis yet.

---

## Target Specification by Language

Each language backend uses its ecosystem's native conventions:

### Python (molting-cli)
```
# Pytest-style with :: separator
src/order.py::Order::calculate_total        # Method
src/order.py::Order::calculate_total#L10-L15  # Line range within method
src/order.py::Order                         # Class
src/order.py                                # Module
```

### Ruby (future)
```
# RSpec-style with # for instance methods
lib/order.rb#Order#calculate_total          # Instance method
lib/order.rb#Order.from_hash                # Class method
lib/order.rb#Order                          # Class
```

### Java (future)
```
# Fully qualified with . separator
src/main/java/Order.java:Order.calculateTotal  # Method
src/main/java/Order.java:Order                 # Class
```

### Go (future)
```
# Package path style
order/order.go:Order.CalculateTotal         # Method
order/order.go:Order                        # Struct
```

---

## Backend Adapter Interface

Each hardcoded adapter implements this interface:

```python
class BackendAdapter(ABC):
    """Abstract base for language backend adapters."""

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
        """Check if backend CLI is installed and accessible."""
        pass

    @abstractmethod
    def list_refactorings(self) -> list[RefactoringSpec]:
        """Return available refactorings with their parameter specs."""
        pass

    @abstractmethod
    def build_command(
        self,
        refactoring: str,
        target: str,
        params: dict,
        preview: bool = True
    ) -> list[str]:
        """Build CLI command args for a refactoring."""
        pass

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> Result:
        """Parse CLI output into structured result."""
        pass

    def supports_analysis(self) -> bool:
        """Whether this backend supports code smell analysis."""
        return False

    def build_analysis_command(self, path: str, smells: list[str]) -> list[str]:
        """Build CLI command for code analysis (if supported)."""
        raise NotImplementedError("Analysis not supported by this backend")
```

### Python Adapter (Initial Implementation)

```python
class PythonAdapter(BackendAdapter):
    language = "python"
    cli_command = "molting"  # or configured path

    def is_available(self) -> bool:
        return shutil.which(self.cli_command) is not None

    def build_command(self, refactoring, target, params, preview=True):
        cmd = [self.cli_command, refactoring, target]

        # Add refactoring-specific params
        for key, value in params.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key.replace('_', '-')}")
            else:
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        # Add output format
        cmd.append("--output=toon")

        if preview:
            cmd.append("--dry-run")

        return cmd
```

---

## Configuration

### Config File: `~/.mcp-refactoring/config.toml`

```toml
# Backend configuration
[backends.python]
enabled = true
command = "molting"  # Override CLI path
# command = "/usr/local/bin/molting"  # Absolute path

[backends.ruby]
enabled = false  # Disabled until backend exists
command = "molting-rb"

[backends.java]
enabled = false
command = "molting-java"

[backends.go]
enabled = false
command = "molting-go"

# Default settings
[defaults]
preview_by_default = true  # Always preview unless --apply
output_format = "toon"

# File detection
[detection]
# Map file extensions to languages
extensions.py = "python"
extensions.pyi = "python"
extensions.rb = "ruby"
extensions.java = "java"
extensions.go = "go"
```

### Environment Variable Overrides

```bash
# Override backend commands
MCP_REFACTORING_PYTHON_COMMAND=/path/to/molting
MCP_REFACTORING_RUBY_COMMAND=/path/to/molting-rb

# Enable/disable backends
MCP_REFACTORING_PYTHON_ENABLED=true
MCP_REFACTORING_RUBY_ENABLED=false

# Config file location
MCP_REFACTORING_CONFIG=~/.mcp-refactoring/config.toml
```

---

## Project Structure

```
refactoring-mcp/
├── pyproject.toml              # Package configuration
├── LICENSE                     # MIT License
├── README.md                   # Documentation
├── src/
│   └── mcp_refactoring/
│       ├── __init__.py
│       ├── __main__.py         # Entry point: python -m mcp_refactoring
│       ├── server.py           # FastMCP server setup
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── list_refactorings.py
│       │   ├── preview_refactoring.py
│       │   ├── apply_refactoring.py
│       │   ├── inspect_structure.py
│       │   └── analyze_code.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py         # BackendAdapter ABC
│       │   ├── python.py       # molting-cli adapter
│       │   ├── ruby.py         # Future: Ruby adapter (stub)
│       │   ├── java.py         # Future: Java adapter (stub)
│       │   └── go.py           # Future: Go adapter (stub)
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py       # Config file + env var loading
│       │   └── schema.py       # Config validation (Pydantic)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── refactoring.py  # RefactoringSpec, Result, etc.
│       │   └── analysis.py     # CodeSmell, StructureInfo, etc.
│       └── utils/
│           ├── __init__.py
│           ├── toon.py         # TOON format encoder
│           ├── subprocess.py   # Safe subprocess handling
│           └── detection.py    # Language/backend detection
└── tests/
    ├── conftest.py
    ├── test_server.py
    ├── test_tools/
    │   ├── test_list_refactorings.py
    │   ├── test_preview_refactoring.py
    │   └── ...
    ├── test_adapters/
    │   ├── test_python_adapter.py
    │   └── ...
    └── fixtures/
        └── ...
```

---

## Dependencies

### Runtime Dependencies

```toml
[project]
dependencies = [
    "mcp>=1.0.0",              # MCP Python SDK (FastMCP)
    "pydantic>=2.0",           # Config and model validation
    "tomli>=2.0;python<'3.11'", # TOML parsing (stdlib in 3.11+)
]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
```

---

## Refactoring Catalog

The full catalog of 71+ refactorings from Martin Fowler, organized by category:

### Composing Methods (10)
- `extract-method` - Extract code block into new method
- `extract-function` - Extract code into module-level function
- `inline-method` - Replace method calls with method body
- `inline-temp` - Replace temporary variable with its value
- `replace-temp-with-query` - Replace temp variable with method call
- `introduce-explaining-variable` - Extract expression into named variable
- `split-temporary-variable` - Separate variables for different purposes
- `remove-assignments-to-parameters` - Use temp variable instead
- `replace-method-with-method-object` - Convert method into its own object
- `substitute-algorithm` - Replace algorithm with clearer implementation

### Moving Features Between Objects (8)
- `move-method` - Move method between classes
- `move-field` - Move field between classes
- `extract-class` - Split class into two classes
- `inline-class` - Merge class into another class
- `hide-delegate` - Create delegating methods
- `remove-middle-man` - Call delegate directly
- `introduce-foreign-method` - Add method to class you can't modify
- `introduce-local-extension` - Create subclass or wrapper

### Organizing Data (13)
- `self-encapsulate-field` - Create getter/setter for field
- `replace-data-value-with-object` - Convert data item into object
- `change-value-to-reference` - Convert value object to reference
- `change-reference-to-value` - Convert reference to value object
- `replace-array-with-object` - Replace array with object
- `duplicate-observed-data` - Copy data to domain object
- `change-unidirectional-to-bidirectional` - Add back pointers
- `change-bidirectional-to-unidirectional` - Remove back pointers
- `replace-magic-number` - Create named constant
- `encapsulate-field` - Add accessors
- `encapsulate-collection` - Add collection accessors
- `replace-type-code-with-class` - Refactor type codes
- `replace-type-code-with-subclasses` - Use inheritance
- `replace-type-code-with-state-strategy` - Use State/Strategy pattern

### Simplifying Conditional Expressions (8)
- `decompose-conditional` - Extract condition and branches
- `consolidate-conditional-expression` - Combine conditions
- `consolidate-duplicate-conditional-fragments` - Move common code
- `remove-control-flag` - Use break/return instead
- `replace-nested-conditional-with-guard-clauses` - Use guard clauses
- `replace-conditional-with-polymorphism` - Use polymorphic dispatch
- `introduce-null-object` - Replace null checks
- `introduce-assertion` - Make assumptions explicit

### Simplifying Method Calls (14)
- `rename-method` - Rename method
- `add-parameter` - Add method parameter
- `remove-parameter` - Remove method parameter
- `separate-query-from-modifier` - Split read/write operations
- `parameterize-method` - Combine similar methods
- `replace-parameter-with-explicit-methods` - Create separate methods
- `preserve-whole-object` - Pass entire object
- `replace-parameter-with-method-call` - Call method instead
- `introduce-parameter-object` - Group parameters into object
- `remove-setting-method` - Remove setter
- `hide-method` - Make method private
- `replace-constructor-with-factory-function` - Use factory
- `replace-error-code-with-exception` - Throw exception
- `replace-exception-with-test` - Use conditional check

### Dealing with Generalization (11)
- `pull-up-field` - Move field to superclass
- `pull-up-method` - Move method to superclass
- `pull-up-constructor-body` - Move constructor logic to superclass
- `push-down-method` - Move method to subclass
- `push-down-field` - Move field to subclass
- `extract-subclass` - Create subclass
- `extract-superclass` - Create superclass
- `extract-interface` - Create interface
- `collapse-hierarchy` - Merge subclass into superclass
- `form-template-method` - Extract algorithm to superclass
- `replace-inheritance-with-delegation` - Use composition
- `replace-delegation-with-inheritance` - Use inheritance

---

## Backend CLI Requirements

For a language backend to be compatible with mcp-refactoring, it must:

1. **Support TOON output format** via `--output=toon` or similar flag
2. **Support dry-run mode** via `--dry-run` or `--preview` flag
3. **Use consistent exit codes:**
   - `0` - Success
   - `1` - Refactoring failed (invalid target, parse error, etc.)
   - `2` - Invalid arguments
4. **Implement the same refactoring names** from the Fowler catalog
5. **Return structured output** with:
   - Status (success/failure)
   - Files affected
   - Diff or changes made
   - Error messages (if any)

### Example Backend CLI Usage (molting-cli)

```bash
# Preview a refactoring
molting extract-method src/order.py::Order::calculate#L10-L15 \
  --name calculate_tax \
  --dry-run \
  --output=toon

# Apply a refactoring
molting extract-method src/order.py::Order::calculate#L10-L15 \
  --name calculate_tax \
  --output=toon

# List available refactorings
molting --list-refactorings --output=toon

# Analyze code (future)
molting analyze src/order.py --output=toon
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project setup with pyproject.toml
- [ ] FastMCP server skeleton
- [ ] Configuration loading (config.toml + env vars)
- [ ] TOON output encoder
- [ ] Base adapter interface

### Phase 2: Python Adapter
- [ ] Python adapter implementation
- [ ] Backend detection and availability checking
- [ ] Command building for all refactorings
- [ ] Output parsing

### Phase 3: MCP Tools
- [ ] `list_refactorings` tool
- [ ] `preview_refactoring` tool
- [ ] `apply_refactoring` tool
- [ ] `inspect_structure` tool
- [ ] `analyze_code` tool (stubbed)

### Phase 4: molting-cli Enhancements
- [ ] Add `--output=toon` flag to molting-cli
- [ ] Add `--list-refactorings` command
- [ ] Ensure consistent exit codes
- [ ] (Future) Add `analyze` command

### Phase 5: Testing & Documentation
- [ ] Unit tests for adapters
- [ ] Integration tests with molting-cli
- [ ] MCP Inspector testing
- [ ] README and usage documentation
- [ ] PyPI publishing setup

### Phase 6: Future Language Backends
- [ ] Define adapter stubs for Ruby, Java, Go
- [ ] Create backend development guide
- [ ] (Separate repos) Implement language-specific backends

---

## Usage Examples

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "refactoring": {
      "command": "uvx",
      "args": ["mcp-refactoring"]
    }
  }
}
```

### Example LLM Interaction

```
User: Refactor the calculate_total method in src/order.py to extract
      the discount calculation into a separate method.

LLM: I'll help you extract the discount calculation. Let me first
     inspect the structure of that file.

     [calls inspect_structure(path="src/order.py")]

     I can see Order.calculate_total spans lines 15-45. Let me preview
     extracting the discount logic.

     [calls preview_refactoring(
       refactoring="extract-method",
       target="src/order.py::Order::calculate_total#L28-L35",
       params={"name": "calculate_discount"}
     )]

     Here's what the refactoring would change:
     - Extract lines 28-35 into a new method `calculate_discount`
     - Replace the original code with a call to the new method

     Would you like me to apply this refactoring?

User: Yes, apply it.

LLM: [calls apply_refactoring(
       refactoring="extract-method",
       target="src/order.py::Order::calculate_total#L28-L35",
       params={"name": "calculate_discount"}
     )]

     Done! The discount calculation has been extracted into
     Order.calculate_discount().
```

---

## Open Questions for Future Consideration

1. **Cross-file refactorings:** How should move-method handle imports in other files that reference the moved method?

2. **Undo support:** Should the MCP track refactoring history for undo operations, or rely on git?

3. **Batch operations:** Should there be a `batch_refactoring` tool for applying multiple refactorings atomically?

4. **IDE integration:** Should adapters support LSP-style workspace edits for better IDE integration?

5. **Conflict detection:** How should the MCP handle concurrent file modifications?

---

## Success Criteria

The mcp-refactoring project will be considered successful when:

1. LLMs can discover available refactorings via `list_refactorings`
2. LLMs can safely preview refactorings before applying them
3. Applied refactorings produce correct, parseable code
4. The adapter interface is clear enough for community backend development
5. Installation via `uvx mcp-refactoring` works out of the box with molting-cli
6. Documentation enables new contributors to add language backends
