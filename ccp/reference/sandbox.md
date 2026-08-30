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

The repo includes a graphical Ubuntu template at
`templates/sandbox/desktop.yaml`. Apply it, wait for its immutable build to
become ready, and create a Sandbox as usual:

```sh
ccp apply -f templates/sandbox/desktop.yaml --org-id "$CCP_ORG_ID"
ccp sandbox create --template desktop --ttl 1h --org-id "$CCP_ORG_ID"
```

Open its noVNC desktop without copying a bearer into a browser URL:

```sh
ccp sandbox desktop sbx_... --ttl 20m
```

The command opens a token-free `127.0.0.1` URL and remains in the foreground.
It injects the scoped `desktop` service bearer into upstream HTTPS and WSS
requests, rejects cross-origin browser access, and closes on Ctrl-C or access
expiry. Raw VNC is not published; it remains loopback-only inside the guest.
Use `ccp sandbox connect` for non-browser automation that can set an
`Authorization` header itself.

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
