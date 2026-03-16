import duckdb

def execute_sql_on_csv(csv_path: str, query: str) -> str:
    """
    Executes a SQL query on a CSV file using DuckDB and returns the result as string.
    The table name in the query MUST be exactly 'data'.
    Example: SELECT * FROM data LIMIT 5;
    """
    try:
        # Create a DuckDB connection
        con = duckdb.connect(database=':memory:')
        
        # Create a view 'data' that reads directly from the CSV
        con.execute(f"CREATE VIEW data AS SELECT * FROM read_csv_auto('{csv_path}')")
        
        # Execute the user query
        result = con.execute(query).fetchdf()
        
        if result.empty:
            return "Query executed successfully. The result is empty."
        
        return result.to_string()
    except Exception as e:
        return f"Error executing SQL: {str(e)}"
        
def get_sql_results_as_df(csv_path: str, query: str):
    """
    Execute a SQL query and return the resulting pandas DataFrame.
    """
    con = duckdb.connect(database=':memory:')
    con.execute(f"CREATE VIEW data AS SELECT * FROM read_csv_auto('{csv_path}')")
    return con.execute(query).fetchdf()
