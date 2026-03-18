import json
import os
import re
import sys

# Thêm thư mục gốc và baseline_system vào sys.path để import các module
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'baseline_system'))

from utils.csv_helpers import get_csvs_schema_string
from agents.analyzer_agent import get_analyzer_agent
from agents.sql_agent import get_sql_agent
from semantic import SemanticAnalyzer


def _extract_columns(schema_info: str) -> list:
    """Trích xuất tên cột từ chuỗi schema."""
    columns = []
    for line in schema_info.split("\n"):
        if line.strip().startswith("Columns:"):
            cols_str = line.split(":", 1)[1].strip()
            columns.extend([c.strip() for c in cols_str.split(",") if c.strip()])
    return columns

def extract_answers(text: str):
    # Dùng regex để trích xuất cấu trúc @key[value]
    pattern = r'@([a-zA-Z0-9_]+)\[([^\]]+)\]'
    matches = re.findall(pattern, text)
    return [[m[0], m[1].strip()] for m in matches]

def main():
    questions_file = "data/InfiAgent/da-dev-questions.jsonl"
    labels_file = "data/InfiAgent/da-dev-labels.jsonl"
    tables_dir = "data/InfiAgent/da-dev-tables"
    results_file = "benchmark/results.json"
    
    # Load dotenv
    from dotenv import load_dotenv
    load_dotenv()
    
    # Load labels
    labels = {}
    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            labels[data['id']] = data['common_answers']

    results = []
    correct_count = 0
    total_count = 0
    
    limit = 2 # Total is 257
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        for line in f:
            q_data = json.loads(line)
            q_id = q_data['id']
            
            if total_count >= limit:
                break
                
            csv_file = q_data['file_name']
            csv_path = os.path.join(tables_dir, csv_file)
            
            if not os.path.exists(csv_path):
                print(f"Warning: CSV file {csv_path} not found.")
                continue
                
            prompt = f"Question: {q_data['question']}\n\nConstraints: {q_data['constraints']}\n\nFormat: {q_data['format']}"
            
            print(f"\n--- Evaluating Question ID: {q_id} ---")
            
            try:
                schema_info = get_csvs_schema_string([csv_path])
            except Exception as e:
                print(f"Error reading schema for {csv_path}: {e}")
                schema_info = "Could not read schema."

            # --- Semantic Layer ---
            schema_columns = _extract_columns(schema_info)
            semantic_analyzer = SemanticAnalyzer(schema_columns=schema_columns)
            semantic_result = semantic_analyzer.analyze(q_data['question'])
            semantic_text = semantic_result.to_prompt_string()
            
            analyzer = get_analyzer_agent()
            sql_agent = get_sql_agent([csv_path])
            
            analyzer_prompt = (
                f"CSV Schema:\n{schema_info}\n\n"
                f"Phân tích ngữ nghĩa tự động (Semantic Analysis):\n{semantic_text}\n\n"
                f"User Question:\n{prompt}"
            )
            
            analyzer_text = ""
            sql_text = ""
            sql_prompt = ""
            
            try:
                analyzer_response = analyzer.run(analyzer_prompt)
                analyzer_text = analyzer_response.content
                
                table_name = os.path.splitext(csv_file)[0]
                sql_prompt = f"Yêu cầu từ Analyzer:\n{analyzer_text}\n\nLƯU Ý: Tên bảng (table name) trong SQL là \"{table_name}\". Luôn dùng dấu nháy kép bao quanh tên bảng và tên cột, ví dụ: SELECT \"col\" FROM \"{table_name}\".\n\nHãy viết câu lệnh SQL và chạy công cụ để lấy dữ liệu đúng format. Constraint và Format bắt buộc phải được xuất ra nguyên văn ở cuối câu trả lời (ví dụ: @answer_name[value]).\n\nConstraints: {q_data['constraints']}\n\nFormat: {q_data['format']}"
                sql_response = sql_agent.run(sql_prompt)
                sql_text = sql_response.content
            except Exception as e:
                print(f"Agent error: {e}")

            agent_text = sql_text
            extracted = extract_answers(agent_text)
            expected = labels.get(q_id, [])
            
            def to_sorted_tuple_list(lst):
                return sorted([(c[0], c[1]) for c in lst])
            
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
                "file_name": csv_file,
                "semantic_analysis": {
                    "intent": semantic_result.intent,
                    "operations": semantic_result.operations,
                    "group_by_hint": semantic_result.group_by_hint,
                    "time_info": semantic_result.time_info,
                    "output_type": semantic_result.output_type,
                    "sort_order": semantic_result.sort_order,
                    "matched_columns": [
                        {"column": m.column_name, "term": m.query_term, 
                         "type": m.match_type, "confidence": m.confidence}
                        for m in semantic_result.matched_columns
                    ],
                    "confidence": semantic_result.confidence,
                },
                "analyzer_prompt": analyzer_prompt,
                "analyzer_response": analyzer_text,
                "sql_prompt": sql_prompt,
                "sql_response": sql_text,
                "extracted_answers": extracted_sorted,
                "expected_answers": expected_sorted,
                "is_correct": is_correct
            })
            
            with open(results_file, 'w', encoding='utf-8') as out_f:
                json.dump(results, out_f, indent=2, ensure_ascii=False)
                
    accuracy = correct_count / total_count if total_count > 0 else 0
    summary_text = f"Evaluation Complete on {total_count} questions.\nCorrect: {correct_count}\nAccuracy: {accuracy * 100:.2f}%"
    print(f"\n{summary_text}")
    
    with open("benchmark/summary.txt", "w", encoding="utf-8") as f:
        f.write(summary_text + "\n")

if __name__ == "__main__":
    main()
