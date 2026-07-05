import os
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from tools import tools_list
from validation import validate_prompt

# Load environment variables
load_dotenv()

# Define the state of our graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    requirements_gathered: bool
    architecture_ready: bool
    plan_finalized: bool

# Initialize LLM
llm = ChatOllama(model=os.getenv("MODEL_NAME", "gemma"), temperature=0)

# Nodes
def moderator_node(state: AgentState):
    print("--- MODERATOR ---")
    messages = state['messages']
    
    if not state.get("requirements_gathered"):
        # First time, forward to Planner
        return {"messages": [AIMessage(content="Forwarding to Planner to gather requirements.")]}
    elif not state.get("architecture_ready"):
        # Requirements gathered, forward to Architecture
        return {"messages": [AIMessage(content="Requirements complete. Forwarding to Architecture.")]}
    else:
        # Architecture is ready, Review it
        last_msg = messages[-1].content
        print("Moderator Reviewing Architecture...")
        
        if "REJECT" in last_msg:
            return {"messages": [AIMessage(content="Architecture rejected. Need revision.")], "architecture_ready": False}
        else:
            final_plan = "# Implementation_Plan.md\n\n(Auto-generated plan based on architecture)"
            return {"messages": [AIMessage(content=f"Plan finalized.\n{final_plan}")], "plan_finalized": True}

def planner_node(state: AgentState):
    print("--- PLANNER ---")
    messages = state['messages']
    
    human_messages = [m for m in messages if isinstance(m, HumanMessage)]
    last_user_msg = human_messages[-1].content if human_messages else ""
    
    # Simple simulated HITL logic
    if "[END_QA]" in last_user_msg:
        print("Planner: Requirements gathered successfully.")
        return {"requirements_gathered": True, "messages": [AIMessage(content="Requirements Document generated.")]}
    else:
        print("Planner: Asking clarifying question...")
        # Simulate wait for user input
        return {"messages": [AIMessage(content="Can you clarify the target platform (Web/Mobile)?")]}

def architecture_node(state: AgentState):
    print("--- ARCHITECTURE ---")
    blueprint = "Technical Blueprint: Microservices, React Frontend, Node.js Backend, PostgreSQL."
    return {"architecture_ready": True, "messages": [AIMessage(content=f"Architecture completed: {blueprint}")]}


# Define the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("moderator", moderator_node)
workflow.add_node("planner", planner_node)
workflow.add_node("architecture", architecture_node)

# Set entry point
workflow.set_entry_point("moderator")

# Add conditional edges
def route_from_moderator(state: AgentState):
    if state.get("plan_finalized"):
        return END
    if not state.get("requirements_gathered"):
        return "planner"
    return "architecture"

workflow.add_conditional_edges("moderator", route_from_moderator)

def route_from_planner(state: AgentState):
    if state.get("requirements_gathered"):
        return "moderator"
    return END

workflow.add_edge("architecture", "moderator")

# Compile
app = workflow.compile()

def run_chat():
    print("Welcome to A2A System.")
    
    # No API Key needed for Local Model

    user_input = input("User: ")
    
    if not validate_prompt(user_input):
        print("System: Malicious input detected. Request blocked.")
        return
        
    inputs = {"messages": [HumanMessage(content=user_input)], "requirements_gathered": False, "architecture_ready": False, "plan_finalized": False}
    
    # Run the graph
    for output in app.stream(inputs):
        pass # output is handled inside nodes for this demo

if __name__ == "__main__":
    run_chat()
