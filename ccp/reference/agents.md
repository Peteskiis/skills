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

Archived agents still appear in `list` and `get`, flagged with an
`archived` marker (and timestamp in `get`) — check for it before using an
agent from a listing. API errors include the server's `request_id`; quote
it when reporting a failure.

## Headless use

`list` and `create` accept `--org-id` (or `CCP_ORG_ID`) to skip the
interactive organization picker. `get` needs no org context — it addresses
the agent by ID directly; an unknown or inaccessible (cross-org) ID returns
the server's 404.

## Endpoint

Commands talk to the managed-agents service, derived from `CCP_API_URL`
(production: `https://agents.clusterbase.dev`). `CCP_AGENTS_API_URL`
overrides the derivation for bespoke clusters.
