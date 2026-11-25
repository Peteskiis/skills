## Reference matrix

With `CCP_HEADLESS=1` set:

| Command | Headless-safe? | What it needs |
|---|---|---|
| `ccp init <name>` | yes | positional `<name>` |
| `ccp dev` | yes | project directory |
| `ccp build` | yes | project directory |
| `ccp deploy` | yes | linked config, or org/app resolution |
| `ccp link` | yes | `--org-id` and `--app-id` |
| `ccp list` / `ccp ls` | yes | linked project or org resolution |
| `ccp logs` | yes | linked project or `APP_ID` |
| `ccp analytics` | yes | linked project or `APP_ID` |
| `ccp remove` | yes, destructive | linked project + `--yes` |
| `ccp project ls` | yes | org resolution |
| `ccp project create <name>` | yes | org resolution |
| `ccp project rm <name> --yes` | yes, destructive | org resolution + exact Project name |
| `ccp promote` | yes | `DEPLOYMENT_ID` |
| `ccp undeploy` | yes, destructive | `DEPLOYMENT_ID` + `--yes` |
| `ccp store create` | yes | org resolution |
| `ccp store put/get/ls` | yes | store resolution; `CCP_STORE_ID` supported |
| `ccp store rm` | yes, destructive | store resolution; `CCP_STORE_ID` supported + `--yes` |
| `ccp db create` (defaults to Postgres) | yes | org resolution and an optional linked App or `--app-id` |
| `ccp db create --type sqlite` | yes | linked App or `--app-id` |
| `ccp db ls` | yes | org resolution |
| `ccp db info/exec/migrate` | yes | linked project or `--db-id` |
| `ccp db destroy` | yes, destructive | `DB_ID` + `--yes` |
| `ccp db connect` | no | use `ccp db exec` |
| `ccp db backup create/ls` | yes | linked project or `--db-id` |
| `ccp db backup restore/delete` | yes, destructive | `BACKUP_ID` + `--yes` |
| `ccp domain ls` | yes | org resolution |
| `ccp domain add/verify/link` | yes | org resolution + command-specific values |
| `ccp domain unlink` | yes, destructive | org resolution + command-specific values + `--yes` |
| `ccp domain remove` | yes, destructive | `DOMAIN` + `--yes` |
| `ccp oidc create` | yes | `--name` and at least one `--redirect-uri` |
| `ccp oidc ls/info/update` | yes | org or client resolution |
| `ccp oidc rotate-secret/destroy` | yes, destructive | org or client resolution + `--yes` |
| `ccp compute deploy` | yes | source/image/binary, name, port, org resolution |
| `ccp compute deploy` (immutable changes) | with `-y` / `--yes` | linked service + `cluster.toml`; interruption and guest-data loss; retry resumes replacement |
| `ccp compute list/status/logs/exec/restart` | yes | linked project or service ID |
| `ccp compute destroy` | yes, destructive | linked project or service ID/name + `--yes` |
| `ccp task delegate` | consent for local snapshots | Task text, `--source DIR` with optional `--include PATH`, or `--repo HTTPS_URL --commit SHA`, `--worker codex`, `--vault-id`, `--org-id`, `--task-context`, `--json` |
| `ccp task integrate` | yes | Successful task IDs, `--source DIR --base SHA --branch NEW_BRANCH --worktree NEW_DIR`, optional `--json` |
| `ccp task result` | yes | Run ID, optional `--patch NEW_FILE`, `--json` |
| `ccp sandbox create` | yes | `--template NAME`; optional `--ttl` and `--org-id` |
| `ccp ci` | yes | git repo with origin and `.cluster-ci.yaml` |
| `ccp env list/get/set` | yes | `--vm <vm_id>` |
| `ccp env unset` | yes, destructive | `--vm <vm_id>` + `--yes` |
| `ccp env refresh-system` | yes | `--vm <vm_id>` |
| `ccp org use [id]` | with ID, or sole accessible org | Lists names interactively; validates access and saves an account/environment default |
| `ccp org current [--json]` | yes | Reports effective org and source; never prompts |
| `ccp org clear` | yes | Removes the current account/environment saved default |
| `ccp apply` | yes | Agent or SandboxTemplate `--file <manifest>`; `--org-id` (or `CCP_ORG_ID`); optional `--dry-run` |
| `ccp delete` | yes, destructive | `--file <manifest>`; `--org-id` (or `CCP_ORG_ID`); `--yes` for deletion or `--dry-run` to preview |
| `ccp agent list` / `ccp agent ls` | yes | `--org-id` (or `CCP_ORG_ID`) for org resolution |
| `ccp agent get` | yes | `AGENT_ID`; optional `--version` (no org context needed — cross-org access 404s) |
| `ccp agent versions` | yes | `AGENT_ID` (no org context needed — cross-org access 404s) |
| `ccp agent delete` | yes, destructive | `AGENT_ID`; `--yes` in headless mode |
| `ccp skills [topic\|all]` | yes | nothing; `--export DIR` writes the agent-skill bundle (maintainer tool) |
| `ccp capabilities` | yes | nothing; offline versioned JSON without configuration, login, or update checks |
| `ccp canvas init/inspect/typecheck/dev` | yes | local path; init/typecheck/dev require Node/npm and project dependencies; no login or publication |
| `ccp auth login [--browser\|--device]` | interactive | browser PKCE locally; device approval on SSH/headless hosts; successful login replaces the saved session |
| `ccp auth print/export-access-token` | yes | logged-in session |
| `ccp auth logout` | yes | existing session |
| `ccp doctor` | yes | nothing (offline V8/JIT self-check; then an advisory toolchain-deps report — go/node/cargo+musl for deploys. Exits non-zero only when the runtime is broken, never for a missing dep. `--deps` = report only, no V8; `--yes` = auto-install the safe subset) |
| `ccp update` | yes (not in managed VMs) | network; writable install dir (else `sudo ccp update`) |
