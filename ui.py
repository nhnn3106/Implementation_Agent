import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from main import app
from validation import validate_prompt
import os

st.set_page_config(page_title="A2A Architecture Agent", layout="wide")

st.title("🚀 A2A Implementation Agent Workflow")

# Display the Graph using LangGraph's mermaid capability
st.sidebar.title("Workflow Graph")
try:
    png_bytes = app.get_graph().draw_mermaid_png()
    st.sidebar.image(png_bytes, use_column_width=True)
except Exception as e:
    st.sidebar.warning(f"Could not render graph image automatically. ({e})")

st.sidebar.markdown("""
**Current Roles:**
1. **Moderator**: PM / Coordinator
2. **Planner**: Requirement Analysis
3. **Architecture**: System Design
""")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.requirements_gathered = False
    st.session_state.architecture_ready = False
    st.session_state.plan_finalized = False
    
# Render chat history
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)

# Input
if prompt := st.chat_input("Enter your request here (e.g., 'Create a video sharing app')..."):
    if not validate_prompt(prompt):
        st.error("System: Malicious input detected. Request blocked.")
    else:
        # Display user input
        st.chat_message("user").write(prompt)
        
        # Add to state
        st.session_state.messages.append(HumanMessage(content=prompt))
        
        # Construct current state
        current_state = {
            "messages": st.session_state.messages,
            "requirements_gathered": st.session_state.requirements_gathered,
            "architecture_ready": st.session_state.architecture_ready,
            "plan_finalized": st.session_state.plan_finalized
        }
        
        # Run through the graph
        with st.spinner("Agents are thinking..."):
            for output in app.stream(current_state):
                for key, value in output.items():
                    if "messages" in value:
                        # Extract the new messages
                        new_messages = value["messages"]
                        for n_msg in new_messages:
                            st.chat_message("assistant").write(f"**{key.upper()}**: {n_msg.content}")
                            st.session_state.messages.append(AIMessage(content=f"**{key.upper()}**: {n_msg.content}"))
                    
                    if "requirements_gathered" in value:
                        st.session_state.requirements_gathered = value["requirements_gathered"]
                    if "architecture_ready" in value:
                        st.session_state.architecture_ready = value["architecture_ready"]
                    if "plan_finalized" in value:
                        st.session_state.plan_finalized = value["plan_finalized"]
                
            if st.session_state.plan_finalized:
                st.success("Implementation Plan Finalized!")
