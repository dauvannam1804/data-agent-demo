import streamlit as st
import os
import re
from dotenv import load_dotenv

# Tải biến môi trường (Ví dụ: OPENAI_API_KEY từ .env)
load_dotenv()

from utils.csv_helpers import get_csv_schema_string
from agents.analyzer_agent import get_analyzer_agent
from agents.sql_agent import get_sql_agent
from agents.chart_agent import get_chart_agent

st.set_page_config(page_title="Data Agent", page_icon="📊", layout="wide")

st.title("📊 Data Agent System")
st.markdown("Hệ thống Agent tự động phân tích truy vấn, truy xuất dữ liệu từ CSV và vẽ biểu đồ. [Dùng mô hình GPT-4o-mini]")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "csv_path" not in st.session_state:
    st.session_state.csv_path = None
    
if "csv_metadata" not in st.session_state:
    st.session_state.csv_metadata = None

# Sidebar for file upload
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        # Save file to data directory
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.session_state.csv_path = file_path
        st.success(f"File {uploaded_file.name} uploaded successfully!")
        
        # Extract and display metadata
        metadata_str = get_csv_schema_string(file_path)
        st.session_state.csv_metadata = metadata_str
        
        with st.expander("CSV Schema", expanded=True):
            st.text(metadata_str)
            
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "html" in message:
            import streamlit.components.v1 as components
            with open(message["html"], 'r', encoding='utf-8') as f:
                components.html(f.read(), height=500)
        elif "image" in message:
            st.image(message["image"])

# React to user input
if prompt := st.chat_input("Hỏi tôi bất kỳ điều gì về dữ liệu... (VD: Tính tổng doanh thu theo tháng rồi vẽ biểu đồ)"):
    if not st.session_state.csv_path:
        st.warning("Vui lòng tải lên file CSV ở cột bên trái trước khi đặt câu hỏi!")
    else:
        # Check API key
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("Chưa cấu hình OPENAI_API_KEY trong file .env!")
            st.stop()
            
        # Display user message
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Process the workflow
        csv_metadata = st.session_state.csv_metadata
        csv_path = st.session_state.csv_path
        
        # 1. Analyzer Agent
        with st.chat_message("assistant"):
            st.markdown("### 🧠 Phân tích yêu cầu...")
            analyzer = get_analyzer_agent()
            analyzer_prompt = f"CSV Schema:\n{csv_metadata}\n\nYêu cầu của người dùng:\n{prompt}"
            
            with st.spinner("Analyzer Agent đang làm việc..."):
                analyzer_response = analyzer.run(analyzer_prompt)
                st.markdown(analyzer_response.content)
            
            st.session_state.messages.append({"role": "assistant", "content": f"**Phân tích yêu cầu:**\n{analyzer_response.content}"})
            
            # 2. SQL Agent
            st.markdown("### 💾 Truy xuất dữ liệu...")
            sql_agent = get_sql_agent(csv_path)
            
            with st.spinner("SQL Agent đang thực thi..."):
                sql_response = sql_agent.run(f"Yêu cầu từ Analyzer:\n{analyzer_response.content}\n\nHãy viết câu lệnh SQL và chạy công cụ để lấy dữ liệu. Hãy TRÌNH BÀY KẾT QUẢ dữ liệu ra vì Chart Agent sẽ cần đọc nó.")
                st.markdown(sql_response.content)
                
            st.session_state.messages.append({"role": "assistant", "content": f"**Kết quả dữ liệu:**\n{sql_response.content}"})
            
            # 3. Chart Agent (Conditionally)
            # Check if user wants a chart
            chart_keywords = ["vẽ", "biểu đồ", "chart", "plot", "visualize", "hình ảnh", "đồ thị"]
            needs_chart = any(keyword in prompt.lower() for keyword in chart_keywords)
            
            if needs_chart:
                st.markdown("### 📊 Vẽ biểu đồ...")
                chart_agent = get_chart_agent()
                
                with st.spinner("Chart Agent đang làm việc..."):
                    chart_prompt = f"Yêu cầu ban đầu: {prompt}\n\nDữ liệu bạn cần vẽ (dạng markdown/text):\n{sql_response.content}"
                    chart_response = chart_agent.run(chart_prompt)
                    st.markdown(chart_response.content)
                    
                # Check for output image or html file path mentioned in text
                file_path_found = None
                if "output/" in chart_response.content:
                    match = re.search(r'output/[\w-]+\.(png|html)', chart_response.content)
                    if match:
                        file_path_found = match.group(0)
                        
                # Default checking
                if not file_path_found:
                    if os.path.exists("output/chart.png"):
                        file_path_found = "output/chart.png"
                    elif os.path.exists("output/chart.html"):
                        file_path_found = "output/chart.html"
                    
                if file_path_found and os.path.exists(file_path_found):
                    is_html = file_path_found.endswith('.html')
                    message_data = {
                        "role": "assistant", 
                        "content": f"**Biểu đồ:**\n{chart_response.content}"
                    }
                    if is_html:
                        message_data['html'] = file_path_found
                        import streamlit.components.v1 as components
                        with open(file_path_found, 'r', encoding='utf-8') as f:
                            components.html(f.read(), height=500)
                    else:
                        message_data['image'] = file_path_found
                        st.image(file_path_found)
                        
                    st.session_state.messages.append(message_data)
                else:
                    st.session_state.messages.append({"role": "assistant", "content": f"**Biểu đồ:**\n{chart_response.content}"})
