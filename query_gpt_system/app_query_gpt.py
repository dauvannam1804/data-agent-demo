import streamlit as st
import os
import json
import traceback
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

from core_agents.intent_agent import get_intent_agent
from core_agents.table_agent import identify_table
from core_agents.column_pruner import prune_columns
from core_agents.genai_gateway import generate_duckdb_sql
from core_agents.sql_sample_retriever import get_sql_samples
from executor.sql_engine import execute_query

st.set_page_config(page_title="Query GPT", page_icon="🚀", layout="wide")

st.title("🚀 Query GPT Data Agent")
st.markdown("Hệ thống phân tích truy vấn dữ liệu dựa trên kiến trúc Uber Query GPT: `Intent -> Table -> Prune -> Generate -> Execute`.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Kiểm tra File Metadata
REGISTRY_PATH = "query_gpt_system/metadata/schema_registry.json"
if not os.path.exists(REGISTRY_PATH):
    st.error(f"⚠️ Không tìm thấy file Metadata tại {REGISTRY_PATH}. Hãy chạy script `schema_builder.py` trước!")
    st.stop()

with st.sidebar:
    st.header("Thông tin Hệ thống")
    try:
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        st.success(f"Đã nạp thành công Metadata của {len(registry)} file CSV.")
        
        with st.expander("Danh sách Bảng dữ liệu", expanded=False):
            for t in registry:
                st.markdown(f"- **{t['table_name']}**")
    except Exception as e:
        st.error(f"Lỗi đọc registry: {e}")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Hỏi tôi bất kỳ điều gì (VD: Độ tuổi trung bình trong file titanic)..."):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Chưa cấu hình OPENAI_API_KEY trong file .env!")
        st.stop()
        
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        try:
            # Bước 1: Ý định
            with st.status("🛸 Bước 1: Phân tích Ý định (Intent Analysis)", expanded=True) as status:
                st.write("**Input:**")
                st.info(prompt)
                
                intent_agent = get_intent_agent()
                intent_response = intent_agent.run(prompt)
                intent = intent_response.content.strip()
                
                st.write("**Output:**")
                st.success(f"Intent: {intent}")
                status.update(label="✅ Bước 1: Xong!", state="complete", expanded=False)

            # Bước 2: Tìm Bảng
            with st.status("📂 Bước 2: Xác định Bảng (Table Identification)", expanded=True) as status:
                st.write("**Input:**")
                st.json({"prompt": prompt, "intent": intent})
                
                table_name = identify_table(prompt, intent, REGISTRY_PATH)
                
                # Load full schema cho bảng này
                with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    reg = json.load(f)
                matched_table_data = next((t for t in reg if t['table_name'] == table_name), None)
                
                st.write("**Output:**")
                if matched_table_data:
                    st.success(f"Table Matched: `{table_name}`")
                else:
                    st.error(f"Không tìm thấy file {table_name} trong Registry!")
                    st.stop()
                status.update(label="✅ Bước 2: Xong!", state="complete", expanded=False)
                    
            # Bước 3: Cắt Cột
            with st.status("✂️ Bước 3: Thu gọn Cột (Column Pruning)", expanded=True) as status:
                st.write("**Input:**")
                st.write(f"Prompt: {prompt}")
                st.write("Full Columns:")
                st.write(matched_table_data['columns'])
                
                pruned_columns = prune_columns(prompt, matched_table_data)
                
                st.write("**Output:**")
                st.success(f"Pruned Columns: `{pruned_columns}`")
                status.update(label="✅ Bước 3: Xong!", state="complete", expanded=False)
                
            # Bước 4: RAG - Tìm SQL mẫu tương tự
            with st.status("🔍 Bước 4: Truy vấn SQL Samples (RAG)", expanded=True) as status:
                st.write("**Input:**")
                st.info(prompt)
                
                sql_samples = get_sql_samples(prompt, top_k=3)
                
                st.write("**Output:**")
                if sql_samples:
                    st.write(f"Tìm thấy {len(sql_samples)} ví dụ tương tự:")
                    for s in sql_samples:
                        with st.expander(f"Ví dụ: {s['question']}", expanded=False):
                            st.code(s['sql'], language="sql")
                else:
                    st.info("Không tìm thấy SQL samples phù hợp trong VectorDB.")
                status.update(label="✅ Bước 4: Xong!", state="complete", expanded=False)

            # Bước 5: Viết SQL
            with st.status("📝 Bước 5: Sinh SQL (SQL Generation)", expanded=True) as status:
                csv_path = matched_table_data['file_path']
                st.write("**Input:**")
                st.json({
                    "prompt": prompt,
                    "table": table_name,
                    "columns": pruned_columns,
                    "num_samples": len(sql_samples) if sql_samples else 0
                })
                
                sql_query = generate_duckdb_sql(prompt, csv_path, pruned_columns, sql_samples)
                
                st.write("**Output:**")
                st.code(sql_query, language="sql")
                status.update(label="✅ Bước 5: Xong!", state="complete", expanded=False)
                
            # Bước 6: Chạy SQL
            with st.status("⚙️ Bước 6: Thực thi SQL (Execution)", expanded=True) as status:
                st.write("**Input:**")
                st.code(sql_query, language="sql")
                
                result_markdown = execute_query(sql_query)
                
                st.write("**Output:**")
                st.markdown(result_markdown)
                status.update(label="✅ Bước 6: Xong!", state="complete", expanded=False)

            # Hiển thị kết quả cuối cùng ra ngoài status containers
            st.markdown("### 🏆 Kết quả cuối cùng")
            st.markdown(result_markdown)
            
            # Ghi nhận log chat cho session state
            full_reply = f"**Intent:** {intent}\n\n**Table:** `{table_name}`\n\n**Pruned Columns:** `{pruned_columns}`\n\n**SQL:**\n```sql\n{sql_query}\n```\n\n### Kết quả:\n{result_markdown}"
            st.session_state.messages.append({"role": "assistant", "content": full_reply})
            
        except Exception as e:
            st.error(f"Quá trình phân tích thất bại: {str(e)}")
            st.code(traceback.format_exc())
