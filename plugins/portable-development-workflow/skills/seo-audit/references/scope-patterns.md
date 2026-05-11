# Public Site SEO Audit Scope Patterns

## Static-Only Crawl

Exclude blog/article routes:

```sh
--exclude-regex '/post(?:/|$)'
```

## Resource-Only Crawl

Include resources only:

```sh
--include-regex '^https://example\\.com/(resources|case-studies|whitepapers)(?:/|$)'
```

## Services-Only Crawl

Include service families:

```sh
--include-regex '^https://example\\.com/(services|solutions|products)(?:/|$)'
```

## Full Public Crawl With Known Utility Exclusions

Example of excluding auth or non-marketing routes:

```sh
--exclude-regex '/(portal|connect|login|admin)(?:/|$)'
```
