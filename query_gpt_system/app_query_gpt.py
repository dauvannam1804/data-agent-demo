import streamlit as st
import os
import json
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
            with st.spinner("Phiên dịch Ý định..."):
                intent_agent = get_intent_agent()
                intent_response = intent_agent.run(prompt)
                intent = intent_response.content.strip()
                st.write(f"👉 **Intent**: {intent}")
                
            # Bước 2: Tìm Bảng
            with st.spinner("Tìm kiếm Cấu trúc Dữ liệu..."):
                table_name = identify_table(prompt, intent, REGISTRY_PATH)
                st.write(f"👉 **Table Matched**: `{table_name}`")
                
                # Load full schema cho bảng này
                with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    reg = json.load(f)
                
                matched_table_data = next((t for t in reg if t['table_name'] == table_name), None)
                if not matched_table_data:
                    st.error(f"Không tìm thấy file {table_name} trong Registry!")
                    st.stop()
                    
            # Bước 3: Cắt Cột
            with st.spinner("Tối ưu Schema..."):
                pruned_columns = prune_columns(prompt, matched_table_data)
                st.write(f"👉 **Pruned Columns**: `{pruned_columns}`")
                
            # Bước 4: RAG - Tìm SQL mẫu tương tự
            with st.spinner("Truy vấn SQL Samples (RAG)..."):
                sql_samples = get_sql_samples(prompt, top_k=3)
                if sql_samples:
                    with st.expander("🔍 Tìm thấy các ví dụ SQL tương tự (Few-shot samples)", expanded=False):
                        for s in sql_samples:
                            st.markdown(f"**Q:** {s['question']}")
                            st.code(s['sql'], language="sql")
                else:
                    st.info("Không tìm thấy SQL samples phù hợp trong VectorDB.")

            # Bước 5: Viết SQL
            with st.spinner("Sinh SQL DuckDB..."):
                # DuckDB cần đường dẫn tuyệt đối hoặc tương đối đúng hướng
                csv_path = matched_table_data['file_path']
                sql_query = generate_duckdb_sql(prompt, csv_path, pruned_columns, sql_samples)
                st.code(sql_query, language="sql")
                
            # Bước 5: Chạy SQL
            with st.spinner("Thực thi Code..."):
                result_markdown = execute_query(sql_query)
                st.markdown("### Kết quả Thực thi")
                st.markdown(result_markdown)
                
                # Ghi nhận log chat
                full_reply = f"**Intent:** {intent}\n\n**Table:** `{table_name}`\n\n**Pruned Columns:** `{pruned_columns}`\n\n**SQL:**\n```sql\n{sql_query}\n```\n\n### Kết quả:\n{result_markdown}"
                st.session_state.messages.append({"role": "assistant", "content": full_reply})
        except Exception as e:
            st.error(f"Quá trình phân tích thất bại: {str(e)}")
