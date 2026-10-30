from pathlib import Path

from code_agent_platform.integrations.file_toolkit import file_tools as create_file_tools


file_tools = create_file_tools(Path(__file__).resolve().parents[3] / ".temp")
