# Publishing Guide

## PyPI Publication

### Prerequisites

```bash
pip install build twine
```

### Build

```bash
cd ~/code/marshally/mcp-refactoring
python -m build
```

Creates:
- `dist/mcp_refactoring-0.1.0-py3-none-any.whl`
- `dist/mcp_refactoring-0.1.0.tar.gz`

### Upload

```bash
twine upload dist/*
```

Or with explicit credentials:
```bash
twine upload dist/* --username __token__ --password pypi-xxxxx
```

### Verify

```bash
pip install mcp-refactoring
uvx mcp-refactoring  # Should start server
```

## MCP Registry Publication

### Prerequisites

```bash
brew install modelcontextprotocol/registry/mcp-publisher
```

### Add MCP Name to README

Add this comment to README.md:
```markdown
<!-- mcp-name: io.github.marshally/mcp-refactoring -->
```

### Create server.json

```json
{
  "serverName": "io.github.marshally/mcp-refactoring",
  "displayName": "Refactoring MCP",
  "description": "MCP server exposing Martin Fowler's refactoring catalog to LLMs",
  "repository": "https://github.com/marshally/mcp-refactoring",
  "packageDeployment": {
    "type": "pypi",
    "packageName": "mcp-refactoring"
  }
}
```

### Publish

```bash
mcp-publisher publish
```

Authenticates via GitHub OAuth for `io.github.*` namespaces.

### Verify

```bash
claude mcp add mcp-refactoring
```

## User Installation Methods

After publishing, users can install via:

| Method | Command |
|--------|---------|
| MCP Registry | `claude mcp add mcp-refactoring` |
| uvx | `uvx mcp-refactoring` |
| pip | `pip install mcp-refactoring` |
| pipx | `pipx install mcp-refactoring` |

## Claude Desktop Config

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

## Version Bumping

Edit `pyproject.toml`:
```toml
version = "0.2.0"
```

Then rebuild and upload.
