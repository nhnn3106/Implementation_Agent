import os
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from tools import tools_list, export_plan_to_json
from validation import validate_prompt

# Load environment variables
load_dotenv()

# Define the state of our graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    requirements_gathered: bool
    architecture_ready: bool
    plan_finalized: bool
    user_approval_pending: bool

# Initialize LLM
llm = ChatOllama(model=os.getenv("MODEL_NAME", "gemma"), temperature=0.2)

def load_skill(skill_name: str) -> str:
    path = os.path.join(".agents", "skills", skill_name, "SKILL.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return f"You are a {skill_name} expert."

# Nodes
def moderator_node(state: AgentState, config: RunnableConfig):
    print("\n--- MODERATOR ---")
    messages = state['messages']
    skill_content = load_skill("moderator")
    
    sys_msg = SystemMessage(content=skill_content)
    # Moderator evaluates the whole conversation
    response = llm.invoke([sys_msg] + messages, config=config)
    print(f"Moderator Output:\n{response.content}\n")
    
    # Intercept Search Command
    import re
    search_match = re.search(r'\[SEARCH:\s*(.*?)\]', response.content)
    if search_match:
        from duckduckgo_search import DDGS
        query = search_match.group(1).strip()
        print(f"Moderator is searching the web for: {query}")
        try:
            results = DDGS().text(query, max_results=3)
            search_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            if not search_text:
                search_text = "No results found."
        except Exception as e:
            search_text = f"Search failed: {e}"
        
        return {"messages": [
            AIMessage(content=response.content),
            SystemMessage(content=f"Web Search Results for '{query}':\n{search_text}\n\nUse this information to continue evaluating the architecture.")
        ]}
        
    if "[ASK_USER]" in response.content:
        return {"messages": [AIMessage(content=response.content)], "user_approval_pending": True}
    
    return {"messages": [AIMessage(content=response.content)]}

def planner_node(state: AgentState, config: RunnableConfig):
    print("\n--- PLANNER ---")
    messages = state['messages']
    skill_content = load_skill("planner")
    
    sys_msg = SystemMessage(content=skill_content)
    response = llm.invoke([sys_msg] + messages, config=config)
    
    print(f"Planner Output:\n{response.content}\n")
    
    # Planner now operates autonomously and immediately finalizes requirements
    return {"requirements_gathered": True, "messages": [AIMessage(content=response.content)]}

def architecture_node(state: AgentState, config: RunnableConfig):
    print("\n--- ARCHITECTURE ---")
    messages = state['messages']
    skill_content = load_skill("architecture")
    
    sys_msg = SystemMessage(content=skill_content)
    # Architecture only needs to see the final BRD from planner and user request, but we pass full context
    response = llm.invoke([sys_msg] + messages, config=config)
    
    print(f"Architecture Output:\n{response.content}\n")
    return {"architecture_ready": True, "messages": [AIMessage(content=response.content)]}


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
    if state.get("user_approval_pending"):
        return END
        
    # Check if the last message is a search result. If so, loop back to moderator.
    if len(state["messages"]) > 0:
        last_msg = state["messages"][-1]
        
        # If it was a search result
        if isinstance(last_msg, SystemMessage) and "Web Search Results for" in last_msg.content:
            return "moderator"
            
        content = last_msg.content.upper()
        if "[ROUTE: PLANNER]" in content:
            return "planner"
        if "[ROUTE: ARCHITECTURE]" in content:
            return "architecture"
            
    # Default to END if no route specified
    return END

workflow.add_conditional_edges("moderator", route_from_moderator)

# Planner always routes back to moderator autonomously
workflow.add_edge("planner", "moderator")

workflow.add_edge("architecture", "moderator")

# Compile
app = workflow.compile()

def run_chat():
    print("Welcome to A2A System.")
    
    # Initialize state
    current_state = {"messages": [], "requirements_gathered": False, "architecture_ready": False, "plan_finalized": False, "user_approval_pending": False}
    
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        if not validate_prompt(user_input):
            print("System: Malicious input detected. Request blocked.")
            continue
            
        current_state["messages"].append(HumanMessage(content=user_input))
        
        # Stream the graph execution
        for output in app.stream(current_state):
            for key, value in output.items():
                if "messages" in value:
                    # Update current state messages
                    current_state["messages"].extend(value["messages"])
                
                # Update state flags
                for state_key in ["requirements_gathered", "architecture_ready", "plan_finalized", "user_approval_pending"]:
                    if state_key in value:
                        current_state[state_key] = value[state_key]
            
            # If we hit END (because of Human-in-the-loop in Planner), we break to wait for next input
            if current_state.get("plan_finalized"):
                print("\nSystem: Implementation Plan Finalized! Exiting...")
                return
        
        if not current_state["requirements_gathered"]:
            print("\n(Waiting for your response to Planner...)")

if __name__ == "__main__":
    run_chat()
