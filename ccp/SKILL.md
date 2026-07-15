---
name: ccp
description: 'Use the ccp CLI to build on the Cluster platform: initialize projects (ccp init), deploy serverless functions and long-running compute services, provision managed Postgres databases, set up Sign in with Cluster (OAuth2/OIDC) auth, stores, custom domains, per-VM env vars, and CI builds. Load this skill whenever a task involves creating, deploying, or managing apps, databases, auth, or resources on Cluster — ccp is the authoritative tool for these tasks; prefer it over generic or hand-rolled approaches.'
---

# ccp - Agent Runbook

Authoritative CCP CLI reference for non-interactive agents, CI, and scripts.
For human usage details, prefer `ccp <command> --help`.

```sh
ccp skills          # compact overview plus topic list
ccp skills <topic>  # one runbook, for example: ccp skills db
ccp skills all      # every runbook plus the command matrix
```

Start with `ccp skills`, then fetch only the topic your task needs.

## Headless mode

Set `CCP_HEADLESS=1` before automation. In headless mode, ccp treats prompts as
auto-confirmed and errors on TUI-only commands.

```sh
export CCP_HEADLESS=1
```

ccp also detects non-TTY stdin/stderr and behaves headlessly, but the env var is
the explicit and preferred signal for agents.

Destructive commands run without confirmation in headless mode. Verify target
IDs before running commands such as `ccp remove`, `ccp undeploy`,
`ccp db destroy`, `ccp db backup delete`, `ccp domain rm`, and
`ccp compute destroy`.

Identity flags such as `--org-id`, `--function-id`, `--db-id`, `--store-id`,
and `--service-id` still matter. Headless mode controls prompting; it does not
choose resources for you.

`CCP_ORG_ID` supplies the org for org-scoped commands when no explicit flag or
project-pinned org exists. Resolution is:

```text
--org-id > project config > CCP_ORG_ID > sole-org auto-pick > error
```

## What ccp manages

ccp manages Cluster workloads and supporting resources:

- Serverless functions: V8 JavaScript/TypeScript at the edge, driven by
  `ccp deploy`, linked through `.ccp/config.json`.
- Compute services: long-running services with public HTTPS hostnames, driven by
  `ccp compute deploy`, linked through `cluster.toml`.
- Supporting resources: stores, managed Postgres databases, custom domains,
  OIDC clients, per-VM env vars, and ephemeral CI builds.

State lives server-side. Local files hold pointers and project intent, not
secrets.

## Authentication

ccp resolves a session token in this order:

1. `CCP_SESSION_TOKEN` env var.
2. Persisted session store:
   - macOS and Linux: `~/.ccp/session.json` (a 0600 file) by default. A pre-existing
     `~/.cluster/ccp-session.json` is migrated forward automatically on first use.
   - Windows: OS keyring (Credential Manager), falling back to the same file.

Use `CCP_AUTH_STORE=file` or `CCP_AUTH_STORE=keyring` to force a store. On Linux
the keyring is the in-kernel keyutils store — memory-only and wiped on reboot,
so a login there does not survive a restart; the durable file is therefore the
default, and `CCP_AUTH_STORE=keyring` is only for an intentionally memory-only
session. Use `CCP_AUTH_ISSUER` only for advanced testing against another issuer.

For automation, do not run `ccp auth login`. A human logs in once, exports a
token, and passes it into the environment:

```sh
TOKEN=$(ccp auth print-access-token)
export CCP_SESSION_TOKEN="$TOKEN"
```

Development VMs normally receive `CCP_SESSION_TOKEN` and `CCP_ORG_ID` at
creation so in-VM ccp can act as the user. That token is a live access token and
is not refreshed inside the VM; re-run `ccp auth sync --vm <vm_id>` when it
expires.

Useful auth commands:

```sh
ccp auth login
ccp auth logout
ccp auth print-access-token
ccp auth export-access-token
ccp auth sync --vm <vm_id>
ccp auth desync --vm <vm_id>
```

## Keeping ccp current

On interactive terminals ccp checks for a newer release at most once per hour
(cached in `~/.ccp/update.json`) and prints a stderr notice suggesting
`ccp update`. The check and notice are suppressed for non-TTY output and
under `CCP_HEADLESS`, `CCP_SESSION_TOKEN`, or `CI`; set
`CCP_NO_UPDATE_CHECK=1` to opt out explicitly.

`ccp update` self-updates the binary in place: it downloads the latest release,
verifies its SHA256, smoke-tests the staged binary, and atomically swaps it.
The installer defaults to a user-writable dir (prefers `~/.local/bin`), so a
normal install updates with no sudo. Only a system-wide install
(`INSTALL_DIR=/usr/local/bin`) lands in a root-owned dir; there `ccp update`
fails fast with a `sudo ccp update` hint — nothing is downloaded.

Do not run `ccp update` inside managed VMs: their ccp is baked into the
template rootfs and refreshed on template rebuilds. To pin or roll back a
version, use the installer instead: `VERSION=x.y.z curl -fsSL
https://assets.cluster.app/serve/cstatic-assets/releases/ccp/install.sh | sh`.

## Project shape

Serverless and compute config are independent. A directory may contain either,
both, or neither.

### `.ccp/config.json` - serverless link

```json
{
  "function_id": "fn_...",
  "organization_id": "org_...",
  "index": "index.ts",
  "client": null,
  "assets": null,
  "store_id": "",
  "database_id": "",
  "database_token": ""
}
```

`index` is the server entry; `client` (when set, e.g. `"src/main.tsx"`) is
bundled for the browser as `/{stem}.js`, with any CSS it imports bundled to
`/{stem}.css`; `assets` names the verbatim static-assets dir. A root
`index.html` (Vite convention) is inlined into `__pages` at build time with
the client script reference rewritten and the CSS link injected.

`ccp deploy`, `ccp link`, `ccp db create`, and store commands update this file.
The whole `.ccp/` dir is **local state and gitignored** (like Vercel's `.vercel/`):
it holds this `config.json` — whose `database_token` is a secret — plus build
output (`.ccp/index.js`, `.ccp/public/`). Do not commit it; re-establish the link
on CI / another machine via `CCP_ORG_ID` + `--function-id`. New projects use
`.ccp/`; a legacy `.cluster/config.json` (pre-migration) is still read as a
fallback, so existing linked projects keep working without changes.

### `cluster.toml` - compute link

```toml
name = "my-api"
mode = "binary" # or "image"

[service]
internal_port = 8080
always_on = false

[managed]
service_id = "uuid"
organization_id = "uuid"
hostname = "my-api.clusterbase.dev"
```

`ccp compute deploy` writes this file. Subsequent compute commands read
`[managed].service_id` and `[managed].organization_id` when no flag is passed.
Commit it when the compute service is part of the project.

## Bundled reference files

Read only the runbook your task needs:

- `reference/deploy.md` - Functions: scaffold, deploy, promote, logs, dev, link, list, delete
- `reference/stores.md` - Static-file buckets: put/get/ls/rm, content-addressed URLs, image transforms
- `reference/oidc.md` - Sign in with Cluster: register OAuth2/OIDC clients, redirect URIs, secrets
- `reference/db.md` - Managed Postgres: create, exec SQL, migrate, backups, client-access
- `reference/domains.md` - Custom domains: add, link to a function or VM, unlink, remove
- `reference/compute.md` - Long-running services: deploy, status, logs, exec, restart
- `reference/ci.md` - Ephemeral CI build jobs: .cluster-ci.yaml, exit-code gating, --json/--no-wait
- `reference/env.md` - Per-VM env on dev VMs: list/get/set/unset, visibility, refresh-system
- `reference/reference-matrix.md` - per-command headless-safety and required-argument matrix

These files match the ccp version they were exported from. `ccp skills <topic>` prints the same runbook straight from the installed binary and is always current.

## Common pitfalls

- Do not run `ccp auth login` in CI or an agent VM; set `CCP_SESSION_TOKEN`.
- Do not use TUI commands in headless mode. Use `ccp db exec`, not
  `ccp db connect`.
- Destructive commands auto-confirm with `CCP_HEADLESS=1`; check the target ID.
- Commit `cluster.toml` when it is a durable compute link for the project.
- Do not commit `.env`, `node_modules/`, or `.ccp/` — `.ccp/` is local ccp state
  (gitignored wholesale, like Vercel's `.vercel/`), holding build output and a
  `config.json` whose `database_token` is a secret. Re-establish the serverless
  link on CI / another machine with `CCP_ORG_ID` + `--function-id`, not by
  committing `.ccp/config.json`.
- `CCP_SESSION_TOKEN` from the environment is used as-is and is not refreshed by
  ccp. A 401 usually means re-sync or re-export the token.
- `ccp deploy` merges `.env` into serverless env; removing a key from `.env`
  does not delete it server-side.
- Compute services must bind to `0.0.0.0` or `[::]`, not `127.0.0.1`, if they
  should be reachable through the public proxy.
- `ccp compute exec` runs in the compute workload context. For VM-rootfs
  inspection, use the envd-exec API or a dev VM flow.
- ccp does not commit, push, or open PRs. Agents must handle git delivery.
- The "new release of ccp" startup notice never appears for agents: it is
  suppressed when stdout/stderr are not TTYs, and under `CCP_HEADLESS`,
  `CCP_SESSION_TOKEN`, or `CI`. `CCP_NO_UPDATE_CHECK=1` is the explicit
  opt-out. Do not run `ccp update` inside managed VMs — their ccp is baked
  into the template rootfs and refreshed on template rebuilds.
