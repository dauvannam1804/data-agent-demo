import json
import os
import re
import sys

# Thêm thư mục gốc và query_gpt_system vào sys.path để import các module
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'query_gpt_system'))

from core_agents.intent_agent import get_intent_agent
from core_agents.table_agent import identify_table
from core_agents.column_pruner import prune_columns
from core_agents.sql_sample_retriever import get_sql_samples
from core_agents.genai_gateway import generate_duckdb_sql
from core_agents.result_refiner import refine_result
from executor.sql_engine import execute_query

def extract_answers(text: str):
    # Dùng regex để trích xuất cấu trúc @key[value]
    pattern = r'@([a-zA-Z0-9_]+)\[([^\]]+)\]'
    matches = re.findall(pattern, text)
    return [[m[0], m[1].strip()] for m in matches]

def main():
    questions_file = "data/InfiAgent/da-dev-questions.jsonl"
    labels_file = "data/InfiAgent/da-dev-labels.jsonl"
    tables_dir = "data/InfiAgent/da-dev-tables"
    registry_path = "query_gpt_system/metadata/schema_registry.json"
    results_file = "benchmark/results_query_gpt.json"
    
    # Load dotenv
    from dotenv import load_dotenv
    load_dotenv()

    # Kiểm tra File Metadata
    if not os.path.exists(registry_path):
        print(f"Error: Metadata registry not found at {registry_path}.")
        print("Please run query_gpt_system/metadata/schema_builder.py first.")
        sys.exit(1)
        
    # Load registry in memory
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Load labels
    labels = {}
    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            labels[data['id']] = data['common_answers']

    results = []
    correct_count = 0
    total_count = 0
    
    limit = 4 # Total is 257
    
    intent_agent = get_intent_agent()
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        for line in f:
            q_data = json.loads(line)
            q_id = q_data['id']
            
            if total_count >= limit:
                break

            if q_id != 6:
                continue
                
            expected_csv_file = q_data['file_name']
            
            # Khởi tạo prompt (Không cần ép format trong SQL nữa)
            prompt = f"Question: {q_data['question']}\n\nConstraints: {q_data['constraints']}\n\nQuản lý: Hãy viết SQL DuckDB chuẩn để lấy dữ liệu."
            
            print(f"\n--- Evaluating Question ID: {q_id} ---")
            
            # Bước 1: Ý định
            try:
                print("STEP 1")
                print("Question:", q_data['question'])
                intent_response = intent_agent.run(q_data['question'])
                print("Intent Response:", intent_response.content.strip())
                intent = intent_response.content.strip()
            except Exception as e:
                intent = "Unknown"
                
            # Bước 2: Xác định Bảng (Sử dụng nhãn đúng thay vì gọi Agent)
            table_name = expected_csv_file
            matched_table_data = next((t for t in registry if t['table_name'] == table_name), None)
            
            if not matched_table_data:
                print(f"Error: CSV {expected_csv_file} not found in registry.")
                continue

            csv_path = matched_table_data['file_path']
            print("STEP 2")
            print("CSV Path:", csv_path)
            
            # Bước 3: Cắt Cột
            try:
                print("STEP 3")
                pruned_columns = prune_columns(q_data['question'], matched_table_data)
                print("Pruned Columns:", pruned_columns)
            except Exception as e:
                pruned_columns = matched_table_data["columns"]
                
            # Bước 4: Lấy ví dụ SQL mẫu (RAG)
            sql_samples = []
            try:
                print("STEP 4")
                sql_samples = get_sql_samples(q_data['question'], top_k=3)
                print("SQL Samples:", sql_samples)
            except Exception as e:
                print(f"RAG error: {e}")
                
            # Bước 5: Viết SQL
            sql_query = ""
            execution_result = ""
            try:
                print("STEP 5")
                sql_query = generate_duckdb_sql(prompt, csv_path, pruned_columns, sql_samples=sql_samples)
                print("SQL Query:", sql_query)
                # Bước 6: Chạy SQL
                print("STEP 6")
                execution_result = execute_query(sql_query)
                print("Raw Execution Result:", execution_result)
            except Exception as e:
                print(f"Agent/Execution error: {e}")

            # Bước 7: Refine kết quả sang định dạng @key[value]
            try:
                print("STEP 7: Refinement")
                refined_text = refine_result(q_data['question'], q_data['format'], execution_result)
                print("Refined Result:", refined_text)
                agent_text = refined_text
            except Exception as e:
                print(f"Refinement error: {e}")
                agent_text = execution_result
            extracted = extract_answers(agent_text)
            
            # Check if LLM outputted the SQL query but DuckDB failed, maybe we try to regex out the answer if LLM mistakenly put the answer directly in query
            if not extracted:
                extracted = extract_answers(sql_query)

            expected = labels.get(q_id, [])
            
            def to_sorted_tuple_list(lst):
                return sorted([(str(c[0]), str(c[1])) for c in lst])
            
            extracted_sorted = to_sorted_tuple_list(extracted)
            expected_sorted = to_sorted_tuple_list(expected)
            
            is_correct = (extracted_sorted == expected_sorted) and len(expected_sorted) > 0
            
            if is_correct:
                correct_count += 1
                
            total_count += 1
            
            print(f"Extracted: {extracted_sorted}")
            print(f"Expected : {expected_sorted}")
            print(f"Correct  : {is_correct}")
            
            results.append({
                "id": q_id,
                "question": q_data['question'],
                "expected_file": expected_csv_file,
                "matched_file": table_name if 'table_name' in locals() else "",
                "intent": intent,
                "pruned_columns": pruned_columns,
                "sql_query": sql_query,
                "execution_result": execution_result,
                "sql_samples": sql_samples,
                "extracted_answers": extracted_sorted,
                "expected_answers": expected_sorted,
                "is_correct": is_correct
            })
            
            with open(results_file, 'w', encoding='utf-8') as out_f:
                json.dump(results, out_f, indent=2, ensure_ascii=False)
                
    accuracy = correct_count / total_count if total_count > 0 else 0
    summary_text = f"Evaluation Query GPT Complete on {total_count} questions.\nCorrect: {correct_count}\nAccuracy: {accuracy * 100:.2f}%"
    print(f"\n{summary_text}")
    
    with open("benchmark/summary_query_gpt.txt", "w", encoding="utf-8") as f:
        f.write(summary_text + "\n")

if __name__ == "__main__":
    main()
