## Domains: custom domains

Domains are org-scoped resources that can be linked to serverless Apps or
compute VMs.

```sh
ccp domain add example.com [--org-id O]
# Add the printed TXT and A records, then complete the claim:
ccp domain verify CLAIM_ID [--org-id O]
ccp domain ls [--org-id O]
ccp domain link example.com --app A [--org-id O]
ccp domain link example.com --vm "<vm_id>:<port>" [--org-id O]
ccp domain unlink example.com [--org-id O]
ccp domain remove example.com [--org-id O]
```

For Apps, prefer `--app` when headless. For compute services, read
the VM ID from `ccp compute status`, then link with the service port:

```sh
ccp domain link example.com --vm "<vm_id>:8080"
```

`add` starts an expiring ownership claim; the domain does not enter inventory
until `verify` can resolve its TXT proof. `unlink` submits a withdrawal but
keeps the owned domain. Wait for routing to disappear before `remove`, which
retires the ownership record and auto-confirms in headless mode.

Binding, withdrawal, and certificate readiness are asynchronous. A successful
link or unlink means Domains durably accepted the next desired revision;
external reachability can lag.
