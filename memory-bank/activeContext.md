# Active Context

## User Preferences

- **Git Identity**: u9401066 <u9401066@gap.kmu.edu.tw>

## 當前焦點 (2026-03-02)

v0.4.6 released — VSX zero-config marketplace mode + testability refactor。

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
| VSX vitest             | **106 passed** (4 test files)                                                               |
| Ruff errors            | **0**                                                                                       |

### 三層演進架構實作狀態

| 層級                         | 狀態                   | 說明                                                 |
| ---------------------------- | ---------------------- | ---------------------------------------------------- |
| L1 Event-Driven Hooks        | ⚠️ 34/76 Code-Enforced | 42 個 Agent-Driven 僅靠 SKILL.md                     |
| L2 Code-Level Enforcement    | ✅ 完整                | 5 元件全部上線                                       |
| L3 Autonomous Self-Evolution | ⚠️ Phase C 完成        | Git post-commit / EvolutionVerifier / Auto-PR 未實作 |

### 最近變更 (v0.4.6 Zero-Config Marketplace)

- **uvManager.ts**: 跨平台 uv 自動偵測 + headless 安裝（Windows PowerShell / Unix curl）
- **extensionHelpers.ts**: 6 個純函數從 extension.ts 抽取（shouldSkipMcpRegistration, isDevWorkspace, isMedPaperProject, determinePythonPath, countMissingBundledItems, buildDevPythonPath）
- **Marketplace mode**: `uvx med-paper-assistant`（完全隔離，無 PYTHONPATH 污染）
- **ensureUvReady()**: 啟動時自動安裝 uv，VS Code progress notification
- **mcp.json skip fix**: 同時檢查 server name + module path，避免誤跳過
- **getPythonPath fix**: 只對 med-paper-assistant pyproject.toml 返回 'uv'
- **Tests**: 52 → 106 vitest（extensionHelpers 30, packaging 21, uvManager 20, extension 35）

### 已知問題

- `application/__init__.py` 的 import chain（missing pubmed modules）— 測試用 sys.modules mock 繞過
- 部分 test files 需外部模組（pubmed_search, matplotlib）— 已 ignore

## 下一步

- [ ] Phase 5c TreeView/CodeLens/Diagnostics features
- [ ] Dashboard Webview 內嵌（取代 Simple Browser）
- [ ] CI/CD pipeline for automated VSIX publish
- [ ] Run actual project pipeline to generate evolution data
- [ ] Consider grammar checker (language-tool-python as A7)

2026-03-02
