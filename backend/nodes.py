import logging
import os
import requests
import json
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.messages import HumanMessage, SystemMessage

from models import AgentState
from llm_factory import get_llm

logger = logging.getLogger("backend.nodes")

# Load configuration from JSON file
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r") as f:
    config = json.load(f)


# Define Pydantic model for structured output
class IntentExtraction(BaseModel):
    """Extraction of the target country and the user's specific intent fields."""
    country: Optional[str] = Field(description="The name of the country the user is asking about, if any.")
    intent_fields: Optional[List[str]] = Field(description="The specific attributes or facts the user wants to know about the country (e.g., population, capital, currency, area, languages, borders).")
    dynamic_instructions: Optional[str] = Field(description="Custom instructions or prompts generated for the synthesis and validation nodes based on the user's specific query tone or complexity.")


def identify_intent(state: AgentState) -> AgentState:
    """
    Node 1: Identify intent. Extracts the country name and fields the user wants.
    """
    logger.info("Node: identify_intent")
    messages = state["messages"]
    retry_count = state.get("retry_count", 0)
    
    # Create a transcript of the last few messages for context
    transcript = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-5:]])
    
    llm = get_llm()
    eval_llm = llm.with_structured_output(IntentExtraction)
    
    # Use LLM to extract the structure
    prompt = config["prompts"]["identify_intent"].format(transcript=transcript)
    extraction = eval_llm.invoke(prompt)
    
    logger.info(f"Extraction result: country={extraction.country}, fields={extraction.intent_fields}")
    logger.info(f"Dynamic Instructions: {extraction.dynamic_instructions}")
    
    return {
        "country": extraction.country,
        "intent_fields": extraction.intent_fields,
        "dynamic_instructions": extraction.dynamic_instructions,
        "error": None,
        "api_response": None,
        "retry_count": retry_count,
        "validator_feedback": None
    }

def invoke_tool(state: AgentState) -> AgentState:
    """
    Node 2: Tool Invocation. Calls the REST Countries API.
    """
    country = state.get("country")
    logger.info(f"Node: invoke_tool for country={country}")
    if not country:
        logger.warning("No country identified for invocation")
        return {"error": "No country identified in the query.", "api_response": None}
    
    url = config["tool_url"].format(country=country)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            logger.warning(f"Country {country} not found (404)")
            return {"error": f"Country '{country}' not found.", "api_response": None}
        elif response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                logger.info("Successfully retrieved API data")
                return {"api_response": data[0], "error": None}
            else:
                logger.error("Unexpected API response format")
                return {"error": "Unexpected API response format.", "api_response": None}
        else:
            logger.error(f"API returned status code {response.status_code}")
            return {"error": f"API returned status code {response.status_code}", "api_response": None}
    except Exception as e:
        logger.exception("API request failed")
        return {"error": f"API request failed: {str(e)}", "api_response": None}

def synthesize_answer(state: AgentState) -> AgentState:
    """
    Node 3: Answer Synthesis. Takes the original message and the API data to format a response.
    """
    logger.info("Node: synthesize_answer")
    messages = state["messages"]
    api_response = state.get("api_response")
    error = state.get("error")
    country = state.get("country")
    dynamic_instructions = state.get("dynamic_instructions")
    
    feedback = state.get("validator_feedback")
    
    llm = get_llm()
    
    if error:
        logger.info(f"Synthesizing error response: {error}")
        system_prompt = config["prompts"]["synthesize_error"].format(error=error)
    elif not country:
        logger.info("Synthesizing no-country response")
        system_prompt = config["prompts"]["synthesize_no_country"]
    else:
        logger.info(f"Synthesizing success response for {country}")
        system_prompt = config["prompts"]["synthesize_success"].format(
            country=country,
            api_response=api_response
        )
        if dynamic_instructions:
            logger.info("Appending dynamic instructions to synthesis prompt")
            system_prompt += f"\n\nADDITIONAL INSTRUCTIONS: {dynamic_instructions}"
            
        if feedback:
            logger.info("Incorporating validator feedback into prompt")
            system_prompt += f"\n\nCRITICAL FEEDBACK FROM PREVIOUS ATTEMPT: {feedback}. Please address this in your response."
    
    messages_for_llm = [SystemMessage(content=system_prompt)] + messages
    response = llm.invoke(messages_for_llm)
    
    new_messages = messages + [response]
    return {"messages": new_messages}

def validate_answer(state: AgentState) -> AgentState:
    """
    Node 4: Validator. Evaluates the synthesized answer.
    """
    logger.info("Node: validate_answer")
    new_message = state["messages"][-1].content
    user_query = state["messages"][-2].content if len(state["messages"]) >= 2 else "Initial query"
    api_data = state.get("api_response")
    dynamic_instructions = state.get("dynamic_instructions")
    
    if not api_data:
        logger.info("No API data, bypassing validation")
        return {"validator_feedback": "VALID"}
        
    llm = get_llm()
    prompt = config["prompts"]["validator"].format(
        query=user_query,
        api_data=api_data,
        answer=new_message
    )
    
    if dynamic_instructions:
        prompt += f"\n\nNote: The synthesized answer should have followed these instructions: {dynamic_instructions}"
    
    response = llm.invoke(prompt).content.strip()
    logger.info(f"Validator result: {response}")
    
    if response.startswith("VALID"):
        return {"validator_feedback": "VALID"}
    else:
        return {
            "validator_feedback": response,
            "retry_count": state.get("retry_count", 0) + 1
        }

def correct_country_name(state: AgentState) -> AgentState:
    """
    Node 5: Correction. Attempts to fix a misspelled country name.
    """
    country = state.get("country")
    logger.info(f"Node: correct_country_name for {country}")
    llm = get_llm()
    prompt = config["prompts"]["correction"].format(country=country)
    
    correction = llm.invoke(prompt).content.strip().split("\n")[0].replace(".", "").replace("\"", "")
    logger.info(f"Correction suggested: {correction}")
    
    return {
        "country": correction,
        "retry_count": state.get("retry_count", 0) + 1,
        "error": None
    }
