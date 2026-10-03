## CI: ephemeral build jobs

`ccp ci` submits `.cluster-ci.yaml` to an isolated build machine and exits with
the remote build result.

```sh
ccp ci [DIRECTORY] [-f FILE] [--org-id O] [--git-ref REF] [--no-wait] [--json]
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

Job results contain result metadata, not the submitted environment or raw spec.
Native log following resumes after an exact cursor and ends with the terminal
marker. Artifact and archived-log downloads require current organization access
and use the immutable winning object generation.

Minimal spec shape:

```yaml
version: 1
timeout_sec: 600

steps:
  - run: cargo test -p ccp
```

`--json` prints one machine-readable result line and suppresses streamed logs.
`--no-wait` submits and prints the job ID without waiting.

Use a saved default, `--org-id`, or `CCP_ORG_ID` for multi-org accounts. The command exits with
the build exit code when waiting, so it can gate scripts directly.

A failed build forwards its nonzero exit code only when it is between `1` and `255` inclusive;
missing, zero, or out-of-range codes become `1`. Timeout and cancellation use
`124` and `130`. The JSON `exit_code` matches the command exit status.
