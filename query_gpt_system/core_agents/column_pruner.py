import json
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_column_pruner_agent() -> Agent:
    return Agent(
        name="Column Pruner Agent",
        role="Loại bỏ các cột dư thừa không cần thiết cho câu hỏi",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn nhận được Query của người dùng và Schema đầy đủ của một bảng CSV bao gồm tên tất cả các cột.",
            "Nhiệm vụ của bạn là chỉ giữ lại những cột THỰC SỰ CẦN THIẾT để viết câu query SQL trả lời câu hỏi.",
            "Hãy trả về MỘT CHUỖI JSON hợp lệ có định dạng: {\"needed_columns\": [\"col1\", \"col2\"]}.",
            "Không giải thích, chỉ trả về JSON. Đảm bảo JSON có thể parse được."
        ]
    )

def prune_columns(query: str, table_schema: dict) -> list:
    """
    Pass the user query and the full table schema to the LLM to get a pruned list of columns.
    """
    agent = get_column_pruner_agent()
    prompt = f"Query: {query}\nFull Schema: {json.dumps(table_schema, ensure_ascii=False)}"
    response = agent.run(prompt)
    try:
        content = json.loads(response.content.strip().strip('```json').strip('```'))
        return content.get("needed_columns", [])
    except Exception as e:
        print(f"Error parsing prune response: {e}")
        # Gặp lỗi parse thì trả về toàn bộ cột để safe
        return table_schema.get("columns", [])
