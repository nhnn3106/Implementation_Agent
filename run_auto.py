import sys
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from main import app
from tools import export_plan_to_json
import json

if len(sys.argv) > 1:
    prompt = sys.argv[1]
else:
    prompt = """Tôi đang cần một website bán giày với số lượng người 100000 người trong mỗi phút thời gian sống của dự án lâu , không cần bảo trì nhiều, đồ trễ của web thì thấp nhất < 10 ms, thời gian hoạt động mãi mãi, giao diện phải dễ nhìn, có các tính năng chính như đăng ký, đăng nhập, quên mật khẩu, xem các mặt hàng, lọc mặt hàng theo các tiêu chí quan trọng như giá cả, độ hot, độ mới, hãng nào, size nào, màu nào, thêm giỏ hàng, xóa giỏ hàng, xem giỏ hàng, thanh toán bằng chuyển khoản và tiền mặt, comment, đánh giá mặt hàng, xem tiến độ giao hàng"""

current_state = {
    "messages": [HumanMessage(content=prompt)],
    "requirements_gathered": False,
    "architecture_ready": False,
    "plan_finalized": False,
    "user_approval_pending": False,
    "debate_loop_count": 0
}

print("Running graph...")
for output in app.stream(current_state):
    for key, value in output.items():
        if "messages" in value:
            current_state["messages"].extend(value["messages"])
        for state_key in ["requirements_gathered", "architecture_ready", "plan_finalized", "user_approval_pending", "debate_loop_count"]:
            if state_key in value:
                current_state[state_key] = value[state_key]

        print(f"[{key}] processed.")
        if current_state.get("user_approval_pending"):
            print("Approval pending, exporting plan...")
            history = [{"role": getattr(m, "name", "assistant") if isinstance(m, AIMessage) else "user", "content": m.content} for m in current_state["messages"]]
            
            import re
            plan_messages = []
            for msg in current_state["messages"]:
                if isinstance(msg, AIMessage) and getattr(msg, "name", "") in ["moderator", "architecture"]:
                    clean_content = re.sub(r'<thought>.*?</thought>', '', msg.content, flags=re.DOTALL)
                    clean_content = re.sub(r'\[ROUTE:.*?\]', '', clean_content, flags=re.IGNORECASE)
                    clean_content = clean_content.replace("[ASK_USER]", "").strip()
                    if clean_content:
                        plan_messages.append(f"**[{getattr(msg, 'name', 'agent').upper()}]**\n{clean_content}")
            
            plan_content = "\n\n---\n\n".join(plan_messages)
            
            data = {
                "project_status": "Approved by Auto-runner",
                "additional_requirements": "None",
                "implementation_plan": plan_content,
                "conversation_history": history
            }
            from tools import export_plan_to_md
            res = export_plan_to_md(data)
            print(f"Export result: {res}")
            sys.exit(0)
