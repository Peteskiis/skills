## Databases: managed Postgres

```sh
ccp db create [--name mydb] [--function-id F] [--org-id ORG]
ccp db ls [--org-id ORG]
ccp db info <DB_ID>
ccp db destroy <DB_ID>
```

`ccp db create` writes `database_id`, `database_token`, and `organization_id` to
`.ccp/config.json`, injects `DATABASE_URL` and `DATABASE_TOKEN` into the
linked Function when possible, and mirrors them into local `.env`.

Databases are organization-owned. Create and list resolve the organization in
this order: `--org-id`, `.ccp/config.json`, `CCP_ORG_ID`, sole organization, or
the interactive picker. In headless multi-organization environments, pass
`--org-id` or set `CCP_ORG_ID`.

`ccp db destroy` auto-confirms in headless mode and removes matching DB env from
local `.env` when the current project is linked to that DB.

### SQL and migrations

```sh
ccp db exec '<SQL>' [--db-id D] [--token T]
ccp db migrate [--dir ./migrations] [--db-id D] [--token T]
ccp db migrate --status
```

Never use `ccp db connect` in headless mode. It opens a TUI and errors fast for
agents; use `ccp db exec` instead.

`ccp db exec` reaches the database over `https://<DB_ID>.<base-domain>`, where the
base domain is derived from `CCP_API_URL` (`api.example.dev` → `example.dev`), so it
follows whichever cluster the CLI is pointed at. If `CCP_API_URL` has no `api.`
prefix, `ccp db exec` fails asking for `CCP_DB_BASE_DOMAIN` rather than guessing —
set that variable to the cluster's base domain. Prefer `DATABASE_URL` (the bare
proxy host injected on create) over rebuilding the host yourself in handler code.

### Backups

```sh
ccp db backup create [--db-id D]
ccp db backup ls [--db-id D]
ccp db backup restore <BACKUP_ID> [--db-id D]
ccp db backup delete <BACKUP_ID> [--db-id D]
```

Restore and delete are destructive and auto-confirm in headless mode.

### Client access

```sh
ccp db client-access enable [DB_ID]
ccp db client-access disable [DB_ID]
```

The DB must be running. Paused DBs return 409; wake with a query and retry. The
toggle restarts db-proxy, so in-flight requests can fail and clients should
retry.

The toggle is idempotent. If restart fails, the API returns
`proxy_restart_failed` and the DB row is not flipped, so stored state remains
truthful. Retry once; if the VM remains wedged, recovery is destroy and recreate,
which loses data.

Do not use `ccp compute restart` for managed DBs. They are not compute services.
