import duckdb
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def execute_query(sql_query: str) -> str:
    """
    Thực thi mã DuckDB SQL an toàn và trả về kết quả dưới dạng chuỗi (markdown).
    Tích hợp cơ chế tự đọc báo lỗi ngầm nếu query fail.
    """
    logger.info(f"Executing DuckDB SQL:\n{sql_query}")
    try:
        # Establish connection. Memory DB is sufficient.
        con = duckdb.connect(database=':memory:', read_only=False)
        result_df = con.execute(sql_query).df()
        
        # Nếu empty dataframe
        if result_df.empty:
            return "Truy vấn thành công nhưng bảng dữ liệu rỗng (Không có bản ghi thoả mãn)."
            
        return result_df.to_markdown(index=False)
        
    except Exception as e:
        logger.error(f"Execution Error: {e}")
        return f"Lỗi khi thực thi truy vấn SQL: {e}"
