#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.join(process.cwd(), "package.json"));
const { chromium } = require("playwright");

const GOOGLEBOT_SMARTPHONE_UA =
  "Mozilla/5.0 (Linux; Android 12; Pixel 5) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/122.0.0.0 Mobile Safari/537.36 " +
  "(compatible; Googlebot/2.1; +http://www.google.com/bot.html)";

function parseArgs(argv) {
  const args = {
    urls: [],
    output: "",
    waitUntil: "load",
    timeoutMs: 45000,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--url") {
      args.urls.push(argv[++i]);
    } else if (arg === "--output") {
      args.output = argv[++i];
    } else if (arg === "--wait-until") {
      args.waitUntil = argv[++i];
    } else if (arg === "--timeout-ms") {
      args.timeoutMs = Number(argv[++i]);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!args.urls.length) {
    throw new Error("At least one --url is required");
  }

  return args;
}

async function collectSchemaTypes(page) {
  return page.evaluate(() => {
    const found = new Set();

    const walk = (node) => {
      if (Array.isArray(node)) {
        node.forEach(walk);
        return;
      }
      if (!node || typeof node !== "object") {
        return;
      }
      const type = node["@type"];
      if (Array.isArray(type)) {
        type.forEach((item) => found.add(String(item)));
      } else if (type) {
        found.add(String(type));
      }
      Object.values(node).forEach(walk);
    };

    for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
      const raw = script.textContent?.trim();
      if (!raw) {
        continue;
      }
      try {
        walk(JSON.parse(raw));
      } catch {
        // Ignore malformed blocks; they are still counted separately.
      }
    }

    return Array.from(found);
  });
}

async function probeUrl(browser, url, options) {
  const context = await browser.newContext({
    userAgent: GOOGLEBOT_SMARTPHONE_UA,
    viewport: { width: 412, height: 915 },
    deviceScaleFactor: 2.625,
    isMobile: true,
    hasTouch: true,
    locale: "en-US",
    colorScheme: "light",
  });
  const page = await context.newPage();

  const consoleMessages = [];
  const failedRequests = [];
  const problemResponses = [];

  page.on("console", (message) => {
    const type = message.type();
    if (type === "error" || type === "warning") {
      consoleMessages.push({ type, text: message.text() });
    }
  });

  page.on("requestfailed", (request) => {
    failedRequests.push({
      url: request.url(),
      method: request.method(),
      resourceType: request.resourceType(),
      failure: request.failure()?.errorText || "",
    });
  });

  page.on("response", (response) => {
    if (response.status() >= 400) {
      problemResponses.push({
        url: response.url(),
        status: response.status(),
        resourceType: response.request().resourceType(),
      });
    }
  });

  const startedAt = Date.now();
  const response = await page.goto(url, { waitUntil: options.waitUntil, timeout: options.timeoutMs });
  await page.waitForTimeout(750);

  const pageData = await page.evaluate(() => {
    const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.getAttribute("content")?.trim() || "";
    const canonical = document.querySelector('link[rel="canonical"]')?.getAttribute("href")?.trim() || "";
    const h1s = Array.from(document.querySelectorAll("h1")).map((node) => node.textContent?.trim() || "");
    const html = document.documentElement.outerHTML;
    const nextAssets = Array.from(document.querySelectorAll('script[src], link[href]'))
      .map((node) => node.getAttribute("src") || node.getAttribute("href") || "")
      .filter(Boolean)
      .filter((value) => value.includes("/_next/"));

    return {
      title: document.title || "",
      metaDescription: meta("description"),
      metaRobots: meta("robots"),
      canonical,
      h1s,
      h1Count: h1s.length,
      htmlLang: document.documentElement.getAttribute("lang") || "",
      viewportMeta: meta("viewport"),
      jsonldCount: document.querySelectorAll('script[type="application/ld+json"]').length,
      hasNextFlight: html.includes("self.__next_f.push"),
      hasRscMarkers: html.includes("<!--$"),
      nextAssetCount: nextAssets.length,
      nextAssets: nextAssets.slice(0, 25),
      mailtoCount: (html.match(/mailto:/g) || []).length,
    };
  });

  const schemaTypes = await collectSchemaTypes(page);
  const elapsedMs = Date.now() - startedAt;

  await context.close();

  return {
    url,
    finalUrl: page.url(),
    status: response?.status() || 0,
    elapsedMs,
    userAgent: GOOGLEBOT_SMARTPHONE_UA,
    rendered: {
      ...pageData,
      schemaTypes,
    },
    consoleIssueCount: consoleMessages.length,
    consoleMessages: consoleMessages.slice(0, 20),
    failedRequestCount: failedRequests.length,
    failedRequests: failedRequests.slice(0, 30),
    problemResponseCount: problemResponses.length,
    problemResponses: problemResponses.slice(0, 30),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const browser = await chromium.launch({ headless: true });
  const results = [];

  try {
    for (const url of args.urls) {
      results.push(await probeUrl(browser, url, args));
    }
  } finally {
    await browser.close();
  }

  const output = {
    generatedAt: new Date().toISOString(),
    mode: "googlebot-smartphone-render-probe",
    waitUntil: args.waitUntil,
    timeoutMs: args.timeoutMs,
    results,
  };

  const serialized = JSON.stringify(output, null, 2);
  if (args.output) {
    await fs.mkdir(path.dirname(args.output), { recursive: true });
    await fs.writeFile(args.output, serialized, "utf8");
  } else {
    process.stdout.write(`${serialized}\n`);
  }
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
