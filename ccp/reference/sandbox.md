# Sandboxes

Validate a versioned, organization-scoped ephemeral Sandbox declaration:

```sh
ccp sandbox run -f sandbox.yaml --org-id "$CCP_ORG_ID" --dry-run
```

The first manifest slice is deliberately read-only. `--dry-run` is required;
the server validates the complete contract and resolves the semantic
`development` base to one exact immutable build without creating a template,
build, VM, Sandbox, billing session, or artifact.

## Manifest

```yaml
apiVersion: sandboxes.clusterbase.ai/v1
kind: Sandbox
metadata:
  name: python-tools
spec:
  template:
    base: development
    packages:
      apt: [jq]
      pip: [cowsay==6.1]
    steps:
      - run: touch /workspace/ready
  ttlSeconds: 900
```

`metadata.name` is the stable organization-scoped template identity. The
manifest accepts the same typed `apt`, `pip`, `npm`, `cargo`, `gem`, and `go`
package specifications as Sandbox template builds, followed by exactly one
`run` step. TTL must be between 60 seconds and 24 hours.

Keep manifests commit-safe. Unknown fields are rejected, including plaintext
`secrets` or `env` blocks and mutable `templateId`, `templateBuildId`, `vmId`,
or `sandboxId` fields. The server returns the exact resolved base-build ID,
canonical recipe hash, and TTL in the dry-run plan.
