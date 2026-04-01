# 医学论文写作助手 — Claude Code 项目指引

> 中文回复。每次做完任务需要进行详细的检查和汇报。

---

## 核心价值：逐步多轮演进

写论文是高度专业化的多轮迭代过程。Agent + MCP 框架通过三层架构实现类似的逐步演进：

| 层级 | 机制 | 触发 |
|------|------|------|
| **L1** Event-Driven Hooks | 78 个品质检查（55 Code-Enforced / 23 Agent-Driven） | Agent 操作 |
| **L2** Code-Level Enforcement | DomainConstraintEngine + ToolInvocationStore + PendingEvolutionStore | 工具调用 |
| **L3** Autonomous Self-Evolution | MetaLearningEngine (D1-D9)，跨对话持久化 | Phase 10 |

---

## 法规层级

CONSTITUTION.md > `.github/bylaws/*.md` > `.claude/skills/*/SKILL.md`

---

## MCP Server 架构

本项目使用以下 MCP server（注册在 `.mcp.json`）：

| Server | 功能 | Tool 数 |
|--------|------|---------|
| **mdpaper** | 项目管理、草稿、引用、分析、导出、质量检查 | 89 |
| **pubmed-search** | 多源文献搜索、引用网络、PICO、NCBI 扩展 | ~40 |
| **cgu** | 创意生成、深度思考、概念碰撞 | 13 |
| **asset-aware** | PDF 结构化解析、知识图谱、Docx 编辑 | 47 |
| **drawio** | 流程图（CONSORT/PRISMA 等） | — |

用户还有全局 MCP：`zotero-mcp`（Zotero 本地管理）、`mem0`（记忆系统）。

### 储存文献（MCP-to-MCP 优先）

| 方法 | 数据来源 | 使用时机 |
|------|---------|---------|
| `save_reference_mcp(pmid)` | PubMed API 直取 | **永远优先** |
| `save_reference(article)` | Agent 传递 | API 不可用时 fallback |

信任层：🔒 VERIFIED（PubMed 原始）→ 🤖 AGENT（`agent_notes`）→ ✏️ USER（人类笔记，AI 不碰）

---

## 研究技能（Skills）

位于 `.claude/skills/*/SKILL.md`。识别用户意图 → 读取 SKILL.md → 按工作流执行 → 决策点询问用户。

### 论文写作技能

| 技能 | 触发词 |
|------|--------|
| auto-paper | 全自动写论文、autopilot、一键写论文 |
| literature-review | 文献回顾、找论文、PubMed、全文阅读 |
| concept-development | concept、novelty、验证失败 |
| concept-validation | 验证、validate、可以开始写了吗 |
| parallel-search | 并行搜索、多组搜索、广泛搜索 |
| project-management | 新项目、切换项目、paper type |
| draft-writing | 写草稿、draft、Introduction、Methods |
| reference-management | 存这篇、save、储存文献 |
| word-export | 导出 Word、export、docx |
| academic-debate | 辩论、debate、devil's advocate |
| idea-validation | 假说验证、feasibility、PICO |
| manuscript-review | peer review、CONSORT、STROBE |
| submission-preparation | 投稿准备、cover letter |

### Novelty Check 规则

犀利回馈 + 给选项（直接写？修正？用 CGU？）。
- 禁止：讨好式回馈、自动改 NOVELTY、反复追分
- CGU 整合：`deep_think`（找弱点）、`spark_collision`（碰撞论点）、`generate_ideas`（广泛发想）

---

## Hook 架构（78 checks）

### Code-Enforced（55 个，Python 层确定性逻辑）

**A 系列 — post-write（每次写完即时）：**
A1 字数合规、A2 引用密度、A3 Anti-AI 检测、A3b AI 结构信号、A3c 语体一致性、A4 Wikilink 格式、A5 语言一致性（BrE/AmE）、A6 段落重复、A7 文献数量充足性

**B 系列 — post-section：**
B2 保护内容、B8 统计对齐、B9 时态一致性、B10 段落质量、B11 Results 客观性、B12 Introduction 结构、B13 Discussion 结构、B14 伦理声明、B15 Hedging 密度、B16 效果量报告

**C 系列 — post-manuscript：**
C2 投稿清单、C3 N 值一致性、C4 缩写首次定义、C5 Wikilink 可解析、C6 全文字数、C7a-d 图表/交叉引用、C9-C13 补充材料/引用分布/引用适切性/图表质量

**其他：**
D1-D9 Meta-Learning、F 数据溯源、G9 Git 状态、P1-P7 Pre-commit、R1-R6 Review hooks

### Agent-Driven（23 个，依赖 Agent 遵循 SKILL.md）

B1/B3-B7（post-section）、C1/C8（post-manuscript）、E1-E5（EQUATOR 报告指引）、P3/P8（commit）、G1-G8（通用）

---

## Pipeline 弹性机制

| 功能 | MCP Tool | 说明 |
|------|---------|------|
| Phase 回退 | `request_section_rewrite(sections, reason)` | 仅 Phase 7，regression > 2 强制询问 |
| 暂停 | `pause_pipeline(reason)` | 记录 draft hash |
| 恢复 | `resume_pipeline()` | 检测用户编辑，建议重新验证 |
| Section 审阅 | `approve_section(section, action)` | Autopilot 或手动 |

---

## 跨 MCP 编排

| 外部 MCP | Pipeline Phase | 触发条件 |
|----------|---------------|---------|
| pubmed-search | Phase 2 文献、Phase 2.1 全文 | 永远 |
| asset-aware | Phase 2.1 全文解析 | 有 PDF/OA 可取 |
| zotero-mcp | Phase 2 文献 | 用户需要导入 Zotero 文献 |
| cgu | Phase 3 概念、Phase 5 Discussion | novelty < 75 或论点弱 |
| drawio | Phase 5 Methods | 需 flow diagram |

---

## Workspace State

| 时机 | 动作 |
|------|------|
| 新对话 / 用户说「继续」 | `get_workspace_state()` |
| 开始重要任务 / 完成阶段 | `sync_workspace_state(doing, next_action)` |
| 写作中段落切换前 | `checkpoint_writing_context(section, plan, notes, refs)` |

`write_draft()` / `patch_draft()` 成功后自动写入写作检查点。

---

## 核心设计原则（CONSTITUTION §22-23）

| 原则 | 实现 |
|------|------|
| 可审计 | `.audit/` + quality-scorecard（0-10） |
| 可拆解 | Phase 独立、Hook 可插拔、输入/输出是文件 |
| 可重组 | checkpoint.json、Pipeline 任意 Phase 继续 |

### 自我改进边界

| 层级 | 限制 |
|------|------|
| L1 Skill — 更新 Lessons Learned | 自动 |
| L2 Hook — 调整阈值 | ±20% |
| L3 Instruction — 事实性内容 | 记录 decisionLog |

**禁止自动修改**：CONSTITUTION 原则、🔒 保护内容规则、save_reference_mcp 优先规则。

---

## 文件保护

**只读**（除非明确要求修改）：`.claude/skills/`、`src/`、`tests/`、`integrations/`、`CLAUDE.md`、`CONSTITUTION.md`、`ARCHITECTURE.md`、`pyproject.toml`

**可写**：`projects/`、`memory-bank/`、`docs/`、`templates/journal-profiles/`

---

## 用户研究方向

流行病学/生物统计学、生物信息学、机器学习/深度学习、医学影像。
当前项目：MASLD-CKM 广西社区队列研究（基于玉林纵向体检数据）。

## Python 环境

uv 优先。`pyproject.toml` + `uv.lock`。禁止全局安装。
