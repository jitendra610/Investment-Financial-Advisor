import asyncio

from app.prompts.manager import get_prompt


async def load_system_prompt(agent_name: str):
    """Load the active prompt without blocking the event loop."""
    return await asyncio.to_thread(get_prompt, agent_name)