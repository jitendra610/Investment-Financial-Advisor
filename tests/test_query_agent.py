import asyncio

from app.agents.query_agent import query_agent


async def test_query_agent():

    state = {
        "query": "I want to invest £10,000 for five years."
    }

    result = await query_agent(state)

    
    for key, value in result["intent"].items():
        print(f"{key}: {value}")

    for key, value in result["query_prompt_version"].items():
        print(f"{key}: {value}")
  


asyncio.run(test_query_agent())