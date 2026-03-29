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
        all_table_names = sorted([t['table_name'] for t in registry])
    except Exception as e:
        st.error(f"Lỗi đọc registry: {e}")
        st.stop()

# Initialize session state for table confirmation and UI persistence
if "confirmed_table_names" not in st.session_state:
    st.session_state.confirmed_table_names = None
if "active_query" not in st.session_state:
    st.session_state.active_query = None
if "active_intent" not in st.session_state:
    st.session_state.active_intent = None
if "active_suggestions" not in st.session_state:
    st.session_state.active_suggestions = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Hỏi tôi bất kỳ điều gì (VD: Độ tuổi trung bình trong file titanic)..."):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Chưa cấu hình OPENAI_API_KEY trong file .env!")
        st.stop()
        
    # Reset all processing state on new prompt
    st.session_state.active_query = prompt
    st.session_state.active_intent = None
    st.session_state.active_suggestions = []
    st.session_state.confirmed_table_names = None
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Processing Pipeline (Renders if there's an active query)
if st.session_state.active_query:
    prompt = st.session_state.active_query
    with st.chat_message("assistant"):
        try:
            # Bước 1: Ý định
            with st.spinner("🛸 Bước 1: Phân tích Ý định (Intent Analysis)..."):
                # st.write("**Input:**")
                # st.info(prompt)
                
                if st.session_state.active_intent is None:
                    intent_agent = get_intent_agent()
                    intent_response = intent_agent.run(prompt)
                    intent = intent_response.content.strip()
                    st.session_state.active_intent = intent
                
                # st.write("**Output:**")
                # st.success(f"Intent: {st.session_state.active_intent}")
                # status.update(label="✅ Bước 1: Xong!", state="complete", expanded=False)

            intent = st.session_state.active_intent

            # Bước 2: Tìm Bảng
            with st.spinner("📂 Bước 2: Xác định Bảng (Table Identification)..."):
                # st.write("**Input:**")
                # st.json({"prompt": prompt, "intent": intent})
                
                if not st.session_state.active_suggestions:
                    table_names = identify_table(prompt, intent, REGISTRY_PATH)
                    st.session_state.active_suggestions = table_names
                
                # st.write("**Output:**")
                # st.success(f"Suggested: `{', '.join(st.session_state.active_suggestions)}`")
                # status.update(label="✅ Bước 2: Xong!", state="complete", expanded=False)

            table_names = st.session_state.active_suggestions

            # --- INTERACTION STEP: ACK/EDIT TABLES ---
            if st.session_state.confirmed_table_names is None:
                st.markdown("### 🛠️ Xác nhận Danh sách Bảng")
                st.info("Vui lòng kiểm tra và chỉnh sửa danh sách bảng cần dùng.")
                selected_tables = st.multiselect(
                    "Danh sách bảng:",
                    options=all_table_names,
                    default=[t for t in table_names if t in all_table_names]
                )
                if st.button("Xác nhận & Chạy tiếp 🚀"):
                    st.session_state.confirmed_table_names = selected_tables
                    st.rerun()
                st.stop()
            
            # Nếu đã xác nhận, lấy danh sách cuối cùng
            final_table_names = st.session_state.confirmed_table_names
            st.success(f"**Bảng đã xác nhận:** `{', '.join(final_table_names)}`")
            
            # Tạm thời lấy bảng đầu tiên để chạy tiếp (chờ nâng cấp multi-table toàn diện nếu cần)
            table_name = final_table_names[0]
            with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                reg = json.load(f)
            matched_table_data = next((t for t in reg if t['table_name'] == table_name), None)

            if not matched_table_data:
                st.error(f"Không tìm thấy bảng `{table_name}` trong Registry!")
                st.stop()

            # Bước 3: Cắt Cột
            with st.spinner("✂️ Bước 3: Thu gọn Cột (Column Pruning)..."):
                # st.write("**Input:**")
                # st.write(f"Prompt: {prompt}")
                # st.write("Full Columns:")
                # st.write(matched_table_data['columns'])
                
                pruned_columns = prune_columns(prompt, matched_table_data)
                
                # st.write("**Output:**")
                # st.success(f"Pruned Columns: `{pruned_columns}`")
                # status.update(label="✅ Bước 3: Xong!", state="complete", expanded=False)
                
            # Bước 4: RAG
            with st.spinner("🔍 Bước 4: Truy vấn SQL Samples (RAG)..."):
                # st.write("**Input:**")
                # st.info(prompt)
                
                sql_samples = get_sql_samples(prompt, top_k=3)
                
                # st.write("**Output:**")
                # if sql_samples:
                #     st.write(f"Tìm thấy {len(sql_samples)} ví dụ tương tự:")
                #     for s in sql_samples:
                #         with st.expander(f"Ví dụ: {s['question']}", expanded=False):
                #             st.code(s['sql'], language="sql")
                # else:
                #     st.info("Không tìm thấy SQL samples phù hợp trong VectorDB.")
                # status.update(label="✅ Bước 4: Xong!", state="complete", expanded=False)

            # Bước 5: Viết SQL
            with st.spinner("📝 Bước 5: Sinh SQL (SQL Generation)..."):
                csv_path = matched_table_data['file_path']
                # st.write("**Input:**")
                # st.json({
                #     "prompt": prompt,
                #     "table": table_name,
                #     "columns": pruned_columns,
                #     "num_samples": len(sql_samples) if sql_samples else 0
                # })
                
                sql_query = generate_duckdb_sql(prompt, csv_path, pruned_columns, sql_samples)
                
                # st.write("**Output:**")
                # st.code(sql_query, language="sql")
                # status.update(label="✅ Bước 5: Xong!", state="complete", expanded=False)
                
            # Bước 6: Chạy SQL
            with st.spinner("⚙️ Bước 6: Thực thi SQL (Execution)..."):
                # st.write("**Input:**")
                # st.code(sql_query, language="sql")
                
                result_markdown = execute_query(sql_query)
                
                # st.write("**Output:**")
                # st.markdown(result_markdown)
                # status.update(label="✅ Bước 6: Xong!", state="complete", expanded=False)

            # Hiển thị kết quả cuối cùng
            # st.markdown("### 🏆 Kết quả cuối cùng")
            st.markdown(result_markdown)
            
            # Ghi nhận log chat và RESET active query
            # full_reply = f"**Intent:** {intent}\n\n**Tables:** `{', '.join(final_table_names)}`\n\n**SQL:**\n```sql\n{sql_query}\n```\n\n### Kết quả:\n{result_markdown}"
            st.session_state.messages.append({"role": "assistant", "content": result_markdown})
            
            # Clear active query to allow next input
            st.session_state.active_query = None
            st.session_state.confirmed_table_names = None
            
        except Exception as e:
            st.error(f"Quá trình phân tích thất bại: {str(e)}")
            st.code(traceback.format_exc())
            st.session_state.active_query = None # Clear on error too
           