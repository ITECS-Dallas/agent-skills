#!/usr/bin/env python3
import argparse
import csv
import json
import re
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup


TIMEOUT = (10, 20)
GOOGLEBOT_DESKTOP_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
GOOGLEBOT_SMARTPHONE_UA = (
    "Mozilla/5.0 (Linux; Android 12; Pixel 5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Mobile Safari/537.36 "
    "(compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)
UA_PROFILES = {
    "googlebot-smartphone": GOOGLEBOT_SMARTPHONE_UA,
    "googlebot-desktop": GOOGLEBOT_DESKTOP_UA,
}
NON_HTML_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".zip",
    ".xml",
    ".css",
    ".js",
    ".json",
    ".txt",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".ico",
    ".mp4",
    ".webm",
    ".mp3",
    ".mov",
    ".avi",
)
HTML_LIKE_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
EMAIL_PROTECTION_RE = re.compile(r"^/cdn-cgi/l/email-protection", re.I)
FRAMEWORK_ASSET_MARKERS = (
    "/_next/",
    "/cdn-cgi/",
    "/_vercel/",
    "/static/",
    "/build/",
    "/dist/",
)
NOINDEX_RECOMMENDED_CONTENT_TYPE_HINTS = (
    "javascript",
    "ecmascript",
    "css",
    "json",
    "font/",
    "wasm",
)


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_url(url: str, keep_query: bool = False) -> str:
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query = parsed.query if keep_query else ""
    return urlunparse((scheme, netloc, path, "", query, ""))


def page_like_url(url: str) -> bool:
    parsed = urlparse(url)
    path = (parsed.path or "/").lower()
    return not path.endswith(NON_HTML_EXTENSIONS)


def looks_like_html_content_type(content_type: str) -> bool:
    lowered = (content_type or "").lower()
    return any(item in lowered for item in HTML_LIKE_CONTENT_TYPES)


def framework_asset_url(url: str) -> bool:
    path = (urlparse(url).path or "/").lower()
    return any(marker in path for marker in FRAMEWORK_ASSET_MARKERS)


def asset_requires_noindex(url: str, content_type: str) -> bool:
    lowered = (content_type or "").lower()
    if framework_asset_url(url):
        return True
    return any(hint in lowered for hint in NOINDEX_RECOMMENDED_CONTENT_TYPE_HINTS)


def meta_content(soup: BeautifulSoup, attr: str, value: str) -> str:
    node = soup.find("meta", attrs={attr: value})
    if node and node.get("content"):
        return clean_text(node["content"])
    return ""


def visible_text(node: BeautifulSoup) -> str:
    clone = BeautifulSoup(str(node), "html.parser")
    for tag in clone(["script", "style", "noscript", "template", "svg", "iframe"]):
        tag.decompose()
    return clean_text(clone.get_text(" ", strip=True))


def word_count(text: str) -> int:
    return len(re.findall(r"[a-z0-9']+", text.lower()))


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def parse_srcset(srcset: str) -> List[str]:
    urls = []
    for part in srcset.split(","):
        candidate = part.strip().split(" ")[0].strip()
        if candidate:
            urls.append(candidate)
    return urls


def extract_schema_types(raw_text: str) -> List[str]:
    found: List[str] = []

    def walk(node):
        if isinstance(node, dict):
            node_type = node.get("@type")
            if isinstance(node_type, list):
                for item in node_type:
                    found.append(clean_text(str(item)))
            elif node_type:
                found.append(clean_text(str(node_type)))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    try:
        payload = json.loads(raw_text)
    except Exception:
        return []
    walk(payload)
    return [item for item in dedupe_preserve_order(found) if item]


def extract_streamed_jsonld_blocks(html_text: str) -> List[str]:
    blocks = []
    pattern = re.compile(
        r'"type":"application/ld\+json","children":"((?:\\.|[^"])*)"',
        re.S,
    )
    for match in pattern.finditer(html_text):
        raw = match.group(1)
        try:
            decoded = json.loads(f'"{raw}"')
        except Exception:
            continue
        decoded = decoded.strip()
        if decoded:
            blocks.append(decoded)
    return dedupe_preserve_order(blocks)


def classify_page_type(path: str) -> str:
    if path in {"", "/"}:
        return "homepage"
    if path in {"/blog", "/blogs", "/post", "/posts", "/articles", "/news"}:
        return "blog_index"
    if path.startswith(("/blog/", "/blogs/", "/post/", "/posts/", "/articles/", "/news/")):
        return "blog_post"
    if path in {"/resources", "/resource-center", "/whitepapers", "/case-studies", "/white-papers-case-studies"}:
        return "resources_index"
    if path.startswith(("/resources/", "/resource-center/", "/whitepapers/", "/case-studies/", "/white-papers-case-studies/")):
        return "resource"
    if path.startswith(("/locations/", "/location/", "/service-areas/", "/areas-served/")):
        return "service_area"
    if path.startswith(("/industries/", "/industry/", "/verticals/")):
        return "industry"
    if path.startswith(("/services/", "/service/", "/solutions/", "/solution/", "/products/", "/product/")):
        return "service"
    if path in {
        "/contact",
        "/contact-us",
        "/about",
        "/about-us",
        "/careers",
        "/faq",
        "/faqs",
        "/leadership",
        "/privacy-policy",
        "/privacy",
        "/terms",
        "/terms-of-service",
    }:
        return "utility"
    return "page"


def url_flags(url: str) -> List[str]:
    parsed = urlparse(url)
    path = parsed.path or "/"
    flags = []
    if parsed.query:
        flags.append("query")
    if parsed.fragment:
        flags.append("fragment")
    if "%" in path:
        flags.append("encoded")
    if any(ch.isupper() for ch in path):
        flags.append("uppercase")
    if "//" in path.replace("://", ":/"):
        flags.append("double-slash")
    if " " in path or "+" in path:
        flags.append("space-or-plus")
    if EMAIL_PROTECTION_RE.search(path):
        flags.append("cloudflare-email-protection")
    return flags


@dataclass
class SitemapEntry:
    loc: str
    source_sitemap: str
    lastmod: str = ""
    changefreq: str = ""
    priority: str = ""


@dataclass
class CrawlContext:
    in_sitemap: bool = False
    sitemap_sources: Set[str] = field(default_factory=set)
    discovered_from: Set[str] = field(default_factory=set)
    depth: Optional[int] = None


@dataclass
class RedirectCheck:
    start_url: str
    final_url: str
    final_status: int
    redirect_count: int
    chain: List[Dict[str, object]]


class PublicSiteAuditor:
    def __init__(
        self,
        base_url: str,
        output_slug: str,
        max_pages: int,
        asset_sample_size: int,
        user_agent_profile: str,
        crawl_delay_override: Optional[float] = None,
        include_regexes: Optional[List[str]] = None,
        exclude_regexes: Optional[List[str]] = None,
        sitemap_non_html_probe_limit: int = 50,
    ):
        self.base_url = normalize_url(base_url)
        self.base_parsed = urlparse(self.base_url)
        self.output_slug = output_slug
        self.max_pages = max_pages
        self.asset_sample_size = asset_sample_size
        self.user_agent_profile = user_agent_profile
        self.user_agent = UA_PROFILES[user_agent_profile]
        self.robots_token = "Googlebot"
        self.sitemap_non_html_probe_limit = sitemap_non_html_probe_limit
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self.last_request_at = 0.0
        self.robots = RobotFileParser()
        self.robots_url = urljoin(self.base_url + "/", "robots.txt")
        self.robots_text = ""
        self.robots_status = None
        self.crawl_delay_override = crawl_delay_override
        self.crawl_delay = 0.0
        self.include_regexes = [re.compile(pattern) for pattern in (include_regexes or [])]
        self.exclude_regexes = [re.compile(pattern) for pattern in (exclude_regexes or [])]

        self.allowed_hosts = {
            self.base_parsed.netloc.lower(),
        }
        if self.base_parsed.netloc.startswith("www."):
            self.allowed_hosts.add(self.base_parsed.netloc[4:])
        else:
            self.allowed_hosts.add(f"www.{self.base_parsed.netloc}")

        self.sitemap_entries: Dict[str, SitemapEntry] = {}
        self.sitemaps_seen: Set[str] = set()
        self.sitemap_fetches: List[Dict[str, object]] = []
        self.page_context: Dict[str, CrawlContext] = defaultdict(CrawlContext)
        self.pages: Dict[str, Dict[str, object]] = {}
        self.link_edges: List[Dict[str, object]] = []
        self.asset_edges: List[Dict[str, object]] = []
        self.sampled_assets: List[Dict[str, object]] = []
        self.sitemap_non_html_probes: List[Dict[str, object]] = []
        self.host_variant_checks: List[Dict[str, object]] = []
        self.blocked_urls: Dict[str, Dict[str, object]] = {}
        self.fetch_errors: List[Dict[str, str]] = []
        self.request_count = 0

    def internal_url(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return host in self.allowed_hosts

    def url_in_scope(self, url: str) -> bool:
        normalized = normalize_url(url)
        path = urlparse(normalized).path or "/"
        targets = (normalized, path)
        if self.include_regexes and not any(
            pattern.search(target) for pattern in self.include_regexes for target in targets
        ):
            return False
        if any(pattern.search(target) for pattern in self.exclude_regexes for target in targets):
            return False
        return True

    def robots_allows(self, url: str) -> bool:
        return self.robots.can_fetch(self.robots_token, url)

    def throttle(self):
        delay = self.crawl_delay_override if self.crawl_delay_override is not None else self.crawl_delay
        if not delay:
            return
        elapsed = time.time() - self.last_request_at
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def fetch(self, url: str, allow_redirects: bool = True, stream: bool = False) -> Tuple[requests.Response, float]:
        self.throttle()
        started = time.time()
        response = self.session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=allow_redirects,
            stream=stream,
        )
        elapsed_ms = round((time.time() - started) * 1000, 1)
        self.last_request_at = time.time()
        self.request_count += 1
        return response, elapsed_ms

    def load_robots(self):
        response, _ = self.fetch(self.robots_url)
        response.raise_for_status()
        self.robots_status = response.status_code
        self.robots_text = response.text
        self.robots.parse(response.text.splitlines())
        parsed_delay = self.robots.crawl_delay(self.robots_token)
        if parsed_delay is None:
            parsed_delay = self.robots.crawl_delay("*")
        self.crawl_delay = float(parsed_delay or 0)

    def fetch_redirect_chain(self, url: str, max_hops: int = 10) -> RedirectCheck:
        current = normalize_url(url, keep_query=True)
        seen = set()
        chain: List[Dict[str, object]] = []

        for _ in range(max_hops):
            response, elapsed_ms = self.fetch(current, allow_redirects=False)
            location = clean_text(response.headers.get("Location", ""))
            chain.append(
                {
                    "url": current,
                    "status": response.status_code,
                    "location": location,
                    "elapsed_ms": elapsed_ms,
                }
            )
            if not (300 <= response.status_code < 400 and location):
                return RedirectCheck(
                    start_url=normalize_url(url),
                    final_url=normalize_url(current, keep_query=True),
                    final_status=response.status_code,
                    redirect_count=max(0, len(chain) - 1),
                    chain=chain,
                )

            next_url = normalize_url(urljoin(current, location), keep_query=True)
            if next_url in seen:
                chain.append(
                    {
                        "url": next_url,
                        "status": "loop",
                        "location": "",
                        "elapsed_ms": 0,
                    }
                )
                return RedirectCheck(
                    start_url=normalize_url(url),
                    final_url=next_url,
                    final_status=0,
                    redirect_count=max(0, len(chain) - 1),
                    chain=chain,
                )

            seen.add(current)
            current = next_url

        return RedirectCheck(
            start_url=normalize_url(url),
            final_url=current,
            final_status=0,
            redirect_count=max(0, len(chain) - 1),
            chain=chain,
        )

    def check_host_variants(self):
        bare_host = self.base_parsed.netloc[4:] if self.base_parsed.netloc.startswith("www.") else self.base_parsed.netloc
        www_host = self.base_parsed.netloc if self.base_parsed.netloc.startswith("www.") else f"www.{self.base_parsed.netloc}"
        variants = dedupe_preserve_order(
            [
                f"http://{bare_host}/",
                f"https://{bare_host}/",
                f"http://{www_host}/",
                f"https://{www_host}/",
            ]
        )
        self.host_variant_checks = [check.__dict__ for check in (self.fetch_redirect_chain(url) for url in variants)]

    def discover_sitemaps(self) -> List[str]:
        declared = []
        for line in self.robots_text.splitlines():
            if line.lower().startswith("sitemap:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    declared.append(value)
        declared.append(urljoin(self.base_url + "/", "sitemap.xml"))
        return dedupe_preserve_order(declared)

    def parse_sitemap(self, xml_text: str, source_sitemap: str) -> Tuple[List[str], List[SitemapEntry]]:
        root = ET.fromstring(xml_text)
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        indexes = []
        entries = []
        if root.tag.endswith("sitemapindex"):
            for node in root.findall("sm:sitemap", namespace):
                loc = node.findtext("sm:loc", default="", namespaces=namespace)
                if loc:
                    indexes.append(clean_text(loc))
        else:
            for node in root.findall("sm:url", namespace):
                loc = clean_text(node.findtext("sm:loc", default="", namespaces=namespace))
                if not loc:
                    continue
                entries.append(
                    SitemapEntry(
                        loc=loc,
                        source_sitemap=source_sitemap,
                        lastmod=clean_text(node.findtext("sm:lastmod", default="", namespaces=namespace)),
                        changefreq=clean_text(node.findtext("sm:changefreq", default="", namespaces=namespace)),
                        priority=clean_text(node.findtext("sm:priority", default="", namespaces=namespace)),
                    )
                )
        return indexes, entries

    def collect_sitemaps(self):
        queue = deque(self.discover_sitemaps())
        while queue:
            sitemap_url = normalize_url(queue.popleft())
            if sitemap_url in self.sitemaps_seen:
                continue
            self.sitemaps_seen.add(sitemap_url)
            try:
                response, elapsed_ms = self.fetch(sitemap_url)
                payload = {
                    "url": sitemap_url,
                    "status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "elapsed_ms": elapsed_ms,
                }
                self.sitemap_fetches.append(payload)
                if response.status_code >= 400:
                    continue
                indexes, entries = self.parse_sitemap(response.text, sitemap_url)
                queue.extend(indexes)
                for entry in entries:
                    normalized = normalize_url(entry.loc)
                    if not self.url_in_scope(normalized):
                        continue
                    if normalized in self.sitemap_entries:
                        self.sitemap_entries[normalized].source_sitemap = entry.source_sitemap
                        continue
                    self.sitemap_entries[normalized] = entry
                    ctx = self.page_context[normalized]
                    ctx.in_sitemap = True
                    ctx.sitemap_sources.add(entry.source_sitemap)
            except Exception as exc:
                self.fetch_errors.append({"url": sitemap_url, "error": str(exc)})

    def probe_sitemap_non_html_entries(self):
        non_html_urls = [url for url in sorted(self.sitemap_entries.keys()) if not page_like_url(url)]
        for url in non_html_urls[: self.sitemap_non_html_probe_limit]:
            try:
                response, elapsed_ms = self.fetch(url, stream=True)
                record = {
                    "url": url,
                    "final_url": response.url,
                    "status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "x_robots_tag": clean_text(response.headers.get("X-Robots-Tag", "")),
                    "cache_control": response.headers.get("Cache-Control", ""),
                    "framework_asset": framework_asset_url(url),
                    "requires_noindex": asset_requires_noindex(url, response.headers.get("Content-Type", "")),
                    "elapsed_ms": elapsed_ms,
                    "flags": ",".join(url_flags(url)),
                }
                self.sitemap_non_html_probes.append(record)
                response.close()
            except Exception as exc:
                self.sitemap_non_html_probes.append({"url": url, "error": str(exc)})

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[Dict[str, object]]:
        links = []
        for anchor in soup.select("a[href]"):
            raw_href = anchor.get("href", "").strip()
            if not raw_href or raw_href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(current_url, raw_href)
            if not absolute.startswith("http"):
                continue
            normalized = normalize_url(absolute, keep_query=True)
            links.append(
                {
                    "href": normalized,
                    "text": clean_text(anchor.get_text(" ", strip=True)),
                    "rel": [item.lower() for item in anchor.get("rel", [])],
                    "internal": self.internal_url(normalized),
                    "flags": url_flags(normalized),
                }
            )
        return links

    def extract_assets(self, soup: BeautifulSoup, current_url: str) -> List[Dict[str, object]]:
        assets = []
        for script in soup.select("script[src]"):
            src = script.get("src", "").strip()
            if src:
                absolute = urljoin(current_url, src)
                assets.append(
                    {
                        "url": normalize_url(absolute, keep_query=True),
                        "kind": "script",
                        "source_attr": "src",
                        "internal": self.internal_url(absolute),
                    }
                )
        for link in soup.select("link[href]"):
            href = link.get("href", "").strip()
            if not href:
                continue
            rel_tokens = [item.lower() for item in link.get("rel", [])]
            kind = "link"
            if "stylesheet" in rel_tokens:
                kind = "stylesheet"
            elif "icon" in rel_tokens or "apple-touch-icon" in rel_tokens:
                kind = "icon"
            elif "preload" in rel_tokens:
                kind = f"preload:{clean_text(link.get('as', 'unknown')) or 'unknown'}"
            absolute = urljoin(current_url, href)
            assets.append(
                {
                    "url": normalize_url(absolute, keep_query=True),
                    "kind": kind,
                    "source_attr": "href",
                    "internal": self.internal_url(absolute),
                }
            )
        for image in soup.select("img[src]"):
            src = image.get("src", "").strip()
            if src:
                absolute = urljoin(current_url, src)
                assets.append(
                    {
                        "url": normalize_url(absolute, keep_query=True),
                        "kind": "image",
                        "source_attr": "src",
                        "internal": self.internal_url(absolute),
                        "alt": clean_text(image.get("alt", "")),
                    }
                )
            for candidate in parse_srcset(image.get("srcset", "")):
                absolute = urljoin(current_url, candidate)
                assets.append(
                    {
                        "url": normalize_url(absolute, keep_query=True),
                        "kind": "image:srcset",
                        "source_attr": "srcset",
                        "internal": self.internal_url(absolute),
                        "alt": clean_text(image.get("alt", "")),
                    }
                )
        for source in soup.select("source[srcset]"):
            for candidate in parse_srcset(source.get("srcset", "")):
                absolute = urljoin(current_url, candidate)
                assets.append(
                    {
                        "url": normalize_url(absolute, keep_query=True),
                        "kind": "source:srcset",
                        "source_attr": "srcset",
                        "internal": self.internal_url(absolute),
                    }
                )
        deduped = []
        seen = set()
        for asset in assets:
            key = (asset["url"], asset["kind"], asset["source_attr"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(asset)
        return deduped

    def extract_schema(self, soup: BeautifulSoup, html_text: str) -> Tuple[int, List[str]]:
        raw_blocks = []
        for script in soup.select('script[type="application/ld+json"]'):
            raw = (script.string or script.get_text() or "").strip()
            if raw:
                raw_blocks.append(raw)
        raw_blocks.extend(extract_streamed_jsonld_blocks(html_text))

        schema_types = []
        for raw in dedupe_preserve_order(raw_blocks):
            schema_types.extend(extract_schema_types(raw))
        schema_types = dedupe_preserve_order(item for item in schema_types if item)
        return len(dedupe_preserve_order(raw_blocks)), schema_types

    def analyze_html_page(
        self,
        seed_url: str,
        response: requests.Response,
        elapsed_ms: float,
        ctx: CrawlContext,
    ) -> Dict[str, object]:
        soup = BeautifulSoup(response.text, "html.parser")
        title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
        canonical_node = soup.select_one("link[rel=canonical]")
        canonical = clean_text(canonical_node.get("href", "")) if canonical_node else ""
        meta_robots = meta_content(soup, "name", "robots")
        meta_description = meta_content(soup, "name", "description")
        meta_viewport = meta_content(soup, "name", "viewport")
        h1s = [clean_text(node.get_text(" ", strip=True)) for node in soup.find_all("h1")]
        h2s = [clean_text(node.get_text(" ", strip=True)) for node in soup.find_all("h2")]
        jsonld_count, schema_types = self.extract_schema(soup, response.text)
        links = self.extract_links(soup, response.url)
        assets = self.extract_assets(soup, response.url)
        text = visible_text(soup.body or soup)
        x_robots = clean_text(response.headers.get("X-Robots-Tag", ""))
        final_normalized = normalize_url(response.url)
        canonical_normalized = normalize_url(canonical) if canonical else ""
        noindex = "noindex" in meta_robots.lower() or "noindex" in x_robots.lower()
        robots_allowed = self.robots_allows(seed_url)
        soft_404_signals = ("404", "page not found", "article not found", "not found")
        soft_404 = response.status_code == 200 and any(
            term in f"{title} {' '.join(h1s)}".lower() for term in soft_404_signals
        )

        page = {
            "url": seed_url,
            "final_url": response.url,
            "normalized_final_url": final_normalized,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": response.headers.get("Content-Length", ""),
            "cache_control": response.headers.get("Cache-Control", ""),
            "x_robots_tag": x_robots,
            "meta_robots": meta_robots,
            "robots_allowed": robots_allowed,
            "canonical": canonical,
            "canonical_mismatch": bool(canonical_normalized and canonical_normalized != final_normalized),
            "title": title,
            "title_length": len(title),
            "meta_description": meta_description,
            "meta_description_length": len(meta_description),
            "meta_viewport": meta_viewport,
            "h1s": h1s,
            "h2s": h2s[:10],
            "h1_count": len(h1s),
            "word_count": word_count(text),
            "html_lang": clean_text((soup.html or {}).get("lang", "")) if soup.html else "",
            "links": links,
            "link_count": len(links),
            "internal_link_count": sum(1 for link in links if link["internal"]),
            "assets": assets,
            "asset_count": len(assets),
            "jsonld_count": jsonld_count,
            "schema_types": schema_types,
            "page_type": classify_page_type(urlparse(final_normalized).path),
            "in_sitemap": ctx.in_sitemap,
            "sitemap_sources": sorted(ctx.sitemap_sources),
            "discovered_from": sorted(ctx.discovered_from),
            "depth": ctx.depth,
            "flags": url_flags(seed_url),
            "noindex": noindex,
            "indexable": (
                response.status_code == 200
                and looks_like_html_content_type(response.headers.get("Content-Type", ""))
                and robots_allowed
                and not noindex
            ),
            "next_stream_markers": {
                "has_next_flight": "self.__next_f.push" in response.text,
                "has_rsc_markers": "<!--$" in response.text,
            },
            "soft_404": soft_404,
            "redirect_count": len(response.history),
        }
        return page

    def crawl_pages(self):
        seeds = [normalize_url(self.base_url)]
        seeds.extend(sorted(self.sitemap_entries.keys()))
        queue = deque(dedupe_preserve_order(seeds))
        crawled = 0

        while queue and crawled < self.max_pages:
            seed_url = normalize_url(queue.popleft())
            if seed_url in self.pages:
                continue

            ctx = self.page_context[seed_url]
            if not ctx.depth and seed_url == normalize_url(self.base_url):
                ctx.depth = 0

            if not self.internal_url(seed_url):
                continue
            if not self.url_in_scope(seed_url):
                continue
            if not page_like_url(seed_url):
                continue
            if not self.robots_allows(seed_url):
                self.blocked_urls[seed_url] = {
                    "url": seed_url,
                    "reason": "robots",
                    "in_sitemap": ctx.in_sitemap,
                    "discovered_from": sorted(ctx.discovered_from),
                }
                continue

            try:
                response, elapsed_ms = self.fetch(seed_url)
                if not looks_like_html_content_type(response.headers.get("Content-Type", "")):
                    self.blocked_urls[seed_url] = {
                        "url": seed_url,
                        "reason": "non-html-content-type",
                        "status": response.status_code,
                        "content_type": response.headers.get("Content-Type", ""),
                        "in_sitemap": ctx.in_sitemap,
                    }
                    continue
                page = self.analyze_html_page(seed_url, response, elapsed_ms, ctx)
                self.pages[seed_url] = page
                crawled += 1

                for link in page["links"]:
                    edge = {
                        "source": seed_url,
                        "target": link["href"],
                        "internal": link["internal"],
                        "text": link["text"],
                        "rel": " ".join(link["rel"]),
                        "target_flags": ",".join(link["flags"]),
                        "target_robots_allowed": self.robots_allows(link["href"]) if link["internal"] else None,
                    }
                    self.link_edges.append(edge)

                    if not link["internal"]:
                        continue

                    target_norm = normalize_url(link["href"])
                    target_ctx = self.page_context[target_norm]
                    target_ctx.discovered_from.add(seed_url)
                    candidate_depth = (ctx.depth or 0) + 1
                    if target_ctx.depth is None or candidate_depth < target_ctx.depth:
                        target_ctx.depth = candidate_depth

                    if not page_like_url(link["href"]):
                        continue
                    if not self.url_in_scope(link["href"]):
                        continue
                    if urlparse(link["href"]).query or urlparse(link["href"]).fragment:
                        continue
                    if target_norm in self.pages:
                        continue
                    queue.append(target_norm)

                for asset in page["assets"]:
                    asset_edge = {
                        "source": seed_url,
                        "url": asset["url"],
                        "kind": asset["kind"],
                        "internal": asset["internal"],
                        "source_attr": asset["source_attr"],
                    }
                    if "alt" in asset:
                        asset_edge["alt"] = asset["alt"]
                    self.asset_edges.append(asset_edge)
            except Exception as exc:
                self.fetch_errors.append({"url": seed_url, "error": str(exc)})

    def sample_assets(self):
        asset_counter = Counter()
        asset_kind = {}
        asset_sources = defaultdict(set)
        for edge in self.asset_edges:
            if not edge["internal"]:
                continue
            asset_counter[edge["url"]] += 1
            asset_kind[edge["url"]] = edge["kind"]
            asset_sources[edge["url"]].add(edge["source"])

        for url, count in asset_counter.most_common(self.asset_sample_size):
            try:
                response, elapsed_ms = self.fetch(url, stream=True)
                content_type = response.headers.get("Content-Type", "")
                x_robots = response.headers.get("X-Robots-Tag", "")
                record = {
                    "url": url,
                    "final_url": response.url,
                    "kind": asset_kind.get(url, ""),
                    "source_count": len(asset_sources[url]),
                    "status": response.status_code,
                    "content_type": content_type,
                    "x_robots_tag": clean_text(x_robots),
                    "cache_control": response.headers.get("Cache-Control", ""),
                    "framework_asset": framework_asset_url(url),
                    "requires_noindex": asset_requires_noindex(url, content_type),
                    "elapsed_ms": elapsed_ms,
                    "flags": ",".join(url_flags(url)),
                }
                self.sampled_assets.append(record)
                response.close()
            except Exception as exc:
                self.sampled_assets.append(
                    {
                        "url": url,
                        "kind": asset_kind.get(url, ""),
                        "source_count": len(asset_sources[url]),
                        "error": str(exc),
                    }
                )

    def build_issue_rows(self) -> List[Dict[str, object]]:
        issues = []
        titles = defaultdict(list)
        descriptions = defaultdict(list)
        expected_home = normalize_url(urlunparse((self.base_parsed.scheme, self.base_parsed.netloc, "/", "", "", "")))

        for url, page in self.pages.items():
            titles[page["title"]].append(url)
            descriptions[page["meta_description"]].append(url)

            if page["in_sitemap"] and page["status"] >= 400:
                issues.append({"severity": "high", "type": "sitemap_error_url", "url": url, "detail": str(page["status"])})
            if page["in_sitemap"] and page["canonical_mismatch"]:
                issues.append(
                    {
                        "severity": "high",
                        "type": "sitemap_canonical_mismatch",
                        "url": url,
                        "detail": page["canonical"],
                    }
                )
            if page["in_sitemap"] and page["noindex"]:
                issues.append({"severity": "high", "type": "sitemap_noindex", "url": url, "detail": page["meta_robots"] or page["x_robots_tag"]})
            if page["h1_count"] == 0:
                issues.append({"severity": "medium", "type": "missing_h1", "url": url, "detail": page["page_type"]})
            if page["h1_count"] > 1:
                issues.append({"severity": "medium", "type": "multiple_h1", "url": url, "detail": str(page["h1_count"])})
            if not page["meta_description"]:
                issues.append({"severity": "medium", "type": "missing_meta_description", "url": url, "detail": page["page_type"]})
            if not page["canonical"]:
                issues.append({"severity": "medium", "type": "missing_canonical", "url": url, "detail": page["page_type"]})
            if page["indexable"] and not page["meta_viewport"]:
                issues.append({"severity": "medium", "type": "missing_viewport_meta", "url": url, "detail": page["page_type"]})
            if page["soft_404"]:
                issues.append({"severity": "high", "type": "soft_404_pattern", "url": url, "detail": page["title"]})
            if (
                page["soft_404"]
                and not page["in_sitemap"]
                and page["noindex"]
                and not page["canonical"]
            ):
                issues.append(
                    {
                        "severity": "high",
                        "type": "orphan_soft_404_not_found_page",
                        "url": url,
                        "detail": ",".join(page["discovered_from"]),
                    }
                )
            if page["page_type"] == "blog_post" and not any(item in page["schema_types"] for item in ("Article", "BlogPosting", "NewsArticle")):
                issues.append({"severity": "medium", "type": "blog_missing_article_schema", "url": url, "detail": ",".join(page["schema_types"])})
            if page["page_type"] in {"service", "service_area", "industry"} and "Service" not in page["schema_types"]:
                issues.append({"severity": "medium", "type": "service_missing_service_schema", "url": url, "detail": ",".join(page["schema_types"])})
            if page["page_type"] == "resource" and page["jsonld_count"] == 0:
                issues.append({"severity": "low", "type": "resource_missing_structured_data", "url": url, "detail": page["page_type"]})
            if "cloudflare-email-protection" in page["flags"]:
                issues.append({"severity": "high", "type": "email_protection_page_url", "url": url, "detail": "Page URL itself is email-protection link"})

        for sitemap_url in self.sitemap_entries:
            if not page_like_url(sitemap_url):
                issue_type = "sitemap_framework_asset_url" if framework_asset_url(sitemap_url) else "sitemap_non_html_url"
                issues.append({"severity": "high", "type": issue_type, "url": sitemap_url, "detail": self.sitemap_entries[sitemap_url].source_sitemap})

        for title, urls in titles.items():
            if title and len(urls) > 1:
                for url in urls:
                    issues.append({"severity": "medium", "type": "duplicate_title", "url": url, "detail": title})
        for description, urls in descriptions.items():
            if description and len(urls) > 1:
                for url in urls:
                    issues.append({"severity": "low", "type": "duplicate_meta_description", "url": url, "detail": description})

        for blocked in self.blocked_urls.values():
            severity = "high" if blocked.get("in_sitemap") else "medium"
            issues.append(
                {
                    "severity": severity,
                    "type": f"blocked_{blocked['reason']}",
                    "url": blocked["url"],
                    "detail": ",".join(blocked.get("discovered_from", [])),
                }
            )

        for edge in self.link_edges:
            if not edge["internal"]:
                continue
            target = normalize_url(edge["target"])
            if EMAIL_PROTECTION_RE.search(urlparse(target).path):
                issues.append(
                    {
                        "severity": "high",
                        "type": "internal_link_to_cloudflare_email_protection",
                        "url": edge["source"],
                        "detail": edge["target"],
                    }
                )
            target_page = self.pages.get(target)
            if target_page and target_page.get("soft_404"):
                issues.append(
                    {
                        "severity": "high",
                        "type": "internal_link_to_soft_404_page",
                        "url": edge["source"],
                        "detail": edge["target"],
                    }
                )
            if edge["target_robots_allowed"] is False:
                issues.append(
                    {
                        "severity": "medium",
                        "type": "internal_link_to_robots_blocked_url",
                        "url": edge["source"],
                        "detail": edge["target"],
                    }
                )

        for asset in self.sampled_assets:
            if (
                asset.get("status") == 200
                and asset.get("requires_noindex")
                and "noindex" not in (asset.get("x_robots_tag") or "").lower()
            ):
                issue_type = "framework_asset_missing_noindex_header" if asset.get("framework_asset") else "asset_missing_noindex_header"
                issues.append(
                    {
                        "severity": "medium",
                        "type": issue_type,
                        "url": asset["url"],
                        "detail": asset.get("kind", ""),
                    }
                )

        for probe in self.sitemap_non_html_probes:
            if (
                probe.get("status") == 200
                and probe.get("requires_noindex")
                and "noindex" not in (probe.get("x_robots_tag") or "").lower()
            ):
                issues.append(
                    {
                        "severity": "high",
                        "type": "sitemap_non_html_missing_noindex_header",
                        "url": probe["url"],
                        "detail": probe.get("content_type", ""),
                    }
                )

        for check in self.host_variant_checks:
            final_url = normalize_url(check.get("final_url", ""))
            if final_url != expected_home:
                issues.append(
                    {
                        "severity": "high",
                        "type": "host_variant_not_canonical",
                        "url": check.get("start_url", ""),
                        "detail": check.get("final_url", ""),
                    }
                )
            if (check.get("redirect_count") or 0) > 1:
                issues.append(
                    {
                        "severity": "medium",
                        "type": "host_variant_redirect_chain",
                        "url": check.get("start_url", ""),
                        "detail": str(check.get("redirect_count")),
                    }
                )

        deduped = []
        seen = set()
        for issue in issues:
            key = (issue["severity"], issue["type"], issue["url"], issue["detail"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(issue)
        return deduped

    def build_summary(self, issues: List[Dict[str, object]]) -> Dict[str, object]:
        sitemap_urls = list(self.sitemap_entries.keys())
        html_sitemap_urls = [url for url in sitemap_urls if page_like_url(url)]
        non_html_sitemap_urls = [url for url in sitemap_urls if not page_like_url(url)]
        crawled_not_in_sitemap = sorted(url for url in self.pages if not self.page_context[url].in_sitemap)
        issue_counter = Counter(issue["type"] for issue in issues)
        severity_counter = Counter(issue["severity"] for issue in issues)

        return {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "base_url": self.base_url,
            "user_agent_profile": self.user_agent_profile,
            "user_agent": self.user_agent,
            "scope": {
                "include_regexes": [pattern.pattern for pattern in self.include_regexes],
                "exclude_regexes": [pattern.pattern for pattern in self.exclude_regexes],
            },
            "robots_url": self.robots_url,
            "robots_status": self.robots_status,
            "crawl_delay_seconds": self.crawl_delay_override if self.crawl_delay_override is not None else self.crawl_delay,
            "declared_sitemaps": len(self.sitemaps_seen),
            "sitemap_url_count": len(sitemap_urls),
            "sitemap_html_url_count": len(html_sitemap_urls),
            "sitemap_non_html_url_count": len(non_html_sitemap_urls),
            "sitemap_non_html_probe_count": len(self.sitemap_non_html_probes),
            "crawled_page_count": len(self.pages),
            "crawled_not_in_sitemap_count": len(crawled_not_in_sitemap),
            "blocked_url_count": len(self.blocked_urls),
            "internal_link_edge_count": len(self.link_edges),
            "asset_edge_count": len(self.asset_edges),
            "sampled_asset_count": len(self.sampled_assets),
            "host_variant_check_count": len(self.host_variant_checks),
            "fetch_error_count": len(self.fetch_errors),
            "request_count": self.request_count,
            "issue_counts": issue_counter,
            "issue_severity_counts": severity_counter,
            "crawled_not_in_sitemap": crawled_not_in_sitemap[:50],
            "sitemap_non_html_examples": non_html_sitemap_urls[:20],
        }

    def build_output(self) -> Dict[str, object]:
        issues = self.build_issue_rows()
        summary = self.build_summary(issues)
        return {
            "summary": summary,
            "robots": {
                "status": self.robots_status,
                "content": self.robots_text,
            },
            "sitemaps": self.sitemap_fetches,
            "sitemap_entries": [entry.__dict__ for entry in self.sitemap_entries.values()],
            "pages": self.pages,
            "blocked_urls": self.blocked_urls,
            "link_edges": self.link_edges,
            "assets": self.sampled_assets,
            "sitemap_non_html_probes": self.sitemap_non_html_probes,
            "host_variant_checks": self.host_variant_checks,
            "fetch_errors": self.fetch_errors,
            "issues": issues,
        }


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = {}
            for key in fieldnames:
                value = row.get(key, "")
                if isinstance(value, (list, dict, set, tuple)):
                    serialized[key] = json.dumps(value, ensure_ascii=True)
                else:
                    serialized[key] = value
            writer.writerow(serialized)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Public-site crawl and indexability audit.")
    parser.add_argument("--base-url", required=True, help="Canonical base URL, e.g. https://example.com")
    parser.add_argument("--output-slug", default="", help="File slug for outputs, defaults to host name")
    parser.add_argument("--max-pages", type=int, default=500, help="Maximum HTML pages to crawl")
    parser.add_argument("--asset-sample-size", type=int, default=80, help="Number of internal assets to sample")
    parser.add_argument(
        "--user-agent-profile",
        choices=sorted(UA_PROFILES.keys()),
        default="googlebot-smartphone",
        help="Crawler user-agent profile to emulate for raw HTTP fetches.",
    )
    parser.add_argument(
        "--sitemap-non-html-probe-limit",
        type=int,
        default=50,
        help="Number of non-HTML sitemap URLs to fetch for header/content-type verification.",
    )
    parser.add_argument("--crawl-delay", type=float, default=None, help="Override robots crawl delay")
    parser.add_argument(
        "--include-regex",
        action="append",
        default=[],
        help="Scope include regex. Evaluated against both normalized URL and path. Repeat as needed.",
    )
    parser.add_argument(
        "--exclude-regex",
        action="append",
        default=[],
        help="Scope exclude regex. Evaluated against both normalized URL and path. Repeat as needed.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    base_url = normalize_url(args.base_url)
    host_slug = args.output_slug or urlparse(base_url).netloc.replace(".", "_")

    auditor = PublicSiteAuditor(
        base_url=base_url,
        output_slug=host_slug,
        max_pages=args.max_pages,
        asset_sample_size=args.asset_sample_size,
        user_agent_profile=args.user_agent_profile,
        crawl_delay_override=args.crawl_delay,
        include_regexes=args.include_regex,
        exclude_regexes=args.exclude_regex,
        sitemap_non_html_probe_limit=args.sitemap_non_html_probe_limit,
    )

    print(f"Loading robots.txt for {base_url}")
    auditor.load_robots()
    print("Checking canonical host variants")
    auditor.check_host_variants()
    print("Collecting sitemaps")
    auditor.collect_sitemaps()
    print(f"Found {len(auditor.sitemap_entries)} sitemap URLs across {len(auditor.sitemaps_seen)} sitemap files")
    print("Probing non-HTML sitemap URLs")
    auditor.probe_sitemap_non_html_entries()
    print("Crawling HTML pages")
    auditor.crawl_pages()
    print(f"Crawled {len(auditor.pages)} HTML pages")
    print("Sampling internal assets")
    auditor.sample_assets()

    output = auditor.build_output()

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / f"{host_slug}_audit_data.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=True)

    page_rows = []
    for page in output["pages"].values():
        page_rows.append(
            {
                "url": page["url"],
                "final_url": page["final_url"],
                "status": page["status"],
                "content_type": page["content_type"],
                "indexable": page["indexable"],
                "noindex": page["noindex"],
                "robots_allowed": page["robots_allowed"],
                "in_sitemap": page["in_sitemap"],
                "page_type": page["page_type"],
                "canonical": page["canonical"],
                "canonical_mismatch": page["canonical_mismatch"],
                "title": page["title"],
                "meta_description": page["meta_description"],
                "meta_viewport": page["meta_viewport"],
                "h1_count": page["h1_count"],
                "word_count": page["word_count"],
                "jsonld_count": page["jsonld_count"],
                "schema_types": page["schema_types"],
                "redirect_count": page["redirect_count"],
                "depth": page["depth"],
                "flags": page["flags"],
                "discovered_from": page["discovered_from"],
                "sitemap_sources": page["sitemap_sources"],
            }
        )

    sitemap_rows = [entry.__dict__ for entry in auditor.sitemap_entries.values()]
    issue_rows = output["issues"]
    asset_rows = output["assets"]

    write_csv(
        data_dir / f"{host_slug}_pages.csv",
        page_rows,
        [
            "url",
            "final_url",
            "status",
            "content_type",
            "indexable",
            "noindex",
            "robots_allowed",
            "in_sitemap",
            "page_type",
            "canonical",
            "canonical_mismatch",
            "title",
            "meta_description",
            "meta_viewport",
            "h1_count",
            "word_count",
            "jsonld_count",
            "schema_types",
            "redirect_count",
            "depth",
            "flags",
            "discovered_from",
            "sitemap_sources",
        ],
    )
    write_csv(
        data_dir / f"{host_slug}_sitemap_urls.csv",
        sitemap_rows,
        ["loc", "source_sitemap", "lastmod", "changefreq", "priority"],
    )
    write_csv(
        data_dir / f"{host_slug}_issues.csv",
        issue_rows,
        ["severity", "type", "url", "detail"],
    )
    write_csv(
        data_dir / f"{host_slug}_assets.csv",
        asset_rows,
        [
            "url",
            "final_url",
            "kind",
            "source_count",
            "status",
            "content_type",
            "x_robots_tag",
            "cache_control",
            "framework_asset",
            "requires_noindex",
            "elapsed_ms",
            "flags",
            "error",
        ],
    )
    write_csv(
        data_dir / f"{host_slug}_sitemap_non_html.csv",
        output["sitemap_non_html_probes"],
        [
            "url",
            "final_url",
            "status",
            "content_type",
            "x_robots_tag",
            "cache_control",
            "framework_asset",
            "requires_noindex",
            "elapsed_ms",
            "flags",
            "error",
        ],
    )
    write_csv(
        data_dir / f"{host_slug}_host_variants.csv",
        output["host_variant_checks"],
        ["start_url", "final_url", "final_status", "redirect_count", "chain"],
    )

    print(f"Wrote {json_path}")
    print(f"Issue count: {len(issue_rows)}")


if __name__ == "__main__":
    main()
