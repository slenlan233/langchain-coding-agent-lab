import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Annotated
from uuid import uuid4

import pyautogui
import pygetwindow as gw
import pyperclip
from mcp.server.fastmcp import FastMCP
from pydantic.fields import Field

mcp = FastMCP()
WORK_DIR = Path(__file__).resolve().parents[2] / ".temp"
LOG_DIR = WORK_DIR / "terminal_logs"
POWERSHELL = "pwsh"
TERMINAL_TITLE = "Code Agent Terminal"
TerminalId = Annotated[str, Field(description="open_terminal 返回的终端 ID；留空使用当前选中的 Agent 终端。")]


@dataclass
class TerminalSession:
    terminal_id: str
    process: subprocess.Popen
    title: str
    transcript: Path
    working_directory: Path


# 由持续 MCP 会话管理。关闭窗口后保留映射，允许继续读取历史。
terminals: dict[str, TerminalSession] = {}
current_terminal_id = ""
# 多窗口共享键盘和剪贴板，必须串行完成定位和输入。
terminal_lock = RLock()


def _resolve_terminal(terminal_id: str = "") -> TerminalSession:
    selected = terminal_id or current_terminal_id
    if selected not in terminals:
        raise ValueError(f"未知终端 ID: {selected}" if selected else "没有选中的终端，请先调用 open_terminal")
    return terminals[selected]


def _get_window(terminal: TerminalSession):
    if terminal.process.poll() is not None:
        return None
    # 精确匹配独立标题，不会把另一个 Agent 终端当作目标。
    return next((w for w in gw.getWindowsWithTitle(terminal.title)
                 if w.title == terminal.title), None)


def _activate(terminal: TerminalSession) -> None:
    global current_terminal_id
    window = _get_window(terminal)
    # PowerShell 进程先启动，窗口标题稍后才可被检索到。
    for _ in range(25):
        if window is not None or terminal.process.poll() is not None:
            break
        time.sleep(0.2)
        window = _get_window(terminal)
    if window is None:
        raise ValueError(f"终端 {terminal.terminal_id} 已退出或窗口暂不可定位；请用相同 ID 重试，不要新建终端")
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(0.4)
    current_terminal_id = terminal.terminal_id


def _quote(value: str) -> str:
    return value.replace("'", "''")


@mcp.tool(name="open_terminal", description="仅当后台 run_shell 无法完成交互式任务时使用。默认复用已有的运行中终端；首次调用创建终端。只有用户明确要求多个窗口时才能传 new_window=true。传 terminal_id 激活指定终端，每个窗口拥有独立 ID 和日志。")
def open_terminal(
    working_directory: Annotated[str, Field(description="新终端工作目录，留空使用项目的 .temp 目录。")] = "",
    terminal_id: TerminalId = "",
    new_window: Annotated[bool, Field(description="仅需要额外新窗口时设为 true；默认复用已有终端。不能与 terminal_id 同时使用。")] = False,
) -> str:
    global current_terminal_id
    with terminal_lock:
        try:
            if terminal_id and new_window:
                return "参数冲突：terminal_id 和 new_window=true 不能同时使用"
            if terminal_id:
                terminal = _resolve_terminal(terminal_id)
                _activate(terminal)
                return f"已选中终端 ID: {terminal_id}"
            if not new_window:
                candidates = sorted(terminals.values(), key=lambda t: t.terminal_id != current_terminal_id)
                terminal = next((t for t in candidates if t.process.poll() is None), None)
                if terminal is not None:
                    if working_directory and Path(working_directory).resolve() != terminal.working_directory:
                        return f"已有终端 {terminal.terminal_id}；请在其中执行 Set-Location，或传 new_window=true 在其他目录新建终端"
                    _activate(terminal)
                    return f"已复用终端 ID: {terminal.terminal_id}"
            work_dir = Path(working_directory).resolve() if working_directory else WORK_DIR
            if working_directory and not work_dir.is_dir():
                return f"工作目录不存在: {working_directory}"
            work_dir.mkdir(parents=True, exist_ok=True)
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            new_id = uuid4().hex
            transcript = LOG_DIR / f"terminal_{new_id}.txt"
            title = f"{TERMINAL_TITLE} [{new_id}]"
            startup = (
                f"$Host.UI.RawUI.WindowTitle='{_quote(title)}'; "
                f"Start-Transcript -Path '{_quote(str(transcript))}' -NoClobber -ErrorAction Stop | Out-Null"
            )
            process = subprocess.Popen(
                [POWERSHELL, "-NoLogo", "-NoProfile", "-NoExit", "-Command", startup],
                cwd=str(work_dir), creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            terminal = TerminalSession(new_id, process, title, transcript, work_dir)
            terminals[new_id] = terminal
            time.sleep(1)
            if process.poll() is not None:
                return f"终端启动失败，进程已退出。终端 ID: {new_id}"
            current_terminal_id = new_id
            return (f"PowerShell 7 终端已打开\n终端 ID: {new_id}\nPID: {process.pid}\n"
                    f"工作目录: {work_dir}\n终端历史: {transcript}")
        except Exception as e:
            return f"打开终端失败: {e}"


@mcp.tool(name="list_terminals", description="列出本次 MCP 会话创建的终端 ID、当前选择、运行状态及各自日志路径。")
def list_terminals() -> str:
    with terminal_lock:
        return json.dumps([
            {"terminal_id": t.terminal_id, "selected": t.terminal_id == current_terminal_id,
             "running": t.process.poll() is None, "working_directory": str(t.working_directory),
             "transcript": str(t.transcript)}
            for t in terminals.values()
        ], ensure_ascii=False, indent=2)


@mcp.tool(name="close_terminal", description="仅关闭指定 ID 的 Agent 终端；留空关闭当前选中的终端。保留独立日志用于读取历史。")
def close_terminal(terminal_id: TerminalId = "") -> str:
    with terminal_lock:
        try:
            terminal = _resolve_terminal(terminal_id)
            if terminal.process.poll() is not None:
                return f"终端 {terminal.terminal_id} 已关闭，日志保留"
            # 使用原始 Popen 句柄，避免 PID 重用时误关闭其他进程。
            terminal.process.terminate()
            try:
                terminal.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                terminal.process.kill()
                terminal.process.wait(timeout=2)
            return f"已关闭终端 {terminal.terminal_id}，日志保留"
        except Exception as e:
            return f"关闭终端失败: {e}"


@mcp.tool(name="run_terminal_script", description="仅当后台 run_shell 无法完成交互式任务时使用。在指定可见终端执行 PowerShell 命令，然后用相同 terminal_id 调用 get_terminal_text。等待当前命令完成后再发送下一条；必须复用已有 terminal_id，不要因输出延迟新建窗口。首次不传 ID 时自动创建一个终端。")
def run_terminal_script(
    script: Annotated[str, Field(description="PowerShell 命令，例如 Get-ChildItem -Force；不要使用 ls -al。", min_length=1)],
    terminal_id: TerminalId = "",
) -> str:
    with terminal_lock:
        try:
            if not script.strip():
                return "执行终端脚本失败：命令不能为空"
            if not terminal_id and not current_terminal_id:
                result = open_terminal()
                if not current_terminal_id:
                    return result
            terminal = _resolve_terminal(terminal_id)
            _activate(terminal)
            pyautogui.FAILSAFE = True
            pyperclip.copy(script)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.15)
            pyautogui.press("enter")
            time.sleep(0.3)
            return f"命令已发送到终端 {terminal.terminal_id}:\n{script}\n请使用相同 terminal_id 调用 get_terminal_text 查看结果"
        except Exception as e:
            return f"执行终端脚本失败: {e}"


@mcp.tool(name="get_terminal_text", description="读取指定终端的独立 Transcript 日志，包含本次窗口会话的历史；关闭后仍可读取。不会读取其他窗口的日志。")
def get_terminal_text(terminal_id: TerminalId = "") -> str:
    with terminal_lock:
        try:
            terminal = _resolve_terminal(terminal_id)
            if not terminal.transcript.exists():
                return f"终端 {terminal.terminal_id} 的日志尚未生成，请稍后重试；若持续缺失请检查窗口中的 Start-Transcript 错误"
            text = terminal.transcript.read_text(encoding="utf-8-sig", errors="replace").strip()
            return f"终端 ID: {terminal.terminal_id}\n{text or '终端历史当前为空'}"
        except Exception as e:
            return f"获取终端文本失败: {e}"


@mcp.tool(name="send_terminal_keyboard_key", description="向指定终端依次发送按键，例如 up、enter 或 ctrl+c。留空 ID 使用当前选中终端。")
def send_terminal_keyboard_key(
    key_codes: Annotated[list[str], Field(description="按键列表，return 等同 enter，组合键如 ctrl+c。", examples=[["up", "enter"], ["ctrl+c"]], min_length=1)],
    terminal_id: TerminalId = "",
) -> bool:
    with terminal_lock:
        try:
            aliases = {"return": "enter", "dot": "."}
            keys = [[aliases.get(p.strip().lower(), p.strip().lower()) for p in key.split("+")]
                    for key in key_codes]
            if not keys or any(p not in pyautogui.KEYBOARD_KEYS for group in keys for p in group):
                return False
            _activate(_resolve_terminal(terminal_id))
            for group in keys:
                if len(group) == 1:
                    pyautogui.press(group[0])
                else:
                    pyautogui.hotkey(*group)
                time.sleep(0.15)
            return True
        except Exception as e:
            print(f"发送终端按键失败: {e}", file=sys.stderr)
            return False


if __name__ == "__main__":
    mcp.run(transport="stdio")
