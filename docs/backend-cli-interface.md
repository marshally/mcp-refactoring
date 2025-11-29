# Backend CLI Interface

## Requirements for Language Backends

For a CLI tool to be compatible with mcp-refactoring, it must implement:

### 1. Command Structure

```bash
{cli} {refactoring} {target} [--param value ...] [--dry-run] [--output=toon]
```

Example:
```bash
molting extract-method src/order.py::Order::calculate#L10-L15 \
  --name calculate_tax \
  --dry-run \
  --output=toon
```

### 2. Required Flags

| Flag | Purpose |
|------|---------|
| `--dry-run` | Preview mode - show diff without modifying files |
| `--output=toon` | Return TOON-formatted structured output |

### 3. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Refactoring failed (invalid target, parse error, etc.) |
| 2 | Invalid arguments |

### 4. Output Format (TOON)

**Preview output:**
```
preview:
  refactoring: extract-method
  status: success
  files_affected: 1
changes[1]{file,action,diff}:
  src/order.py,modified,"@@ -10,5 +10,10 @@..."
```

**Apply output:**
```
result:
  refactoring: extract-method
  status: success
  files_modified: 1
files[1]{path,action}:
  src/order.py,modified
```

**Error output:**
```
error:
  message: "Could not find method 'calculate' in class 'Order'"
  code: invalid_target
```

### 5. Introspection Commands

```bash
# List available refactorings
{cli} --list-refactorings --output=toon

# Inspect code structure
{cli} inspect {path} --depth=method --output=toon

# Analyze for smells (optional)
{cli} analyze {path} --output=toon
```

## Current molting-cli Status

**Implemented:**
- All 71+ refactoring commands
- Target syntax parsing (file.py::Class::method#L10-L15)

**Not yet implemented (needed for MCP):**
- `--dry-run` flag
- `--output=toon` flag
- `--list-refactorings` command
- `inspect` command
- `analyze` command
