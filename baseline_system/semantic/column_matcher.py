"""
Fuzzy Column Matcher module.
So khớp các từ trong câu query của người dùng với tên cột trong CSV schema.
Hỗ trợ: exact match, normalized match, synonym match, fuzzy match.
"""

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Dict, Optional

from semantic.keyword_dicts import COLUMN_SYNONYMS


@dataclass
class ColumnMatch:
    """Kết quả match giữa một term trong query và một cột trong schema."""
    query_term: str       # Từ/cụm từ trong câu query
    column_name: str      # Tên cột khớp trong schema
    match_type: str       # "exact", "normalized", "synonym", "fuzzy"
    confidence: float     # 0.0 - 1.0


def _normalize(text: str) -> str:
    """
    Chuẩn hóa chuỗi: lowercase, bỏ dấu tiếng Việt, 
    thay thế ký tự đặc biệt bằng underscore.
    """
    text = text.lower().strip()
    # Bỏ dấu tiếng Việt
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Thay ký tự đặc biệt bằng underscore
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text


def _fuzzy_score(a: str, b: str) -> float:
    """Tính điểm tương đồng giữa 2 chuỗi bằng SequenceMatcher."""
    return SequenceMatcher(None, a, b).ratio()


def match_columns(
    query: str,
    schema_columns: List[str],
    threshold: float = 0.55
) -> List[ColumnMatch]:
    """
    So khớp các từ/cụm từ trong câu query với danh sách cột CSV.
    
    Args:
        query: Câu query của người dùng
        schema_columns: Danh sách tên cột trong CSV schema
        threshold: Ngưỡng tối thiểu để coi là match (cho fuzzy)
    
    Returns:
        Danh sách ColumnMatch đã sắp xếp theo confidence giảm dần.
        Mỗi cột chỉ xuất hiện tối đa 1 lần (lấy match tốt nhất).
    """
    matches: Dict[str, ColumnMatch] = {}  # column_name → best match
    
    query_lower = query.lower()
    normalized_query = _normalize(query)
    
    # Tạo normalized map cho schema columns
    col_normalized = {col: _normalize(col) for col in schema_columns}
    
    for col in schema_columns:
        col_lower = col.lower()
        col_norm = col_normalized[col]
        best_match: Optional[ColumnMatch] = None
        
        # === 1. Exact match: tên cột xuất hiện nguyên vẹn trong query ===
        if col_lower in query_lower:
            best_match = ColumnMatch(
                query_term=col_lower,
                column_name=col,
                match_type="exact",
                confidence=1.0
            )
        
        # === 2. Normalized match ===
        if not best_match and col_norm in normalized_query:
            best_match = ColumnMatch(
                query_term=col_norm,
                column_name=col,
                match_type="normalized",
                confidence=0.9
            )
        
        # === 3. Synonym match ===
        if not best_match:
            for viet_term, eng_patterns in COLUMN_SYNONYMS.items():
                # Check if Vietnamese synonym is in query
                if viet_term in query_lower:
                    # Check if column matches any of the English patterns
                    for pattern in eng_patterns:
                        if pattern in col_lower or col_lower in pattern:
                            best_match = ColumnMatch(
                                query_term=viet_term,
                                column_name=col,
                                match_type="synonym",
                                confidence=0.8
                            )
                            break
                
                # Check if any English pattern is in query
                if not best_match:
                    for pattern in eng_patterns:
                        if pattern in query_lower:
                            if pattern in col_lower or col_lower in pattern:
                                best_match = ColumnMatch(
                                    query_term=pattern,
                                    column_name=col,
                                    match_type="synonym",
                                    confidence=0.8
                                )
                                break
                
                if best_match:
                    break
        
        # === 4. Fuzzy match: so khớp từng token trong query với tên cột ===
        if not best_match:
            query_tokens = re.split(r"[\s,;.!?]+", query_lower)
            for token in query_tokens:
                if len(token) < 3:  # Bỏ qua token quá ngắn
                    continue
                score = _fuzzy_score(_normalize(token), col_norm)
                if score >= threshold:
                    if not best_match or score > best_match.confidence:
                        best_match = ColumnMatch(
                            query_term=token,
                            column_name=col,
                            match_type="fuzzy",
                            confidence=round(score, 3)
                        )
        
        if best_match:
            # Giữ match tốt nhất cho mỗi column
            existing = matches.get(col)
            if not existing or best_match.confidence > existing.confidence:
                matches[col] = best_match
    
    # Sắp xếp theo confidence giảm dần
    result = sorted(matches.values(), key=lambda m: m.confidence, reverse=True)
    return result
