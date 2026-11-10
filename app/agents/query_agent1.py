import asyncio
import logging

from langsmith import traceable

from app.agents.llm import llm
from app.agents.schemas import QueryPlan
from app.prompts.manager import get_prompt

logger = logging.getLogger(__name__)


@traceable(name="query-analyzer", run_type="chain")
async def query_agent(state):

    logger.info("Query Analyzer started")

    # Load the active Query Agent prompt.
    prompt = await asyncio.to_thread(
        get_prompt, "query"
    )

    # Configure structured LLM output.
    model = llm.with_structured_output(QueryPlan)

    # Analyze the user's question.
    result = await model.ainvoke([
        ("system", prompt.content),
        ("human", state["query"]),
    ])

    logger.info(
        "Query Analyzer completed | intent=%s",
        result.intent,
    )

    # Return analysis to LangGraph state.
    return {
        "query_plan": result.model_dump(),
        "intent": result.intent,
        "required_information": result.required_information,
        "query_prompt_version": {
            "query": {
                "id": prompt.id,
                "version": prompt.version,
            }
        },
    }