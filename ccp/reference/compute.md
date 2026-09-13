## Compute services

Compute services are long-running workloads reached at
`<name>.clusterbase.dev`. They are separate from serverless Apps and use
`cluster.toml`.

### Deploy

```sh
# Source autodetect from cwd: Dockerfile, go.mod, Cargo.toml, package.json
ccp compute deploy --name N --port P [--org-id O] [-y]

# Container image
ccp compute deploy --name N --image I --port P [--org-id O] [-y]

# Native binary; auto selects Alpine for musl/static and Debian for glibc
ccp compute deploy --name N --binary ./server --runtime auto --port P [--org-id O] [-y]

# Optional published VM shape (flags must be paired)
ccp compute deploy --name N --port P --vcpu 2 --memory-mb 1024
```

`--image` and `--binary` are mutually exclusive. With no mode flag, source
autodetect currently builds Go and Rust projects through the binary path.
Dockerfile and package.json detection bail with a clear unsupported message.

Source-mode builds shell out to a host toolchain: Go projects need `go`; Rust
projects need `cargo` + the `x86_64-unknown-linux-musl` target (plus, on macOS,
the `x86_64-linux-musl-gcc` cross-linker from
`brew install FiloSottile/musl-cross/musl-cross`). Run `ccp doctor` to see which
of these are installed and how to install any that are missing (`--binary` with
a pre-built static Linux ELF, or `--image`, skips the local toolchain entirely).

Native binaries must be non-empty and no larger than 256 MiB. ccp records the
size and SHA-256 during upload; each deploy or restart gives the VM a fresh
short-lived download capability, and the guest installs the file only after
both values match. A failed download or verification leaves the prior
executable in place and returns a typed `binary_download_*`/`invalid_binary`
error rather than starting partial bytes.

First deploy creates the service, writes the description to `cluster.toml`
(commit it) and this machine's link to `.ccp/compute-link.json` (gitignored).
Redeploy reads the link or `--service-id` and PATCH-updates the service. Mode is
immutable; edit the manifest and use `ccp compute deploy` to switch modes.

Binary paths are resolved against the project directory for reading and
uploading, but remain portable in `cluster.toml`: relative spellings such as
`./server` are preserved, an absolute path inside the project is recorded as
`./…`, and an absolute path outside the project remains absolute to make its
machine-local nature explicit. Redeploy does not rewrite `[binary].path`.

Binary runtimes are `auto`, `alpine`, and `debian`. Resolution precedence is
`--runtime` → `[binary].runtime` → `auto`. `auto` routes static/musl ELFs to
Alpine and glibc ELFs to Debian; explicit incompatible combinations fail before
upload. The successful deploy writes the concrete runtime to
`[binary].runtime`. Runtime is immutable for an existing service, so changing
between Alpine and Debian requires `ccp compute deploy`.

Compute resources may be omitted to use the runtime default, or selected with
paired `--vcpu` and `--memory-mb` flags / a `[resources]` manifest block. The
published shapes are `1/256`, `1/512`, `2/1024`, `4/2048`, and `4/4096`
(vCPU/MiB). Resources are immutable after creation; edit `[resources]` and run
`ccp compute deploy` to change shape. `compute list` and `compute status` show the persisted shape.

### Replace immutable configuration

Ordinary deploy detects immutable changes automatically and asks before replacing.
Mutable changes continue to redeploy the existing service.

```sh
# After editing cluster.toml, review the plan and confirm interactively
ccp compute deploy

# Explicit consent for automation; non-interactive replacement requires -y or --yes
ccp compute deploy -y # --yes is equivalent
```

Replacement requires this project's existing local link and a valid compute
`cluster.toml`. It reads the manifest and `.env`; put overrides in those files
before replacing. Source/name/resource/env overrides must be moved into those files when
replacement is needed. An explicit `--service-id` must match the local link. An optional `--org-id` must match the linked service.
The plan names changed immutable fields and shows existing/requested resources.

CCP prepares and uploads binaries before deleting the old service. Replacement
then deletes the old guest and creates a new service: expect an interruption,
loss of the old guest filesystem and deployment history, and new service/VM IDs.
The existing service name and built-in public hostname are preserved, including
a per-environment name previously set with `--name`. Custom domains targeting
the old VM must be rebound. The committed manifest is preserved byte-for-byte.
If `[resources]` is omitted, replacement retains the existing resource shape.

The original local link remains until the API accepts the replacement. A local,
context-scoped recovery record stores only the original identity, endpoint and
resource shape. If deletion or creation fails, fix the reported cause and retry
`ccp compute deploy --yes` in the same project/context. Keep
`cluster.toml`, `.env`, the link and the recovery record while recovering.
Deploy resumes any unfinished replacement. A retry first looks
for an already accepted service under the original name; it can recover the
link after a lost response without deleting that service or creating a duplicate.
Use `ccp compute status` to inspect a recovered service's readiness. A failed
server-side image pull or capacity check after deletion means the old guest is
already gone; retry can recreate it, but cannot restore its disk contents.

### Private networking

An always-on service may join an organization-scoped private network by adding
the following block to `cluster.toml`:

```toml
[service]
internal_port = 8080
always_on = true

[network]
name = "backend"
```

The network is created automatically on first deploy. Members can reach one
another across VM nodes at `<service>.backend.internal`; services outside the
network cannot resolve or connect to that private address. Network and service
names must be lowercase DNS labels. Private networking currently requires
`always_on = true`, is immutable for an existing service, and does not change
its public `<name>.clusterbase.dev` route.

A checkout with a `cluster.toml` but no link — a fresh clone, or CI — attaches
on deploy: ccp looks the name up in the org and redeploys that service, and
only creates one when the name is free (confirmed interactively, auto-yes with
`-y`). `--name` overrides the committed name for that deploy and is **not**
written back, so it stays per-environment; `--port` is recorded, because the
port is part of what to run rather than which environment this is. Headless on a multi-org
account this uses a saved default, `--org-id`, or `CCP_ORG_ID`; organization
identity is not committed.

**A redeploy needs a `cluster.toml` that describes the service.** With a link
but no committed description — the file deleted, on a branch without it, or
`--service-id` in a bare directory — `env`, `[binary].args` and `[health]` have
no source of truth here, and the API applies them as full mirrors (a missing
key clears the value server-side). So ccp refuses rather than guessing, and
tells you to pass `--image`/`--binary` (which change only the source) or to run
`ccp compute restart`. `--env` on its own is refused for the same reason: it is
one layer of the `.env` < `[env]` < `--env` merge, not a standalone edit.

Bind the app to `0.0.0.0` or `[::]`, not `127.0.0.1`. The public proxy runs
outside the VM network namespace and cannot reach loopback-only listeners.

Env merge order for deploy is:

```text
.env < cluster.toml [env] < --env KEY=VALUE
```

Removing a key from all three sources clears it server-side on the next deploy.

### Manage

```sh
ccp compute list [--org-id O]       # alias: ls
ccp compute status [SERVICE_ID]
ccp compute logs [SERVICE_ID] [-n TAIL]
ccp compute exec [SERVICE_ID] [--timeout-ms MS] -- <CMD> [ARGS...]
ccp compute restart [SERVICE_ID]
ccp compute destroy [SERVICE_ID|NAME] [-y]
```

`exec` requires a literal `--` before the command so clap stops parsing ccp
flags.

Auto-pause is transparent for deploy, logs, exec, restart, and status paths that
need the VM awake. `--always-on` only applies at first deploy.
A VM previously paused by Billing performs a fresh admission check on the next
wake attempt. If the account is now eligible, the operation resumes normally;
otherwise it remains paused and returns `payment_required` (HTTP 402).
Workload operations return `service_not_running` while initial deployment is
still pending; wait for deployment to finish before retrying.

`compute destroy` tears down the service, VM, and route, then deletes only the
local `.ccp/compute-link.json` deployment identity. It preserves `cluster.toml`
unchanged so `ccp compute deploy --yes` can recreate the service from the same
committed description. Local cleanup runs only when the destroyed service is
the one this directory is linked to. It auto-confirms in headless mode.

### Health probes

`[health]` in `cluster.toml` opts into HTTP readiness checks. Without it, deploy
only checks that the service is listening on the configured TCP port.

### Custom domains

Use the VM ID from `ccp compute status`:

```sh
ccp domain link example.com --vm "<vm_id>:<port>"
```


Service lookup accepts an explicit UUID without reading project state. Names
resolve within the selected organization; otherwise the local compute link is
used before an interactive picker. A malformed compute link fails loudly,
including on `ccp compute ls`; fix the link or supply the organization explicitly
instead of relying on an ambient organization to hide invalid state.
