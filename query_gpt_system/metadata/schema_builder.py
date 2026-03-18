import os
import json
import pandas as pd
import glob
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_schema_registry(data_dir: str, output_file: str):
    """
    Quét tất cả các file CSV trong thư mục data_dir và tạo ra một file schema_registry.json
    lưu trữ metadata (tên cột, kiểu dữ liệu, sample data) để phục vụ Table Agent.
    """
    logger.info(f"Scanning directory: {data_dir} for CSV files...")
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    registry = []
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        try:
            # Đọc 5 dòng đầu tiên để phân tích schema và lấy mẫu
            df = pd.read_csv(file_path, nrows=5)
            
            # Trích xuất kiểu dữ liệu
            dtypes = df.dtypes.apply(lambda x: str(x)).to_dict()
            
            # Trích xuất 3 dòng dữ liệu mẫu
            sample_data = df.head(3).to_dict(orient='records')
            
            # Lấy danh sách cột
            columns = list(df.columns)
            
            registry.append({
                "table_name": filename,
                "file_path": file_path,
                "columns": columns,
                "dtypes": dtypes,
                "sample_data": sample_data
            })
            
            logger.info(f"Successfully extracted schema for {filename}")
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            
    # Lưu vào file JSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Schema registry built successfully at {output_file} with {len(registry)} tables.")

if __name__ == "__main__":
    # Đường dẫn thư mục
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data", "InfiAgent", "da-dev-tables")
    output_path = os.path.join(base_dir, "query_gpt_system", "metadata", "schema_registry.json")
    
    build_schema_registry(data_dir, output_path)
