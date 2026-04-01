
# 匯出 Word

技能：word-export

## Pipeline

1. `list_templates()` → 選擇模板
2. `read_template(name)` → 確認結構
3. `read_draft("manuscript.md")` → 取得內容
4. `start_document_session(template, journal?)` → 建立 session
5. `insert_section(section, content)` — 依序插入每個 section
6. `verify_document()` → 確認完整
7. `check_word_limits()` → 檢查字數（期刊限制）
8. `save_document(filename?)` → 輸出 .docx

## 規則

- 每個 section 獨立 `insert_section`，不合併
- `verify_document` 失敗 → 修正後重試
- 🔒 NOVELTY / SELLING POINTS → 必完整保留
- References → `format_references()` 先格式化
