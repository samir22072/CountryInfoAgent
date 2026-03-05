from typing import Literal
from langgraph.graph import StateGraph, START, END

from models import AgentState
from nodes import identify_intent, invoke_tool, synthesize_answer, validate_answer, correct_country_name

def route_after_intent(state: AgentState) -> Literal["invoke_tool", "synthesize_answer"]:
    """Decide whether to call the tool or go straight to synthesis."""
    if state.get("country"):
        return "invoke_tool"
    return "synthesize_answer"

def route_after_tool(state: AgentState) -> Literal["correct_country_name", "synthesize_answer"]:
    """If tool fails with 404, try to correct the name once."""
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    
    if error and "not found" in error.lower() and retry_count < 2:
        return "correct_country_name"
    return "synthesize_answer"

def route_after_synthesis(state: AgentState) -> Literal["synthesize_answer", "__end__"]:
    """Decide whether to End or loop back for refinement based on validation."""
    feedback = state.get("validator_feedback")
    retry_count = state.get("retry_count", 0)
    
    if feedback and feedback != "VALID" and retry_count < 3:
        return "synthesize_answer"
    return END

# Define the graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("identify_intent", identify_intent)
builder.add_node("invoke_tool", invoke_tool)
builder.add_node("synthesize_answer", synthesize_answer)
builder.add_node("validate_answer", validate_answer)
builder.add_node("correct_country_name", correct_country_name)

# Add edges
builder.add_edge(START, "identify_intent")

builder.add_conditional_edges(
    "identify_intent", 
    route_after_intent
)

builder.add_conditional_edges(
    "invoke_tool",
    route_after_tool
)

builder.add_edge("correct_country_name", "invoke_tool")

builder.add_edge("synthesize_answer", "validate_answer")

builder.add_conditional_edges(
    "validate_answer",
    route_after_synthesis
)

# Compile graph
graph = builder.compile()
