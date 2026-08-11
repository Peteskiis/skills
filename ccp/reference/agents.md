# Agents

Manage AI agents on the managed-agents service. The server owns all
validation (membership, model, tools, reasoning effort) — on a 400, read the
error message: it names valid values.

## Commands

- `ccp apply -f <manifest.yaml> [--org-id <org>] [--dry-run]` — reconcile one
  `Agent` document and its optional Deployments and schedules. The server reports each resource
  as `created`, `updated`, `unchanged`, or `deleted`. `--dry-run` performs the
  same validation and diff without persisting anything.
- `ccp delete -f <manifest.yaml> [--org-id <org>] [--dry-run]` — permanently
  delete an applied Agent, all versions, and dependent runtime history. A later
  apply creates a new Agent id at version 1.
- `ccp agent list [--org-id <org>]` (alias `ls`) — list the organization's
  agents: id, name, model, version, definition source, updated time.
- `ccp agent get <agent_id> [--version <number>]` — full definition: model,
  reasoning effort, tools, MCP declarations, metadata, version, source,
  timestamps, system prompt. Omit `--version` for the current definition.
  Unknown or inaccessible IDs return the server's 404.
- `ccp agent versions <agent_id>` — list every persisted definition snapshot,
  oldest first, with the latest marked `current`.
- `ccp agent create --name <name> --model <model> [options]` — create an
  agent and print its id. Options: `--org-id`, `--system <text>` or
  `--system-file <path>` (mutually exclusive; file must be UTF-8),
  repeatable `--tool <name>`, `--reasoning-effort <level>`, repeatable
  `--metadata key=value`. MCP server declarations cannot be set from the
  CLI yet.
- `ccp agent delete <agent_id> [--yes]` — permanently delete any customer-owned
  Agent, all versions, and dependent runtime history. For an applied Agent this
  also removes its manifest binding; reapplying the file creates a new Agent id.
- `ccp delete -f <manifest.yaml>` is the equivalent declarative addressing form
  when the manifest is available.

## Agent manifest

```yaml
apiVersion: agents.clusterbase.ai/v1
kind: Agent
metadata:
  name: release-notes
spec:
  name: Release Notes
  model: claude-sonnet-5
  system: |
    Write concise release notes.
  tools:
    - web_search
  mcp_servers: []
  reasoning_effort: low
  metadata:
    team: platform
  deployments:
    - name: weekday-build
      kickoff: Build and test the repository.
      environment:
        type: ephemeral
        template_id: workspace
        repos:
          - url: octocat/Hello-World
  schedules:
    - name: weekday-summary
      cron: "0 9 * * 1-5"
      timezone: America/Los_Angeles
      deployment: weekday-build
      enabled: true
```

`metadata.name` is the stable organization-scoped identity; changing
`spec.name` only changes the display name. Applied agents remain runnable but
must be edited by reapplying their manifest, not through imperative patch or
archive calls. Deployment and schedule names are stable within the Agent. Omitting
`spec.deployments` leaves existing applied Deployments untouched; a present list
is authoritative, and `deployments: []` removes them only when no preserved
schedule still references one. A Deployment supplies its kickoff and either an
HTTP-only execution lane (no `environment`) or a fresh ephemeral VM with an
optional validated template and repository list. Saved environment IDs, vaults,
secret environment variables, and private scheduled-repository credentials are
not accepted in this slice. Omitting
`spec.schedules` leaves existing applied schedules untouched; a present list is
authoritative, and `schedules: []` explicitly removes all schedules managed by
that Agent manifest. A schedule sets exactly one of `kickoff` (HTTP-only) or a
manifest-local `deployment` name. Imperative and boot-managed resources are
never pruned. Unknown fields and additional YAML documents are rejected.

Archived agents still appear in `list` and `get`, flagged with an
`archived` marker (and timestamp in `get`) — check for it before using an
agent from a listing. API errors include the server's `request_id`; quote
it when reporting a failure.

## Headless use

`apply`, manifest `delete`, `list`, and `create` accept `--org-id` (or `CCP_ORG_ID`) to skip the
interactive organization picker. `get` and `versions` need no org context —
they address the agent by ID directly; an unknown or inaccessible (cross-org)
ID returns the server's 404.

## Endpoint

Commands talk to the managed-agents service, derived from `CCP_API_URL`
(production: `https://agents.clusterbase.dev`). `CCP_AGENTS_API_URL`
overrides the derivation for bespoke clusters.
