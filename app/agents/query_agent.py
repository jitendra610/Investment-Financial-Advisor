#from app.agents.state import InvestmentState
'''
def query_agent(state: InvestmentState) -> dict:
    question = state['query'].lower()
    personal = any(term in question for term in ('my ', 'me ', 'i ', 'recommend', 'should i', 'portfolio', 'allocate', 'invest for'))
    return {'intent': 'personal' if personal else 'education'}
'''

# Import function to retrieve an agent-specific system prompt.
# The prompt may be stored in a database with version information.
from app.prompts.manager import get_prompt

import asyncio

# Import the configured LLM instance.
# Example: ChatOpenAI(model="gpt-4o-mini")
from app.agents.llm import llm

# Import the Pydantic schema defining the expected
# structured output of the Query Analysis Agent.
from app.agents.schemas import QueryAnalysis
from app.prompts import load_system_prompt

async def load_system_prompt(agent_name: str):
    # Run the synchronous get_prompt() function
    # in a separate thread to avoid blocking the event loop.
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

# Analyzes the user's query and identifies its intent.
async def query_agent(state):
    prompt = await load_system_prompt("query")

    model = llm.with_structured_output(QueryAnalysis)

    result = await model.ainvoke([
        ("system", prompt.content),
        ("human", state["query"]),
    ])




    return {
        # Convert the Pydantic QueryAnalysis object
        # into a standard Python dictionary.
        "intent": result.model_dump(),
        

        # Store the system prompt version used by this agent.
        # Useful for debugging, auditing, and reproducibility.
        "query_prompt_version": {
            "query": {
                "id": prompt.id,
                "version": prompt.version,
            }
        },
    }




'''
replace with "intent": result.model_dump()
by
 # Investment query classification.
    "intent": analysis["intent"],

    # Information required for investment assessment.
    "required_information": analysis["required_information"],

    # Explanation of query classification.
    "reasoning": analysis["reasoning"],
'''