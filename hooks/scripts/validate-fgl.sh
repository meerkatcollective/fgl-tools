#!/usr/bin/env bash
# PostToolUse hook: validate .fgl files written or edited by Claude Code.
#
# Reads the hook's JSON input from stdin, extracts the file path from
# tool_input.file_path, runs the bundled fgl_validator against it, and
# emits diagnostics back to Claude via the documented JSON output channel
# (advisory-only — never blocks the write).
set -u

input=$(cat)

# Extract file path. The hook payload shape is documented at
# https://code.claude.com/docs/en/hooks — tool_input.file_path is the
# canonical field for Write and Edit.
file_path=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    payload = json.load(sys.stdin)
    print(payload.get("tool_input", {}).get("file_path", ""))
except Exception:
    pass
')

if [ -z "$file_path" ]; then
    exit 0
fi

# Defensive: only act on .fgl files. The hooks.json `if` clause should already
# guarantee this, but matchers can vary across Claude Code versions.
case "$file_path" in
    *.fgl) ;;
    *) exit 0 ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
    cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"FGL validator unavailable: python3 not found on PATH. Install Python 3.10+ to enable .fgl validation."}}
JSON
    exit 0
fi

if ! PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -c 'import lark' >/dev/null 2>&1; then
    cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"FGL validator unavailable: `lark` not installed. Run `pip install lark` (or `uv pip install --system lark`) on the host to enable .fgl validation."}}
JSON
    exit 0
fi

output=$(PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m fgl_validator "$file_path" 2>&1)
status=$?

if [ "$status" -eq 0 ] && [ -z "$output" ]; then
    summary="✓ FGL valid: $file_path"
else
    summary=$(printf 'FGL validator output for %s (exit %d):\n%s' "$file_path" "$status" "$output")
fi

python3 -c '
import json, sys
summary = sys.argv[1]
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": summary}}))
' "$summary"

exit 0
