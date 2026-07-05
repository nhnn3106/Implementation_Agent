from langchain_core.tools import tool

@tool
def calculate_infrastructure_cost(server_type: str, instances: int) -> str:
    """Calculates estimated monthly infrastructure cost based on server type and count."""
    rates = {
        "t3.micro": 10,
        "m5.large": 70,
        "c5.xlarge": 150
    }
    cost_per_instance = rates.get(server_type.lower(), 50)
    total = cost_per_instance * instances
    return f"Estimated cost for {instances}x {server_type}: ${total}/month"

import json
import os
import datetime

def export_plan_to_json(data: dict, filename: str = None) -> str:
    """Exports the final implementation plan to a JSON file with a timestamp."""
    try:
        # Ensure output directory exists
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename or filename == "final_plan.json":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"final_plan_{timestamp}.json"
            
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return f"Successfully saved to {filepath}"
    except Exception as e:
        return f"Error saving file: {e}"

def export_plan_to_md(data: dict, filename: str = None) -> str:
    """Exports the final implementation plan to a Markdown file with a timestamp."""
    try:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename or filename == "final_plan.md":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"final_plan_{timestamp}.md"
            
        filepath = os.path.join(output_dir, filename)
        
        md_content = f"# 🚀 Implementation Plan\n\n"
        md_content += f"**Status:** {data.get('project_status', 'N/A')}\n\n"
        
        reqs = data.get('additional_requirements', '').strip()
        if reqs:
            md_content += f"## 📌 Additional Requirements\n{reqs}\n\n"
            
        md_content += f"## 🏗️ Architecture & Blueprint\n{data.get('implementation_plan', '')}\n\n"
        md_content += f"## 💬 Debate & Conversation History\n"
        
        for msg in data.get('conversation_history', []):
            role = str(msg.get('role')).upper()
            content = str(msg.get('content'))
            if content.strip():
                md_content += f"**[{role}]**:\n{content}\n\n"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        return f"Successfully saved to {filepath}"
    except Exception as e:
        return f"Error saving markdown file: {e}"

# Define your list of tools here
tools_list = [calculate_infrastructure_cost]
