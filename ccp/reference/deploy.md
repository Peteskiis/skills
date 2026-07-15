## Functions: scaffold, deploy, logs, and local dev

Use this topic for serverless functions. Compute services use
`ccp skills compute`.

### Scaffold and first deploy

```sh
ccp init my-app --template react   # blank | api | static | react
cd my-app
ccp deploy
```

Headless first deploy auto-creates and links a Function when it can resolve an
org. Org resolution is `--org-id` > project config > `CCP_ORG_ID` > sole-org
auto-pick > error. The remote IDs land in `.ccp/config.json` (gitignored local
state — not committed).

To target the same Function from CI or another machine, pass `--function-id` and
set `CCP_ORG_ID` (dev VMs get `CCP_ORG_ID` + `CCP_SESSION_TOKEN` auto-injected)
rather than committing `.ccp/config.json`.

### Deploy

```sh
ccp deploy [--prod] [--org-id O] [--function-id F] [--public-dir DIR] [PATH]
```

- Linked config or explicit `--org-id` plus `--function-id` deploys to that
  Function without prompting.
- Unlinked headless deploy creates and links a Function named after the project.
- Preview deploy is the default; `--prod` promotes the new deployment to prod.
- The deployment URL is printed on stdout.

`ccp deploy` merges local `.env` into remote env. Keys present locally are
added/updated; absent keys are preserved server-side. A failed env write aborts
the deploy.

### Client bundle and CSS imports

When `.ccp/config.json` sets `"client"` (e.g. `src/main.tsx`), that entry is
bundled for the browser and served at `/{stem}.js` (`main.js`). CSS imported
from the client (`import "./App.css"` — multiple files, `@import`, and
`*.module.css` all work) is bundled into a single `/{stem}.css` (`main.css`).
The server entry (`index.ts`) must not import CSS — that's a deploy error.

A root `index.html` (Vite convention) is inlined into `__pages` at build time:
`<script>` tags referencing the client source (`src="/src/main.tsx"`) are
rewritten to the built bundle, and a `<link rel="stylesheet">` for the emitted
CSS is injected before `</head>`. Hand-managed HTML that already references
built names passes through untouched.

### Public assets and `serveAsset`

Use `public/` or `--public-dir DIR` for verbatim static assets (favicons,
images, fonts) referenced by absolute URL. HTML files in it are inlined into
`__pages`; other assets are served same-origin from disk by the runtime, with
nested paths preserved. A `public/` file whose path collides with a bundler
output (`main.js`, `main.css`) fails the deploy instead of silently shadowing
it.

Inside a handler, `await serveAsset(path)` returns a `Response` for a deployed
public asset. Use it for auth-gated assets, SSR reads, and catch-all fallbacks.
Missing assets return a 404 `Response`; traversal or absolute paths reject.

### Logs

```sh
ccp logs [FUNCTION_ID] [-n LIMIT] [--level info,warn,error,debug] \
  [--deployment DEPLOYMENT_ID] [-f]
```

`FUNCTION_ID` falls back to `.ccp/config.json`. Output is one plain line per
entry and pipes cleanly.

### Web analytics

```sh
ccp analytics [FUNCTION_ID] [--period 24h|7d|30d|90d] \
  [--by url|referrer|browser|os|device|country]
```

Product traffic view for a deployed Function — cookieless pageviews
(visitors, visits, pageviews, bounce rate, average visit); `--by` prints a
top-10 breakdown ranked by visitors. Default period is `7d`; `FUNCTION_ID`
falls back to `.ccp/config.json`. Collection is on by default per function
(toggle with `PATCH /functions/:id {"analytics_enabled": false}` via the
API). For per-request debugging use `ccp logs`, not analytics.
"Analytics backend is unavailable" means the ClickHouse store is down or not
configured in this environment — it never blocks serving traffic.

Two collection tiers, selected per deployment by `analytics` in
`.ccp/config.json`:

- `"server"` (default): pageviews derived from HTML responses at the edge.
  Zero setup; SPA soft-navigations are not visible.
- `"client"`: on deploy, ccp injects `<script defer src="/_cluster/a.js">`
  into the root `index.html` (hand-managed HTML without a `</head>` gets a
  warning — embed the snippet yourself), and the runtime serves the tracker +
  `POST /_cluster/send` same-origin. Captures SPA route changes, screen size
  and page titles; server-derived counting is suppressed for that deployment
  so nothing double-counts. Switching tiers takes effect on the next deploy.

### Local dev

```sh
ccp dev [--port 1234] [--hostname 0.0.0.0]
ccp build [PATH]
```

Use `ccp dev` directly for Cluster projects. Do not substitute package-manager
dev scripts when the goal is to run the Cluster local runtime.

### Link, list, promote, delete

```sh
ccp link --org-id O --function-id F
ccp list                 # alias: ccp ls
ccp promote DEPLOYMENT_ID
ccp undeploy DEPLOYMENT_ID
ccp remove               # alias: ccp rm
```

`promote`, `undeploy`, and `remove` auto-confirm in headless mode when
destructive.
