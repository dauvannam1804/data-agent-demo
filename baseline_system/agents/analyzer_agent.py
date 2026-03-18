from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_analyzer_agent() -> Agent:
    """
    Returns the Analyzer Agent responsible for parsing user queries 
    and outputting clear instructions for the SQL agent based on CSV metadata.
    
    Updated: Nhận thêm SemanticResult (phân tích ngữ nghĩa tự động) trong prompt
    để giảm tải cho LLM và tăng accuracy.
    """
    return Agent(
        name="Analyzer Agent",
        role="Phân tích ngữ nghĩa yêu cầu của User và đối chiếu với CSV Schema để tạo ra yêu cầu truy xuất dữ liệu chi tiết.",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn là một chuyên gia phân tích dữ liệu Data Analyst.",
            "Bạn sẽ nhận được 'CSV Schema/Metadata', 'Phân tích ngữ nghĩa tự động' (Semantic Analysis) và 'Câu hỏi của người dùng'.",
            "Phần 'Phân tích ngữ nghĩa tự động' đã được hệ thống xử lý sẵn, bao gồm: ý định (intent), các cột liên quan, phép toán gợi ý, GROUP BY, thông tin thời gian, và loại output mong muốn.",
            "Hãy SỬ DỤNG thông tin từ phân tích ngữ nghĩa như một GỢI Ý tham khảo. Nếu thông tin đó hợp lý, hãy dùng nó để viết yêu cầu chính xác hơn. Nếu thông tin đó chưa đúng hoặc chưa đủ, hãy tự bổ sung hoặc sửa lại.",
            "Nhiệm vụ của bạn là hiểu người dùng muốn tìm thông tin gì, sau đó xác định các cột cần thiết từ CSV Schema có thể trả lời câu hỏi đó.",
            "Hãy viết ra một danh sách các yêu cầu rõ ràng, chỉ định rõ tên cột có trong CSV để gửi cho SQL Agent. Lưu ý chỉ dùng những cột có tồn tại trong Schema.",
            "Không tự viết code SQL. Chỉ giải thích, làm rõ yêu cầu và đưa ra chỉ dẫn.",
            "Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu và súc tích."
        ],
        markdown=True
    )
