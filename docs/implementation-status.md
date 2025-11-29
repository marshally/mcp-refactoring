# Implementation Status

## MCP Server Components

| Component | Status | Notes |
|-----------|--------|-------|
| FastMCP server | **Complete** | 5 tools registered, stdio transport |
| Configuration | **Complete** | TOML + env vars |
| TOON encoder | **Complete** | Full encoder implementation |
| Adapter interface | **Complete** | ABC with all methods |
| Python adapter | **Partial** | See below |
| Ruby adapter | **Stub only** | Not implemented |
| Java adapter | **Stub only** | Not implemented |
| Go adapter | **Stub only** | Not implemented |

## MCP Tools

| Tool | Status | Notes |
|------|--------|-------|
| `list_refactorings` | **Working** | Returns full 71+ catalog from adapter |
| `preview_refactoring` | **Wired** | Calls CLI, needs `--dry-run` in molting |
| `apply_refactoring` | **Wired** | Calls CLI, works if molting works |
| `inspect_structure` | **Stub** | Returns empty, needs implementation |
| `analyze_code` | **Stub** | Returns "not supported" |

## Python Adapter (molting-cli)

| Feature | Status |
|---------|--------|
| Refactoring catalog | **Complete** | All 71+ defined with params |
| CLI detection | **Complete** | `shutil.which("molting")` |
| Command building | **Complete** | Builds correct CLI args |
| Output parsing | **Placeholder** | Needs TOON parsing |

## molting-cli Gaps

For full MCP functionality, molting-cli needs:

| Feature | Priority | Effort |
|---------|----------|--------|
| `--dry-run` flag | **High** | Medium |
| `--output=toon` flag | **High** | Medium |
| `--list-refactorings` | Medium | Low |
| `inspect` command | Medium | Medium |
| `analyze` command | Low | High |
| Consistent exit codes | Medium | Low |

## What Works Today

1. **`list_refactorings`** - Fully functional, returns catalog
2. **`apply_refactoring`** - Works for refactorings that molting-cli supports (output won't be TOON formatted)
3. **Server startup** - `python -m mcp_refactoring` runs

## What Doesn't Work Yet

1. **`preview_refactoring`** - Needs `--dry-run` in molting-cli
2. **`inspect_structure`** - Returns empty (not implemented)
3. **`analyze_code`** - Returns "not supported"
4. **Structured output** - All output is raw CLI text until TOON support added
