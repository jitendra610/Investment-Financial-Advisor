import asyncio

from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
from ragas.metrics import Faithfulness, ResponseRelevancy

from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def evaluate_answer(query, contexts, response):
    sample = SingleTurnSample(
        user_input=query,
        retrieved_contexts=contexts,
        response=response,
    )

    dataset = EvaluationDataset(samples=[sample])

    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            ResponseRelevancy(),
        ],
        llm=ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        ),
        embeddings=OpenAIEmbeddings(
            model="text-embedding-3-small"
        ),
    )

    return result.to_pandas().to_dict(
        orient="records"
    )[0]