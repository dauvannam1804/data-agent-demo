"""
Semantic Analyzer module.
Phân tích cấu trúc câu query người dùng (rule-based, không dùng LLM)
để trích xuất: intent, cột liên quan, phép toán, filters, thời gian, output type.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from semantic.keyword_dicts import (
    AGGREGATION_KEYWORDS,
    INTENT_KEYWORDS,
    TIME_GRANULARITY_KEYWORDS,
    OUTPUT_TYPE_KEYWORDS,
    SORT_KEYWORDS,
    GROUP_BY_INDICATORS,
)
from semantic.column_matcher import match_columns, ColumnMatch


@dataclass
class SemanticResult:
    """Kết quả phân tích ngữ nghĩa của một câu query."""
    intent: str = "unknown"                          # "aggregation", "filter", ...
    matched_columns: List[ColumnMatch] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)  # "SUM", "AVG", "GROUP BY", ...
    group_by_hint: Optional[str] = None              # Gợi ý cột GROUP BY
    sort_order: Optional[str] = None                 # "ascending" / "descending"
    time_info: Optional[Dict] = None                 # {"granularity": "month", ...}
    output_type: str = "table"                       # "chart", "table", "single_value"
    confidence: float = 0.0                          # Tổng confidence

    def to_prompt_string(self) -> str:
        """Chuyển kết quả thành chuỗi readable để inject vào prompt LLM."""
        lines = []
        lines.append(f"- Ý định (intent): {self.intent}")

        if self.matched_columns:
            col_strs = [
                f"{m.column_name} (khớp từ '{m.query_term}', loại: {m.match_type}, "
                f"confidence: {m.confidence})"
                for m in self.matched_columns
            ]
            lines.append(f"- Các cột liên quan: {', '.join(col_strs)}")

        if self.operations:
            lines.append(f"- Phép toán gợi ý: {', '.join(self.operations)}")

        if self.group_by_hint:
            lines.append(f"- Gợi ý GROUP BY theo: {self.group_by_hint}")

        if self.sort_order:
            lines.append(f"- Sắp xếp: {self.sort_order}")

        if self.time_info:
            lines.append(f"- Thời gian: {self.time_info}")

        lines.append(f"- Loại output mong muốn: {self.output_type}")
        lines.append(f"- Confidence tổng: {self.confidence}")

        return "\n".join(lines)


class SemanticAnalyzer:
    """
    Phân tích ngữ nghĩa câu query dựa trên rule-based approach.
    
    Usage:
        analyzer = SemanticAnalyzer(schema_columns=["Revenue", "Month", "Product"])
        result = analyzer.analyze("Tính tổng doanh thu theo tháng")
    """

    def __init__(self, schema_columns: Optional[List[str]] = None):
        """
        Args:
            schema_columns: Danh sách tên cột từ CSV schema.
                            Nếu None, bỏ qua bước column matching.
        """
        self.schema_columns = schema_columns or []

    def analyze(self, query: str) -> SemanticResult:
        """
        Phân tích câu query và trả về SemanticResult.
        """
        result = SemanticResult()

        query_lower = query.lower().strip()

        # 1. Detect intent
        result.intent = self._detect_intent(query_lower)

        # 2. Detect aggregation operations
        result.operations = self._detect_operations(query_lower)

        # 3. Detect GROUP BY hint
        result.group_by_hint = self._detect_group_by(query_lower)

        # 4. Detect time info
        result.time_info = self._detect_time_info(query_lower)

        # 5. Detect output type
        result.output_type = self._detect_output_type(query_lower)

        # 6. Detect sort order
        result.sort_order = self._detect_sort_order(query_lower)

        # 7. Match columns from schema
        if self.schema_columns:
            result.matched_columns = match_columns(query, self.schema_columns)

        # 8. Compute overall confidence
        result.confidence = self._compute_confidence(result)

        return result

    def _detect_intent(self, query: str) -> str:
        """Phát hiện intent chính của câu query."""
        scores: Dict[str, int] = {}

        for intent, keywords in INTENT_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in query:
                    score += 1
            if score > 0:
                scores[intent] = score

        if not scores:
            return "unknown"

        # Trả về intent có score cao nhất
        return max(scores, key=scores.get)

    def _detect_operations(self, query: str) -> List[str]:
        """Phát hiện các phép toán aggregation."""
        ops = set()
        for keyword, sql_op in AGGREGATION_KEYWORDS.items():
            if keyword in query:
                ops.add(sql_op)
        return sorted(ops)

    def _detect_group_by(self, query: str) -> Optional[str]:
        """
        Phát hiện gợi ý GROUP BY.
        Tìm pattern: "theo <X>", "by <X>", "per <X>", "mỗi <X>"
        """
        for indicator in GROUP_BY_INDICATORS:
            pattern = rf"{re.escape(indicator)}\s+(\S+)"
            match = re.search(pattern, query)
            if match:
                group_term = match.group(1).strip(",.;!?")
                # Nếu group_term là một time keyword, dùng nó
                if group_term in TIME_GRANULARITY_KEYWORDS:
                    return TIME_GRANULARITY_KEYWORDS[group_term]
                # Nếu group_term khớp với cột nào trong schema
                if self.schema_columns:
                    for col in self.schema_columns:
                        if group_term.lower() in col.lower() or col.lower() in group_term.lower():
                            return col
                # Trả về nguyên gốc nếu không match
                return group_term
        return None

    def _detect_time_info(self, query: str) -> Optional[Dict]:
        """Phát hiện thông tin thời gian."""
        time_info = {}

        # Detect granularity
        for keyword, granularity in TIME_GRANULARITY_KEYWORDS.items():
            if keyword in query:
                time_info["granularity"] = granularity
                break

        # Detect specific year (4 digits)
        year_match = re.search(r"\b(19|20)\d{2}\b", query)
        if year_match:
            time_info["year_filter"] = int(year_match.group())

        # Detect specific month number
        month_match = re.search(r"tháng\s+(\d{1,2})", query)
        if not month_match:
            month_match = re.search(r"month\s+(\d{1,2})", query)
        if month_match:
            month_num = int(month_match.group(1))
            if 1 <= month_num <= 12:
                time_info["month_filter"] = month_num

        # Detect quarter
        quarter_match = re.search(r"(?:quý|quarter|q)\s*(\d)", query)
        if quarter_match:
            q_num = int(quarter_match.group(1))
            if 1 <= q_num <= 4:
                time_info["quarter_filter"] = q_num

        return time_info if time_info else None

    def _detect_output_type(self, query: str) -> str:
        """Phát hiện loại output mong muốn."""
        scores = {}
        for output_type, keywords in OUTPUT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query)
            if score > 0:
                scores[output_type] = score

        if not scores:
            return "table"

        return max(scores, key=scores.get)

    def _detect_sort_order(self, query: str) -> Optional[str]:
        """Phát hiện thứ tự sắp xếp."""
        for order, keywords in SORT_KEYWORDS.items():
            for kw in keywords:
                if kw in query:
                    return order
        return None

    def _compute_confidence(self, result: SemanticResult) -> float:
        """
        Tính confidence tổng dựa trên số lượng thông tin trích xuất được.
        Càng nhiều thông tin → confidence càng cao.
        """
        score = 0.0
        max_score = 5.0

        if result.intent != "unknown":
            score += 1.0

        if result.matched_columns:
            # Bonus theo số cột match và avg confidence
            avg_col_conf = sum(m.confidence for m in result.matched_columns) / len(result.matched_columns)
            score += min(avg_col_conf, 1.0)

        if result.operations:
            score += 1.0

        if result.group_by_hint:
            score += 0.5

        if result.time_info:
            score += 0.5

        if result.output_type != "table":  # table là default
            score += 0.5

        if result.sort_order:
            score += 0.5

        return round(score / max_score, 2)
