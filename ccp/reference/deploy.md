## Apps: scaffold, deploy, logs, and local dev

Use this topic for serverless apps. Compute services use
`ccp skills compute`.

### Scaffold, preview, and first deploy

```sh
ccp init my-app --template react   # blank | api | static | react
cd my-app
ccp dev                           # 0.0.0.0:8000, also reachable via localhost
# In another shell, after validation:
ccp build
ccp deploy                        # hosted preview; --prod publishes production
```

Read this runbook before scaffolding or deploying. Inspect existing projects
first and preserve their established structure and tooling. Prefer
`ccp init <name> --template react` for suitable new React apps and
`ccp init <name> --template static` for simple HTML sites.

In Build, start `ccp dev` in the background, verify
`http://127.0.0.1:8000` from the workspace, then call `show_preview` with no
arguments. The Sandbox preview routes port 8000; it is separate from a hosted
CCP deployment. Run `ccp build` and relevant project checks before deployment.

`ccp init` also creates a git repository with an initial commit of the
scaffold, unless the target directory is already inside one; `--no-git` skips
this. It is best-effort: a missing `git` or an unconfigured commit identity
prints a notice and never fails the scaffold.

Headless first deploy resolves an org, then attaches an exact same-named App
when one already exists there. Otherwise it reuses or creates a same-named
Project and creates the App inside it. Org resolution is `--org-id` > project
config > `CCP_ORG_ID` > sole-org auto-pick > error. The Project, App, and org
IDs land in `.ccp/config.json` (gitignored local state — not committed).

Manage empty Projects directly when needed:

```sh
ccp project ls [--org-id O]
ccp project create my-project [--org-id O]
ccp project rm my-project --yes [--org-id O]
```

Project names are normalized to lowercase kebab-case. Removing a Project also
deletes its Apps and Deployments.

To target the same App from CI or another machine, pass `--app-id` and
set `CCP_ORG_ID` (dev VMs get `CCP_ORG_ID` + `CCP_SESSION_TOKEN` auto-injected)
rather than committing `.ccp/config.json`.

### A config written before the App rename

A `.ccp/config.json` that links the project by `function_id` (the pre-rename
key) is **rejected**, not silently ignored:

```
.ccp/config.json predates the App rename: it links this project by
`function_id`, which is no longer read.
```

Relink explicitly — the id itself did not change, only the key name:

```sh
ccp deploy --app-id <the id from the error>
```

That clears the retired key and links the project properly; every later command
works normally. Do not delete the key by hand: an exact same-name App can be
reattached, but a renamed directory cannot identify the original App safely.

### Deploy

```sh
ccp deploy [--prod] [--org-id O] [--app-id A] [--public-dir DIR] [PATH]
```

- Linked config or explicit `--org-id` plus `--app-id` deploys to that
  App without prompting.
- Unlinked headless deploy attaches an exact same-org name before creating;
  otherwise it creates a same-named Project and App.
- Preview deploy is the default; `--prod` promotes the new deployment to prod.
- The deployment URL is printed on stdout.

Before deploying, resolve the intended project, App, and organization from
existing linkage and explicit user intent. Inspect with `ccp list` and link
explicitly with `ccp link --org-id O --app-id A` when needed. An exact same-name
match in an unlinked directory does not establish that it is the intended App;
resolve ambiguity before deploying. Never delete linkage to bypass an error or
silently deploy to a replacement App.

After deploying, request the returned URL and verify the app before reporting
success. If the command times out or its result is uncertain, inspect
`ccp list` for the attempted deployment before retrying. Do not create a second
deployment merely because the first response was lost.

`ccp deploy` merges local `.env` into remote env. Keys present locally are
added/updated; absent keys are preserved server-side. A failed env write aborts
the deploy.

Bundling requires `esbuild` on PATH (`brew install esbuild`, or
`npm install -g esbuild`). Run `ccp doctor` to check it and the other deploy
toolchains.

### Client bundle and CSS imports

When `cluster.toml`'s `[serverless]` sets `client` (e.g. `src/main.tsx`), that entry is
bundled for the browser and served at `/{stem}.js` (`main.js`). CSS imported
from the client (`import "./App.css"` — multiple files, `@import`, and
`*.module.css` all work) is bundled into a single `/{stem}.css` (`main.css`).

The server entry may import CSS too — that is how SSR shares a component with
the client. Stylesheets reached from the handler are discarded (the client is
the sole producer of `/{stem}.css`), so **import the same styles from the
client entry**, which SSR does naturally by sharing the component. Two notes:

- With **no** `"client"` entry there is nothing to serve the stylesheet, so a
  CSS import from the handler is still a deploy error.
- `*.module.css` from the handler is a warning, not an error: class names
  resolve correctly, but esbuild builds the two entries as separate graphs, so
  the generated names can disagree if two `*.module.css` files share a
  basename. Prefer plain CSS, or unique basenames, for shared components.

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
ccp logs [APP_ID] [-n LIMIT] [--level info,warn,error,debug] \
  [--deployment DEPLOYMENT_ID] [-f]
```

`APP_ID` falls back to `.ccp/config.json`. Output is one plain line per
entry and pipes cleanly.

### Web analytics

```sh
ccp analytics [APP_ID] [--period 24h|7d|30d|90d] \
  [--by url|referrer|browser|os|device|country]
```

Product traffic view for a deployed App — cookieless pageviews
(visitors, visits, pageviews, bounce rate, average visit); `--by` prints a
top-10 breakdown ranked by visitors. Default period is `7d`; `APP_ID`
falls back to `.ccp/config.json`. Collection is on by default per app
(toggle with `PATCH /apps/:id {"analytics_enabled": false}` via the
API). For per-request debugging use `ccp logs`, not analytics.
"Analytics backend is unavailable" means the ClickHouse store is down or not
configured in this environment — it never blocks serving traffic.

Two collection tiers, selected per deployment by `analytics` under
`[serverless]` in `cluster.toml`:

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
ccp dev                           # defaults to 0.0.0.0:8000
ccp dev --port 3000 --hostname 127.0.0.1  # explicit overrides
ccp build [PATH]
```

The default bind is identical in terminals and headless execution.
`0.0.0.0` listens on all IPv4 interfaces, including localhost; it needs no
second localhost listener. `--port` and `--hostname` override independently.
Use `--hostname 127.0.0.1` for localhost-only access. Build's development
preview requires `0.0.0.0:8000`, regardless of overrides used elsewhere.

Use `ccp dev` directly for Cluster projects. Do not substitute package-manager
dev scripts when the goal is to run the Cluster local runtime.

### Link, list, promote, delete

```sh
ccp link --org-id O --app-id A
ccp list                 # alias: ccp ls
ccp promote DEPLOYMENT_ID
ccp undeploy DEPLOYMENT_ID
ccp remove               # alias: ccp rm
```

`promote`, `undeploy`, and `remove` auto-confirm in headless mode when
destructive.
