# Agents

Create and update durable Agents by committing a manifest and running
`ccp apply -f agent.yaml` or `ccp apply -f agent.toml`. Keep the manifest as the source of truth.

Manage existing Agents on the managed-agents service. The server owns all
validation (membership, model, tools, reasoning effort) — on a 400, read the
error message: it names valid values.

## Commands

- `ccp apply -f <manifest.yaml> [--org-id <org>] [--dry-run]` — reconcile one
  `Agent` document and its optional Deployments, schedules, and GitHub triggers. The server reports each resource
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
        template_id: development
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

YAML, JSON and TOML encode the same document and use the same apply/delete
API. Files ending in `.toml` use TOML parsing; malformed TOML never falls back
to YAML. Other filenames use YAML/JSON parsing. TOML uses `[metadata]` and
`[spec]` tables, with `[[spec.deployments]]` and `[[spec.schedules]]` for children.
For an external Markdown prompt, replace `spec.system` with
`spec.system_file: prompt.md` in YAML, or `system_file = "prompt.md"` under
`[spec]` in TOML. CCP resolves the path relative to the manifest directory,
reads UTF-8 text verbatim, and sends it as `system`. It does not expand shell
variables. Apply and dry-run reject missing/unreadable files, invalid path
values, or both fields being present before contacting the API. The server
receives no `system_file` field. Manifest deletion strips the local reference
without reading the prompt, so it still works after the prompt file is gone.

Select a catalog skill with `spec.skills: [{skill_id: skill-id, version: 2}]`,
or package a local directory with `spec.skills: [{path: ./skills/news-writing}]`.
In TOML use `[[spec.skills]]` followed by `path = "./skills/news-writing"`.
The directory is relative to the manifest and must contain `SKILL.md` with
`name` and `description` YAML frontmatter, plus instructions. Supporting files
are included with their executable flags; no files run during packaging. Paths
must remain inside the manifest directory with no symlinks. Each bundle allows
128 files and 8 MiB; all bundles together allow 16 MiB. Python caches and `.git`
are excluded. Do not combine `path` with a catalog pin in one entry.

`ccp apply -f agent.yaml --org-id <org> --dry-run --json` reports planned skill
IDs, immutable versions and content digests without writing. Apply previews
bundles, checks expected versions and saves skills and agent pins atomically.
An unchanged reapply reuses its revision; changed or removed files produce a
new snapshot. Concurrent edits reject the apply; preview and retry. `--json`
returns the complete machine-readable apply receipt. Omission preserves pins;
`skills: []` detaches them. Deletion needs no local skill files and retains
immutable revisions for other agents. Skills grant no tools or credentials.

Archived agents still appear in `list` and `get`, flagged with an
`archived` marker (and timestamp in `get`) — check for it before using an
agent from a listing. API errors include the server's `request_id`; quote
it when reporting a failure.

## Headless use

`apply`, manifest `delete`, and `list` accept `--org-id` (or `CCP_ORG_ID`) to skip the
interactive organization picker. `get` and `versions` need no org context —
they address the agent by ID directly; an unknown or inaccessible (cross-org)
ID returns the server's 404.

## Endpoint

Commands talk to the managed-agents service, derived from `CCP_API_URL`
(production: `https://agents.clusterbase.dev`). `CCP_AGENTS_API_URL`
overrides the derivation for bespoke clusters.

### GitHub event triggers

Declare `spec.triggers` alongside deployments. CCP forwards the declarations to
Agents and prints per-trigger create/update/unchanged/delete receipts; `--json`
preserves the same receipts. Example declaration:

```yaml
triggers:
  - name: repo-merged
    repo: owner/repo
    events: [pull_request.merged]
    deployment: merge-review
    enabled: false
    kickoff_template: "Describe {{repo}} PR {{pr}}. Do not publish."
```

Names and deployment references are lowercase DNS labels. The referenced
Deployment must belong to this applied Agent. Events may be
`pull_request.opened`, `pull_request.ready_for_review`, or `pull_request.merged`.
GitHub repository access is resolved from the caller's authorization, including
for disabled declarations. Do not put installation IDs or credentials in YAML.
The deployment supplies environment/vaults; an omitted kickoff template uses the
neutral event kickoff, not the deployment kickoff. Enabled defaults to true;
keep source inventories explicitly disabled until activation is requested.

Omitting triggers preserves them; `triggers: []` removes only this Agent's
apply-owned subscriptions. Only their execution owner may reconcile them.
Dry-run writes nothing, reapply is idempotent, and a still-referenced deployment
cannot be removed. Remove/rebind its triggers in the same manifest. Applied
triggers cannot be changed through imperative trigger PATCH/DELETE routes.
