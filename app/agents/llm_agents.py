import json
import asyncio

async def human_review_agent(state):
    return {
        "status": "needs_review",
        "response": (
            "This request requires review by an appropriately "
            "qualified adviser or compliance reviewer before "
            "personalized investment guidance can be provided."
        ),
    }