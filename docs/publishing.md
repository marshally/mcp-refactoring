# Publishing Guide

## Automated Publishing (Recommended)

Releases are automatically published to PyPI when you create a GitHub release.

### Steps

1. Bump version in both files:
   - `pyproject.toml`
   - `src/mcp_refactoring/__init__.py`

2. Commit and push:
   ```bash
   git add -A && git commit -m "Bump version to X.Y.Z" && git push
   ```

3. Create a GitHub release:
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes "Release notes here"
   ```
   Or via https://github.com/marshally/mcp-refactoring/releases/new

4. The workflow automatically builds and publishes to PyPI.

### Configuration

The workflow uses PyPI trusted publishing (OIDC) - no API tokens needed.

Setup is in:
- `.github/workflows/python-publish.yml` - GitHub Actions workflow
- GitHub repo settings → Environments → `pypi`
- PyPI project settings → Publishing → Trusted publisher

---

## Manual Publishing

For manual releases or troubleshooting.

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

Update version in both files:

1. `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. `src/mcp_refactoring/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

Then commit and create a release (automated) or rebuild and upload (manual).
