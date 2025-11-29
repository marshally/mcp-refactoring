# TOON Output Format

## What is TOON?

**Token-Oriented Object Notation** is a compact, LLM-friendly format that minimizes token usage while maintaining readability.

Reference: https://github.com/toon-format/toon

## Why TOON?

- ~40% fewer tokens than JSON
- Combines YAML indentation with CSV-style tabular arrays
- Lossless round-trip conversion
- Optimized for uniform object arrays (common in refactoring output)

## Syntax Examples

### Simple Object
```
preview:
  refactoring: extract-method
  status: success
  files_affected: 1
```

### Tabular Array (uniform objects)
```
refactorings[3]{name,category,params,description}:
  extract-method,composing_methods,"target,name",Extract code block into new method
  rename-method,simplifying_method_calls,"target,new_name",Rename a method
  move-method,moving_features,"target,to_class",Move method to another class
```

### Mixed Output
```
analysis:
  path: src/order.py
  language: python
  backend_supported: true
smells[2]{type,location,severity,suggested_refactoring,details}:
  long-method,Order::calculate_total,high,extract-method,"45 lines (threshold: 20)"
  feature-envy,Order::format_address,medium,move-method,"Accesses Customer 8 times"
```

## Implementation

The encoder is in `utils/toon.py`:

```python
from mcp_refactoring.utils import encode_toon

result = encode_toon({
    "status": "success",
    "files": [
        {"path": "order.py", "action": "modified"},
        {"path": "customer.py", "action": "modified"},
    ]
})
```

## Backend Requirements

Language backends should support `--output=toon` flag to return TOON-formatted output directly, avoiding parsing overhead in the MCP server.
