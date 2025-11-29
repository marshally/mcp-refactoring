# Instructions for AI Agents

This file contains instructions for AI coding agents working on this repository.

## Changelog Requirements

**Every PR must update CHANGELOG.md.**

Add your changes under the `## [Unreleased]` section using these categories:

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

Example:
```markdown
## [Unreleased]

### Added
- New `foo` parameter to `bar_refactoring` tool

### Fixed
- Handle edge case in extract-method when selection is empty
```

## Version Bumping

When preparing a release, update the version in both:
- `pyproject.toml`
- `src/mcp_refactoring/__init__.py`

## Commit Messages

Use clear, concise commit messages that describe the "why" not just the "what".

## Testing

Run tests before submitting PRs:
```bash
pytest
ruff check .
mypy src/
```
