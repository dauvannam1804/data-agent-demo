from agno.agent import Agent
from agno.models.openai import OpenAIChat
from tools.sql_tools import execute_sql_on_csv

from typing import List

def get_sql_agent(csv_paths: List[str]) -> Agent:
    """
    Returns the SQL Agent responsible for writing and executing SQL queries on multiple CSVs using DuckDB.
    """
    
    # We create a closure so the agent doesn't need to guess the CSV paths
    def run_sql(query: str) -> str:
        """
        Thực thi câu lệnh SQL trên các file CSV.
        Tên bảng sẽ tương ứng với tên file (bỏ đuôi .csv).
        Ví dụ: SELECT * FROM sales s JOIN customers c ON s.customer_id = c.id LIMIT 10;
        """
        return execute_sql_on_csv(csv_paths, query)
        
    return Agent(
        name="SQL Agent",
        role="Chuyên gia phân tích dữ liệu Data Engineer và viết SQL.",
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[run_sql],
        instructions=[
            "Bạn sẽ nhận được yêu cầu truy xuất dữ liệu từ Analyzer Agent.",
            "Nhiệm vụ của bạn là viết câu lệnh SQL và sử dụng tool `run_sql` để thực thi câu lệnh đó nhằm lấy ra dữ liệu.",
            "LƯU Ý QUAN TRỌNG VỀ SQL: Hệ thống có thể có nhiều bảng. Tên bảng (table name) trong câu lệnh SQL sẽ TƯƠNG ỨNG với tên file csv (đã bỏ đuôi .csv). Ví dụ: file 'sales.csv' sẽ có bảng là 'sales'. Hãy sử dụng JOIN nếu cần thiết.",
            "Nếu kết quả truy vấn bị lỗi, hãy phân tích lỗi, sửa lại câu SQL rồi chạy lại tool.",
            "Bạn có thể chạy thử truy vấn nhiều lần.",
            "Sau khi có kết quả thành công, hãy trình bày lại kết quả dữ liệu một cách rõ ràng dưới dạng Markdown Table hoặc danh sách.",
            "Nếu người dùng (thông qua Analyzer) có yêu cầu chuẩn bị dữ liệu để vẽ biểu đồ, hãy cung cấp kết quả thật chi tiết (toàn bộ các dòng kết quả) ở output của bạn để Chart Agent có thể đọc được.",
        ],
        markdown=True
    )
