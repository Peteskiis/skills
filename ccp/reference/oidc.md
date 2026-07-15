## OIDC: Sign in with Cluster clients

OIDC clients are org-scoped OAuth2 clients for "Sign in with Cluster".

```sh
ccp oidc create --name app \
  --redirect-uri https://app.example.com/auth/callback

ccp oidc ls [--org-id O]
ccp oidc info <client_id>
ccp oidc update <client_id> --add-redirect-uri URL
ccp oidc update <client_id> --remove-redirect-uri URL
ccp oidc rotate-secret <client_id>
ccp oidc destroy <client_id>
```

`create` prints the client secret once. Save it immediately; later commands can
rotate but not reveal the old secret.

Serverless prod deploys can keep redirect URIs in sync automatically. Preview
deploys require explicit opt-in:

```sh
ccp deploy --register-redirect-uri
```

Redirect URI updates are exact string operations. Remove stale preview URLs when
they are no longer needed.

Headless behavior:

- `create` needs `--name` and at least one `--redirect-uri`.
- Single-org accounts auto-resolve org; multi-org accounts need `--org-id` or
  `CCP_ORG_ID`.
- `rotate-secret` and `destroy` auto-confirm in headless mode.
