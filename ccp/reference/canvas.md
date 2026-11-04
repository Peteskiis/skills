## Canvas

Canvas is a local interactive React project. Creation and preview do not log in,
create a cloud App, or publish content.

```sh
ccp canvas init ./vector-lab --title "Vector lab"
ccp canvas inspect ./vector-lab
ccp canvas dev ./vector-lab
```

`init` requires a new directory, writes source and `canvas.json`, and installs
React dependencies with npm scripts disabled. `--no-install` writes source only.
The metadata has version 1, a stable random ID, and a title. Do not change the ID
when revising an existing canvas. `inspect` validates and prints that metadata.

Edit `src/App.tsx`, `src/styles.css`, and files beneath `src/`; place static assets
in `public/`. Canvas preview compiles `src/main.tsx` and `index.html`. It does not
read the server handler, project `.env`, or CCP login credentials. Compiler inputs
must resolve inside `src/` or `node_modules/`; public assets cannot escape their
directory through symlinks. No package scripts run during preview.

Use `useCanvasState<T>(key, initial)` from `./canvas` for JSON interaction state.
The starter demonstrates a counter. Local state is bounded to 200 KiB, belongs
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

Publishing remains explicit: the project has the ordinary `cluster.toml` shape
and static server handler for CCP build/deploy. Only run deployment after a user
requests it, selecting their intended environment and organization. Deployed
readers use their own browser storage; the author's local interaction state and
preview capability are not uploaded. Deployment is not proof of a verified live
view. The Canvas command itself does not publish.
