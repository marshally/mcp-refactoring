# Target Syntax

## Design Decision

Each language backend uses its **native ecosystem conventions** for target specification. The MCP server does not normalize these - it passes them through to the backend.

## Python (molting-cli)

Pytest-style with `::` separator:

```
src/order.py                              # Module
src/order.py::Order                       # Class
src/order.py::Order::calculate_total      # Method
src/order.py::Order::calculate_total#L10  # Specific line
src/order.py::Order::calculate_total#L10-L15  # Line range
src/order.py::Order::calculate_total::temp_var  # Variable in method
```

## Ruby (future)

RSpec-style with `#` for instance methods:

```
lib/order.rb#Order                        # Class
lib/order.rb#Order#calculate_total        # Instance method
lib/order.rb#Order.from_hash              # Class method
```

## Java (future)

Fully qualified with `.` separator:

```
src/main/java/Order.java:Order            # Class
src/main/java/Order.java:Order.calculateTotal  # Method
```

## Go (future)

Package path style:

```
order/order.go:Order                      # Struct
order/order.go:Order.CalculateTotal       # Method
order/order.go:CalculateTotal             # Package function
```

## Detection

The MCP server detects language from file extension:

```python
# config/schema.py defaults
extensions = {
    "py": "python",
    "pyi": "python",
    "rb": "ruby",
    "java": "java",
    "go": "go",
}
```

This routes to the correct adapter which knows how to parse its native syntax.
