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

def export_plan_to_json(plan_content: str, filename: str = "implementation_plan.json") -> str:
    """Exports the final implementation plan to a JSON file."""
    try:
        data = {"implementation_plan": plan_content}
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return f"Successfully saved to {filename}"
    except Exception as e:
        return f"Error saving file: {e}"

# Define your list of tools here
tools_list = [calculate_infrastructure_cost]
