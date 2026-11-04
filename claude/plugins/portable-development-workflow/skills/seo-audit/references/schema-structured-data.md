# Schema Markup & Structured Data Reference

## Overview

Structured data is standardized, machine-readable markup that describes what page content means. It can help search engines and other systems understand entities, page purpose, relationships, and eligibility for supported search features.

Use structured data as an accuracy and clarity layer, not as a ranking shortcut. It should describe visible, verifiable content and should be checked against current platform documentation before implementation.

## Key Concepts

- **Structured data**: The concept of organizing information in a machine-readable way
- **Schema (Schema.org)**: The vocabulary defining entities like Article, Product, FAQ, LocalBusiness
- **JSON-LD**: The format most commonly used to implement schema (Google's recommended format)
- **Rich results**: Enhanced search listings (star ratings, FAQs, product cards, etc.) powered by schema

## Why Structured Data Matters

1. **Entity clarity.** Structured data helps systems understand the organization, person, product, service, article, event, location, or other entity represented by a page.

2. **Feature eligibility.** Some search features require specific structured data and policy compliance. Support changes, so verify current documentation before promising a result.

3. **Content disambiguation.** Markup can reduce confusion between similar brands, products, locations, authors, services, and page types.

4. **Reuse and consistency.** Template-level markup can keep repeated business, author, product, breadcrumb, and page information consistent.

5. **Validation discipline.** Structured data forces claims to be explicit and testable.

## Implementation Format: JSON-LD

Always use JSON-LD (JavaScript Object Notation for Linked Data). It's:
- Separate from HTML, so it doesn't affect layout
- Scales better for large sites
- Easier to debug and update
- Supported by major search platforms for many use cases, though exact feature support varies

Place JSON-LD in a `<script type="application/ld+json">` tag, typically in the `<head>` or end of `<body>`.

## Schema Selection Model

Do not apply a fixed schema checklist to every project. Select schema by asking:

1. What entity or entities are actually on this page?
2. Which claims are visible and substantiated in the user-facing content?
3. Which search features or downstream consumers matter for this project?
4. Which schema types and properties are currently supported by the relevant platform docs?
5. Can the project keep this data accurate over time?

Common candidates include:

- **Organization / LocalBusiness / Person** for real-world entity identity.
- **WebSite / WebPage / BreadcrumbList** for site and page context.
- **Article / BlogPosting / NewsArticle** for editorial content.
- **Product / Offer / AggregateRating / Review** only when product, pricing, availability, rating, and review claims are visible and accurate.
- **Service** for service pages when the service is clearly described.
- **FAQPage / HowTo / Event / VideoObject / JobPosting / Recipe / Dataset** only when the page genuinely contains that content and current platform docs support the intended use.

When a project already has a schema strategy, follow that project strategy first.

## Implementation Examples

### Organization Schema
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://www.example.com",
  "logo": "https://www.example.com/logo.png",
  "description": "Brief company description with key services",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "City",
    "addressRegion": "ST",
    "postalCode": "12345",
    "addressCountry": "US"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-123-4567",
    "contactType": "customer service"
  },
  "sameAs": [
    "https://www.linkedin.com/company/example",
    "https://www.facebook.com/example",
    "https://twitter.com/example"
  ]
}
```

### LocalBusiness Schema
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Company Name",
  "url": "https://www.example.com",
  "telephone": "+1-555-123-4567",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "City",
    "addressRegion": "ST",
    "postalCode": "75024",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "00.0000",
    "longitude": "00.0000"
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
      "opens": "08:00",
      "closes": "17:00"
    }
  ],
  "areaServed": {
    "@type": "City",
    "name": "Primary service area"
  },
  "priceRange": "$$"
}
```

### Article Schema
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title Here",
  "author": {
    "@type": "Person",
    "name": "Author Name",
    "jobTitle": "Title",
    "url": "https://www.example.com/about/author-name"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Company Name",
    "logo": {
      "@type": "ImageObject",
      "url": "https://www.example.com/logo.png"
    }
  },
  "datePublished": "YYYY-MM-DD",
  "dateModified": "YYYY-MM-DD",
  "image": "https://www.example.com/images/article-image.jpg",
  "description": "Brief article description for search results"
}
```

### FAQ Schema
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is [service or topic]?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Provide a concise answer that matches the visible page content."
      }
    },
    {
      "@type": "Question",
      "name": "How much does [service or product] cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Only include pricing ranges if the page visibly supports them and they are accurate for the project."
      }
    }
  ]
}
```

### Service Schema
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Service Name",
  "description": "Short description of the service that matches the visible page content.",
  "provider": {
    "@type": "Organization",
    "name": "Company Name"
  },
  "areaServed": {
    "@type": "City",
    "name": "Target market"
  },
  "serviceType": "Service category"
}
```

## Validation & Testing

### Before Publishing — Always Validate
1. Write or generate the schema
2. Test with **Google Rich Results Test** (https://search.google.com/test/rich-results)
3. Test with **Schema Markup Validator** (https://validator.schema.org/)
4. Fix all errors and warnings
5. Re-test before publishing
6. After indexing, monitor **Google Search Console > Enhancements** for issues

### Common Validation Errors
- Missing required properties (e.g., Article without author)
- Invalid JSON syntax (missing brackets, commas, quotes)
- Markup that doesn't match visible page content
- Using deprecated schema types
- Incorrect nesting of schema objects

## Best Practices

1. **Accuracy is mandatory.** Schema must reflect what's actually visible on the page. Don't mark up reviews that don't exist, claim ratings you don't have, or fabricate information.

2. **Start with high-value pages.** Don't try to schema every page at once. Prioritize: homepage, service pages, location pages, key blog posts, about page.

3. **Use the most accurate specific type.** Prefer a precise subtype only when it truly fits the visible content and current platform guidance.

4. **Keep it updated.** When business hours, prices, services, or other information changes, update schema markup accordingly.

5. **Don't stack conflicting schema.** One page shouldn't have both Product and Service schema unless it genuinely offers both.

6. **Implement at template level.** For CMS-based sites, add schema to page templates so it applies consistently across all pages of that type.

7. **Monitor performance.** Track which pages show rich results, CTR changes, and any enhancement errors in Search Console.

## Current Support And Validation

Search engines periodically add, remove, or change support for structured data features. Before recommending or implementing a type for a rich-result goal:

1. Check the current documentation for the target platform.
2. Confirm that the page visibly contains the required content.
3. Validate syntax and required/recommended properties.
4. Avoid promising that markup will produce a rich result; search engines choose when to show enhancements.

Unsupported or deprecated markup usually does not create a direct penalty by itself, but stale markup creates maintenance noise and can mislead future implementers. Remove or update it during routine SEO maintenance.

## Schema and AI Systems

Structured data can help AI and search systems understand content, but it is not a substitute for visible, accurate page copy:

- Entity markup can clarify organizations, people, products, locations, and services.
- FAQ or HowTo markup may help where those formats are visible and supported.
- Structured data should align with on-page content, internal links, business data, and external entity profiles.
- It does not prevent systems from making errors; it simply gives them cleaner signals.

The goal is not "more schema." The goal is accurate, maintainable structured data that makes the page easier to understand.
