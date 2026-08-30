## Databases: managed Postgres

```sh
ccp db create [--name mydb] [--app-id A] [--org-id ORG] [--network backend]
ccp db ls [--org-id ORG]
ccp db info <DB_ID>
ccp db destroy <DB_ID>
```

`ccp db create` writes `database_id`, `database_token`, and `organization_id` to
`.ccp/config.json` and binds the selected App when possible. A networked bound
App receives a native PostgreSQL `DATABASE_URL`; the existing HTTPS interface
uses `DATABASE_HTTP_URL` and `DATABASE_HTTP_TOKEN`. The CLI mirrors only the
HTTP values into local `.env` so code-only deploys preserve the server-managed
native URL.

`--network` joins the database to the named organization-scoped private network.
The database name becomes `<name>.<network>.internal`, so both names must be
lowercase DNS labels. Networked databases and compute members can connect
across VM nodes.

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
set that variable to the cluster's base domain. Prefer `DATABASE_HTTP_URL` (the
bare proxy host injected on create) over rebuilding the host yourself in handler
code. Serverless Apps using Postgres.js or Drizzle use the native `DATABASE_URL`.

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

The toggle is idempotent. The API first commits the desired mode, then reconciles
db-proxy and records the applied generation. If convergence cannot finish in the
request, the API returns `client_access_pending` (503). Retry safely; background
recovery also resumes the same operation. Do not destroy and recreate the
database to recover a pending toggle. If it remains pending, inspect VM and
db-proxy health without discarding database state.

Do not use `ccp compute restart` for managed DBs. They are not compute services.
