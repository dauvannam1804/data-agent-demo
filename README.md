# Data Agent System

A multi-agent AI system built with [`agno`](https://agno.com) and Streamlit that allows you to chat with your CSV data. The system automatically analyzes your data, writes SQL queries via `duckdb`, and generates custom charts based on your natural language questions.

## Features

- **Upload any CSV file**: It automatically infers the data schema and reads metadata.
- **Natural Language to SQL**: Converts your chat questions into optimized DuckDB queries.
- **Automated Data Visualization**: Automatically writes Python code to generate and display plots inline using Matplotlib/Plotly.
- **Architecture**: Employs a 3-agent pipeline:
  1. `AnalyzerAgent`: Semantically understands your question against the CSV schema.
  2. `SqlAgent`: Writes and executes SQL on the CSV to extract necessary data points.
  3. `ChartAgent`: Parses the extracted data to formulate and visualize charts.

## System Architecture

```text
[User Chat]
      │
      ▼
┌──────────────┐
│  Streamlit   │───────┐
│     UI       │       │ (Uploads CSV)
└──────────────┘       │
      │                ▼
      │         ┌──────────────┐
      │         │ CSV Metadata │
      │         │  Extraction  │
      │         └──────────────┘
      │                │
      ▼                ▼
┌──────────────┐ ◀─────┘ (Uses Schema info)
│   Analyzer   │
│    Agent     │
└──────────────┘
      │
      │ (Generates Data Retrieval Plan)
      ▼
┌──────────────┐
│     SQL      │ ──▶ [DuckDB Executes SQL]
│    Agent     │ ◀── [Returns Data subset]
└──────────────┘
      │
      │ (Passes subset & checks if plot is needed)
      ▼
┌──────────────┐
│    Chart     │ ──▶ [Generates Plotly/Matplotlib]
│    Agent     │ ──▶ [Saves to output/]
└──────────────┘
      │
      ▼
[Streamlit UI Displays Data/Chart]
```

The Data Agent system is designed to break down complex data analytics into a pipeline of specialized agents:

1. **Analyzer Agent**
   - **Role**: Data Semantic Understanding
   - **Process**: Takes the user's natural language request and the schema of the uploaded CSV file (inferred using Pandas). It interprets the user's intent and maps it to the available columns in the dataset without writing any queries itself. It outputs a clear set of step-by-step instructions for data retrieval.

2. **SQL Agent**
   - **Role**: Data Extraction & Query Execution
   - **Process**: Receives the instructions from the Analyzer Agent. It translates these instructions into optimized SQL queries. Using the `DuckDB` engine, it safely executes these queries against the CSV data without loading the entire dataset into memory. It then formats the result into a clean structure (e.g., Markdown table) for the final agent.

3. **Chart Agent (Optional)**
   - **Role**: Data Visualization
   - **Process**: Triggered only if the user's request involves visualization (e.g., "plot", "chart", "vẽ biểu đồ"). It acts on the extracted dataset provided by the SQL Agent, writes Python code utilizing `matplotlib` or `plotly`, executes the script to generate an image or HTML file, and saves it to the `output/` directory so Streamlit can render it in the UI.

This modular architecture ensures separation of concerns, increases accuracy (as SQL Agent doesn't have to guess the user intent blindly), and allows for robust error handling at each step.

## Setup

1. **Prerequisites**: Ensure you have Python installed. We recommend using [`uv`](https://github.com/astral-sh/uv) to manage your environment.

2. **Initialize python environment and install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the example environment file and add your OpenAI API Key:
   ```bash
   cp .env.example .env
   ```
   Then, open the `.env` file and set your key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run main.py
   ```
2. Upload a CSV file through the sidebar on the left.
3. Chat with your data! 

### Example Prompts
- "What is the average age of passengers in each ticket class?"
- "Find the top 10 countries with the highest happiness score and plot them."
- "What is the correlation between the number of rooms and house prices?"

## Built With
- [Agno](https://agno.com/) - Multi-agent framework
- [Streamlit](https://streamlit.io/) - Interactive Web UI
- [DuckDB](https://duckdb.org/) - In-memory analytical SQL database
- [OpenAI](https://openai.com/) - Using the `gpt-4o-mini` language model