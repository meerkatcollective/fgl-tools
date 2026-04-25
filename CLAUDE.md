# fgl-tools

Tools for working with BOCA Friendly Ghost Language (FGL) — the markup language used by BOCA Lemur / Ghostwriter ticket printers (FGL22/24/26/42/44/46). Distributed as a Claude Code plugin.

## Layout

- `.claude-plugin/plugin.json` — plugin manifest.
- `marketplace.json` — marketplace entry pointing at this repo.
- `skills/fgl-layout/` — the FGL authoring skill (SKILL.md, references, templates, image-conversion script).
- `hooks/` — `PostToolUse` hook that runs the validator on any Write/Edit of a `.fgl` file.
- `src/fgl_validator/` — Python LALR validator (lark-based). Invokable as `python -m fgl_validator <path>`.
- `tests/` — fixture corpus and pytest suite (29 tests).
- `plans/` — implementation plans.

## Skill invocation

After installing the plugin, the skill is namespaced: `/fgl-tools:fgl-layout`.

The validation hook fires automatically on any `.fgl` write or edit and surfaces diagnostics into the next tool result.

## Host prerequisites

- Python ≥ 3.10
- `lark` (`pip install lark` or `uv pip install --system lark`)
