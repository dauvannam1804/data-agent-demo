import json
import os
from typing import List
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.document import Document
from dotenv import load_dotenv

load_dotenv()

# Cấu hình đường dẫn
JSON_PATH = "data-code/sql_samples.json"
COLLECTION_NAME = "sql_samples"
# Database sẽ được lưu tại đây
CHROMA_PATH = "query_gpt_system/sql_samples/chroma_db"

def ingest_sql_samples():
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} không tìm thấy.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples", [])
    print(f"👉 Tìm thấy {len(samples)} câu hỏi mẫu để lập chỉ mục (index).")

    # Khởi tạo VectorDB với Chroma
    # Lưu ý: Agno sử dụng ChromaDb làm wrap cho chromadb
    vector_db = ChromaDb(
        collection=COLLECTION_NAME,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    )

    documents: List[Document] = []
    
    for sample in samples:
        question = sample.get("question")
        table = sample.get("table")
        
        # Mặc định lấy SQL variant 'direct' làm ví dụ điển hình
        direct_sql = ""
        variants = sample.get("variants", [])
        for v in variants:
            if v.get("variant_style") == "direct":
                direct_sql = v.get("sql")
                break
        
        if not direct_sql and variants:
            direct_sql = variants[0].get("sql")

        # Lưu thông tin bổ trợ vào metadata
        metadata = {
            "question_id": sample.get("question_id"),
            "table": table,
            "level": sample.get("level"),
            "concepts": ", ".join(sample.get("concepts", [])),
            "sql": direct_sql,
            # Lưu chuỗi JSON của các variants khác để có thể truy xuất sau nếu cần
            "variants_json": json.dumps(variants)
        }

        doc = Document(
            content=question,
            meta_data=metadata,
            id=str(sample.get("question_id"))
        )
        documents.append(doc)

    print(f"🚀 Đang đưa {len(documents)} bản ghi vào ChromaDB tại {CHROMA_PATH}...")
    
    # Đảm bảo collection tồn tại trước khi cập nhật
    vector_db.create()
    
    # Sử dụng upsert để ghi đè nếu đã tồn tại id
    # content_hash giúp Agno quản lý phiên bản của tập tài liệu này
    vector_db.upsert(documents=documents, content_hash="sql_samples_v1")
    print("✅ Hoàn tất: Các câu SQL mẫu đã được lập chỉ mục thành công.")

if __name__ == "__main__":
    # Đảm bảo thư mục đích tồn tại
    os.makedirs(CHROMA_PATH, exist_ok=True)
    ingest_sql_samples()
