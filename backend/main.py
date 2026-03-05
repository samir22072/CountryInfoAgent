import logging
import os
import uuid
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from langchain_core.messages import HumanMessage, AIMessage
from graph import graph
from models import ChatRequest, TaskStatus, ChatMessage

# In-memory store for background tasks
task_store = {}

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backend")

load_dotenv()
app = FastAPI(title="Country Info Agent API")

# Allow CORS for Next.js frontend
allow_origins = os.environ.get("ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", status_code=202)
async def start_chat(req: ChatRequest, background_tasks: BackgroundTasks):
    logger.info("Received chat request")
    try:
        if "GOOGLE_API_KEY" not in os.environ:
            logger.error("GOOGLE_API_KEY missing from environment")
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY missing.")
        
        task_id = str(uuid.uuid4())
        from models import TaskUpdate
        task_store[task_id] = TaskUpdate(task_id=task_id, status=TaskStatus.PENDING)
        
        logger.info(f"Task created: {task_id}")
        background_tasks.add_task(run_agent_task, task_id, req.messages)
        
        return {"task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in start_chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/chat/{task_id}")
async def get_task_status(task_id: str):
    try:
        if task_id not in task_store:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
        return task_store[task_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_task_status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

def run_agent_task(task_id: str, messages: List[ChatMessage]):
    """
    Background worker that executes the LangGraph and updates the task store.
    """
    logger.info(f"Starting background task: {task_id}")
    langchain_msgs = []
    for msg in messages:
        if msg.role == "user":
            langchain_msgs.append(HumanMessage(content=msg.content))
        else:
            langchain_msgs.append(AIMessage(content=msg.content))
            
    initial_state = {
        "messages": langchain_msgs,
        "retry_count": 0
    }
    task_store[task_id].status = TaskStatus.RUNNING
    
    try:
        logger.info(f"Invoking graph for task: {task_id}")
        for output in graph.stream(initial_state):
            for node_name, state in output.items():
                logger.debug(f"Task {task_id} - Processed node: {node_name}")
                thought_text = ""
                
                if node_name == "identify_intent":
                    country = state.get("country")
                    fields = state.get("intent_fields", [])
                    if country:
                        fields_str = ", ".join(fields) if fields else "general info"
                        thought_text = f"Identified intent: Looking up {fields_str} for {country}."
                    else:
                        thought_text = "Could not identify a specific country from the query."
                        
                elif node_name == "invoke_tool":
                    if state.get("error"):
                        thought_text = f"API Tool Execution Failed: {state.get('error')}"
                    else:
                        thought_text = "Successfully retrieved data from the REST Countries API."
                
                elif node_name == "correct_country_name":
                    thought_text = f"Attempting to correct country name to: {state.get('country')}."
                        
                elif node_name == "synthesize_answer":
                    thought_text = "Synthesizing the answer based on available data."
                
                elif node_name == "validate_answer":
                    feedback = state.get("validator_feedback")
                    if feedback == "VALID":
                        thought_text = "Quality check passed! Finalizing response."
                    else:
                        thought_text = f"Quality check flagged a potential improvement: {feedback}"

                if thought_text:
                    logger.info(f"Task {task_id} thought: {thought_text}")
                    task_store[task_id].thoughts.append(thought_text)
                
                # Check if it's the final output (or if synthesis just finished and validation succeeded)
                if node_name == "validate_answer" and state.get("validator_feedback") == "VALID":
                    if "messages" in state and len(state["messages"]) > 0:
                        logger.info(f"Task {task_id} completed successfully via validator")
                        task_store[task_id].result = state["messages"][-1].content
                        task_store[task_id].status = TaskStatus.COMPLETED
                
                # Handling completion if it didn't go through validation (e.g. no country found)
                elif node_name == "synthesize_answer" and not state.get("country"):
                    if "messages" in state and len(state["messages"]) > 0:
                        logger.info(f"Task {task_id} completed (no country case)")
                        task_store[task_id].result = state["messages"][-1].content
                        task_store[task_id].status = TaskStatus.COMPLETED

        # Final safety check: if the loop finished but status isn't completed, mark it
        if task_store[task_id].status == TaskStatus.RUNNING:
            logger.info(f"Task {task_id} finished iteration, marking COMPLETED")
            task_store[task_id].status = TaskStatus.COMPLETED

    except Exception as e:
        logger.exception(f"Exception in task {task_id}")
        task_store[task_id].status = TaskStatus.FAILED
        task_store[task_id].error = str(e)
