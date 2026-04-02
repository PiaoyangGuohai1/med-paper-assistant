# mdpaper + pubmed-search 全面测试报告

**测试日期**: 2026-04-02（重启后二次验证完成）
**测试项目**: masld-ckm-guangxi
**测试环境**: macOS Darwin 24.6.0, Claude Code (Opus 4.6), pandoc 3.9.0.2

---

## 重启后验证结果（2026-04-02 二次验证）

| 修复项 | 验证结果 |
|--------|---------|
| PubMed API SSL (`mcp__pubmed__search_pubmed`) | ✅ 完全修复，返回结构化数据 |
| `get_reference_for_analysis` | ✅ 完全修复 |
| `save_reference_analysis` | ✅ 完全修复 |
| `save_reference_mcp` | ⚠️ 仍不可用 — 依赖 pubmed-search HTTP API（非 SSL 问题） |
| `pubmed-search` 的 `fetch_article_details` | ⚠️ DNS 解析失败，与 SSL 无关 |

### 可行的文献保存流程（已验证）

`save_reference_mcp` 不可用时的替代方案：
```
mcp__pubmed__search_pubmed(query="PMID[pmid]")  →  获取结构化数据
mcp__mdpaper__save_reference(article={...})      →  用 last_name/initials 格式保存
```
此流程已验证端到端可用。

### 两个 PubMed MCP Server 的区别

| Server | 工具 | 状态 |
|--------|------|------|
| `mcp__pubmed` | `search_pubmed`, `get_paper_fulltext` | ✅ 正常 |
| `mcp__pubmed-search` | `unified_search`, `fetch_article_details`, `find_related_articles` 等 | ⚠️ PubMed 源有 DNS 问题，OpenAlex 等备选源正常 |

---

## 已修复的问题（2 个）

### 1. PubMed API SSL 故障

- **症状**: `search_pubmed`、`fetch_article_details`、`save_reference_mcp` 全部报 SSL EOF 错误
- **根因**: 系统代理（port 7890/8443）无法处理 NCBI 等学术 API 的 SSL 连接。Python urllib 使用小写 `https_proxy`（7890），curl 使用大写 `HTTPS_PROXY`（8443），两个代理对 NCBI 都不通。直连无代理时完全正常。
- **修复**: 在 `/Users/longxinyang/Documents/OBSIDIAN/03_课题进度/.mcp.json` 中为 `pubmed-search` 和 `mdpaper` 的 `env` 添加：
  ```json
  "no_proxy": "ncbi.nlm.nih.gov,nlm.nih.gov,nih.gov,api.openalex.org,api.crossref.org,api.semanticscholar.org,api.unpaywall.org,europepmc.org",
  "NO_PROXY": "ncbi.nlm.nih.gov,nlm.nih.gov,nih.gov,api.openalex.org,api.crossref.org,api.semanticscholar.org,api.unpaywall.org,europepmc.org"
  ```
- **状态**: ✅ 已修改配置文件，**需重启 Claude Code 会话生效**

### 2. `get_reference_for_analysis` / `save_reference_analysis` 代码 bug

- **症状**: 调用时报 `'ReferenceManager' object has no attribute 'get_reference_details'`
- **根因**: MCP 工具层（`interfaces/mcp/tools/reference/manager.py` L537, L640）调用 `ref_manager.get_reference_details(pmid)`，但 `ReferenceManager` 类（`infrastructure/persistence/reference_manager.py`）只有 `get_reference_summary()` 和 `get_metadata()` 方法，没有 `get_reference_details()`
- **修复**: 在 `reference_manager.py` 的 `get_reference_summary()` 方法前添加了 `get_reference_details()` 方法：
  ```python
  def get_reference_details(self, pmid: str) -> Optional[Dict[str, Any]]:
      meta = self.get_metadata(pmid)
      if not meta:
          return None
      ref_dir = os.path.join(self.base_dir, pmid)
      return {"metadata": meta, "ref_dir": ref_dir}
  ```
- **文件**: `/Users/longxinyang/Documents/OBSIDIAN/tools/med-paper-assistant/src/med_paper_assistant/infrastructure/persistence/reference_manager.py`
- **状态**: ✅ 已修改代码，**需重启 MCP server 生效**

---

## 工具测试总表（38 个工具）

### 项目管理（9/9 通过）

| 工具 | 状态 | 备注 |
|------|------|------|
| `create_project` | ✅ | |
| `list_projects` | ✅ | |
| `get_workspace_state` | ✅ | |
| `get_current_project` | ✅ | |
| `switch_project` | ✅ | |
| `update_project_settings` | ✅ | |
| `validate_project_structure` | ✅ | 首次运行缺 `.audit` 目录，需手动 `mkdir` |
| `list_drafts` | ✅ | |
| `list_templates` | ✅ | |

### 文献管理（8/11 通过，3 个待重启）

| 工具 | 状态 | 备注 |
|------|------|------|
| `save_reference` (手动) | ✅ | `authors_full` 必须用 `{"last_name": "xx", "initials": "xx"}` 格式 |
| `save_reference_mcp` | ⏳ | 依赖 PubMed API，重启后可用 |
| `list_saved_references` | ✅ | |
| `get_reference_details` | ✅ | |
| `search_local_references` | ✅ | |
| `get_available_citations` | ✅ | |
| `suggest_citations` | ✅ | |
| `scan_draft_citations` | ✅ | |
| `preview_citations` | ✅ | |
| `get_reference_for_analysis` | ⏳ | 代码已修复，重启后可用 |
| `save_reference_analysis` | ⏳ | 代码已修复，重启后可用 |

### 写作（5/5 通过）

| 工具 | 状态 | 备注 |
|------|------|------|
| `write_draft` | ✅ | 硬门槛：需 ≥20 篇文献，可用 `skip_validation=true` 绕过 |
| `read_draft` | ✅ | |
| `draft_section` | ✅ | 返回写作指令，非直接写内容 |
| `patch_draft` | ✅ | |
| `insert_citation` | ✅ | |

### 质控（5/5 通过）

| 工具 | 状态 | 备注 |
|------|------|------|
| `count_words` | ✅ | |
| `check_formatting` | ✅ | |
| `validate_concept` | ✅ | `structure_only=true` 跳过 LLM 评估 |
| `run_quality_audit` | ✅ | |
| `build_bibliography` | ✅ | 只识别 `[[wikilink]]` 引用，不识别 `[1]` 编号引用 |

### 导出（1/1 受限）

| 工具 | 状态 | 备注 |
|------|------|------|
| `export_docx` | ⚠️ | review loop 硬门槛阻塞。pandoc 底层导出正常 |

### pubmed-search 搜索工具（6/7 通过）

| 工具 | 状态 | 备注 |
|------|------|------|
| `unified_search` | ✅ | PubMed 不通时自动 fallback 到 OpenAlex |
| `search_pubmed` | ⏳ | SSL 问题，重启后可用 |
| `parse_pico` | ✅ | |
| `generate_search_queries` | ✅ | |
| `find_related_articles` | ✅ | |
| `find_citing_articles` | ✅ | |
| `get_article_references` | ⚠️ | 依赖 PMC 索引，非所有文章可用（设计限制） |

---

## 关键发现与注意事项

### `save_reference` 手动保存的作者格式

`authors_full` 字段 **必须** 用以下格式：
```json
{"last_name": "Ndumele", "initials": "CE"}
```
**不能** 用 `{"family": "Ndumele", "given": "CE"}`（CSL-JSON 格式），后者会导致 Vancouver 引用中作者名为空。

这是因为 `csl_formatter.py` 的转换逻辑：
```python
authors.append({
    "family": au.get("last_name", ""),
    "given": au.get("first_name", au.get("initials", "")),
})
```
它从 `last_name`/`first_name`/`initials` 读取，输出为 CSL-JSON 的 `family`/`given`。

### 两种引用格式路径

| 路径 | 语法 | 适用场景 |
|------|------|---------|
| PMID 直接引用 | `(PMID:37807924)` 在 `write_draft` 中 | 写草稿时自动转换为编号 `[1]` |
| Wikilink 引用 | `[[ndumele2023_37807924]]` 在 `patch_draft` 中 | 编辑时使用，`build_bibliography` 和 `export_docx` 识别 |

建议统一使用 **wikilink** 格式，以确保 `build_bibliography` 和 `export_docx` 正常工作。

### 硬门槛（Hard Gates）

| 门槛 | 要求 | 绕过方式 |
|------|------|---------|
| 文献数量 | ≥20 篇才能 `write_draft` | `skip_validation=true` |
| Review Loop | 完成审稿轮次才能 `export_docx` | 无（需完成 `start_review_round` → `submit_review_round`） |
| Concept 验证 | novelty score ≥75 才能写正文 | `skip_validation=true` 或 `structure_only=true` |

---

## 待办事项

- [ ] 重启 Claude Code 会话使配置生效
- [ ] 重启后验证 `search_pubmed` 和 `save_reference_mcp` 正常
- [ ] 重启后验证 `get_reference_for_analysis` 和 `save_reference_analysis` 正常
- [ ] 考虑是否需要将 `NO_PROXY` 配置也加到全局 `~/.claude/settings.json`

---

## 测试项目信息

- **项目 slug**: `masld-ckm-guangxi`
- **项目路径**: `/Users/longxinyang/Documents/OBSIDIAN/tools/med-paper-assistant/projects/masld-ckm-guangxi/`
- **期刊配置**: IJE (International Journal of Epidemiology)
- **已保存文献**: 3 篇（PMID: 37807924, 37364790, 37807920）
- **已保存草稿**: methods.md (776 words)
- **paper 备份**: `paper_backup_20260402`
