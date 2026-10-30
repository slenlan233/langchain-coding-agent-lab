import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic.fields import Field

mcp = FastMCP()
WORK_DIR = Path(__file__).resolve().parents[2] / '.temp'


def _stop_process_tree(process):
    """终止本次命令及 Git 等子进程，避免超时后仍在后台运行。"""
    if os.name == 'nt':
        try:
            result = subprocess.run(
                ['taskkill', '/PID', str(process.pid), '/T', '/F'],
                capture_output=True, timeout=10,
            )
        finally:
            if process.poll() is None:
                process.kill()
        process.wait(timeout=5)
        if result.returncode != 0:
            detail = result.stderr.decode(errors='replace')
            raise RuntimeError(f'Process-tree cleanup failed; child processes may still be running: {detail}')
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=5)


@mcp.tool(name='run_shell', description=(
    'Run finite shell commands using PowerShell 7 on Windows. '
    'Use PowerShell syntax, not Bash/Linux syntax. '
    'Commands time out after 120 seconds by default (maximum 600). '
    'Do not use this tool for interactive commands or long-running servers.'
))
def run_shell_command(
    command: Annotated[str, Field(description='The PowerShell 7 command to execute.')],
    timeout_seconds: Annotated[int, Field(ge=1, le=600, description='Command timeout in seconds.')] = 120,
) -> str:
    if not command.strip():
        return 'ERROR: command must not be empty.'
    if not 1 <= timeout_seconds <= 600:
        return 'ERROR: timeout_seconds must be between 1 and 600.'

    env = os.environ.copy()
    env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
    # MCP stdout 专用于 JSON-RPC；诊断只能写到 stderr。
    print(f'[run_shell] cwd={WORK_DIR}\n[run_shell] {command}', file=sys.stderr, flush=True)
    process = None
    started = time.monotonic()
    timed_out = False
    try:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        # 文件捕获避免子进程继承管道后，communicate 一直等不到 EOF。
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            process = subprocess.Popen(
                ['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-Command',
                 '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); ' + command],
                cwd=WORK_DIR, env=env, stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr,
                start_new_session=os.name != 'nt',
            )
            deadline = started + timeout_seconds
            while process.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    _stop_process_tree(process)
                    break
                try:
                    process.wait(timeout=min(10, remaining))
                except subprocess.TimeoutExpired:
                    print(f'[run_shell] 执行中，已等待 {time.monotonic() - started:.0f}s '
                          f'（上限 {timeout_seconds}s）', file=sys.stderr, flush=True)
            stdout.seek(0)
            stderr.seek(0)
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
        status = (f'TIMEOUT after {timeout_seconds}s; process tree terminated.'
                  if timed_out else f'Exit code: {process.returncode}')
        print(f'[run_shell] {status}', file=sys.stderr, flush=True)
        return f'{status}\nstdout:\n{out}\nstderr:\n{err}'
    except Exception as exc:
        return f'ERROR: {type(exc).__name__}: {exc}'
    finally:
        if process is not None and process.poll() is None:
            _stop_process_tree(process)


if __name__ == '__main__':
    mcp.run(transport='stdio')
