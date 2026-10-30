"""Compatibility entry point; implementation is shared with the platform."""
from code_agent_platform.integrations.mysql import *

if __name__ == "__main__":
    mcp.run(transport="stdio")
