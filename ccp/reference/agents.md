# Agents

Manage AI agents on the managed-agents service. The server owns all
validation (membership, model, tools, reasoning effort) — on a 400, read the
error message: it names valid values.

## Commands

- `ccp agents list [--org-id <org>]` (alias `ls`) — list the organization's
  agents: id, name, model, version, definition source, updated time.
- `ccp agents get <agent_id>` — full definition: model, reasoning effort,
  tools, MCP declarations, metadata, version, source, timestamps, system
  prompt. Unknown or inaccessible IDs return the server's 404.
- `ccp agents create --name <name> --model <model> [options]` — create an
  agent and print its id. Options: `--org-id`, `--system <text>` or
  `--system-file <path>` (mutually exclusive; file must be UTF-8),
  repeatable `--tool <name>`, `--reasoning-effort <level>`, repeatable
  `--metadata key=value`. MCP server declarations cannot be set from the
  CLI yet.

## Headless use

Pass `--org-id` (or set `CCP_ORG_ID`) to skip the interactive organization
picker. `list`, `get`, and `create` are all non-interactive with it.

## Endpoint

Commands talk to the managed-agents service, derived from `CCP_API_URL`
(production: `https://agents.clusterbase.dev`). `CCP_AGENTS_API_URL`
overrides the derivation for bespoke clusters.
