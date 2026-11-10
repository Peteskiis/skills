## Canvas

Canvas is a local information document with interactive React content. Creation and preview do not log in,
create a cloud App, or publish content.

```sh
ccp canvas init ./vector-lab --title "Vector lab"
ccp canvas inspect ./vector-lab
ccp canvas typecheck ./vector-lab
ccp canvas dev ./vector-lab
```

`init` requires a new directory, writes source and `canvas.json`, and installs
React dependencies with npm scripts disabled. `--no-install` writes source only.
The metadata has version 1, a stable random ID, and a title. Do not change the ID
when revising an existing canvas. `inspect` validates and prints that metadata.

Read `CANVAS.md` and `src/App.tsx` first. Compose the supplied typed Canvas,
Section, Columns, Stat, Table, and Callout components from `./canvas-ui`.
Lead with the explanation; use diagrams, examples, comparisons, and controls
to support it. Keep the neutral document styling, light/dark colors and narrow
panel layout. Avoid building a branded website or app shell unless requested.

Edit `src/App.tsx` and files beneath `src/`; extend `src/styles.css` for figures and place static assets
in `public/`. Canvas preview compiles `src/main.tsx` and `index.html`. It does not
read the server handler, project `.env`, or CCP login credentials. Compiler inputs
must resolve inside `src/` or `node_modules/`; public assets cannot escape their
directory through symlinks. No package scripts run during preview.

Use `useCanvasState<T>(key, initial)` from `./canvas` for JSON interaction state.
The starter demonstrates scaling a list with a slider and result table. Local state is bounded to 200 KiB, belongs
to the canvas ID, and persists under `.ccp/` across server restarts. One process
owns state writes. Viewers use revisions; a stale save refreshes the view and
asks the viewer to repeat their edit instead of overwriting another viewer.
Do not edit `.ccp/canvas-state.json` while a preview is running.

`dev` always emits the same version-1 JSON envelope as `dev --json`. Its startup
event is `canvas_listening` with `data.id` and `data.url`. Open that exact URL to
establish the preview's scoped cookie. The URL is a temporary capability; do not
publish it, persist it as identity, or substitute a remote host's localhost.
The server binds an ephemeral loopback port. Rebuilding uses the ordinary CCP
watcher and live-reload client; `build_failed` retains the previous good build,
and `ready` marks a successful rebuild. Process exit is authoritative.

Preview resources require the capability. Host and Origin checks reject other
origins; CSP restricts scripts and resource requests to this preview. The runtime
does not execute generated server code or expose host IPC. A Desktop embedding
must also constrain native navigation and keep app privileges out of the page.

Publishing requires a user request. Run `ccp canvas typecheck .`, then `ccp deploy`
in the Canvas folder. The ordinary App workflow builds the saved source and
publishes a hosted preview; use `--prod` only when production is requested.
Reuse existing App linkage and organization defaults. If CCP needs an
organization, offer the returned names and supply the chosen ID yourself.
Read `ccp skills deploy` for details and verify the returned URL. Published
readers use browser-local state; the author's local state and preview capability
are not uploaded. Canvas creation and preview never publish.

Host installers can query `ccp capabilities` for versioned JSON without loading
user configuration, logging in, or checking for updates. Canvas requires Node/npm
for dependencies and typechecking. The compiler invokes the native esbuild executable
provided by the scaffold dependency or host PATH. Managed hosts supply CCP and Node/npm together; do not suggest updating a managed CCP in place.
