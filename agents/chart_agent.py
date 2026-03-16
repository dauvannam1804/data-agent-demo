from agno.agent import Agent
from agno.models.openai import OpenAIChat
from tools.chart_tools import execute_python_code

def get_chart_agent() -> Agent:
    """
    Returns the Chart Agent responsible for generating Python code to visualize data.
    """
    return Agent(
        name="Chart Agent",
        role="Chuyên gia trực quan hóa dữ liệu (Data Visualization Expert).",
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[execute_python_code],
        instructions=[
            "Bạn sẽ nhận được bảng dữ liệu từ SQL Agent và yêu cầu vẽ biểu đồ ban đầu.",
            "Nhiệm vụ của bạn là viết code Python (dùng plotly, matplotlib, seaborn, hoặc pandas) để vẽ biểu đồ.",
            "LƯU Ý QUAN TRỌNG: Bạn KHÔNG được dùng lệnh hiển thị giao diện như plt.show(). Bạn PHẢI lưu biểu đồ thành file vào thư mục 'output/' (đã được tạo sẵn). Tên file có thể là 'output/chart.png' hoặc 'output/chart.html'.",
            "Vì dữ liệu được truyền cho bạn ở dạng text, bạn có thể cần hardcode hoặc parse lại dữ liệu đó vào biến pandas DataFrame trong code Python của bạn.",
            "Ví dụ (Python code bạn viết):",
            "import pandas as pd",
            "import matplotlib.pyplot as plt",
            "data = {'Category': ['A', 'B'], 'Value': [10, 20]}",
            "df = pd.DataFrame(data)",
            "fig, ax = plt.subplots()",
            "ax.bar(df['Category'], df['Value'])",
            "plt.savefig('output/chart.png')",
            "plt.close()",
            "",
            "Sau khi viết xong đoạn code Python, hãy chạy thử bằng tool `execute_python_code`.",
            "Nếu tool trả về lỗi, hãy đọc lỗi, sửa code và chạy lại.",
            "Khi đã thành công, hãy trả lời kết luận rằng biểu đồ đã được lưu và chỉ định rõ đường dẫn file (ví dụ: output/chart.png) để hiển thị lên giao diện."
        ],
        markdown=True
    )
