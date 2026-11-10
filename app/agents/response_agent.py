# Import function to retrieve an agent-specific system prompt
from app.prompts.manager import get_prompt
import asyncio
import json
from app.agents.llm import llm # Import the configured LLM instance.
from app.prompts import load_system_prompt
import os
from langchain_openai import ChatOpenAI
# Import the LangGraph state schema.
# Defines data shared between different agents.
from app.agents.state import InvestmentState
import logging

logger = logging.getLogger(__name__)


async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

# Helper function to convert Python data into a JSON string.
def as_json(value):
    return json.dumps(value, default=str)

async def response_agent(state):
    logger.info("Response Agent started")
    start_time = time.perf_counter()

    try:
        prompt = await load_system_prompt("response")
        result = await llm.ainvoke([
            (
                "system",
                prompt.content
            ),
            (
                "human",
                as_json({
                    "query": state["query"],
                    "knowledge": state["knowledge"],
                    "portfolio": state["portfolio"],
                    "compliance": state["compliance"],
                }),
            ),
        ])

        logger.info("Response Agent completed")

        return {
            "response": result.content,  # Store the final LLM-generated response.
            "status": "completed",       # Mark the response generation process as completed.
            "response_prompt_version": prompt.version  # Record the system prompt version used.
        }

    except Exception as e:
        logger.error(f"Response Agent failed: {e}")
        raise




"""
The Response Agent should use a different system prompt or response strategy for 
general conversation, 
education, customer-profile summaries, and regulated financial analysis.
"""