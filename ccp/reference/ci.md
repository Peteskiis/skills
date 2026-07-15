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
as normalized JSON; the server clones the repo and runs the job remotely.

Minimal spec shape:

```yaml
steps:
  - name: test
    run: cargo test -p ccp
    timeout_sec: 600
```

`--json` prints one machine-readable result line and suppresses streamed logs.
`--no-wait` submits and prints the job ID without waiting.

Use `--org-id` or `CCP_ORG_ID` for multi-org accounts. The command exits with
the build exit code when waiting, so it can gate scripts directly.
