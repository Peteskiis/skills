## Reference matrix

With `CCP_HEADLESS=1` set:

| Command | Headless-safe? | What it needs |
|---|---|---|
| `ccp init <name>` | yes | positional `<name>` |
| `ccp dev` | yes | project directory |
| `ccp build` | yes | project directory |
| `ccp deploy` | yes | linked config, or org/function resolution |
| `ccp link` | yes | `--org-id` and `--function-id` |
| `ccp list` / `ccp ls` | yes | linked project or org resolution |
| `ccp logs` | yes | linked project or `FUNCTION_ID` |
| `ccp analytics` | yes | linked project or `FUNCTION_ID` |
| `ccp remove` | yes, destructive | linked project |
| `ccp promote` | yes | `DEPLOYMENT_ID` |
| `ccp undeploy` | yes, destructive | `DEPLOYMENT_ID` |
| `ccp store create` | yes | org resolution |
| `ccp store put/get/ls/rm` | yes | store resolution |
| `ccp db create` | yes | org resolution; optional linked project or `--function-id` |
| `ccp db ls` | yes | org resolution |
| `ccp db info/exec/migrate` | yes | linked project or `--db-id` |
| `ccp db destroy` | yes, destructive | `DB_ID` |
| `ccp db connect` | no | use `ccp db exec` |
| `ccp db backup create/ls` | yes | linked project or `--db-id` |
| `ccp db backup restore/delete` | yes, destructive | `BACKUP_ID` |
| `ccp domain ls` | yes | org resolution |
| `ccp domain add/link/unlink` | yes | command-specific flags |
| `ccp domain remove` | yes, destructive | `DOMAIN` |
| `ccp oidc create` | yes | `--name` and at least one `--redirect-uri` |
| `ccp oidc ls/info/update/rotate-secret/destroy` | yes | org or client resolution |
| `ccp compute deploy` | yes | source/image/binary, name, port, org resolution |
| `ccp compute list/status/logs/exec/restart` | yes | linked project or service ID |
| `ccp compute destroy` | yes, destructive | linked project or service ID/name |
| `ccp ci` | yes | git repo with origin and `.cluster-ci.yaml` |
| `ccp env list/get/set/unset` | yes | `--vm <vm_id>` |
| `ccp env refresh-system` | yes | `--vm <vm_id>` |
| `ccp skills [topic\|all]` | yes | nothing; `--export DIR` writes the agent-skill bundle (maintainer tool) |
| `ccp auth login` | interactive | human approval in browser |
| `ccp auth print/export-access-token` | yes | logged-in session |
| `ccp auth logout` | yes | existing session |
| `ccp doctor` | yes | nothing (offline V8/JIT self-check; then an advisory toolchain-deps report — go/esbuild/cargo+musl for deploys. Exits non-zero only when the runtime is broken, never for a missing dep. `--deps` = report only, no V8; `--yes` = auto-install the safe subset) |
| `ccp update` | yes (not in managed VMs) | network; writable install dir (else `sudo ccp update`) |
