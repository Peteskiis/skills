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
  packages:
    apt: [jq]
    pip: [cowsay==6.1]
  steps:
    - run: touch /workspace/ready
```

`metadata.name` is the stable organization-scoped template identity. The
manifest accepts the same typed `apt`, `pip`, `npm`, `cargo`, `gem`, and `go`
package specifications as Sandbox template builds, followed by exactly one
`run` step. Changing the recipe admits a new immutable build; existing builds
are never mutated.

Keep manifests commit-safe. Unknown fields are rejected, including plaintext
`secrets` or `env` blocks and mutable `templateId`, `templateBuildId`, `vmId`,
or `sandboxId` fields. Build and runtime identities are server-derived.

Ephemeral creation is a separate lifecycle operation. The next Sandbox slice
adds `ccp sandbox create --template <name>`; applying desired template state
does not launch a Sandbox.
