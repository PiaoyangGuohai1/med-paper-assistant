"""
Paper-aware pre-commit hook — P-series quality checks.

Scans all projects under projects/ for draft files, then runs
WritingHooksEngine.run_precommit_hooks() on each. Exits non-zero
if any CRITICAL issue is found **and** drafted files are staged.

When no draft files are staged (e.g. infrastructure-only commits),
the hook still runs but only prints warnings — never blocks.

Registered in .pre-commit-config.yaml as a local hook.

Usage:
    uv run python scripts/hooks/paper_precommit.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _staged_files_include_drafts(workspace: Path) -> bool:
    """Check if any staged files are inside projects/*/drafts/."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=workspace,
            check=False,
        )
        for line in result.stdout.splitlines():
            parts = line.split("/")
            if len(parts) >= 3 and parts[0] == "projects" and parts[2] == "drafts":
                return True
    except Exception:
        pass
    return False


def find_projects_with_drafts(workspace: Path) -> list[Path]:
    """Return project directories that contain at least one .md draft."""
    projects_dir = workspace / "projects"
    if not projects_dir.is_dir():
        return []

    result = []
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir():
            continue
        drafts_dir = proj_dir / "drafts"
        if drafts_dir.is_dir() and any(drafts_dir.glob("*.md")):
            result.append(proj_dir)
    return result


def collect_draft_content(project_dir: Path) -> str:
    """Read and concatenate all .md drafts (excluding concept.md) in a project."""
    drafts_dir = project_dir / "drafts"
    parts: list[str] = []
    for md_file in sorted(drafts_dir.glob("*.md")):
        if md_file.name == "concept.md":
            continue
        try:
            parts.append(md_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return "\n\n".join(parts)


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    projects = find_projects_with_drafts(workspace)

    if not projects:
        return 0  # No drafts to check — pass silently

    drafts_staged = _staged_files_include_drafts(workspace)

    # Lazy import to avoid slow startup when no drafts exist
    from med_paper_assistant.infrastructure.persistence.writing_hooks import WritingHooksEngine

    total_critical = 0
    reports: list[str] = []

    for proj_dir in projects:
        content = collect_draft_content(proj_dir)
        if not content.strip():
            continue

        engine = WritingHooksEngine(proj_dir)
        results = engine.run_precommit_hooks(content)

        proj_name = proj_dir.name
        proj_criticals = 0
        proj_warnings = 0
        proj_issues: list[str] = []

        for hook_id, hook_result in results.items():
            for issue in hook_result.issues:
                if issue.severity == "CRITICAL":
                    proj_criticals += 1
                    proj_issues.append(f"  ❌ [{hook_id}] {issue.message}")
                elif issue.severity == "WARNING":
                    proj_warnings += 1
                    proj_issues.append(f"  ⚠️  [{hook_id}] {issue.message}")

        if proj_issues:
            reports.append(
                f"📄 {proj_name}: {proj_criticals} critical, {proj_warnings} warnings\n"
                + "\n".join(proj_issues)
            )
        total_critical += proj_criticals

    if reports:
        header = "🔍 Paper Pre-commit Hooks (P1, P2, P4, P5, P7)\n" + "=" * 50
        print(header, file=sys.stderr)
        for r in reports:
            print(r, file=sys.stderr)
        print("=" * 50, file=sys.stderr)

    if total_critical > 0:
        if drafts_staged:
            print(
                f"\n❌ BLOCKED: {total_critical} CRITICAL issue(s). Fix before committing.",
                file=sys.stderr,
            )
            return 1
        else:
            print(
                f"\n⚠️  {total_critical} CRITICAL issue(s) in drafts (not blocking — no draft files staged).",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
