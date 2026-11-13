# Agent compatibility test matrix

Test date: 2026-11-13

All Agent tests used the same read-only acceptance:

```text
psup selftest
psup print kp-verify-18
```

Expected result: `count=42`, matching SHA-256, and exact `kp-verify-18` Chinese text.

| Agent | Installed version | Result | Notes |
|---|---|---|---|
| 1Agent | 0.96.1 | PASS with caveat | `terminal_create/terminal_exec` works; this build exposes deterministic provider only and rejects `deepseek` |
| Hermes | 0.22.5+3133.gc419cf7 | PASS | 8.5s |
| pi | 1.5.0 | PASS | package installed; 3.4s |
| Claude Code | 2.1.314 | PASS | custom endpoint warning `deepseek-flash[1m]`; commands worked |
| OpenCode | 2.2.7 | PASS, standalone required | default background server failed; `--standalone` succeeded |
| Codex | 0.167.2 | PASS | plugin refreshed to 0.3.0; memory DB diagnostic warning unrelated to test |
| Copilot CLI | 1.0.107 | PASS | slow: about 4m41s |
| DeepSeek Harness headless | 0.2.1-rc.5 | PASS with env | requires `DEEPSEEK_API_KEY` in launch env |
| DeepSeek Harness web | 0.2.1-rc.5 | PASS, auth-gated | `127.0.0.1:35921` returns 401 without the browser URL token |

## Reproduction

Use each Agent's native non-interactive mode:

```sh
1agent run --task "$PROMPT" --read-root /home/skynet/skynet-prompt
hermes -z "$PROMPT"
pi -p --no-session --approve --tools read,bash,grep,find,ls "$PROMPT"
claude -p --no-session-persistence --allowedTools='Bash,Read' "$PROMPT"
opencode run --standalone --auto "$PROMPT"
codex exec --ephemeral --sandbox read-only "$PROMPT"
copilot -p "$PROMPT" --allow-all-tools --no-ask-user --stream off
set -a; . ~/.hermes/.env; set +a; dsh headless "$PROMPT"
```

`dsh web`:

```sh
set -a; . ~/.hermes/.env; set +a
dsh web --no-open --port 0
```

## Issues found

- 1Agent default `~/.1a` lacked `home.json`; initialized after backing up two empty lock files.
- 1Agent's current build has no DeepSeek provider despite accepting generic provider flags.
- OpenCode's default background service can fail; standalone mode is reliable.
- Codex `doctor` reports unrelated deficiencies: low disk warning, damaged memories DB, local provider reachability from restricted sandbox.
- dsh Web requires the printed browser-trust URL; raw loopback request correctly receives 401.

## Unified trigger acceptance

Canonical trigger: `；；`. ASCII `;;` is a compatibility alias only.

| Surface | Expected behavior | Result |
|---|---|---|
| Hermes | `；；` opens the native drawer | PASS; full-width trigger covered by drawer and session tests |
| pi | `；；` opens the native drawer | PASS; extension accepts full-width and ASCII triggers |
| Codex | `；；定验收` activates the index skill without `$psup` | PASS; returned the nine `定验收` entries |
| MCP | initialize advertises `；；` handling | PASS; contract test checks `prompt_search` guidance |
| OpenCode | `/prompts` remains the native entry | KNOWN LIMIT; text `；；` is not intercepted by the current TUI plugin |
| CLI / HTTP / Web | `psup` and normal UI controls remain available | PASS |

Machine-readable contract:

```json
{
  "trigger": "；；",
  "aliases": [";;"],
  "literal_escape": "；；；"
}
```

## Agent self-install acceptance

Codex was given one instruction to read `AGENT_INSTALL.md` and perform all four stages in a
new isolated HOME with `PATH=/usr/bin:/bin`:

```text
--plan --adapter cli
--apply --adapter cli
--verify --adapter cli
--uninstall --adapter cli
```

Result: `STATUS=PASS`.

- All four stages exited 0 and returned `ok=true`;
- installation wrote only under the temporary HOME and was fully uninstalled;
- real HOME and repository files were unchanged;
- `selftest` returned 42 entries and matching SHA-256;
- `doctor.ok=true`;
- host status is verified through `scripts/install.py --list --json`, so a zero exit code
  from a host command cannot be mistaken for a successful adapter installation.

### Copilot adapter installation

Real installation on Copilot CLI `1.0.107`:

```text
copilot skill add <repo>/adapters/copilot/psup/SKILL.md
copilot mcp add skynet-prompt -- ~/.local/bin/psup-mcp
```

Readback passed:

- personal skill `skynet-prompt` is enabled;
- MCP server `skynet-prompt` is enabled and points to `psup-mcp`;
- Extension `~/.copilot/extensions/skynet-prompt/extension.mjs` is installed;
- `agent_install.py --verify` reports the Copilot adapter installed.

`onUserPromptSubmitted` rewrites the trigger into an explicit skynet-prompt Skill/MCP request.
Model-level execution is not yet accepted because the current Copilot authentication token
cannot be validated. Installation and configuration succeeded independently of login.

### Claude Code adapter installation

Real installation on Claude Code `2.1.314`:

```text
~/.claude/skills/skynet-prompt/SKILL.md
~/.claude/skynet-prompt/hook.py
UserPromptSubmit hook in ~/.claude/settings.json
user-scope MCP server skynet-prompt
```

Configuration readback passed and `agent_install.py --verify` reports the Claude adapter
installed. Claude currently reports `CONNECTION_CLOSED` for every user MCP server, including
pre-existing `skynet-term` and `pencil`; MCP connectivity is therefore an environment blocker,
not a skynet-prompt-specific configuration failure.
