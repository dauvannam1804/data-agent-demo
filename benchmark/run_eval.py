import json
import os
import re
import sys

# Thêm thư mục gốc vào sys.path để import các module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_helpers import get_csv_schema_string
from agents.analyzer_agent import get_analyzer_agent
from agents.sql_agent import get_sql_agent

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
    
    limit = 257 # Total is 257
    
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
                schema_info = get_csv_schema_string(csv_path)
            except Exception as e:
                print(f"Error reading schema for {csv_path}: {e}")
                schema_info = "Could not read schema."

            analyzer = get_analyzer_agent()
            sql_agent = get_sql_agent(csv_path)
            
            analyzer_prompt = f"CSV Schema:\n{schema_info}\n\nUser Question:\n{prompt}"
            
            analyzer_text = ""
            sql_text = ""
            
            try:
                analyzer_response = analyzer.run(analyzer_prompt)
                analyzer_text = analyzer_response.content
                
                sql_prompt = f"Yêu cầu từ Analyzer:\n{analyzer_text}\n\nHãy viết câu lệnh SQL và chạy công cụ để lấy dữ liệu đúng format. Constraint và Format bắt buộc phải được xuất ra nguyên văn ở cuối câu trả lời (ví dụ: @answer_name[value]).\n\nConstraints: {q_data['constraints']}\n\nFormat: {q_data['format']}"
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
                "analyzer_prompt": analyzer_prompt,
                "analyzer_response": analyzer_text,
                "sql_prompt": sql_text if not sql_text else sql_prompt, # Prevent undefined if except block catches
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
