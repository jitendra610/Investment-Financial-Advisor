import os
from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()


def get_langfuse_handler():
    required = (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_BASE_URL",
    )

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            f"Missing Langfuse configuration: {missing}"
        )

    return CallbackHandler()