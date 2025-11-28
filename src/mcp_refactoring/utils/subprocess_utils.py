"""Safe subprocess handling utilities."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from typing import Sequence


@dataclass
class CommandResult:
    """Result of running a command."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """Whether the command succeeded."""
        return self.returncode == 0


async def run_command(
    args: Sequence[str],
    cwd: str | None = None,
    timeout: float = 60.0,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a command asynchronously and return the result.

    Args:
        args: Command and arguments to run
        cwd: Working directory for the command
        timeout: Timeout in seconds (default: 60)
        env: Environment variables to set

    Returns:
        CommandResult with returncode, stdout, and stderr

    Raises:
        asyncio.TimeoutError: If the command times out
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )

        return CommandResult(
            returncode=process.returncode or 0,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        )

    except asyncio.TimeoutError:
        if process:
            process.kill()
            await process.wait()
        raise


def run_command_sync(
    args: Sequence[str],
    cwd: str | None = None,
    timeout: float = 60.0,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a command synchronously and return the result.

    Args:
        args: Command and arguments to run
        cwd: Working directory for the command
        timeout: Timeout in seconds (default: 60)
        env: Environment variables to set

    Returns:
        CommandResult with returncode, stdout, and stderr

    Raises:
        subprocess.TimeoutExpired: If the command times out
    """
    result = subprocess.run(
        args,
        capture_output=True,
        cwd=cwd,
        timeout=timeout,
        env=env,
    )

    return CommandResult(
        returncode=result.returncode,
        stdout=result.stdout.decode("utf-8", errors="replace"),
        stderr=result.stderr.decode("utf-8", errors="replace"),
    )
