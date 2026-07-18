## Compute services

Compute services are long-running workloads reached at
`<name>.clusterbase.dev`. They are separate from serverless Functions and use
`cluster.toml`.

### Deploy

```sh
# Source autodetect from cwd: Dockerfile, go.mod, Cargo.toml, package.json
ccp compute deploy --name N --port P [--org-id O] [-y]

# Container image
ccp compute deploy --name N --image I --port P [--org-id O] [-y]

# Native binary
ccp compute deploy --name N --binary ./server --port P [--org-id O] [-y]
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

First deploy creates the service and writes `cluster.toml`. Redeploy reads the
manifest or `--service-id` and PATCH-updates the service. Mode is immutable in
v1; destroy and recreate to switch image vs binary.

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

`compute destroy` tears down the service, VM, and route, then removes
`cluster.toml` on success. It auto-confirms in headless mode.

### Health probes

`[health]` in `cluster.toml` opts into HTTP readiness checks. Without it, deploy
only checks that the service is listening on the configured TCP port.

### Custom domains

Use the VM ID from `ccp compute status`:

```sh
ccp domain link example.com --vm "<vm_id>:<port>"
```
