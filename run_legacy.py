"""Explicit entry point for the current app/ prototype, not the platform CLI."""
import asyncio
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    from app.code_agent.agent.code_agent import run_agent
    asyncio.run(run_agent())
