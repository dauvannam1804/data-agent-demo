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

from typing import List

def get_csvs_schema_string(file_paths: List[str], sample_size: int = 3) -> str:
    """
    Returns a concatenated formatted string describing the schemas of multiple CSV files.
    """
    import os
    schemas = []
    
    for file_path in file_paths:
        metadata = get_csv_metadata(file_path, sample_size)
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        
        if "error" in metadata:
            schemas.append(f"Table '{table_name}' (Error reading {file_path}): {metadata['error']}")
            continue
            
        schema_str = f"Table: '{table_name}' (Source: {os.path.basename(file_path)})\n"
        schema_str += f"Total Rows: {metadata['total_rows']}\n"
        schema_str += f"Columns: {', '.join(metadata['columns'])}\n\n"
        
        schema_str += "Data Types:\n"
        for col, dtype in metadata["data_types"].items():
            schema_str += f"- {col}: {dtype}\n"
            
        schema_str += f"\nSample Data ({sample_size} rows):\n"
        for row in metadata['sample_data']:
            schema_str += f"{row}\n"
            
        schemas.append(schema_str)
        
    return "\n" + "="*40 + "\n\n".join(schemas) + "\n" + "="*40 + "\n"
