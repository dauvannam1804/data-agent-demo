from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_refiner_agent() -> Agent:
    return Agent(
        name="Result Refiner",
        role="Định dạng kết quả dữ liệu thô thành chuỗi kết quả theo yêu cầu của benchmark",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn là một chuyên gia định dạng dữ liệu (Data Formatter).",
            "Bạn nhận được:",
            "1. Câu hỏi gốc của người dùng.",
            "2. Hướng dẫn định dạng (Format instructions) có cấu trúc @key[value].",
            "3. Kết quả dữ liệu thô (Raw execution result) từ việc thực thi SQL.",
            "Nhiệm vụ của bạn là trích xuất các giá trị từ dữ liệu thô và điền chúng vào đúng định dạng yêu cầu.",
            "QUY TẮC:",
            "- CHỈ trả về chuỗi kết quả sau khi đã định dạng. KHÔNG giải thích, KHÔNG thêm bớt ký tự nào khác.",
            "- Nếu có nhiều giá trị, hãy liệt kê chúng cách nhau bởi dấu phẩy hoặc xuống dòng tùy theo hướng dẫn format.",
            "- Giữ nguyên các nhãn (keys) bắt đầu bằng @.",
            "- Đảm bảo các giá trị (values) được làm tròn hoặc định dạng đúng theo yêu cầu trong Question/Format.",
            "Ví dụ:",
            "Input Format: @mean_fare[mean_fare_value]",
            "Input Raw Data: | mean_fare | \\n | 34.6532 |",
            "Output: @mean_fare[34.65]"
        ]
    )

def refine_result(question: str, format_instruction: str, raw_result: str) -> str:
    agent = get_refiner_agent()
    prompt = f"Question: {question}\n\nFormat Instruction: {format_instruction}\n\nRaw Execution Result:\n{raw_result}\n\nFormatted Output:"
    response = agent.run(prompt)
    return response.content.strip()
