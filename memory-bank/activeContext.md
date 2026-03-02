# Active Context

## User Preferences

- **Git Identity**: u9401066 <u9401066@gap.kmu.edu.tw>

## 當前焦點 (2026-03-02)

v0.4.0 Bug Report 全部修復 + VSX macOS/Insiders 相容性修復完成。

### 當前狀態

| 項目                   | 數量/狀態                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| MCP Tools              | **85** (project/17, reference/12, draft/13, validation/3, analysis/9, review/21, export/10) |
| Skills                 | **26**                                                                                      |
| Hooks                  | **76 checks** (34 Code-Enforced / 42 Agent-Driven)                                          |
| Prompts                | **15**                                                                                      |
| Agents                 | **9**                                                                                       |
| Infrastructure classes | **8** core                                                                                  |
| Python unit tests      | **730 passed** (excl. external-dep tests)                                                   |
| VSX vitest             | **35 passed**                                                                               |
| Ruff errors            | **0**                                                                                       |

### 三層演進架構實作狀態

| 層級                         | 狀態                   | 說明                                                 |
| ---------------------------- | ---------------------- | ---------------------------------------------------- |
| L1 Event-Driven Hooks        | ⚠️ 34/76 Code-Enforced | 42 個 Agent-Driven 僅靠 SKILL.md                     |
| L2 Code-Level Enforcement    | ✅ 完整                | 5 元件全部上線                                       |
| L3 Autonomous Self-Evolution | ⚠️ Phase C 完成        | Git post-commit / EvolutionVerifier / Auto-PR 未實作 |

### 最近變更 (v0.4.0 Bug Fixes + macOS)

- **Bug 1**: `_compute_manuscript_hash()` 改為 hash 所有 `drafts/*.md`（修復 review deadlock）
- **Bug 2**: `citeproc-py` 改為 try/except lazy import + `_CITEPROC_AVAILABLE` flag
- **Bug 3**: `start_document_session` 的 `template_name` 改為可選，空值建立空白文件
- **Bug 4**: Hook A1 加入 `_strip_frontmatter()`、A6 排除統計標記假陽性
- **Bug 5**: export_pdf 連鎖修復（同 Bug 2 保護鏈）
- **macOS 相容性**: MCP env 繼承 PATH/HOME/SHELL/LANG，支援 homebrew 版本化 Python（python3.12）
- **VSX 完整性**: agents/ 新增 9 個 .agent.md、autoScaffoldIfNeeded()、build/validate 腳本更新
- **VSX bundle**: 所有 Python source 與 bundled 同步確認

### 已知問題

- `application/__init__.py` 的 import chain（missing pubmed modules）— 測試用 sys.modules mock 繞過
- 部分 test files 需外部模組（pubmed_search, matplotlib）— 已 ignore

## 下一步

- [ ] Git commit + marketplace publish
- [ ] Run actual project pipeline to generate evolution data
- [ ] Dashboard integration for evolution reports
- [ ] Consider grammar checker (language-tool-python as A7)

2026-03-02
