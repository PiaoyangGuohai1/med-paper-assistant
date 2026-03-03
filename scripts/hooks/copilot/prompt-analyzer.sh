#!/bin/bash
# =============================================================================
# UserPromptSubmit Hook — Intent Detection & Mode Enforcement
# =============================================================================
# Fires: when user submits a prompt.
# Purpose:
#   1. Detect research intent → inject workflow guidance
#   2. Detect mode-switch requests → remind to update .copilot-mode.json
#   3. Detect commit intent → remind pre-commit hooks
# Chain: [SessionStart] → UserPromptSubmit → [PreToolUse] → ...
# =============================================================================
set -e

if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null) || exit 0
if [ -z "$PROMPT" ]; then exit 0; fi

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
STATE_DIR="$WORKSPACE_ROOT/.github/hooks/_state"
mkdir -p "$STATE_DIR"

CONTEXT_PARTS=()

# --- 1. Detect mode-switch intent ---
if echo "$PROMPT" | grep -qiE '(開發模式|development mode|dev mode)'; then
    CONTEXT_PARTS+=("MODE SWITCH DETECTED: User wants development mode. Check .copilot-mode.json.")
elif echo "$PROMPT" | grep -qiE '(一般模式|normal mode|研究模式|research mode)'; then
    CONTEXT_PARTS+=("MODE SWITCH DETECTED: User wants normal/research mode. Check .copilot-mode.json.")
fi

# --- 2. Detect commit intent → chain to git-precommit skill ---
if echo "$PROMPT" | grep -qiE '(commit|提交|推送|push|收工|做完了)'; then
    CONTEXT_PARTS+=("COMMIT INTENT: Load git-precommit SKILL.md. Run G1-G9 + P1-P8 if paper files changed.")
fi

# --- 3. Detect writing intent → remind concept validation ---
if echo "$PROMPT" | grep -qiE '(寫草稿|draft|撰寫|Introduction|Methods|Results|Discussion|write section)'; then
    CONTEXT_PARTS+=("WRITING INTENT: Remember to validate_concept() before drafting (CONSTITUTION rule).")
fi

# --- 4. Detect autopilot intent ---
if echo "$PROMPT" | grep -qiE '(autopilot|全自動|一鍵|auto.?paper|從頭到尾)'; then
    CONTEXT_PARTS+=("AUTOPILOT INTENT: Load auto-paper SKILL.md. Follow 11-phase pipeline.")
fi

# --- 5. Detect checkpoint/memory intent ---
if echo "$PROMPT" | grep -qiE '(存檔|checkpoint|save|要離開|暫停|pause|怕忘記)'; then
    CONTEXT_PARTS+=("CHECKPOINT INTENT: Load memory-checkpoint SKILL.md. Externalize context now.")
fi

# --- Output ---
if [ ${#CONTEXT_PARTS[@]} -eq 0 ]; then
    exit 0
fi

CONTEXT=""
for PART in "${CONTEXT_PARTS[@]}"; do
    CONTEXT="${CONTEXT}${PART}\n"
done

jq -n \
    --arg ctx "$(echo -e "$CONTEXT")" \
    '{
        hookSpecificOutput: {
            hookEventName: "UserPromptSubmit",
            additionalContext: $ctx
        }
    }'
