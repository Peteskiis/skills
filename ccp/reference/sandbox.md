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
  base: development
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
are required as one supported `vcpu` and `memory_mb` pair. The manifest accepts
the same typed `apt`, `pip`, `npm`, `cargo`, `gem`, and `go` package
specifications as Sandbox template builds, followed by exactly one `run` step.
Changing resources, packages, ports, or the run step admits a new immutable
build; existing builds are never mutated.

Named ports are private immutable metadata. A declaration has a unique DNS-label
name, a unique guest port, and a protocol of `http` or `websocket`; at most eight
may be declared. The template's boot setup must start the service and bind it to
the guest interface. A running Sandbox publishes declared `http` ports behind
an authenticated HTTPS route. The API can mint an opaque token scoped to one
Sandbox and port for at most one hour and never beyond the Sandbox TTL. Raw VM
addresses and arbitrary undeclared ports remain private. WebSocket access and
the `ccp sandbox connect` convenience command are a later slice.

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
