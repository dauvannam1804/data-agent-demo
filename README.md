# Data Agent System

A dual-architecture AI system that allows you to chat with your CSV data using Natural Language to generate SQL queries and charts. This repository actively develops and compares two distinct architectural methodologies side-by-side.

## Features

- **Upload any CSV file**: The applications automatically infer the data schema and read metadata.
- **Natural Language to SQL**: Converts your chat questions into optimized DuckDB queries.
- **Automated Data Visualization (Baseline)**: Automatically writes Python code to generate and display plots inline using Matplotlib/Plotly.
- **Dual Architecture Deployment**: 
  - **Baseline System**: A 3-agent pipeline with **Semantic Layer** for rule-based query pre-analysis (`Semantic → Analyzer → SQL → Chart`).
  - **Query GPT System**: An advanced 5-stage pipeline inspired by Uber's Query GPT (`Intent -> Table -> Prune -> GenAI -> Execute`).

## System Architectures

### 1. Baseline System (3-Agent Pipeline + Semantic Layer)

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
┌─────────────────────────────┐
│    🔍 Semantic Layer        │ ◀── (Rule-based, No LLM)
│  ┌────────────────────────┐ │
│  │ • Intent Detection     │ │
│  │ • Column Matching      │ │
│  │ • Aggregation Detection│ │
│  │ • Time Period Detection│ │
│  │ • Output Type Detection│ │
│  └────────────────────────┘ │
└─────────────────────────────┘
      │
      │ (SemanticResult: intent, columns, ops, ...)
      ▼
┌──────────────┐ ◀── (Schema + SemanticResult + User Query)
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

1. **Semantic Layer (`semantic/`)**: A **rule-based** pre-processing module (no LLM calls) that analyzes the user's query before passing it to the LLM agents. It extracts structured metadata to reduce LLM workload and improve accuracy:
   - **Intent Detection**: Classifies query intent (aggregation, filter, comparison, ranking, trend, distribution) using keyword matching.
   - **Column Matching**: Fuzzy-matches terms in the query to CSV column names using 4 strategies: exact, normalized (diacritics-free), synonym-based (Vietnamese ↔ English), and fuzzy (SequenceMatcher).
   - **Aggregation Detection**: Identifies SQL operations (SUM, AVG, COUNT, MAX, MIN) from Vietnamese/English keywords.
   - **Time Period Detection**: Extracts time granularity (day/month/quarter/year) and specific time filters.
   - **Output Type Detection**: Determines desired output format (chart, table, single value).
   - **GROUP BY / Sort Detection**: Identifies grouping and ordering hints.
2. **Analyzer Agent**: Interprets the user's intent using **both** the CSV schema and the `SemanticResult` from the Semantic Layer. The structured hints allow the LLM to validate and refine rather than analyze from scratch.
3. **SQL Agent**: Translates instructions into optimized SQL queries and safely executes them using the `DuckDB` engine. Uses double-quoted identifiers to support table/column names with special characters.
4. **Chart Agent (Optional)**: Triggered if visualization is requested, it writes and executes Python code (matplotlib/plotly) to render charts within Streamlit.

### 2. Query GPT System (Uber Inspired)

A newly introduced schema-driven architecture optimized for large sets of CSV files and context-window minimization.

```text
       [User Chat Query]
              │
              ▼
   ┌──────────────────────┐    ┌──────────────────────┐
   │ 1. Intent Agent      │    │ 0. Metadata Scanner  │
   │   (Classify Topic)   │    │ (Pre-builds Schema)  │
   └──────────────────────┘    └──────────┬───────────┘
              │                           │
              ▼                           ▼
   ┌──────────────────────────────────────────────────┐
   │ 2. Table Agent (Finds Best Matching CSV)         │
   └──────────────────────────────────────────────────┘
              │
              ▼ (Matched CSV Schema + Query)
   ┌──────────────────────────────────────────────────┐
   │ 3. Column Pruner (Removes Irrelevant Columns)    │
   └──────────────────────────────────────────────────┘
              │
              ▼ (Pruned Schema + Query)
   ┌──────────────────────────────────────────────────┐
   │ 4. GenAI SQL Gateway (Generates DuckDB SQL)      │
   └──────────────────────────────────────────────────┘
              │
              ▼ (Executable SQL)
   ┌──────────────────────────────────────────────────┐
   │ 5. SQL Executor (Runs DuckDB & Formats Markdown) │
   └──────────────────────────────────────────────────┘
              │
              ▼
      [Streamlit UI Shows Markdown Data]
```

1. **Metadata Scanner (`schema_builder.py`)**: Pre-scans the `data/` directory and builds a global `schema_registry.json`.
2. **Intent Agent**: Classifies the semantic topic of the user's input.
3. **Table Agent**: Uses the Intent and Query to identify the single most relevant CSV file out of dozens of files.
4. **Column Pruner Agent**: Selects ONLY the absolutely necessary columns required to answer the query, discarding the rest to dramatically save LLM token usage and prevent hallucinations.
5. **GenAI SQL Gateway**: A specialized pipeline that takes the fully optimized/pruned payload and generates highly accurate Zero-Shot DuckDB SQL.
6. **SQL Executor**: A sandboxed wrapper that runs the query on DuckDB and streams Markdown results back to the user.

## Setup

1. **Prerequisites**: Ensure you have Python installed. We recommend using [`uv`](https://github.com/astral-sh/uv) to manage your environment.

2. **Initialize python environment and install dependencies**:
   ```bash
   uv init
   uv venv
   source .venv/bin/activate
   uv add -r requirements.txt
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

This repository contains executable bash scripts for both distinct systems. Data resources (`data/`) are heavily shared between them.

### Running Baseline System
1. Start the Streamlit application:
   ```bash
   ./run_baseline.sh
   ```
2. Upload a CSV file through the sidebar on the left.
3. Chat with your data! 

### Running Query GPT System
Before launching the query GPT architecture, you **must** build the metadata schema registry at least once:
```bash
python query_gpt_system/metadata/schema_builder.py
```
This command will deeply scan all the large CSVs inside `data/` and structure their formats for the Table Agent.

After the registry is successfully populated:
```bash
./run_query_gpt.sh
```

### Example Prompts
- "What is the average age of passengers in each ticket class?"
- "Find the top 10 countries with the highest happiness score and plot them."
- "What is the correlation between the number of rooms and house prices?"

## Built With
- [Agno](https://agno.com/) - Multi-agent framework
- [Streamlit](https://streamlit.io/) - Interactive Web UI
- [DuckDB](https://duckdb.org/) - In-memory analytical SQL database
- [OpenAI](https://openai.com/) - Using the `gpt-4o-mini` language model