---
name: seo-audit
description: Use when auditing or improving SEO, crawlability, indexing, metadata, schema, internal links, local SEO, Core Web Vitals, content strategy, authority signals, Search Console issues, AI visibility, or public-site search performance.
---

# SEO Audit

## Purpose

Run strategic and technical SEO work across any website without assuming an industry, geography, CMS, framework, or analytics stack. Combine project-local evidence, current primary-source search guidance, and reproducible crawl/render checks.

## When To Use

- Technical SEO audits, site health reviews, crawlability, indexability, sitemap, robots, canonical, redirect, metadata, schema, or internal-linking work.
- On-page SEO, content strategy, keyword mapping, local SEO, backlink/authority analysis, GEO/AEO/AI visibility, and Search Console triage.
- Public production validation after SEO fixes.
- Repo implementation work that changes metadata, schema, routing, sitemap, robots, public page rendering, or crawl-facing headers.

## Read First

Use progressive disclosure. Read only the references needed for the task:

| Need | Read |
| --- | --- |
| Full audit or strategy | `references/technical-seo.md` + `references/on-page-seo.md` |
| Public crawl/indexability validation | `references/scope-patterns.md` + `references/reporting-checklist.md` |
| Mobile/rendered Googlebot validation | `references/mobile-render-checklist.md` |
| Schema and rich results | `references/schema-structured-data.md` |
| Local/maps visibility | `references/local-seo.md` |
| AI Overviews, LLM citations, GEO/AEO | `references/geo-aeo.md` |
| Authority, links, brand signals | `references/off-page-authority.md` |
| Measurement and reporting | `references/measurement-kpis.md` |

## Core Rules

- Verify volatile search guidance against current primary sources when it materially affects the answer.
- Use project-local docs, source code, analytics exports, Search Console data, and CMS facts before making recommendations.
- Do not fabricate rankings, traffic, reviews, ratings, locations, prices, credentials, schema facts, or service areas.
- Do not assume one schema type fits all pages; select schema from visible, accurate, page-specific facts.
- For implementation work, follow the repo's existing metadata, schema, sitemap, routing, and test patterns.
- For public-page SEO signoff, use mobile-first rendered validation plus raw fetch/header checks when crawl/indexability is in scope.
- Keep production interactions read-only unless explicitly authorized.

## Strategic Audit Framework

1. Technical foundation: crawlability, indexation, redirects, canonical host, robots, sitemap hygiene, page speed, mobile usability, framework rendering, and crawl-facing headers.
2. On-page optimization: intent fit, titles, descriptions, heading structure, entity clarity, internal links, media, copy depth, and content quality.
3. Structured data: valid JSON-LD, correct entity typing, rich-result eligibility, no unsupported or invisible claims.
4. Local SEO: Google Business Profile, NAP consistency, service-area logic, local landing pages, reviews, and citations when location matters.
5. Authority: backlinks, mentions, digital PR, directories, social proof, author/entity evidence, and competitor gaps.
6. AI visibility: concise answer blocks, citable facts, entity disambiguation, source clarity, comparison content, and information gain.
7. Measurement: Search Console, analytics, conversion tracking, rank clusters, branded demand, AI citations, and reporting cadence.

## Reproducible Public Audit Workflow

Use the bundled scripts when the task requires production crawl evidence.

### Raw Crawl

```sh
python3 -m pip install requests beautifulsoup4
python3 scripts/public_site_audit.py \
  --base-url https://example.com \
  --output-slug example_static \
  --user-agent-profile googlebot-smartphone \
  --exclude-regex '/(admin|login|portal)(?:/|$)'
```

The crawler exports metadata, canonicals, viewport tags, robots directives, H1 counts, schema summaries, sitemap issues, redirect-chain observations, and asset samples under `data/`.

### Rendered Mobile Probe

```sh
npx -y -p playwright node scripts/mobile_render_probe.mjs \
  --url https://example.com/ \
  --url https://example.com/important-page \
  --output data/example_render_probe.json
```

Use rendered checks for JavaScript-heavy sites, metadata trust issues, framework migrations, public-page release signoff, or any Googlebot Smartphone-sensitive validation.

## Repo Implementation Workflow

1. Inspect local project instructions and existing SEO conventions.
2. Identify the route/template/page type and current ownership.
3. Validate raw source and rendered output when metadata/schema/crawlability can diverge.
4. Update the smallest owning source: metadata object, schema helper, sitemap config, robots file, redirect map, CMS field, or template.
5. Add or update tests/audits already used by the repo.
6. Run raw Googlebot-style fetch/header checks and mobile rendered checks for public-facing SEO changes.
7. Document findings with examples, severity, reproduction, and validation evidence.

## Output Format

Lead with findings and prioritized actions:

- Critical: crawl/indexation blockers, broken canonicals, noindex mistakes, robots/sitemap defects, major rendering mismatch.
- High: missing or duplicated page templates, invalid schema, title/meta systemic issues, internal-linking holes on money pages.
- Medium: content/entity gaps, local SEO opportunities, image/media optimization, FAQ or schema expansion.
- Low: polish, optional enhancements, reporting improvements.

For each issue, include:

- affected URL or template
- evidence
- why it matters
- recommended fix
- validation step

## Resources

- `scripts/public_site_audit.py`
- `scripts/mobile_render_probe.mjs`
- `references/technical-seo.md`
- `references/on-page-seo.md`
- `references/schema-structured-data.md`
- `references/local-seo.md`
- `references/geo-aeo.md`
- `references/off-page-authority.md`
- `references/measurement-kpis.md`
- `references/scope-patterns.md`
- `references/mobile-render-checklist.md`
- `references/reporting-checklist.md`
