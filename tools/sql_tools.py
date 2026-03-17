import duckdb
import os
from typing import List

def execute_sql_on_csv(csv_paths: List[str], query: str) -> str:
    """
    Executes a SQL query on multiple CSV files using DuckDB and returns the result as string.
    The table names will be the names of the files (e.g. 'sales' for 'sales.csv').
    Example: SELECT * FROM sales s JOIN customers c ON s.customer_id = c.id LIMIT 5;
    """
    try:
        # Create a DuckDB connection
        con = duckdb.connect(database=':memory:')
        
        # Create a view for each CSV file
        for csv_path in csv_paths:
            table_name = os.path.splitext(os.path.basename(csv_path))[0]
            con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
        
        # Execute the user query
        result = con.execute(query).fetchdf()
        
        if result.empty:
            return "Query executed successfully. The result is empty."
        
        return result.to_string()
    except Exception as e:
        return f"Error executing SQL: {str(e)}"
        
def get_sql_results_as_df(csv_paths: List[str], query: str):
    """
    Execute a SQL query and return the resulting pandas DataFrame.
    """
    con = duckdb.connect(database=':memory:')
    for csv_path in csv_paths:
        table_name = os.path.splitext(os.path.basename(csv_path))[0]
        con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
    return con.execute(query).fetchdf()
