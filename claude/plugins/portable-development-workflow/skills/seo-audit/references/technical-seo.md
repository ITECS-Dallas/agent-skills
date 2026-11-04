# Technical SEO Reference

## Overview

Technical SEO is the foundation that supports all other SEO efforts. If search engines can't crawl, render, index, and rank pages correctly, no amount of content or link building will compensate. The goal is to make important pages crawlable, renderable, indexable, fast, secure, and machine-readable.

A technical audit asks: "Can search systems discover, render, understand, and trust this page?"

## Crawlability & Indexing

### robots.txt
- Verify important pages, CSS, and JavaScript files are not accidentally blocked
- Include sitemap reference: `Sitemap: https://example.com/sitemap.xml`
- Test changes in Google Search Console before deploying
- Common mistake: blocking CSS/JS files prevents Google from rendering pages properly

### XML Sitemaps
- Submit to the webmaster tools that matter for the target market, commonly Google Search Console and Bing Webmaster Tools
- Include only indexable, canonical URLs (no redirects, no noindexed pages, no 404s)
- Keep sitemaps under 50,000 URLs / 50MB per file; use sitemap index for larger sites
- Include `<lastmod>` dates and keep them accurate (not auto-generated)
- For Bing specifically: use the IndexNow API for faster indexing of new/updated content

### Index Coverage
- Monitor Google Search Console "Pages" report regularly for errors, warnings, exclusions
- Compare submitted sitemap URLs against indexed pages — gaps indicate problems
- Audit noindex directives and URL parameters to prevent accidental deindexation
- Review URL depth: important pages should be reachable within 3 clicks from homepage

### Crawl Budget
- For most small-to-medium sites, crawl budget is not a concern — focus on sitemap health and indexing
- For large sites (100K+ pages): eliminate crawl waste from faceted navigation, parameter URLs, thin pages
- Log file analysis reveals how search engine bots actually crawl your site vs. how you expect them to
- Consolidate duplicate content, eliminate redirect chains, and prune low-value pages

### Canonical Tags
- Every page should have a self-referencing canonical tag
- Use canonical tags to consolidate duplicate or near-duplicate content
- Canonical signals are hints, not directives — conflicting signals (canonical says X, sitemap includes Y) cause confusion
- Common mistakes: canonicalizing paginated pages to page 1, pointing canonicals to redirected URLs

## Core Web Vitals & Page Performance

### The Core Metrics
- **Largest Contentful Paint (LCP)**: Should be ≤2.5 seconds. Measures loading performance — how fast the main content loads. Common fixes: optimize images (WebP/AVIF, proper sizing, lazy loading), implement CDN, reduce server response time (TTFB), preload critical resources.
- **Interaction to Next Paint (INP)**: Should be ≤200ms. Replaced FID in 2024. Measures responsiveness throughout the entire page lifecycle. Common fixes: break up long JavaScript tasks, defer non-critical scripts, optimize event handlers, reduce DOM size.
- **Cumulative Layout Shift (CLS)**: Should be ≤0.1. Measures visual stability. Common fixes: set explicit dimensions on images/videos/ads, reserve space for dynamic content, avoid inserting content above existing content.

### Performance Optimization
- Target fast, stable loading appropriate to the audience, device mix, and market; use field data when available
- Compress images (use WebP/AVIF), defer non-critical JavaScript, minimize CSS
- Implement CDN for geographic distribution
- Server response time (TTFB): aim for <800ms; consider hosting that matches your target geo
- Enable browser caching with appropriate cache headers
- Reduce render-blocking resources: inline critical CSS, defer non-essential scripts
- Lazy load images and videos below the fold

### Hosting & Infrastructure
- Choose hosting that matches your primary target geography
- Use reputable hosting and monitor uptime, DNS, TLS, and server errors
- HTTPS is a baseline trust and security requirement
- HTTP/2 or HTTP/3 for multiplexing and faster connections

## Mobile Optimization

- Google uses mobile-first indexing — your mobile site IS your primary site
- Test real mobile layouts, tap targets, font sizes, and rendered content because mobile indexing and mobile usage are central for many markets
- Ensure responsive design, readable fonts (16px+ base), adequate tap targets (48px+ minimum)
- Avoid interstitials that block content on mobile
- Test with Google's Mobile-Friendly Test and real device testing
- Check mobile vs. desktop SERP features weekly — they often differ

## Site Architecture & URL Structure

- Flat, logical hierarchy: important pages within 3 clicks of homepage
- Clear URL structure reflecting content hierarchy: `/services/managed-it/` not `/page?id=347`
- Use descriptive, keyword-relevant URLs — keep them concise
- Implement breadcrumb navigation with BreadcrumbList schema
- Ensure consistent internal linking that distributes authority to important pages
- Avoid orphan pages (pages with no internal links pointing to them)

## Redirect Management
- Use 301 redirects for permanent moves, 308 for permanent with method preservation
- Eliminate redirect chains (A → B → C; should be A → C directly)
- Maximum 1 redirect hop
- Audit old redirects periodically — remove those no longer needed
- After site migrations, monitor 404s aggressively for 6+ months

## JavaScript & Rendering
- Google can render JavaScript, but it's a two-phase process (crawl, then render) that can delay indexing
- Critical content should be in initial HTML when possible
- Use server-side rendering (SSR) or pre-rendering for JavaScript-heavy sites
- Test rendering with Google's URL Inspection tool and "View Rendered Page"
- Ensure Googlebot isn't blocked from JS/CSS resources in robots.txt

## Security
- HTTPS everywhere — no mixed content warnings
- Implement HSTS headers
- Monitor Google Search Console for security issues and manual actions
- Keep CMS, plugins, and server software updated
- Implement Content Security Policy (CSP) headers

## International SEO (if applicable)
- Use hreflang tags correctly for multi-language/multi-region sites
- Choose appropriate URL structure: subdirectories (/en/), subdomains (en.example.com), or ccTLDs
- Ensure each language version has unique, translated content — not just auto-translated
- Submit separate sitemaps per language/region

## Audit Frequency
- Full technical audit: quarterly minimum
- Core Web Vitals monitoring: monthly
- Index coverage review: weekly
- Post-migration/redesign: immediate full audit
- After major CMS or plugin updates: immediate spot check

## Tools
- **Google Search Console**: Free, essential — indexing, crawl errors, CWV, structured data, manual actions
- **Bing Webmaster Tools**: Free — important for Bing-specific indexing and diagnostics
- **Screaming Frog SEO Spider**: Desktop crawler for comprehensive site audits
- **Google PageSpeed Insights / Lighthouse**: CWV and performance analysis
- **GTmetrix / WebPageTest**: Detailed waterfall analysis and performance testing
- **Ahrefs or Semrush**: All-in-one platforms with site audit, backlink analysis, keyword research
- **Log file analyzers**: Screaming Frog Log Analyzer, Botify, or custom solutions
