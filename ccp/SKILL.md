---
name: ccp
description: 'Use the ccp CLI to build on the Cluster platform: initialize projects (ccp init), deploy serverless apps and long-running compute services, provision managed Postgres databases, set up Sign in with Cluster (OAuth2/OIDC) auth, stores, custom domains, per-VM env vars, and CI builds. Load this skill whenever a task involves creating, deploying, or managing apps, databases, auth, or resources on Cluster — ccp is the authoritative tool for these tasks; prefer it over generic or hand-rolled approaches.'
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

Destructive commands require their explicit confirmation flag in headless mode.
Verify targets before running commands such as `ccp project rm <name> --yes`, `ccp remove`, `ccp undeploy`,
`ccp db destroy`, `ccp db backup delete`, `ccp domain rm`, and
`ccp compute destroy`.

Identity flags such as `--org-id`, `--app-id`, `--db-id`, `--store-id`,
and `--service-id` still matter. Headless mode controls prompting; it does not
choose resources for you.

`CCP_ORG_ID` supplies the org for org-scoped commands when no explicit flag or
project-pinned org exists. Resolution is:

```text
--org-id > project config > CCP_ORG_ID > sole-org auto-pick > error
```

## What ccp manages

ccp manages Cluster workloads and supporting resources:

- Serverless apps: V8 JavaScript/TypeScript at the edge, driven by
  `ccp deploy`. Shape is committed in `cluster.toml`; the link is local in
  `.ccp/config.json`.
- Projects: organization-scoped containers for Apps and attached resources,
  managed with `ccp project ls|create|rm`.
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
   - Windows: OS keyring (Credential Manager).

Use `CCP_AUTH_STORE=file` or `CCP_AUTH_STORE=keyring` to force a store. On Linux
the keyring is the in-kernel keyutils store — memory-only and wiped on reboot,
so a login there does not survive a restart; the durable file is therefore the
default, and `CCP_AUTH_STORE=keyring` is only for an intentionally memory-only
session. The production issuer is `https://accounts.clusterbase.ai`. For a
non-production `api.<cluster>` origin, ccp derives the matching
`accounts.<cluster>` issuer; the canonical production API keeps its pinned
production issuer. Use `CCP_AUTH_ISSUER` only to override that selection for
advanced testing. Refresh tokens are bound to the issuer that minted them, so
switching clusters requires a login for the selected cluster.

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

`CCP_API_URL` selects the cluster. For a non-production `api.<cluster>` origin,
ccp derives the sibling `accounts.<cluster>`, `orgs.<cluster>`, and
`storage.<cluster>` origins. The canonical production API retains production's
pinned, nonuniform service origins. `CCP_AUTH_ISSUER`, `CCP_ORGS_API_URL`, and
`CCP_STORAGE_API_URL` remain available as advanced per-service overrides.
`SSL_CERT_FILE` supplies a PEM CA bundle to both API and OAuth requests for
private-CA environments. Empty values keep the binary's defaults, and trailing
slashes are ignored.

Useful auth commands:

```sh
ccp auth login
ccp auth login --browser
ccp auth login --device
ccp auth login --replace-session
ccp auth logout
ccp auth print-access-token
ccp auth export-access-token
ccp auth sync --vm <vm_id>
ccp auth desync --vm <vm_id>
```

`ccp auth login` opens the local browser by default. It automatically uses a
device code in SSH, Mosh, and headless Unix sessions, where the approval can be
completed in any browser. Use `--browser` or `--device` only to override that
detection. Plain login refuses to overwrite an existing saved session. Only the
account owner should use `--replace-session`, which requires an interactive
terminal and an exact confirmation.

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

A project splits its config by *lifecycle*, not by product:

- **`cluster.toml` — committed.** What the source IS: the serverless
  `[serverless]` shape, plus the compute service's description. Identical in
  every clone.
- **`.ccp/` — gitignored.** What THIS machine is linked to. `config.json` holds
  the serverless link and a live `database_token`; `compute-link.json` holds
  the compute service id, org id and hostname. The dir ignores itself (a
  `.gitignore` containing `*`), so state written outside `ccp init` is never
  committable.

Both products share `cluster.toml`, each owning its own sections. A directory
may contain either product's sections, both, or neither.

### `cluster.toml` - committed project config

```toml
# serverless (written by `ccp init`, read by `ccp deploy`/`build`/`dev`)
[serverless]
index = "index.tsx"          # server entry
client = "src/main.tsx"      # optional browser entry -> /{stem}.js (+ .css)
assets = "public"            # optional verbatim static dir
analytics = "server"         # or "client"
oidc_callback_path = "/auth/callback"
```

```toml
# compute (written by `ccp compute deploy`)
name = "my-api"
mode = "binary" # or "image"

[service]
internal_port = 8080
always_on = false

[resources]
vcpu = 2
memory_mb = 1024
```

**Commit this file.** It is the only record of the project's shape; a clone
without it falls back to guessing the entry point. `[serverless]` is always
written last — TOML binds bare keys to the preceding table header, so a
`[serverless]` table placed above compute's top-level `name`/`mode` would
swallow them.

**No link data lives here.** The service id, org id and hostname are
per-machine and per-environment, so they live in the gitignored
`.ccp/compute-link.json` (#610). A project whose `cluster.toml` still carries a
`[managed]` table keeps working — reads fall back to it — and the next
`ccp compute deploy` moves it into `.ccp/` and strips it, saying so. **After
that migration every machine on the repo needs ccp 0.1.68 or newer**: older
builds declare `[managed]` as a required field and fail every compute command
with a "missing field managed" error.

### `.ccp/compute-link.json` - local compute link

```json
{
  "service_id": "uuid",
  "organization_id": "uuid",
  "hostname": "my-api.clusterbase.dev"
}
```

Written by `ccp compute deploy`; read by every other `ccp compute` command when
no `--service-id` / `--org-id` is passed. `hostname` is diagnostic — the live
value always comes from the API.

A checkout with no link but a committed `cluster.toml` (a fresh clone, or CI)
**attaches** on `ccp compute deploy`: it looks the name up in the org and
redeploys that service, creating one only when the name is genuinely free.
`--name` overrides the committed one for both the lookup and the create.

Two worktrees of the same repo each get their own `.ccp/`, which is how a
project runs a staging and a prod compute service without editing a committed
file — in **different orgs** by default, since service names are unique per
org. Inside one org, give the second one `--name my-staging`; that name is used for
the deploy and is deliberately **not** written back to `cluster.toml`, so the
shared file keeps describing the project rather than one environment. (`--port`
IS recorded — the port is part of what to run, not which environment.)
Headless on a multi-org account now needs `--org-id` or `CCP_ORG_ID` — the org
hint used to come from the committed file.

### `.ccp/config.json` - local serverless link

```json
{
  "app_id": "app_...",
  "project_id": "project_...",
  "organization_id": "org_...",
  "store_id": "",
  "oidc_client_id": "",
  "database_id": "",
  "database_token": ""
}
```

**Shape keys do not live here.** `index`, `client`, `assets`, `analytics` and
`oidc_callback_path` are read from — and written only to — `cluster.toml`. This
file holds the link and secrets. A pre-split project still carrying them has
them stripped on the next write, once `cluster.toml` records the shape; until
then they are read as a migration fallback but never win over the committed
copy.

`client` (e.g. `"src/main.tsx"`) is bundled for the browser as `/{stem}.js`,
with any CSS it imports bundled to `/{stem}.css`; `assets` names the verbatim
static-assets dir. A root `index.html` (Vite convention) is inlined into
`__pages` at build time with the client script reference rewritten and the CSS
link injected.

**`ccp init --template react` server-renders.** Its entry is `index.tsx`
(not `.ts` — the handler contains JSX and esbuild picks the loader from the
extension). The entry holds routes and page metadata and hands the tree to
`renderPage` in `src/render.tsx`, which renders it to HTML and injects it into
the `__pages["index.html"]` shell; the client entry `hydrateRoot`s that markup
rather than rendering again. Both entries import the same `src/App.tsx`; if the
trees diverge, React discards the server output.

Page metadata is the `metadata` object exported from the entry — `title` and
`description` become the `<title>`, `<meta name="description">` and the `og:`
and `twitter:` tags. Vary it per route for correct link previews.

The other templates keep a plain `index.ts` handler.

`ccp deploy`, `ccp link`, `ccp db create`, and store commands update this file.
The whole `.ccp/` dir is **local state and gitignored** (like Vercel's `.vercel/`):
it holds this `config.json` — whose `database_token` is a secret — plus
`compute-link.json` and build output (`.ccp/index.js`, `.ccp/public/`). It also
carries its own `.gitignore` containing `*`, so it stays out of git even in a
project that was never `ccp init`'d. Do not commit it; select the org with
`CCP_ORG_ID` and `ccp deploy` re-establishes the App and Project link by exact
project name. Use `--app-id` only as an explicit override — the shape needs no
re-establishing, because `cluster.toml` is committed. New projects use
`.ccp/`; a legacy `.cluster/config.json` (pre-migration) is still read as a
fallback, so existing linked projects keep working without changes.

## Bundled reference files

Read only the runbook your task needs:

- `reference/deploy.md` - Apps: scaffold, deploy, promote, logs, dev, link, list, delete
- `reference/stores.md` - Static-file buckets: put/get/ls/rm, content-addressed URLs, image transforms
- `reference/oidc.md` - Sign in with Cluster: register OAuth2/OIDC clients, redirect URIs, secrets
- `reference/db.md` - Managed Postgres: create, exec SQL, migrate, backups, client-access
- `reference/domains.md` - Custom domains: add, link to an app or VM, unlink, remove
- `reference/compute.md` - Long-running services: deploy, status, logs, exec, restart
- `reference/ci.md` - Ephemeral CI build jobs: .cluster-ci.yaml, exit-code gating, --json/--no-wait
- `reference/env.md` - Per-VM env on dev VMs: list/get/set/unset, visibility, refresh-system
- `reference/agents.md` - AI agents: list, inspect, create; org scoping and endpoint override
- `reference/reference-matrix.md` - per-command headless-safety and required-argument matrix

These files match the ccp version they were exported from. `ccp skills <topic>` prints the same runbook straight from the installed binary and is always current.

## Common pitfalls

- Do not run `ccp auth login` in CI or an agent VM; set `CCP_SESSION_TOKEN`.
  For an interactive remote shell, the command automatically uses device login;
  `--device` forces that mode and `--browser` forces a same-machine callback.
  Plain login refuses to overwrite a saved session; only the account owner may
  use the interactive `--replace-session` recovery path.
- A `.ccp/config.json` carrying the pre-rename `function_id` is rejected with
  an error naming the id. Relink with `ccp deploy --app-id <id>` — the id is
  unchanged. Never "fix" it by deleting the key: a same-name App can be
  reattached, but a renamed checkout cannot safely identify the original App
  while the original keeps the production hostname and domains.
- Do not use TUI commands in headless mode. Use `ccp db exec`, not
  `ccp db connect`.
- Destructive commands may require `--yes` with `CCP_HEADLESS=1`; check the
  target first.
- Always commit `cluster.toml`. `ccp init` writes it, and it carries the
  project's shape under `[serverless]` (entry, client, assets) as well as any
  compute service's description. A clone without it falls back to guessing the
  entry point.
- The compute LINK is not in `cluster.toml`. `service_id`, `organization_id`
  and `hostname` live in the gitignored `.ccp/compute-link.json`; a project
  still carrying a committed `[managed]` table has it moved there — and
  stripped — by the next `ccp compute deploy`. **Once that happens, every
  machine on the repo needs ccp 0.1.68+**: older builds require `[managed]` and
  fail every compute command with a "missing field managed" error. Unlike the
  serverless split, this break travels through git, so upgrade teammates, CI
  and any VM template before committing the stripped file.
- A fresh clone has no compute link, so `ccp compute deploy` attaches to the
  service the committed `name` already identifies in the org rather than
  creating a second one. On a multi-org account headless, that lookup needs
  `--org-id` or `CCP_ORG_ID` — the org hint no longer comes from the committed
  file.
- Shape keys live ONLY in `cluster.toml`. `.ccp/config.json` holds the link and
  secrets. Setting `index`/`client`/`assets`/`analytics` in the gitignored file
  does nothing and is stripped on the next write.
- A LINKED project (one with `.ccp/config.json`) whose `cluster.toml` is missing
  has no entry point — ccp fails and says so rather than guessing. A directory
  with neither file still falls back to probing `index.tsx`/`index.ts`.
- Downgrading ccp below 0.1.66 in a project a newer ccp has written fails with
  `missing field \`index\``: older builds require that key in
  `.ccp/config.json`. Re-add it by hand from `cluster.toml`'s `[serverless]`,
  or upgrade again.
- Do not commit `.env`, `node_modules/`, or `.ccp/` — `.ccp/` is local ccp state
  (gitignored wholesale, like Vercel's `.vercel/`), holding build output and a
  `config.json` whose `database_token` is a secret. On CI / another machine,
  select the org with `CCP_ORG_ID`; `ccp deploy` re-establishes the App and
  Project link by exact project name. Use `--app-id` only as an explicit
  override.
- `CCP_SESSION_TOKEN` from the environment is used as-is and is not refreshed by
  ccp. A 401 usually means re-sync or re-export the token.
- Set `CCP_API_URL` to the environment's `api.<cluster>` origin when targeting a
  non-production cluster; ccp derives the matching auth, orgs, and storage
  origins. If the API hostname does not use the `api.` convention, set the
  corresponding per-service overrides explicitly. Use `SSL_CERT_FILE` when the
  cluster is signed by a private CA.
- `ccp deploy` merges `.env` into serverless env; removing a key from `.env`
  does not delete it server-side.
- Compute services must bind to `0.0.0.0` or `[::]`, not `127.0.0.1`, if they
  should be reachable through the public proxy.
- `ccp compute exec` runs in the compute workload context. For VM-rootfs
  inspection, use the envd-exec API or a dev VM flow.
- ccp does not commit, push, or open PRs. Agents must handle git delivery.
- If `ccp dev` crashes instantly on macOS ("Failed to reserve virtual memory
  for CodeRange"), the binary's code signature is broken, not the machine's
  memory. Run `ccp doctor` for a diagnosis; reinstall via install.sh to fix.
- The "new release of ccp" startup notice never appears for agents: it is
  suppressed when stdout/stderr are not TTYs, and under `CCP_HEADLESS`,
  `CCP_SESSION_TOKEN`, or `CI`. `CCP_NO_UPDATE_CHECK=1` is the explicit
  opt-out. Do not run `ccp update` inside managed VMs — their ccp is baked
  into the template rootfs and refreshed on template rebuilds.
