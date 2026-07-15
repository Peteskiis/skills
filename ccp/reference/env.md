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

`refresh-system` re-applies system credentials such as GitHub credentials to the
VM. It does not refresh the user's `CCP_SESSION_TOKEN`; use
`ccp auth sync --vm <vm_id>` for that.

Important distinction: compute deployment env (`ccp compute deploy --env` and
`cluster.toml [env]`) is workload env. `ccp env` is VM-level env for dev VMs.
