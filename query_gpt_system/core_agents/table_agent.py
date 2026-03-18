import json
import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_table_agent() -> Agent:
    return Agent(
        name="Table Agent",
        role="Xác định bảng CSV phù hợp nhất với yêu cầu",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn nhận được một Query của người dùng, Ý định định tuyến và một danh sách các Table Metadata (JSON).",
            "Nhiệm vụ của bạn là chọn ra ĐÚNG 1 TÊN FILE CSV (ví dụ: titanic.csv) cung cấp dữ liệu phù hợp để trả lời câu hỏi.",
            "Phân tích semantic ngữ nghĩa của các cột trong file CSV để tìm ra file có chứa những trường dữ liệu mà user cần hỏi.",
            "CHỈ trả về kết quả là TÊN FILE CSV (không kèm theo văn bản giải thích nào khác)."
        ]
    )

def identify_table(query: str, intent: str, registry_path: str) -> str:
    """
    Load metadata registry and ask the LLM to pick the best table for the query.
    """
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
        
    # Build a compact string of table names and columns for the prompt
    compact_schemas = ""
    for table in registry:
        compact_schemas += f"Table: {table['table_name']} | Columns: {', '.join(table['columns'])}\n"
        
    agent = get_table_agent()
    prompt = f"Query: {query}\nIntent: {intent}\nAvailable Tables:\n{compact_schemas}\n\nTÊN FILE CSV LÀ: "
    
    response = agent.run(prompt)
    # Return matched filename
    ans = response.content.strip()
    return ans
