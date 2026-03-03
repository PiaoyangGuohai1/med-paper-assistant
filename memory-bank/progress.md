# Progress (Updated: 2026-03-03)

## Done

- v0.4.6: uvManager.ts — cross-platform uv auto-detection + headless installation for zero-config marketplace mode
- v0.4.6: extensionHelpers.ts — 6 pure functions extracted from extension.ts for testability
- v0.4.6: Marketplace mode uses uvx med-paper-assistant (PyPI isolation, no PYTHONPATH)
- v0.4.6: Test expansion 52 → 106 vitest (extensionHelpers 30, packaging 21, uvManager 20, extension 35)
- v0.4.6: Fixed mcp.json skip check (require both mdpaper + med_paper_assistant)
- v0.4.6: Fixed getPythonPath only returning uv for med-paper-assistant pyproject.toml
- v0.4.6: CHANGELOG, ROADMAP, version bump completed

## Doing

- v0.4.6 release: git add + commit + push + tag

## Next

- Phase 5c TreeView/CodeLens/Diagnostics features
- Dashboard Webview embedding
- CI/CD pipeline for automated VSIX publish
