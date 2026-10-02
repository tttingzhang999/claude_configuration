---
name: openclaw
description: >-
  Develop, configure, debug, or integrate with OpenClaw — the self-hosted
  gateway that connects chat apps (Discord, Slack, Telegram, WhatsApp,
  iMessage, Signal, Teams, etc.) to AI coding agents.

  Use this skill whenever the user asks about OpenClaw: writing or editing
  `~/.openclaw/openclaw.json`, setting up channels, configuring agents/models,
  running `openclaw` CLI commands, troubleshooting gateway/channel/routing
  issues, developing plugins, or integrating messaging platforms.

  Common triggers:
  - "configure openclaw"
  - "set up [channel] in openclaw"
  - "openclaw not working" / "openclaw doctor"
  - "add a channel" / "route to another agent"
  - writing or editing `~/.openclaw/openclaw.json`
  - any `openclaw <subcommand>` invocation

  This skill ENFORCES two rules: (1) consult the official docs at
  https://docs.openclaw.ai/ BEFORE any change, and (2) verify version
  compatibility between the docs and the local install (`openclaw --version`)
  before relying on any documented feature.

  OpenClaw is assumed to be installed on the user's machine.
---

# OpenClaw Development & Configuration

## STEP 0 — Self-Check (run FIRST, every invocation)

OpenClaw is one of the most-starred repos on GitHub and ships changes very fast. This skill **may be stale**. Before doing anything else:

### 0.1 Capture local version

```bash
openclaw --version
```

### 0.2 Fetch the live docs index

```
WebFetch https://docs.openclaw.ai/llms.txt
```

Then fetch whichever specific page is relevant to the current request (config, channels, troubleshooting, etc.).

### 0.3 Compare docs against this skill

Check these specific items in the live docs against what this file says:

| Skill claim | Verify against docs |
|-------------|---------------------|
| Config path `~/.openclaw/openclaw.json` | Getting Started / Configuration page |
| Default port `18789` | Getting Started page |
| CLI commands in the "Essential CLI Reference" table | Latest CLI reference / `openclaw --help` |
| DM policies (`pairing`/`allowlist`/`open`/`disabled`) | Channel configuration page |
| Hot-reload key categories | Gateway Configuration → reload section |
| Error signatures in the troubleshooting table | Gateway Troubleshooting page |
| Doc URL paths in the topic table | Live sitemap (`llms.txt`) |
| Env vars (`OPENCLAW_HOME`, etc.) | Gateway Configuration → environment section |

Also cross-check anything else you're about to use in this session.

### 0.4 If the skill is wrong, UPDATE IT FIRST

If any item above is outdated, missing, or contradicts the live docs:

1. **Stop** the current task.
2. Tell the user: *"This skill's reference for `<thing>` is outdated against docs version `<X>`. Updating the skill before proceeding."*
3. Edit `~/.claude/skills/openclaw/SKILL.md` to match the live docs (preserve structure; update only the affected sections).
4. After the skill is corrected, resume the original task using the updated guidance.

### 0.5 If the skill matches, proceed

State briefly: *"OpenClaw `<version>` confirmed; skill reference matches docs."* Then continue with the user's task.

---

## Core Rules (non-negotiable)

1. **DOCS FIRST.** Before any config edit, channel setup, plugin work, or troubleshooting step, fetch the relevant page from `https://docs.openclaw.ai/` with WebFetch. Never rely solely on training data — OpenClaw ships frequently and docs change.

2. **VERSION CHECK.** Run `openclaw --version` early. If you cannot find the version referenced in the docs, tell the user and proceed cautiously. Note any features that look newer than the local install.

3. **ASSUME INSTALLED.** OpenClaw is already on the user's machine. Skip install instructions unless explicitly asked.

## Workflow

### Step 1 — Always run first

```bash
openclaw --version
```

Capture the version (e.g. `OpenClaw 2026.4.15 (041266a)`) — every doc lookup in this session should be cross-referenced against it.

### Step 2 — Fetch the right doc page

Use WebFetch. Start from the topic table below. If you don't see a match, fetch the index at `https://docs.openclaw.ai/llms.txt` to discover all available pages.

| Topic | URL |
|-------|-----|
| Home / Overview | `https://docs.openclaw.ai/` |
| Getting Started | `https://docs.openclaw.ai/start/getting-started` |
| Onboarding wizard | `https://docs.openclaw.ai/start/wizard` |
| Gateway Configuration | `https://docs.openclaw.ai/gateway/configuration` |
| Gateway Security | `https://docs.openclaw.ai/gateway/security` |
| Gateway Troubleshooting | `https://docs.openclaw.ai/gateway/troubleshooting` |
| Remote access | `https://docs.openclaw.ai/gateway/remote` |
| Tailscale | `https://docs.openclaw.ai/gateway/tailscale` |
| Control UI | `https://docs.openclaw.ai/web/control-ui` |
| Features | `https://docs.openclaw.ai/concepts/features` |
| Multi-Agent Routing | `https://docs.openclaw.ai/concepts/multi-agent` |
| Nodes (iOS/Android) | `https://docs.openclaw.ai/nodes` |
| Help | `https://docs.openclaw.ai/help` |
| Full sitemap | `https://docs.openclaw.ai/llms.txt` |

**Channel pages** follow `https://docs.openclaw.ai/channels/<name>` (e.g. `telegram`, `discord`, `whatsapp`, `slack`, `signal`, `msteams`, `googlechat`, `matrix`, `feishu`, `imessage`).

### Step 3 — Reconcile docs with local version

- If the doc example uses a flag/field that `openclaw config schema` doesn't know about → version mismatch, warn the user.
- If the local version is much newer than what the docs explicitly document → the docs may lag; say so before guessing.

### Step 4 — Apply the change safely

- Prefer `openclaw config get <path>` / `openclaw config set <path> <value>` over hand-editing `~/.openclaw/openclaw.json` when the change is simple.
- For structural changes, read the config, edit it, and validate with `openclaw doctor` before restarting.
- OpenClaw **refuses to start** with invalid config — always validate before a destructive restart.

### Step 5 — Verify

```bash
openclaw doctor
openclaw gateway status
```

For channel changes: `openclaw channels status --probe`.

## Essential CLI Reference

| Command | Purpose |
|---------|---------|
| `openclaw --version` | Installed version (required before any work) |
| `openclaw status` | Overall system status |
| `openclaw gateway status [--json|--deep]` | Gateway health and diagnostics |
| `openclaw gateway restart` | Restart the gateway |
| `openclaw doctor [--fix]` | Diagnose / auto-fix config issues |
| `openclaw config get <path>` | Read a config value |
| `openclaw config set <path> <value>` | Write a config value |
| `openclaw config unset <path>` | Remove a config value |
| `openclaw config schema` | Output JSON schema for validation |
| `openclaw onboard [--install-daemon]` | Full onboarding wizard |
| `openclaw configure` | Config wizard |
| `openclaw dashboard` | Open Control UI (http://127.0.0.1:18789) |
| `openclaw channels status --probe` | Channel transport health |
| `openclaw logs --follow` | Tail gateway logs |
| `openclaw pairing list --channel <ch>` | Paired senders for a channel |
| `openclaw models status [--probe --probe-provider <p>]` | Model provider health / live auth probe |
| `openclaw models auth list [--provider <p>]` | List stored auth profiles + expiry |
| `openclaw models auth login --provider <p> [--device-code] [--profile-id <id>]` | (Re-)authenticate a provider via OAuth |
| `openclaw update [--dry-run] [--channel <ch>] [--tag <ver>]` | Supervised self-update (npm or git); `update status` shows channel + available version |
| `openclaw backup create --output <dir> --verify` | Backup before a major-release update |
| `openclaw infer model run --model <m> --prompt "hi" --json` | Direct model test |
| `openclaw cron status` / `openclaw cron runs --id <jobId>` | Cron job status |
| `openclaw nodes status` / `openclaw nodes describe --node <id>` | iOS/Android node status |
| `openclaw devices list` / `openclaw devices rotate` / `openclaw devices approve <req>` | Device auth |
| `openclaw browser status` | Browser tool health |
| `openclaw system heartbeat last` | Last heartbeat delivery |

## Config File (JSON5) — `~/.openclaw/openclaw.json`

```json5
{
  gateway: {
    port: 18789,
    auth: { token: "${OPENCLAW_GATEWAY_TOKEN}" },
    reload: { mode: "hybrid", debounceMs: 300 },
  },
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",
      model: {
        primary: "anthropic/claude-sonnet-4-6",
        fallbacks: ["openai/gpt-5.4"],
      },
      sandbox: { mode: "non-main", scope: "agent" },
      heartbeat: { every: "30m", target: "last", directPolicy: "allow" },
    },
    list: [
      { id: "main", default: true },
      { id: "work", workspace: "~/.openclaw/workspace-work" },
    ],
  },
  channels: {
    telegram: {
      enabled: true,
      botToken: "...",
      dmPolicy: "pairing",          // pairing | allowlist | open | disabled
      allowFrom: ["tg:123"],
    },
    whatsapp: {
      allowFrom: ["+15555550123"],
      groups: { "*": { requireMention: true } },
    },
  },
  session: {
    dmScope: "per-channel-peer",
    threadBindings: { enabled: true, idleHours: 24 },
    reset: { mode: "daily", atHour: 4, idleMinutes: 120 },
  },
  cron: { enabled: true, maxConcurrentRuns: 2 },
  hooks: {
    enabled: true,
    token: "${OPENCLAW_HOOKS_TOKEN}",
    path: "/hooks",
    allowedSessionKeyPrefixes: ["hook:"],
  },
  bindings: [
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },
  ],
}
```

### Key facts

- **Format:** JSON5 (comments and trailing commas allowed).
- **Env substitution:** `${VAR}` only matches `[A-Z_][A-Z0-9_]*`. Missing vars fail loudly. Escape with `$${VAR}`.
- **$include:** A single file replaces the object; an array deep-merges in order; up to 10 levels deep.
- **Hot reload (default `hybrid` mode):** Safe changes apply live. Restart-required keys: gateway server settings (port/bind/auth/TLS/tailscale/HTTP), discovery, canvasHost, plugins.
- **DM policies:** `"pairing"` (default) | `"allowlist"` (only `allowFrom`) | `"open"` (requires `allowFrom: ["*"]`) | `"disabled"`.
- **Rate limit:** Control-plane write RPCs (`config.apply`, `config.patch`, `update.run`) — 3 req / 60s per `deviceId+clientIp`.

## File & Path Reference

| Path | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | Main config (JSON5) |
| `~/.openclaw/.env` | Global env fallback |
| `~/.openclaw/workspace` | Default agent workspace |
| `~/.openclaw/control-ui-custom` | Custom Control UI root (if overridden) |
| `http://127.0.0.1:18789/` | Control UI (default) |

### Env vars

- `OPENCLAW_HOME` — home dir override
- `OPENCLAW_STATE_DIR` — state dir override
- `OPENCLAW_CONFIG_PATH` — config path override
- `OPENCLAW_LOAD_SHELL_ENV=1` — import shell env
- `OPENCLAW_APNS_RELAY_BASE_URL` / `OPENCLAW_APNS_RELAY_TIMEOUT_MS` — iOS push relay

## Troubleshooting Playbook

Run in order on any "it's broken":

```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe    # if channel-related
```

Then fetch `https://docs.openclaw.ai/gateway/troubleshooting` and match the error signature. Never guess a fix before reading the doc's signature table.

### Frequent error signatures

| Signature | Likely cause | First action |
|-----------|--------------|--------------|
| `HTTP 429 rate_limit_error: Extra usage required for long context` | Model has `params.context1m: true` | Disable or swap credential |
| `messages[...].content: invalid type: sequence, expected a string` | Local OpenAI backend expects string | Set `compat.requiresStringContent: true` |
| `drop guild message (mention required)` | Group requires mention | Check `groups."*".requireMention` |
| `AUTH_TOKEN_MISSING` / `AUTH_TOKEN_MISMATCH` | Dashboard auth drift | `openclaw config get gateway.auth.token`; re-paste |
| `AUTH_DEVICE_TOKEN_MISMATCH` | Cached device token stale | `openclaw devices rotate` |
| `PAIRING_REQUIRED` | Device not approved | `openclaw devices approve <requestId>` |
| `Gateway start blocked: set gateway.mode=local` | Mode not set | `openclaw onboard --mode local` |
| `refusing to bind gateway ... without auth` | Non-loopback bind with no auth | Configure token/trusted-proxy |
| `another gateway instance is already listening` | Port conflict | Kill other process or change `gateway.port` |
| `NODE_BACKGROUND_UNAVAILABLE` | Mobile node backgrounded | Bring app to foreground |
| `SYSTEM_RUN_DENIED: allowlist miss` | Command blocked by node policy | Add to allowlist or request approval |
| `unknown command 'browser'` | Plugin disabled | Add `browser` to `plugins.allow` |
| `Warning: workdir "<workspace>" is unavailable; using "<sandbox path>"` + `bash: <skill path>: No such file or directory` | Stale Docker sandbox container from prior sandbox mode; `exec` routes into container where workspace path is not mounted (`workspaceAccess: none`) | `openclaw sandbox recreate --agent <id> --force`; then verify with `openclaw sandbox explain --agent <id>` |

## Per-agent sandbox convention (for new agents / subagents)

When adding a new agent to `agents.list[]` in `openclaw.json`, **explicitly set `sandbox.mode`** — don't rely on `agents.defaults`.

Why:
- Default is `"non-main"` (sandboxes non-main sessions — subagents, threads, cron runs). If the agent depends on workspace-local skills (e.g. a skill under `<workspace>/skills/<name>/`), those paths don't exist inside the Docker container because `workspaceAccess: none` by default. Result: `No such file or directory` on skill scripts.
- Changing `agents.defaults.sandbox.mode` later does NOT kill existing containers — they linger and `exec` keeps routing into them. Explicit per-agent config makes each agent's behavior independent of defaults churn.

Template for a new agent that uses workspace-local skills:

```json5
{
  id: "my-agent",
  name: "my-agent",
  workspace: "/path/to/workspace",
  agentDir: "/path/to/agents/my-agent/agent",
  skills: ["my-custom-skill", "..."],
  tools: { profile: "full" },
  sandbox: { mode: "off" }   // ← REQUIRED if skills live under workspace
}
```

If you need sandboxing for security reasons, use `mode: "non-main"` or `"all"` **only after** verifying the workspace skill files are mirrored into the container (check `openclaw sandbox explain` → `workspaceAccess`).

After adding/changing sandbox config, always run `openclaw sandbox recreate --agent <id> --force` to kill any stale container — hot-reload does NOT do this.

## Anti-patterns (don't do these)

- Editing `~/.openclaw/openclaw.json` without first reading the schema or docs for the field you're touching.
- Suggesting a channel/plugin config from memory — channel config surfaces change between releases.
- Skipping `openclaw doctor` before restart; an invalid config prevents the gateway from starting and the user will think you broke it.
- Reusing `gateway.auth.token` as `hooks.token`. They must differ.
- Setting `plugins.allow` just to silence the "plugins.allow is empty; discovered non-bundled plugins may auto-load" warning. `allow` is a **restrictive** allowlist — once set, ONLY the listed ids load, silently disabling every stock plugin you left out (a default install has ~50). Check `openclaw plugins list --enabled` first; if you really want it, the list must enumerate every plugin you depend on. To block a specific plugin, use `plugins.deny` instead.
- Using `allowUnsafeExternalContent` anywhere outside of debugging.
- Re-installing OpenClaw to "fix" a config issue before running `openclaw doctor --fix`.

## When docs and local install disagree

State the disagreement explicitly to the user. Offer options:
1. Upgrade OpenClaw to match the docs (only if the user wants the new feature).
2. Use the older documented pattern that works on their version (fetch the version-pinned docs if available).
3. Work around the missing field (e.g. via an `$include` or a shim).

Do **not** silently pick one.
