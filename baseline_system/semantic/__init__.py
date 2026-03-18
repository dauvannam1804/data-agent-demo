"""
Semantic Layer cho Baseline System.
Cung cấp SemanticAnalyzer (rule-based) để phân tích cấu trúc câu query
trước khi gửi cho LLM agents.
"""

from semantic.semantic_analyzer import SemanticAnalyzer, SemanticResult
from semantic.column_matcher import ColumnMatch, match_columns

__all__ = [
    "SemanticAnalyzer",
    "SemanticResult",
    "ColumnMatch",
    "match_columns",
]
