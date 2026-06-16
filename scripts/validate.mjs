#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const pluginRoot = path.join(repoRoot, 'plugins', 'portable-development-workflow');
const skillsRoot = path.join(pluginRoot, 'skills');
const marketplacePath = path.join(repoRoot, '.agents', 'plugins', 'marketplace.json');
const errors = [];

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    errors.push(`invalid json: ${path.relative(repoRoot, file)}: ${error.message}`);
    return null;
  }
}

function walk(dir) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '.git' || entry.name === 'node_modules') continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walk(fullPath));
    } else {
      results.push(fullPath);
    }
  }
  return results;
}

function parseFrontmatter(file) {
  const content = fs.readFileSync(file, 'utf8');
  const match = content.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) {
    errors.push(`missing yaml frontmatter: ${path.relative(repoRoot, file)}`);
    return null;
  }

  const fields = {};
  for (const line of match[1].split('\n')) {
    const field = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!field) continue;
    fields[field[1]] = field[2].replace(/^["']|["']$/g, '').trim();
  }
  return fields;
}

const plugin = readJson(path.join(pluginRoot, '.codex-plugin', 'plugin.json'));
const manifest = readJson(path.join(repoRoot, 'EXPORT-MANIFEST.json'));
const marketplace = readJson(marketplacePath);

if (plugin) {
  if (plugin.name !== 'portable-development-workflow') {
    errors.push('plugin name must be portable-development-workflow');
  }
  if (plugin.skills !== './skills/') {
    errors.push('plugin skills path must be ./skills/');
  }
}

if (marketplace) {
  if (marketplace.name !== 'itecs-agent-skills') {
    errors.push('marketplace name must be itecs-agent-skills');
  }

  const entries = Array.isArray(marketplace.plugins) ? marketplace.plugins : [];
  const pluginNames = new Set(entries.map((entry) => entry.name));
  for (const requiredPlugin of ['portable-development-workflow', 'itecs-halopsa']) {
    if (!pluginNames.has(requiredPlugin)) {
      errors.push(`marketplace missing plugin: ${requiredPlugin}`);
    }
  }

  for (const entry of entries) {
    if (!entry.name) {
      errors.push('marketplace plugin entry missing name');
      continue;
    }
    if (entry.source?.source !== 'local') {
      errors.push(`${entry.name}: marketplace source must be local`);
    }
    if (!entry.source?.path?.startsWith('./plugins/')) {
      errors.push(`${entry.name}: marketplace source path must start with ./plugins/`);
      continue;
    }

    const entryRoot = path.join(repoRoot, entry.source.path);
    const entryManifest = readJson(path.join(entryRoot, '.codex-plugin', 'plugin.json'));
    if (!entryManifest) continue;

    if (entryManifest.name !== entry.name) {
      errors.push(`${entry.name}: plugin manifest name must match marketplace entry`);
    }
    if (!entry.policy?.installation) {
      errors.push(`${entry.name}: marketplace entry missing policy.installation`);
    }
    if (!entry.policy?.authentication) {
      errors.push(`${entry.name}: marketplace entry missing policy.authentication`);
    }
    if (!entry.category) {
      errors.push(`${entry.name}: marketplace entry missing category`);
    }
  }
}

const halopsaPluginRoot = path.join(repoRoot, 'plugins', 'itecs-halopsa');
const halopsaPlugin = readJson(path.join(halopsaPluginRoot, '.codex-plugin', 'plugin.json'));
if (halopsaPlugin) {
  if (halopsaPlugin.name !== 'itecs-halopsa') {
    errors.push('itecs-halopsa: plugin name must be itecs-halopsa');
  }
  if (halopsaPlugin.skills !== './skills/') {
    errors.push('itecs-halopsa: skills path must be ./skills/');
  }
  if (halopsaPlugin.mcpServers !== './.mcp.json') {
    errors.push('itecs-halopsa: mcpServers path must be ./.mcp.json');
  }
}

const halopsaMcp = readJson(path.join(halopsaPluginRoot, '.mcp.json'));
if (halopsaMcp) {
  const server = halopsaMcp.mcpServers?.halopsa;
  if (!server) {
    errors.push('itecs-halopsa: .mcp.json missing mcpServers.halopsa');
  } else {
    if (server.command !== './scripts/run-halopsa-mcp') {
      errors.push('itecs-halopsa: halopsa server command must be ./scripts/run-halopsa-mcp');
    }
    if (server.cwd !== '.') {
      errors.push('itecs-halopsa: halopsa server cwd must be .');
    }
  }
}

const halopsaRequiredFiles = [
  'README.md',
  'skills/halopsa-mcp/SKILL.md',
  'scripts/run-halopsa-mcp',
  'bin/halopsa-mcp-darwin-arm64',
  'bin/halopsa-mcp-darwin-amd64'
];
for (const relativeFile of halopsaRequiredFiles) {
  const file = path.join(halopsaPluginRoot, relativeFile);
  if (!fs.existsSync(file)) {
    errors.push(`itecs-halopsa missing required file: ${relativeFile}`);
  }
}

for (const relativeExecutable of [
  'scripts/run-halopsa-mcp',
  'bin/halopsa-mcp-darwin-arm64',
  'bin/halopsa-mcp-darwin-amd64'
]) {
  const file = path.join(halopsaPluginRoot, relativeExecutable);
  if (!fs.existsSync(file)) continue;
  const executable = (fs.statSync(file).mode & 0o111) !== 0;
  if (!executable) {
    errors.push(`itecs-halopsa file must be executable: ${relativeExecutable}`);
  }
}

const expectedSkills = manifest?.skills ?? [];
const actualSkills = fs.existsSync(skillsRoot)
  ? fs.readdirSync(skillsRoot).filter((entry) => {
      return fs.existsSync(path.join(skillsRoot, entry, 'SKILL.md'));
    }).sort()
  : [];

for (const skillName of expectedSkills) {
  if (!actualSkills.includes(skillName)) {
    errors.push(`manifest lists missing skill: ${skillName}`);
  }
}

for (const skillName of actualSkills) {
  if (!expectedSkills.includes(skillName)) {
    errors.push(`skill missing from manifest: ${skillName}`);
  }

  const skillFile = path.join(skillsRoot, skillName, 'SKILL.md');
  const frontmatter = parseFrontmatter(skillFile);
  if (!frontmatter) continue;

  if (frontmatter.name !== skillName) {
    errors.push(`${skillName}: frontmatter name must match folder name`);
  }
  if (!frontmatter.description) {
    errors.push(`${skillName}: missing description`);
  } else {
    if (!frontmatter.description.startsWith('Use when')) {
      errors.push(`${skillName}: description should start with "Use when"`);
    }
    if (frontmatter.description.length > 500) {
      errors.push(`${skillName}: description should stay under 500 characters`);
    }
  }
}

const bannedTerms = [
  'stra' + 'vere',
  'mo' + 'mo',
  'omni' + 'gent',
  'fate' + 'weaver',
  'fik' + 'shun',
  '/' + 'Users' + '/',
  '/' + 'home' + '/',
  '/' + 'var' + '/' + 'www' + '/'
];

const textExtensions = new Set([
  '.json',
  '.md',
  '.mjs',
  '.sh',
  '.ts',
  '.tsx',
  '.js',
  '.jsx',
  '.yaml',
  '.yml',
  '.txt'
]);

for (const file of walk(repoRoot)) {
  if (!textExtensions.has(path.extname(file))) continue;
  const rel = path.relative(repoRoot, file);
  const content = fs.readFileSync(file, 'utf8').toLowerCase();
  for (const term of bannedTerms) {
    if (content.includes(term.toLowerCase())) {
      errors.push(`project-specific term "${term}" found in ${rel}`);
    }
  }
}

if (errors.length > 0) {
  console.error('validation failed');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`validation ok: ${actualSkills.length} skills`);
