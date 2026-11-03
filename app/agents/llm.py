from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from app.core.config import settings
import os


load_dotenv()

llm = ChatOpenAI(
    model=getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4o-mini"),
    temperature=0,
    timeout=30,
    max_retries=2,
)