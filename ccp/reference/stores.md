## Stores: static-file buckets

Stores hold static files and return served URLs.

```sh
ccp store create assets
ccp store put logo.png
ccp store get logo.png
ccp store ls
ccp store rm logo.png
```

`store_id` can be pinned in `.ccp/config.json`. Without it, ccp resolves the
store from flags, project config, org state, or a prompt when interactive.

Uploads return content-addressed URLs by default. These URLs are immutable and
safe for long CDN caching.

Use `--mutable` only when a stable URL is required and old content should be
replaced at the same path. Mutable URLs bypass the CDN cache.

Image transform parameters can be appended to served URLs:

```text
?w=400&format=webp
```

Common agent rule: when a store command needs a store and headless resolution is
ambiguous, pass IDs explicitly instead of guessing.
