## Stores: static-file buckets

Stores hold static files and return served URLs.

```sh
ccp store create assets
ccp store put logo.png
ccp store get logo.png
ccp store ls
ccp store rm logo.png
```

`store_id` can be pinned in `.ccp/config.json`. For headless or in-VM use,
`CCP_STORE_ID` is the fallback after project config. Without either, ccp
resolves the store from org state or a prompt when interactive.

When organization selection is needed, project `organization_id` wins over the
named context, `CCP_ORG_ID`, and then the saved default. The selected organization must be an active
membership; a stale project hint fails instead of falling back to another org.
Headless ambiguity errors list the available organizations.

In managed VMs, use the installed managed CCP credential; do not run interactive
login or copy a human token into the VM. Store operations resolve that credential
through Infra to the running VM's actor and organization. The selected Store
must belong to that organization. Revoked membership or a stopped/revoked runtime
fails authorization; fix the runtime or membership instead of retrying with a
different identity.

Uploads return content-addressed URLs by default. These URLs are immutable and
safe for long CDN caching.

Use `--mutable` only when a stable URL is required and old content should be
replaced at the same path. Mutable URLs bypass the CDN cache.

Image transform parameters can be appended to served URLs:

```text
?w=400&format=webp
```

Common agent rule: when a store command needs a store and headless resolution is
ambiguous, set `CCP_ORG_ID` and `CCP_STORE_ID` explicitly instead of guessing.

## Unattended organization credentials

Use an organization API key with `store:use` through `CCP_API_KEY`, and select
`CCP_ORG_ID` and `CCP_STORE_ID` explicitly. Store operations validate the key and
Store ownership on the server; organization keys do not use a human membership
picker. Keys created before the Store scope was added must be replaced rather
than silently gaining a new scope. Revoked or expired keys fail immediately.

For an explicitly configured agent deployment, bind the key as a vault secret
such as `NEWS_STORE_API_KEY` and pass it to the command without printing it:
`CCP_API_KEY="$NEWS_STORE_API_KEY" ccp store put image.png`.
Do not put key values in manifests, prompts, shell literals, receipts or logs.
