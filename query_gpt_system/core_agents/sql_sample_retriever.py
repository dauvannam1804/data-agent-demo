import os
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from dotenv import load_dotenv

load_dotenv()

# Cấu hình phải khớp với ingest_samples.py
CHROMA_PATH = "query_gpt_system/sql_samples/chroma_db"
COLLECTION_NAME = "sql_samples"

def get_sql_samples(user_query: str, top_k: int = 3) -> list:
    """
    Truy vấn các ví dụ SQL (few-shot) tương tự từ ChromaDB.
    Sử dụng Agno framework để thực hiện tìm kiếm ngữ nghĩa (semantic search).
    """
    if not os.path.exists(CHROMA_PATH):
        print(f"⚠️ Cảnh báo: Thư mục VectorDB {CHROMA_PATH} không tồn tại. Hãy chạy ingest_samples.py trước.")
        return []

    # Khởi tạo VectorDB instance kết nối đến DB đã có sẵn
    # Lưu ý: OpenAI API Key cần được cấu hình trong .env
    vector_db = ChromaDb(
        collection=COLLECTION_NAME,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    )

    try:
        # Thực hiện tìm kiếm semantic
        # `vector_db.search` trả về danh sách các đối tượng agno.document.Document
        results = vector_db.search(query=user_query, limit=top_k)
        
        few_shot_samples = []
        for doc in results:
            few_shot_samples.append({
                "question": doc.content,
                "sql": doc.meta_data.get("sql"),
                "table": doc.meta_data.get("table")
            })
            
        return few_shot_samples
    except Exception as e:
        print(f"❌ Lỗi khi truy vấn RAG SQL: {str(e)}")
        return []

if __name__ == "__main__":
    # Script test nhanh
    test_q = "Tính giá trị trung bình cột Giá vé"
    print(f"Bắt đầu tìm kiếm với câu hỏi: '{test_q}'...")
    samples = get_sql_samples(test_q, top_k=2)
    
    if not samples:
        print("Không tìm thấy kết quả nào. Có thể DB chưa được khởi tạo.")
    else:
        for i, s in enumerate(samples):
            print(f"\n--- Ví dụ {i+1} ---")
            print(f"Câu hỏi: {s['question']}")
            print(f"Bảng: {s['table']}")
            print(f"SQL: {s['sql']}")
