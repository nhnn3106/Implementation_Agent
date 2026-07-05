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

# Define your list of tools here
tools_list = [calculate_infrastructure_cost]
