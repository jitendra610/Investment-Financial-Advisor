
import asyncio
import json
import logging
import re
from functools import lru_cache

from dotenv import load_dotenv

from ragas import evaluate
from ragas.dataset_schema import (
    SingleTurnSample,
    EvaluationDataset,
)
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
)

from langchain_openai import (
    ChatOpenAI,
    OpenAIEmbeddings,
)

load_dotenv()

logger = logging.getLogger(__name__)


# --------------------------------------------
# STEP 1: INITIALIZE EVALUATOR MODELS
# --------------------------------------------

@lru_cache(maxsize=1)
def get_evaluator_models():

    return (
        ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        ),
        OpenAIEmbeddings(
            model="text-embedding-3-small"
        ),
    )


# --------------------------------------------
# STEP 2: EXTRACT KNOWLEDGE CONTEXTS
# --------------------------------------------

def get_contexts(knowledge: dict) -> list[str]:

    if not isinstance(knowledge, dict):
        return []

    # Prefer original retrieved chunks.
    chunks = knowledge.get("chunks")

    if isinstance(chunks, list):
        contexts = []

        for chunk in chunks:
            if isinstance(chunk, dict):
                content = chunk.get("content", "")
            elif isinstance(chunk, str):
                content = chunk
            else:
                continue

            if isinstance(content, str) and content.strip():
                contexts.append(content.strip())

        if contexts:
            return contexts

    # Fallback: combined knowledge context.
    context = knowledge.get("context", "")

    if isinstance(context, str) and context.strip():
        return [context.strip()]

    return []


# --------------------------------------------
# STEP 3: EVALUATE RAG ANSWER
# --------------------------------------------

def evaluate_answer(
    query: str,
    contexts: list[str],
    response: str,
) -> dict:

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not contexts:
        raise ValueError("Retrieved contexts cannot be empty.")

    if not response.strip():
        raise ValueError("Response cannot be empty.")

    sample = SingleTurnSample(
        user_input=query,
        retrieved_contexts=contexts,
        response=response,
    )

    dataset = EvaluationDataset(samples=[sample])

    llm, embeddings = get_evaluator_models()

    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            ResponseRelevancy(),
        ],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=True,
    )

    scores = result.to_pandas().to_dict(
        orient="records"
    )[0]

    return {
        "faithfulness": scores.get("faithfulness"),
        "response_relevancy": scores.get(
            "answer_relevancy"
        ),
    }


# --------------------------------------------
# STEP 4: EXECUTE COMPLETE LANGGRAPH WORKFLOW
# --------------------------------------------

async def evaluate_workflow(
    query: str,
    customer_id: str | None = None,
) -> dict:

    # Lazy import prevents circular imports.
    from app.workflows.investment_graph1 import (
        investment_graph,
    )

    logger.info("Starting investment workflow evaluation")

    # Execute complete dynamic-routing workflow.
    result = await investment_graph.ainvoke(
        {
            "query": query,
            "customer_id": customer_id,
        },
        config={
            "run_name": "investment-workflow-ragas",
            "tags": [
                "investment-advisor",
                "evaluation",
                "ragas",
            ],
            "metadata": {
                "evaluation_type": "ragas",
                "environment": "development",
            },
        },
    )

    status = result.get("status")
    intent = result.get("intent")
    selected_agents = result.get("selected_agents") or []
    requires_compliance = result.get(
        "requires_compliance", False
    )

    response = result.get("response")
    knowledge = result.get("knowledge") or {}

    contexts = get_contexts(knowledge)

    output = {
        "query": query,
        "customer_id": customer_id,
        "intent": intent,
        "selected_agents": selected_agents,
        "status": status,
        "response": response,
        "retrieved_context_count": len(contexts),
        "ragas_scores": None,
        "evaluation_status": "skipped",
        "evaluation_reason": None,
    }

    # --------------------------------------------
    # STEP 5: HANDLE DYNAMIC ROUTING
    # --------------------------------------------

    if result.get("requires_clarification"):
        output["evaluation_reason"] = (
            "Workflow requires clarification."
        )
        return output

    if status != "completed":
        output["evaluation_reason"] = (
            f"Workflow status is {status}."
        )
        return output

    if not contexts:
        output["evaluation_reason"] = (
            "Knowledge Agent did not return contexts."
        )
        return output

    if not isinstance(response, str) or not response.strip():
        output["evaluation_reason"] = (
            "Response Agent did not return a valid response."
        )
        return output

    # --------------------------------------------
    # STEP 6: COMPLIANCE VALIDATION
    # --------------------------------------------

    if requires_compliance:

        compliance = result.get("compliance") or {}

        if (
            compliance.get("compliant") is not True
            or compliance.get("human_review_required") is not False
        ):
            output["evaluation_reason"] = (
                "Compliance approval not confirmed."
            )
            return output

    # --------------------------------------------
    # STEP 7: RUN RAGAS
    # --------------------------------------------

    scores = await asyncio.to_thread(
        evaluate_answer,
        query,
        contexts,
        response,
    )

    output["ragas_scores"] = scores
    output["evaluation_status"] = "completed"

    logger.info("RAGAS workflow evaluation completed")

    return output


# --------------------------------------------
# STEP 8: TEST EXECUTION
# --------------------------------------------

async def main():

    # Educational query: suitable for RAGAS testing.
    query = "where to invest 100k in a diversified portfolio with moderate risk tolerance and a 5-year investment horizon"

    result = await evaluate_workflow(
        query=query,
        customer_id="CUST-003",
    )

    print(json.dumps(result, indent=4, default=str))


if __name__ == "__main__":
    asyncio.run(main())
