## CI: ephemeral build jobs

`ccp ci` submits `.cluster-ci.yaml` to an isolated build machine and exits with
the remote build result.

```sh
ccp ci [DIRECTORY] [-f FILE] [--org-id O] [--git-ref REF] [--request-id ID] [--no-wait] [--json]
```

Defaults:

- directory: `.`
- file: `<directory>/.cluster-ci.yaml` or `.cluster-ci.yml`
- git ref: current branch

The directory must be a git repo with an `origin` remote. The CLI sends the spec
as normalized JSON together with the current full commit SHA. The server clones
public repositories or authorized GitHub repositories and checks out that
exact commit; the branch is display metadata only. If local `HEAD` differs from
the remote branch, the CLI warns before submission.

Each invocation generates a fresh request ID and prints it to stderr before
submission. If the response is lost, repeat the same command with
`--request-id ID`, preserving the repository, commit, ref and specification.
The same authenticated actor and organization receive the original job, including
its current terminal result. A fresh execution requires a new request ID.
IDs contain 1–128 ASCII letters, digits, `.`, `:`, `_` or `-`.

Reusing an ID with changed inputs returns a conflict. JSON object key order is
irrelevant; explicitly adding defaults or changing a command is a different input.
Accepted requests keep their original image and timeout when retried, even after
the environment is archived or the queue fills. Current organization membership
is still required. Native API callers must supply `SubmitJobRequest.request_id`;
the retained HTTP adapter requires the same `request_id` field.

Submission pins the selected published environment image (or the default
build-machine image), resources, billing identity and
effective timeout. Server timeout defaults and limits apply when the job is
accepted; later configuration changes do not change queued jobs. A job with an
invalid or missing launch receipt fails before provisioning and must be
resubmitted with a new request ID.

Job results contain result metadata, not the submitted environment or raw spec.
Native log following resumes after an exact cursor and ends with the terminal
marker. Artifact and archived-log downloads require current organization access
and use the immutable winning object generation.

Minimal spec shape:

```yaml
version: 1
timeout_sec: 600

steps:
  - name: Test CLI
    run: cargo test -p ccp
```

Step `name` is an optional display label (1–120 characters after trimming; no
control characters). Unnamed commands appear as “Step 1”, “Step 2”, and so on.
The CI gRPC job includes durable ordered step states, start/end times and command
exit codes. Streamed log entries carry their step ID. Portal groups this output
into collapsible steps; completed runs retain step metadata after live logs expire.
Old runs without step records show ungrouped output. Optional cache/artifact/log
publication steps can fail while the job's commands still pass.

`--json` prints one machine-readable result line and suppresses streamed logs.
`--no-wait` submits and prints the job ID without waiting.

Use a saved default, `--org-id`, or `CCP_ORG_ID` for multi-org accounts. The command exits with
the build exit code when waiting, so it can gate scripts directly.

A failed build forwards its nonzero exit code only when it is between `1` and `255` inclusive;
missing, zero, or out-of-range codes become `1`. Timeout and cancellation use
`124` and `130`. The JSON `exit_code` matches the command exit status.

To reuse a published cloud Build environment, add its immutable revision ID:

```yaml
version: 1
environment_revision_id: envr_REPLACE_WITH_PUBLISHED_REVISION
timeout_sec: 600
steps:
  - run: make check
  - run: make build
artifacts:
  - name: server
    path: dist/server
  - name: SHA256SUMS
    path: dist/SHA256SUMS
```

Use the revision ID returned by `EnvironmentRevisionsService`, not an Agents saved
environment ID or template name. The revision must belong to the selected
organization and remain available at submission. Publication freezes dependencies
in the image and startup configuration; editing a recipe requires a new publication.
An accepted job retains its exact image even if the revision is later archived.

Each job gets a fresh VM. CI checks out its exact commit at `/workspace/repository`,
withdraws checkout credentials, and runs the published startup script before the
steps. Set the startup working directory to `/workspace/repository` when it needs
that checkout. Startup failure or timeout prevents steps from running. Logs,
cancellation, timeouts and VM cleanup use the normal CI lifecycle. Commands are
explicit: CI does not infer which test runner or build command your service uses.

Secondary repositories use exact commits and distinct sibling directories:

```yaml
sources:
  - repository: https://github.com/example/rig.git
    commit: 0123456789abcdef0123456789abcdef01234567
    path: rig
```

CI clones this source at `/workspace/rig` before any user command. Paths must be
single directory names; the main `repository` directory and platform directories
are reserved. At most ten secondary sources are accepted.

Private dependency fetching is an explicit phase before environment startup:

```yaml
dependencies:
  github_repositories:
    - example/protocol
  steps:
    - run: cargo fetch --locked
```

Every declared repository requires current linked-account access to the same
GitHub App installation. The dependency phase receives an installation token
restricted to those repositories with `contents:read`, through the existing Git
HTTPS credential helper. It does not receive the personal checkout token. SSH
Cargo URLs need a process-local HTTPS rewrite during fetching. Dependency output
is masked and retained; failure prevents startup and checks. Credential withdrawal
must be acknowledged before startup or checks run. GitHub grants are short-lived;
withdrawal removes guest delivery, not copies deliberately made by dependency
commands. Only run dependency preparation that you trust with the declared read
access. No token is persisted in the CI specification or reusable image.

The sequence is checkout → dependency preparation → environment startup → caches
→ steps → output capture → cleanup. For Cargo, run `cargo fetch --locked` in
preparation and set `CARGO_NET_OFFLINE=true` for checks to prove that preparation
was complete. Dependency commands can explicitly override that variable while
fetching. A cache is an optional accelerator, not a dependency source.

Artifacts declare up to ten uniquely named files. Names use 1–120 ASCII letters,
digits, `.`, `_` or `-` and cannot be `.` or `..`. Paths are repository-relative;
absolute paths and parent traversal are rejected. Each file must be nonempty and
at most 256 MiB. Each upload has its own step and immutable receipt. A missing or
failed optional upload does not hide other successful outputs or change the check
result. Failed, cancelled and timed-out jobs do not publish artifact winners.

`--json` exposes an `artifacts` list containing each `name`, `source_url`,
`size_bytes` and `sha256`. Portal displays those files with independent downloads.
Native callers select `ArtifactDownloadRequest.artifact_name` from that list;
downloads recheck current organization access and pin the retained generation.
The old singular `artifact` specification is rejected. These are run outputs,
not releases; release publication remains a separate operation.
