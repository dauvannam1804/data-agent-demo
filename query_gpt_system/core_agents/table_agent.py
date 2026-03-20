import json
import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_table_agent() -> Agent:
    return Agent(
        name="Table Agent",
        role="Xác định các bảng CSV phù hợp nhất với yêu cầu",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn nhận được một Query của người dùng, Ý định định tuyến và một danh sách các Table Metadata (JSON).",
            "Nhiệm vụ của bạn là chọn ra DANH SÁCH CÁC TÊN FILE CSV (ví dụ: ['titanic.csv', 'other.csv']) cung cấp dữ liệu phù hợp để trả lời câu hỏi.",
            "Nếu câu hỏi yêu cầu dữ liệu từ nhiều nguồn (JOIN), hãy chọn tất cả các file liên quan.",
            "Phân tích semantic ngữ nghĩa của các cột trong file CSV để tìm ra các file có chứa những trường dữ liệu mà user cần hỏi.",
            "Trả về kết quả dưới dạng JSON ARRAY chứa các tên file CSV. KHÔNG kèm theo văn bản giải thích nào khác."
        ]
    )

def identify_table(query: str, intent: str, registry_path: str) -> list:
    """
    Load metadata registry and ask the LLM to pick the best tables for the query.
    Returns a list of table names.
    """
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
        
    # Build a compact string of table names and columns for the prompt
    compact_schemas = ""
    for table in registry:
        compact_schemas += f"Table: {table['table_name']} | Columns: {', '.join(table['columns'])}\n"
        
    agent = get_table_agent()
    prompt = f"Query: {query}\nIntent: {intent}\nAvailable Tables:\n{compact_schemas}\n\nDANH SÁCH FILE CSV (JSON ARRAY): "
    
    response = agent.run(prompt)
    try:
        # Dọn dẹp markdown nếu có
        content = response.content.strip().strip('```json').strip('```').strip()
        table_names = json.loads(content)
        if isinstance(table_names, list):
            return table_names
        return [table_names] if table_names else []
    except Exception as e:
        print(f"Error parsing table agent response: {e}")
        # Dự phòng: Nếu LLM trả ra chuỗi ngăn cách bởi dấu phẩy
        raw = response.content.strip()
        if "[" not in raw and "," in raw:
            return [t.strip() for t in raw.split(",")]
        # Trả về chuỗi thô trong list nếu trông giống file
        if ".csv" in raw:
            return [raw]
        return []

if __name__ == "__main__":
    # Test nhanh
    res = identify_table("Liệt kê hành khách trong file titanic", "General", "query_gpt_system/metadata/schema_registry.json")
    print(f"Tables Identified: {res}")
