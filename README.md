# fgl-tools

A Claude Code plugin for authoring BOCA Friendly Ghost Language (FGL) ticket layouts. It ships:

- The `fgl-layout` skill — opinionated FGL authoring with embedded knowledge of opcodes, coordinate math, image conversion, and the BOCA Lemur / Ghostwriter command set.
- A Lark LALR validator (`fgl_validator` Python package) covering parse errors, unknown opcodes, wrong arity, coordinate bounds, missing terminators, and `<HW>` state hygiene.
- A `PostToolUse` hook that auto-validates any `.fgl` file Claude writes or edits, surfacing diagnostics into the next tool result.

## Host prerequisites

- Python ≥ 3.10
- `lark` — install once on the host:
  ```sh
  pip install lark
  # or
  uv pip install --system lark
  ```

If `lark` is missing the hook degrades gracefully: it emits a single advisory line telling you (and Claude) to install it, and never blocks the write.

## Install (marketplace)

```sh
claude /plugin marketplace add https://github.com/meerkat/fgl-tools
claude /plugin install fgl-tools
```

After install, the skill is namespaced as `/fgl-tools:fgl-layout`.

### Migration: remove the old standalone skill

If you previously installed the standalone `fgl-layout` skill at `~/.claude/skills/fgl-layout/`, remove it after enabling the plugin to avoid two copies drifting:

```sh
rm -rf ~/.claude/skills/fgl-layout
```

## Local development

From the repo root:

```sh
claude --plugin-dir ./
```

Then inside Claude Code:

```
/plugin list                 # confirm fgl-tools is enabled
/fgl-tools:fgl-layout "2x5.5 event ticket with logo, seat row, code128 barcode"
```

Edit any `.fgl` file the skill produces — the hook fires automatically and you'll see one of:

- `✓ FGL valid: <path>` (clean), or
- `<path>:<line>:<col>: <severity>: [FGL00X] <message>` per diagnostic.

## Repo layout

```
.claude-plugin/plugin.json     # plugin manifest
marketplace.json               # marketplace entry
skills/fgl-layout/             # the skill
hooks/                         # PostToolUse validation hook
src/fgl_validator/             # Lark LALR validator package
tests/                         # 29 pytest cases (fixture corpus)
plans/                         # implementation plans
```

## Running the validator standalone

The validator is a normal Python package; you can use it outside Claude Code:

```sh
python -m fgl_validator path/to/ticket.fgl
python -m fgl_validator --profile fgl46 path/to/ticket.fgl
```

Exit codes: `0` clean, `1` errors found, `2` CLI usage error (e.g. unknown profile).

## Scope

Out of scope: RFID tag programming, magnetic stripe encoding, and printer network/WiFi configuration. See the BOCA programming guide addenda.
