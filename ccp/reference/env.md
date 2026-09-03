## Environment variables on dev VMs

`ccp env` manages VM-level environment variables for development VMs. It does
not mutate already-running process environments.

```sh
ccp env list --vm <vm_id> [--json]
ccp env get KEY --vm <vm_id> [--reveal]
ccp env set KEY=VALUE --vm <vm_id> [--visibility plaintext|sensitive]
ccp env unset KEY --vm <vm_id>
ccp env refresh-system --vm <vm_id>
```

Visibility:

- `sensitive` is the default; list output masks the value.
- `plaintext` can be listed and retrieved without `--reveal`.

Reserved prefixes are blocked for user env: `GH_`, `GIT_`, `CCP_`, `CLUSTA_`.
System/session sources own those names.

`refresh-system` publishes a new runtime-environment generation containing
system credentials such as GitHub credentials. The active VM reconciler applies
it in the background; credential-dependent operations fail with
`runtime_environment_unavailable` until that exact generation is active. CCP
credentials are VM-scoped and renewed automatically while active or resumable,
so start and resume apply current material without waiting on the credential
provider.

Important distinction: compute deployment env (`ccp compute deploy --env` and
`cluster.toml [env]`) is workload env. `ccp env` is VM-level env for dev VMs.
