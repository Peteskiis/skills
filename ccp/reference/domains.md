## Domains: custom domains

Domains are org-scoped resources that can be linked to serverless Functions or
compute VMs.

```sh
ccp domain add example.com [--org-id O]
ccp domain ls [--org-id O]
ccp domain link example.com --function-id F
ccp domain link example.com --vm "<vm_id>:<port>"
ccp domain unlink example.com
ccp domain remove example.com
```

For Functions, prefer `--function-id` when headless. For compute services, read
the VM ID from `ccp compute status`, then link with the service port:

```sh
ccp domain link example.com --vm "<vm_id>:8080"
```

`unlink` detaches a domain from its current target but keeps the domain record.
`remove` deletes the domain record and auto-confirms in headless mode.

DNS and certificate readiness are asynchronous. A successful link means Cluster
accepted the desired target; external reachability can lag.
