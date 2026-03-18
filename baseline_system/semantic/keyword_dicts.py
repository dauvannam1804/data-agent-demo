"""
Từ điển keyword mapping cho Semantic Layer.
Hỗ trợ tiếng Việt và tiếng Anh.
"""

# ============================================================
# AGGREGATION KEYWORDS → SQL aggregation functions
# ============================================================
AGGREGATION_KEYWORDS = {
    # Tiếng Việt
    "tổng": "SUM",
    "tổng cộng": "SUM",
    "tổng số": "SUM",
    "tính tổng": "SUM",
    "cộng": "SUM",
    "trung bình": "AVG",
    "bình quân": "AVG",
    "tb": "AVG",
    "đếm": "COUNT",
    "số lượng": "COUNT",
    "bao nhiêu": "COUNT",
    "lớn nhất": "MAX",
    "cao nhất": "MAX",
    "tối đa": "MAX",
    "nhiều nhất": "MAX",
    "nhỏ nhất": "MIN",
    "thấp nhất": "MIN",
    "tối thiểu": "MIN",
    "ít nhất": "MIN",
    # Tiếng Anh
    "sum": "SUM",
    "total": "SUM",
    "average": "AVG",
    "mean": "AVG",
    "avg": "AVG",
    "count": "COUNT",
    "how many": "COUNT",
    "number of": "COUNT",
    "maximum": "MAX",
    "max": "MAX",
    "highest": "MAX",
    "largest": "MAX",
    "top": "MAX",
    "minimum": "MIN",
    "min": "MIN",
    "lowest": "MIN",
    "smallest": "MIN",
}

# ============================================================
# INTENT KEYWORDS → query intent categories
# ============================================================
INTENT_KEYWORDS = {
    # Aggregation
    "aggregation": [
        "tổng", "trung bình", "đếm", "lớn nhất", "nhỏ nhất", "bình quân",
        "tổng cộng", "tổng số", "tính tổng", "cao nhất", "thấp nhất",
        "tối đa", "tối thiểu", "nhiều nhất", "ít nhất", "bao nhiêu",
        "sum", "total", "average", "mean", "count", "max", "min",
        "how many", "number of", "highest", "lowest",
    ],
    # Filtering
    "filter": [
        "lọc", "tìm", "chọn", "lấy", "hiển thị", "liệt kê", "danh sách",
        "trong đó", "thỏa mãn", "điều kiện", "chỉ", "riêng",
        "filter", "find", "where", "select", "show", "list", "only",
        "which", "that have", "with",
    ],
    # Comparison
    "comparison": [
        "so sánh", "hơn", "kém", "chênh lệch", "khác biệt",
        "giữa", "vs", "versus", "nhiều hơn", "ít hơn",
        "compare", "comparison", "difference", "between", "versus",
        "greater", "less", "more than", "fewer",
    ],
    # Ranking
    "ranking": [
        "top", "xếp hạng", "hạng", "cao nhất", "thấp nhất",
        "đầu tiên", "cuối cùng", "nhiều nhất", "ít nhất",
        "rank", "ranking", "top", "bottom", "first", "last",
        "best", "worst", "leading",
    ],
    # Trend analysis
    "trend": [
        "xu hướng", "biến động", "thay đổi", "tăng", "giảm",
        "qua các", "theo thời gian", "biến thiên", "diễn biến",
        "trend", "over time", "change", "growth", "decline",
        "increase", "decrease", "fluctuation", "evolution",
    ],
    # Distribution / grouped analysis
    "distribution": [
        "phân bổ", "phân phối", "theo", "nhóm", "chia theo",
        "từng", "mỗi", "per", "phân loại",
        "distribution", "breakdown", "by", "per", "each",
        "group by", "grouped", "categorize",
    ],
}

# ============================================================
# TIME-RELATED KEYWORDS → time granularity / filters
# ============================================================
TIME_GRANULARITY_KEYWORDS = {
    # Tiếng Việt
    "ngày": "day",
    "hàng ngày": "day",
    "theo ngày": "day",
    "tuần": "week",
    "hàng tuần": "week",
    "theo tuần": "week",
    "tháng": "month",
    "hàng tháng": "month",
    "theo tháng": "month",
    "quý": "quarter",
    "hàng quý": "quarter",
    "theo quý": "quarter",
    "năm": "year",
    "hàng năm": "year",
    "theo năm": "year",
    # Tiếng Anh
    "daily": "day",
    "day": "day",
    "by day": "day",
    "weekly": "week",
    "week": "week",
    "by week": "week",
    "monthly": "month",
    "month": "month",
    "by month": "month",
    "quarterly": "quarter",
    "quarter": "quarter",
    "by quarter": "quarter",
    "yearly": "year",
    "year": "year",
    "by year": "year",
    "annual": "year",
    "annually": "year",
}

# ============================================================
# OUTPUT TYPE KEYWORDS → chart / table / single value
# ============================================================
OUTPUT_TYPE_KEYWORDS = {
    "chart": [
        "vẽ", "biểu đồ", "đồ thị", "chart", "plot", "graph",
        "visualize", "visualization", "hình ảnh", "minh họa",
        "bar chart", "line chart", "pie chart", "histogram",
        "biểu đồ cột", "biểu đồ đường", "biểu đồ tròn",
    ],
    "table": [
        "bảng", "liệt kê", "danh sách", "table", "list",
        "tabulate", "rows", "dữ liệu", "chi tiết",
    ],
    "single_value": [
        "bao nhiêu", "là gì", "giá trị", "kết quả",
        "how much", "how many", "what is", "value",
    ],
}

# ============================================================
# SORT KEYWORDS → ordering
# ============================================================
SORT_KEYWORDS = {
    "ascending": [
        "tăng dần", "từ thấp đến cao", "nhỏ đến lớn",
        "ascending", "asc", "low to high", "smallest first",
    ],
    "descending": [
        "giảm dần", "từ cao đến thấp", "lớn đến nhỏ",
        "descending", "desc", "high to low", "largest first",
        "top",
    ],
}

# ============================================================
# GROUP BY INDICATORS → signals that query needs GROUP BY
# ============================================================
GROUP_BY_INDICATORS = [
    "theo", "mỗi", "từng", "chia theo", "nhóm theo",
    "phân theo", "per", "by", "each", "every",
    "group by", "grouped by", "for each",
]

# ============================================================
# COMMON COLUMN NAME SYNONYMS (Vietnamese → English patterns)
# Used for fuzzy column matching
# ============================================================
COLUMN_SYNONYMS = {
    "doanh thu": ["revenue", "sales", "income", "total_sales", "amount"],
    "lợi nhuận": ["profit", "net_profit", "gross_profit", "margin"],
    "chi phí": ["cost", "expense", "expenditure", "spending"],
    "giá": ["price", "unit_price", "cost", "amount"],
    "số lượng": ["quantity", "count", "amount", "num", "number"],
    "tên": ["name", "title", "label"],
    "ngày": ["date", "day", "created_at", "updated_at", "timestamp"],
    "tháng": ["month", "month_name", "month_num"],
    "năm": ["year"],
    "khách hàng": ["customer", "client", "buyer", "user"],
    "sản phẩm": ["product", "item", "goods", "sku"],
    "danh mục": ["category", "type", "class", "group"],
    "khu vực": ["region", "area", "zone", "location", "city", "state", "country"],
    "tuổi": ["age"],
    "giới tính": ["gender", "sex"],
    "điểm": ["score", "rating", "grade", "point"],
    "trạng thái": ["status", "state"],
    "mô tả": ["description", "desc", "detail"],
}
