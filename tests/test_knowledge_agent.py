import asyncio
from app.agents.data_agents import knowledge_agent


async def main():
    state = {
        "query": "Explain investment risk capacity and tolerance"
    }

    result = await knowledge_agent(state)

    print("\nRetrieved Knowledge:")
    print(result["knowledge"]["context"])

    print("\nSources:")
    print(result["knowledge"]["sources"])

    assert result["knowledge"]["sources"], "No knowledge retrieved"

    print("\nKNOWLEDGE AGENT TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())