# MedPaper Assistant 架构分析 & 改造蓝图

**分析日期**: 2026-04-02
**当前版本**: fork from u9401066/med-paper-assistant
**目标**: 精简工具、放宽门槛、适配本地环境、深度理解后长期维护

---

## 一句话总结

92 个 MCP 工具，12 个阶段门槛，20 个 Skills。其中 **23 个核心工具 + 9 个硬门槛** 是真正干活的，其余是过度工程。

---

## 当前架构 (DDD 模式)

```
src/med_paper_assistant/
├── domain/          # 纯逻辑（引用格式化、新颖性评分、论文类型）
├── infrastructure/  # 存储+服务（项目管理、文献管理、质量审计、导出）
├── application/     # 用例编排（暂时很薄）
└── interfaces/mcp/  # MCP 工具注册（92 个工具，7 个分类）
    └── tools/
        ├── project/     14 工具
        ├── draft/       13 工具
        ├── reference/   12 工具
        ├── validation/   3 工具
        ├── analysis/    10 工具
        ├── review/      12 工具
        ├── export/       8 工具
        └── _shared/      7 工具 + 其他 13
```

---

## 工具精简方案

### 保留（23 个核心）

| 类别 | 保留工具 | 说明 |
|------|---------|------|
| **项目** | `create_project`, `list_projects`, `switch_project`, `get_current_project`, `update_project_settings`, `get_workspace_state` | 6 个 |
| **草稿** | `write_draft`, `draft_section`, `read_draft`, `patch_draft`, `get_available_citations`, `count_words` | 6 个 |
| **文献** | `save_reference_mcp`, `save_reference`, `list_saved_references`, `search_local_references`, `get_reference_details`, `delete_reference` | 6 个 |
| **质控** | `validate_concept`, `check_formatting` | 2 个 |
| **导出** | `export_docx`, `build_bibliography` | 2 个 |
| **分析** | `insert_figure`, `insert_table` | 2 个（按需） |

### 降级为警告（9 个硬门槛 → 软提示）

| 当前硬门槛 | 改为 |
|-----------|------|
| Phase 2: ≥10 篇文献才能写 | 警告："建议先积累文献" |
| Phase 3: 新颖性 ≥75 才能写 | 警告："新颖性评分偏低" |
| Phase 5: Hook A/B 必须全过 | 报告问题，不阻塞 |
| Phase 6: quality-scorecard 必须存在 | 可选 |
| Phase 6.5: meta-learning 必须完成 | 删除 |
| Phase 7: review loop 必须 2 轮 | 可选 |
| write_draft: ≥20 篇文献 (Hook A7) | 警告 |
| export_docx: review loop 必须完成 | 删除阻塞 |
| review_asset_for_insertion: 图表证书 | 删除阻塞 |

### 可删除（~50 个过度工程工具）

| 类别 | 可删工具 | 理由 |
|------|---------|------|
| 项目 | `archive_project`, `delete_project`, `start_exploration`, `convert_exploration_to_project`, `save_diagram`, `list_diagrams`, `open_project_files`, `checkpoint_writing_context`, `sync_workspace_state` | 极少使用 |
| 草稿 | `check_writing_order`, `delete_draft`, `suggest_citations`, `scan_draft_citations`, `insert_citation`, `sync_references` | 可由 agent 手动完成 |
| 文献 | `read_reference_fulltext`, `save_reference_pdf`, `format_references`, `rebuild_foam_aliases`, `get_reference_for_analysis`, `save_reference_analysis` | 使用频率极低 |
| 验证 | `validate_wikilinks`, `compare_with_literature` | agent 可直接做 |
| 分析 | `generate_table_one`, `detect_variable_types`, `list_data_files`, `run_statistical_test`, `analyze_dataset`, `create_plot`, `review_asset_for_insertion`, `list_assets` | R/Python 脚本更好 |
| 审评 | `validate_phase_gate`, `pipeline_heartbeat`, `start_review_round`, `submit_review_round`, `approve_section`, `request_section_rewrite`, `pause_pipeline`, `resume_pipeline`, `approve_concept_review`, `reset_review_loop`, `record_hook_event`, `verify_evolution`, `evolve_constraint`, `apply_pending_evolutions`, `diagnose_tool_health`, `run_meta_learning`, `run_quality_audit`, `run_writing_hooks`, `run_review_hooks`, `check_domain_constraints` | 整个管道系统过度工程 |
| 导出 | `start_document_session`, `insert_section`, `verify_document`, `save_document`, `list_templates`, `read_template`, `export_pdf`, `preview_citations` | Word 直接写入不如 Pandoc |

### Skills 精简

| 保留 | 删除/合并 |
|------|----------|
| draft-writing | auto-paper (合并到 draft-writing) |
| literature-review | parallel-search (合并到 literature-review) |
| reference-management | concept-validation (合并到 concept-development) |
| concept-development | project-init (合并到 project-management) |
| manuscript-review | ddd-architect, code-refactor, git-doc-updater 等开发类 skill |
| submission-preparation | memory-updater, readme-updater, changelog-updater |
| word-export | test-generator, code-reviewer |
| academic-debate | idea-validation (合并到 concept-development) |

---

## 改造优先级

### P0：立即可做（不改代码，只改配置）
- [ ] 放宽 write_draft 的 20 篇文献门槛 → 改为警告
- [ ] 放宽 export_docx 的 review loop 门槛 → 改为警告
- [ ] 更新 Skills 中的 MCP 工具说明适配已修复的 save_reference_mcp

### P1：短期（改少量代码）
- [ ] 将所有 validate_phase_gate 硬门槛改为软警告
- [ ] 删除 meta-learning 和 evolution 相关工具（过度工程）
- [ ] 精简 review 类工具（12 个 → 2 个）

### P2：中期（重构模块）
- [ ] 合并相似 Skills（20 个 → 8 个）
- [ ] 删除不用的 MCP 工具注册
- [ ] 简化项目目录结构（删除 .audit、.memory 强制要求）

### P3：长期（架构调整）
- [ ] 评估是否将部分 MCP 工具转为 Skill（如质控规则）
- [ ] 统一引用格式路径（PMID vs wikilink 二选一）
- [ ] 适配多期刊投稿流程

---

## 核心文件位置速查

| 要改什么 | 文件 |
|---------|------|
| MCP 工具注册 | `interfaces/mcp/tools/*/` |
| 硬门槛逻辑 | `infrastructure/persistence/pipeline_gate_validator.py` |
| 文献保存 | `infrastructure/persistence/reference_manager.py` |
| 草稿读写 | `infrastructure/services/drafter.py` |
| 引用格式化 | `domain/services/citation_formatter.py` + `infrastructure/services/csl_formatter.py` |
| 新颖性评分 | `domain/services/novelty_scorer.py` |
| Pandoc 导出 | `infrastructure/services/pandoc_exporter.py` |
| 项目管理 | `infrastructure/persistence/project_manager.py` |
| Skills | `.claude/skills/*/SKILL.md` |
| 期刊配置 | `templates/journal-profiles/*.yaml` |
