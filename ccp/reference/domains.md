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

The authenticated Infra standalone proxy HTTP API also accepts a verified,
currently unbound custom hostname for an organization-owned VM. The caller
must own the VM and belong to that organization, and the hostname must appear in its canonical
Domains inventory with the required A record. An active binding conflicts with
standalone registration. Proxy deletion withdraws its accepted Domain revision;
a later Domain link or unlink supersedes that proxy receipt and remains authoritative.
Generated service-name proxy hostnames remain supported and reject collisions.
App names, App identity hostnames, deployment preview UUIDs and Compute hostnames
share this namespace. App creation, rename or deployment allocation rejects a
hostname reserved by another product, including a proxy awaiting deletion.

Standalone HTTP proxy ports must be 1–65535. Its optional path must be an
absolute ASCII path prefix without a query, fragment or Traefik expression
characters; invalid routing input returns `400 invalid_request`. Registering
against a stopped VM retains `400 vm_not_running`. Hostname collisions return
`409 hostname_conflict`; denied custom ownership returns `403 forbidden`.
