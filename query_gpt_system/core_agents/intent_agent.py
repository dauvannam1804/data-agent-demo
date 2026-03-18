from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_intent_agent() -> Agent:
    return Agent(
        name="Intent Agent",
        role="Phân loại ngữ cảnh/chủ đề của câu hỏi",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn nhận được một câu hỏi từ người dùng.",
            "Nhiệm vụ của bạn là xác định chủ đề hoặc ý định của người dùng (ví dụ: Tài chính, Bóng đá, Y tế, Thể thao, Thời tiết).",
            "Chỉ trả về 1 CỤM TỪ duy nhất đại diện cho chủ đề (Ví dụ: Thể thao). Không giải thích dài dòng."
        ]
    )
