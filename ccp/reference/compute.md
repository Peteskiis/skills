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
immutable in v1; destroy and recreate to switch image vs binary.

Binary runtimes are `auto`, `alpine`, and `debian`. Resolution precedence is
`--runtime` → `[binary].runtime` → `auto`. `auto` routes static/musl ELFs to
Alpine and glibc ELFs to Debian; explicit incompatible combinations fail before
upload. The successful deploy writes the concrete runtime to
`[binary].runtime`. Runtime is immutable for an existing service, so changing
between Alpine and Debian also requires destroy/recreate.

A checkout with a `cluster.toml` but no link — a fresh clone, or CI — attaches
on deploy: ccp looks the name up in the org and redeploys that service, and
only creates one when the name is free (confirmed interactively, auto-yes with
`-y`). `--name` overrides the committed name for that deploy and is **not**
written back, so it stays per-environment; `--port` is recorded, because the
port is part of what to run rather than which environment this is. Headless on a multi-org
account this needs `--org-id` or `CCP_ORG_ID`, since the org hint is no longer
committed.

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

`compute destroy` tears down the service, VM, and route, then removes compute's
keys from `cluster.toml` and deletes `.ccp/compute-link.json` — but only when
the destroyed service is the one this directory is linked to, so destroying
some other service from inside a project no longer wipes that project's config.
It auto-confirms in headless mode.

### Health probes

`[health]` in `cluster.toml` opts into HTTP readiness checks. Without it, deploy
only checks that the service is listening on the configured TCP port.

### Custom domains

Use the VM ID from `ccp compute status`:

```sh
ccp domain link example.com --vm "<vm_id>:<port>"
```
