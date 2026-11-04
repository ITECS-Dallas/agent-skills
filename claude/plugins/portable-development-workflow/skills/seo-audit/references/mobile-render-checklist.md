# Mobile Render Checklist

Use this checklist when auditing JavaScript-heavy sites or when Googlebot Smartphone behavior matters.

## Run The Probe

```sh
npx -y -p playwright node scripts/mobile_render_probe.mjs \
  --url https://example.com/ \
  --url https://example.com/template-url \
  --output data/example_render_probe.json
```

## Validate Per URL

- final URL
- rendered title
- rendered meta description
- rendered canonical
- rendered robots meta
- H1 count and H1 text
- JSON-LD count and schema types
- failed request count
- 4xx/5xx asset responses

## Compare Against Raw Crawl

For representative URLs, compare the render probe against the raw crawl export:

- title
- meta description
- canonical
- robots directives
- schema presence

Any mismatch between raw and rendered should be treated as a real search risk until proven harmless.
