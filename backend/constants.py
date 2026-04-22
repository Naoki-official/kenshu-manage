# backend/constants.py
"""
CSV列名・システムフィールド名の定数定義。
列名が変更された場合、このファイルのみ修正すれば全体に反映される。
"""

# CSVの突合キー列名
COL_MANAGEMENT_NUMBER = "管理ナンバー"

# 納期列名
COL_DELIVERY_DATE = "納期"

# システム付加フィールド
FIELD_COMMENT = "_comment"
FIELD_CHECKED = "_checked"
FIELD_UPDATED_AT = "_updated_at"

# 翌月判定の閾値（10日）
NEXT_MONTH_THRESHOLD = 10
