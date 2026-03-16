import pandas as pd
from typing import Dict, Any

def get_csv_metadata(file_path: str, sample_size: int = 5) -> Dict[str, Any]:
    """
    Reads a CSV file and returns its metadata including columns, data types, and a few sample rows.
    """
    try:
        df = pd.read_csv(file_path)
        metadata = {
            "file_path": file_path,
            "total_rows": len(df),
            "columns": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict(),
            "sample_data": df.head(sample_size).to_dict(orient="records")
        }
        return metadata
    except Exception as e:
        return {"error": str(e)}

def get_csv_schema_string(file_path: str, sample_size: int = 3) -> str:
    """
    Returns a formatted string describing the CSV schema, useful for LLM context.
    """
    metadata = get_csv_metadata(file_path, sample_size)
    if "error" in metadata:
        return f"Error reading CSV: {metadata['error']}"
    
    schema_str = f"File: {file_path}\n"
    schema_str += f"Total Rows: {metadata['total_rows']}\n"
    schema_str += f"Columns: {', '.join(metadata['columns'])}\n\n"
    
    schema_str += "Data Types:\n"
    for col, dtype in metadata["data_types"].items():
        schema_str += f"- {col}: {dtype}\n"
        
    schema_str += f"\nSample Data ({sample_size} rows):\n"
    for row in metadata['sample_data']:
        schema_str += f"{row}\n"
        
    return schema_str
