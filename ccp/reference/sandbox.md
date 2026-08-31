# Sandboxes

Apply a versioned, organization-scoped reusable Sandbox template:

```sh
ccp apply -f sandbox.yaml --org-id "$CCP_ORG_ID"
```

Infra reconciles the stable template identity and admits one immutable build
for its exact recipe. Reapplying an unchanged manifest reuses the same template
and ready or in-progress build. Use `--dry-run` to plan the same reconciliation
without writing a template or build.

## Manifest

```yaml
apiVersion: sandboxes.clusterbase.ai/v1
kind: SandboxTemplate
metadata:
  name: python-tools
spec:
  base: ubuntu
  resources:
    vcpu: 2
    memory_mb: 1024
  packages:
    apt: [jq]
    pip: [cowsay==6.1]
  ports:
    - name: cdp
      port: 9222
      protocol: websocket
  steps:
    - run: touch /workspace/ready
```

`metadata.name` is the stable organization-scoped template identity. Resources
are required as one supported `vcpu` and `memory_mb` pair. `base` is exactly one
of `ubuntu`, `debian`, or `alpine`; Infra resolves it to a committed immutable
system build. Ubuntu supports `apt`, `pip`, `npm`, `cargo`, `gem`, and `go`
package lists, Debian supports `apt`, and Alpine supports `apk`. Incompatible
package managers are rejected before build admission. Changing the base,
resources, packages, ports, or run step admits a new immutable build; existing
builds are never mutated.

Named ports are private immutable metadata. A declaration has a unique DNS-label
name, a unique guest port, and a protocol of `http` or `websocket`; at most eight
may be declared. The template's boot setup must start the service and bind it to
the guest interface. A running Sandbox publishes declared ports behind
authenticated HTTPS or WSS routes. Raw VM addresses and arbitrary undeclared
ports remain private.

Create short-lived access to one declared service:

```sh
ccp sandbox connect sbx_... cdp --ttl 5m
ccp sandbox connect sbx_... cdp --ttl 5m --json
```

The response keeps the endpoint and opaque bearer token separate. HTTPS and
WebSocket clients attach `Authorization: Bearer <token>` to the request or
Upgrade; the token is scoped to that Sandbox and service for at most one hour
and never beyond the Sandbox TTL. `--json` is the stable automation contract
with `endpoint`, `token`, and `expires_at` fields; the token is never embedded
in the URL.

The graphical Ubuntu desktop is a native system template. Managed products
create it with the stable `desktop` system identity; it does not require an
organization-owned manifest or custom build.

Once a desktop Sandbox exists, open its read-only noVNC view without copying a
bearer into a browser URL:

```sh
ccp sandbox desktop sbx_... --ttl 20m
```

The command opens a token-free `127.0.0.1` URL and remains in the foreground.
The guest VNC server enforces view-only access; browser settings cannot enable
pointer, keyboard, or clipboard input on this transport.
It injects the scoped `desktop` service bearer into upstream HTTPS and WSS
requests, rejects cross-origin browser access, and closes on Ctrl-C or access
expiry. Raw VNC is not published; it remains loopback-only inside the guest.
Use `ccp sandbox connect` for non-browser automation that can set an
`Authorization` header itself.

The separate `desktop-control` transport cannot be opened with `ccp sandbox
connect` or `ccp sandbox desktop`. Its guest services are stopped by default.
An organization member or an authenticated trusted service may acquire the
current lease with `POST /api/v1/sandboxes/{sandbox_id}/desktop-control`.
The request supplies a fresh `sbxcl_<uuid>` lease ID, a fresh 256-bit
`sbxt_<base64url>` bearer, and `ttl_seconds` from 10 through 900. A successful
response returns that lease ID, its monotonically increasing `fence`, the WSS
`endpoint`, the bearer, and `expires_at` with `Cache-Control: no-store`.
Infra persists only the bearer digest; callers must retain the returned
capability while they hold control.

Renewal uses `PATCH` on the same path with `lease_id`, `fence`, and a new
`ttl_seconds`; release uses `DELETE` with `lease_id` and `fence`. A stale lease
or fence cannot renew or release its replacement. While the lease is active,
AgentGateway and envd both reject model `ComputerAct` input. Release, expiry,
or Sandbox deletion revokes authorization, closes existing control WebSockets,
stops the guest control services, and invalidates the model's current frame, so
automation must obtain a fresh observation before acting again. CCP's desktop
command remains view-only throughout.

Supported resource pairs are `1/256`, `1/512`, `2/1024`, `4/2048`, and
`4/4096`, expressed as vCPU/MiB. Build execution, publication, scheduling, and
every Sandbox launch use the exact pair snapshotted by that build.

Keep manifests commit-safe. Unknown fields are rejected, including plaintext
`secrets` or `env` blocks and mutable `templateId`, `templateBuildId`, `vmId`,
or `sandboxId` fields. Build and runtime identities are server-derived.

Ephemeral creation is a separate lifecycle operation. The next Sandbox slice
launches the applied template's current exact ready build:

```sh
ccp sandbox create --template python-tools --ttl 15m --org-id "$CCP_ORG_ID"
```

`--ttl` defaults to `15m` and accepts whole-second human durations from `1m`
through `24h`. Every invocation creates a distinct Sandbox while reusing the
same immutable build. Applying desired template state never launches a Sandbox.

Creation fails with `template_not_found` when the active organization-scoped
name does not exist and `template_not_ready` while its current recipe has no
ready build. Wait for the applied build to publish, then retry the create.
