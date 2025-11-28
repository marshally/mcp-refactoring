# mcp-refactoring

An MCP (Model Context Protocol) server that exposes Martin Fowler's refactoring catalog to LLMs through a pluggable, language-agnostic architecture.

## Features

- **71+ Refactorings**: Full implementation of Martin Fowler's refactoring catalog
- **Pluggable Architecture**: Support for multiple languages (Python first, Ruby/Java/Go planned)
- **Safe by Default**: Preview mode shows changes before applying
- **LLM-Optimized**: TOON output format for token efficiency

## Installation

```bash
# Using uvx (recommended)
uvx mcp-refactoring

# Using pip
pip install mcp-refactoring

# Using pipx
pipx install mcp-refactoring
```

## Requirements

- Python 3.10+
- A language backend (e.g., `molting-cli` for Python)

Install the Python backend:
```bash
pip install molting-cli
```

## Claude Desktop Configuration

Add to your Claude Desktop config:

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

## Available Tools

### list_refactorings

List available refactorings with their parameter contracts.

```
list_refactorings(language="python", category="composing_methods")
```

### preview_refactoring

Preview what changes a refactoring would make (dry-run).

```
preview_refactoring(
    refactoring="extract-method",
    target="src/order.py::Order::calculate#L10-L15",
    params={"name": "calculate_tax"}
)
```

### apply_refactoring

Apply a refactoring to the codebase.

```
apply_refactoring(
    refactoring="rename-method",
    target="src/order.py::Order::calc",
    params={"new_name": "calculate_total"}
)
```

### inspect_structure

Get structural information about code.

```
inspect_structure(path="src/order.py", depth="method")
```

### analyze_code

Analyze code for smells and suggest refactorings.

```
analyze_code(path="src/order.py", smells=["long-method"])
```

## Target Specification

Each language uses its native conventions:

### Python
```
src/order.py::Order::calculate_total        # Method
src/order.py::Order::calculate_total#L10-L15  # Line range
src/order.py::Order                         # Class
```

## Configuration

Create `~/.mcp-refactoring/config.toml`:

```toml
[backends.python]
enabled = true
command = "molting"

[backends.ruby]
enabled = false
command = "molting-rb"
```

Environment variable overrides:

```bash
MCP_REFACTORING_PYTHON_COMMAND=/path/to/molting
MCP_REFACTORING_PYTHON_ENABLED=true
```

## Refactoring Categories

Based on Martin Fowler's catalog:

- **Composing Methods**: extract-method, inline-method, etc.
- **Moving Features**: move-method, extract-class, etc.
- **Organizing Data**: encapsulate-field, replace-type-code, etc.
- **Simplifying Conditionals**: decompose-conditional, guard-clauses, etc.
- **Simplifying Method Calls**: rename-method, add-parameter, etc.
- **Dealing with Generalization**: pull-up-method, extract-interface, etc.

## Development

```bash
# Clone the repository
git clone https://github.com/marshally/mcp-refactoring.git
cd mcp-refactoring

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
