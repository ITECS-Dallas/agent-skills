# Public Site SEO Audit Reporting Checklist

## Always Capture

- audit date
- base URL
- scope rules
- crawl command
- sitemap count
- non-HTML sitemap URL count
- crawled page count
- blocked URL count
- fetch error count
- issue counts by type and severity

## Always Review In The Export

- status codes
- canonicals
- title coverage
- meta description coverage
- H1 counts
- viewport meta coverage
- schema coverage by page type
- pages not in sitemap
- duplicate titles or descriptions
- framework/internal assets missing `X-Robots-Tag: noindex`
- host/protocol redirect matrix
- raw vs rendered title/meta/canonical on representative URLs

## Prioritization Buckets

- High: crawl/indexation blockers, robots conflicts, non-HTML sitemap URLs, 4xx/5xx sitemap URLs, soft-404 patterns, internal links to invalid targets
- Medium: template metadata defects, missing H1s, multiple H1s, canonical gaps, route-level schema gaps
- Low: enhancement opportunities, optional schema expansion, non-blocking content hygiene

## Verification Section Must Include

- the exact rerun command
- example URLs to recheck
- the expected result after the fix
- if applicable, the mobile-render probe command and before/after comparison
