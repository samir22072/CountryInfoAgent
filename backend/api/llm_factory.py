import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("backend.llm_factory")

def get_llm():
    model = os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash")
    temperature = float(os.environ.get("GOOGLE_TEMPERATURE", 0.0))
    
    logger.info(f"Instantiating LLM: {model} (temp: {temperature})")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature
    )
