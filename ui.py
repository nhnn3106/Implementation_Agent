import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from main import app
from validation import validate_prompt
import os

st.set_page_config(page_title="A2A Architecture Agent", layout="wide")

st.title("🚀 A2A Implementation Agent Workflow")

import streamlit.components.v1 as components

# Dynamic Sequence Diagram
st.sidebar.title("📡 Live Agent Sequence")
sequence_placeholder = st.sidebar.empty()

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
    st.session_state.user_approval_pending = False
    st.session_state.sequence = [
        "sequenceDiagram", 
        "    participant U as User", 
        "    participant M as Moderator", 
        "    participant P as Planner", 
        "    participant A as Architecture",
        "    participant Web as Web Search"
    ]

def render_sequence():
    mermaid_code = "\n".join(st.session_state.sequence)
    with sequence_placeholder:
        components.html(
            f"""
            <div class="mermaid">
                {mermaid_code}
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
            </script>
            """,
            height=600, scrolling=True
        )

import re

def render_assistant_message(content: str):
    thought_match = re.search(r'<thought>(.*?)</thought>', content, re.DOTALL)
    if thought_match:
        thought_process = thought_match.group(1).strip()
        role_match = re.match(r'^\*\*(.*?)\*\*:', content)
        role_name = role_match.group(1) if role_match else "Agent"
        with st.expander(f"🧠 {role_name} Thinking Process"):
            st.write(thought_process)
        content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL).strip()
    if content:
        st.write(content)

# Render initial sequence
render_sequence()
# Render chat history
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            render_assistant_message(msg.content)

# Input
if prompt := st.chat_input("Enter your request here (e.g., 'Create a video sharing app')..."):
    if not validate_prompt(prompt):
        st.error("System: Malicious input detected. Request blocked.")
    else:
        # Display user input
        st.chat_message("user").write(prompt)
        
        # Add to state
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.session_state.sequence.append("    U->>M: User Request")
        render_sequence()
        
        # Construct current state
        current_state = {
            "messages": st.session_state.messages,
            "requirements_gathered": st.session_state.requirements_gathered,
            "architecture_ready": st.session_state.architecture_ready,
            "plan_finalized": st.session_state.plan_finalized,
            "user_approval_pending": st.session_state.user_approval_pending,
            "debate_loop_count": st.session_state.get("debate_loop_count", 0)
        }
        
        # Run through the graph
        from langchain_core.callbacks.base import BaseCallbackHandler
        stream_placeholder = st.empty()
        
        class StreamlitTokenHandler(BaseCallbackHandler):
            def __init__(self, placeholder):
                self.placeholder = placeholder
                self.text = ""
            def on_llm_new_token(self, token: str, **kwargs):
                self.text += token
                self.placeholder.info("🤖 *Agent is thinking in real-time...*\n\n" + self.text + " ▌")

        config = {"callbacks": [StreamlitTokenHandler(stream_placeholder)]}

        with st.spinner("Agents are thinking..."):
            for output in app.stream(current_state, config=config):
                stream_placeholder.empty() # Clear live stream when node finishes
                for key, value in output.items():
                    if "messages" in value:
                        # Extract the new messages
                        new_messages = value["messages"]
                        for n_msg in new_messages:
                            full_content = f"**{key.upper()}**: {n_msg.content}"
                            with st.chat_message("assistant"):
                                render_assistant_message(full_content)
                            st.session_state.messages.append(AIMessage(content=full_content))
                            
                    # Track sequence dynamically
                    for state_key in ["requirements_gathered", "architecture_ready", "plan_finalized", "user_approval_pending", "debate_loop_count"]:
                        if state_key in value:
                            st.session_state[state_key] = value[state_key]

                    if key == "planner":
                        st.session_state.sequence.append("    M->>P: Forward to Planner")
                        st.session_state.sequence.append("    P-->>M: Requirements BRD")
                    elif key == "architecture":
                        st.session_state.sequence.append("    M->>A: Forward to Architecture")
                        st.session_state.sequence.append("    A-->>M: Architecture Blueprint")
                    elif key == "moderator":
                        if any("Web Search Results for" in msg.content for msg in value.get("messages", []) if isinstance(msg, SystemMessage)):
                            st.session_state.sequence.append("    M->>Web: Search Internet")
                            st.session_state.sequence.append("    Web-->>M: Search Results")
                        elif value.get("user_approval_pending"):
                            st.session_state.sequence.append("    M->>U: Request Approval [ASK_USER]")
                        elif not value.get("architecture_ready") and st.session_state.requirements_gathered:
                            st.session_state.sequence.append("    M->>A: REVISE Design!")
                    
                    render_sequence()
                    
                    if "requirements_gathered" in value:
                        st.session_state.requirements_gathered = value["requirements_gathered"]
                    if "architecture_ready" in value:
                        st.session_state.architecture_ready = value["architecture_ready"]
                    if "plan_finalized" in value:
                        st.session_state.plan_finalized = value["plan_finalized"]
                    if "user_approval_pending" in value:
                        st.session_state.user_approval_pending = value["user_approval_pending"]
                
            if st.session_state.plan_finalized:
                st.success("Implementation Plan Finalized and Exported!")
            elif st.session_state.user_approval_pending:
                st.info("Agents finished their evaluation. Awaiting your action.")

# Finalization UI
if st.session_state.user_approval_pending and not st.session_state.plan_finalized:
    st.info("The Moderator is waiting for your approval. You can provide feedback in the chat to revise it, OR finalize it below.")
    
    plan_messages = []
    for msg in st.session_state.messages:
        if isinstance(msg, AIMessage) and getattr(msg, "name", "") in ["moderator", "architecture"]:
            clean_content = re.sub(r'<thought>.*?</thought>', '', msg.content, flags=re.DOTALL)
            clean_content = re.sub(r'\[ROUTE:.*?\]', '', clean_content, flags=re.IGNORECASE)
            clean_content = clean_content.replace("[ASK_USER]", "").strip()
            if clean_content:
                plan_messages.append(f"**[{getattr(msg, 'name', 'agent').upper()}]**\n{clean_content}")
            
    plan_content = "\n\n---\n\n".join(plan_messages)
            
    with st.expander("📄 Review Final Implementation Plan", expanded=True):
        st.markdown(plan_content)
        
    with st.form("finalize_form"):
        reqs = st.text_area("Additional Requirements or Notes (Bổ sung thêm kiến thức hay yêu cầu):")
        submitted = st.form_submit_button("✅ Chốt sổ (Export Plan)")
        if submitted:
            history = [{"role": getattr(m, "name", "assistant") if isinstance(m, AIMessage) else "user", "content": m.content} for m in st.session_state.messages]
            
            data = {
                "project_status": "Approved",
                "additional_requirements": reqs,
                "implementation_plan": plan_content,
                "conversation_history": history
            }
            from tools import export_plan_to_md
            res = export_plan_to_md(data)
            st.session_state.plan_finalized = True
            st.session_state.user_approval_pending = False
            st.success(res)
            st.rerun()

if st.session_state.plan_finalized:
    st.success("Implementation Plan Finalized and Exported to ./output/ !")
