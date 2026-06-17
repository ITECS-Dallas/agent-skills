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
  for (const requiredPlugin of ['portable-development-workflow', 'itecs-halopsa', 'itecs-vcenter', 'itecs-pax8']) {
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

const runtimePlugins = [
  {
    name: 'itecs-halopsa',
    serverName: 'halopsa',
    skillName: 'halopsa-mcp',
    script: 'run-halopsa-mcp',
    binaryPrefix: 'halopsa-mcp'
  },
  {
    name: 'itecs-vcenter',
    serverName: 'vcenter',
    skillName: 'vcenter-mcp',
    script: 'run-vcenter-mcp',
    binaryPrefix: 'vcenter-mcp'
  },
  {
    name: 'itecs-pax8',
    serverName: 'pax8',
    skillName: 'pax8-mcp',
    script: 'run-pax8-mcp',
    binaryPrefix: 'pax8-mcp'
  }
];

for (const runtimePlugin of runtimePlugins) {
  const runtimePluginRoot = path.join(repoRoot, 'plugins', runtimePlugin.name);
  const runtimeManifest = readJson(path.join(runtimePluginRoot, '.codex-plugin', 'plugin.json'));
  if (runtimeManifest) {
    if (runtimeManifest.name !== runtimePlugin.name) {
      errors.push(`${runtimePlugin.name}: plugin name must be ${runtimePlugin.name}`);
    }
    if (runtimeManifest.skills !== './skills/') {
      errors.push(`${runtimePlugin.name}: skills path must be ./skills/`);
    }
    if (runtimeManifest.mcpServers !== './.mcp.json') {
      errors.push(`${runtimePlugin.name}: mcpServers path must be ./.mcp.json`);
    }
  }

  const runtimeMcp = readJson(path.join(runtimePluginRoot, '.mcp.json'));
  if (runtimeMcp) {
    const server = runtimeMcp.mcpServers?.[runtimePlugin.serverName];
    if (!server) {
      errors.push(`${runtimePlugin.name}: .mcp.json missing mcpServers.${runtimePlugin.serverName}`);
    } else {
      if (server.command !== 'bash') {
        errors.push(`${runtimePlugin.name}: ${runtimePlugin.serverName} server command must be bash`);
      }
      if (!Array.isArray(server.args) || server.args[0] !== `./scripts/${runtimePlugin.script}`) {
        errors.push(`${runtimePlugin.name}: ${runtimePlugin.serverName} server args must start with ./scripts/${runtimePlugin.script}`);
      }
      if (server.cwd !== '.') {
        errors.push(`${runtimePlugin.name}: ${runtimePlugin.serverName} server cwd must be .`);
      }
    }
  }

  const requiredFiles = [
    'README.md',
    `skills/${runtimePlugin.skillName}/SKILL.md`,
    `scripts/${runtimePlugin.script}`,
    `bin/${runtimePlugin.binaryPrefix}-darwin-arm64`,
    `bin/${runtimePlugin.binaryPrefix}-darwin-amd64`,
    `bin/${runtimePlugin.binaryPrefix}-windows-arm64.exe`,
    `bin/${runtimePlugin.binaryPrefix}-windows-amd64.exe`
  ];
  for (const relativeFile of requiredFiles) {
    const file = path.join(runtimePluginRoot, relativeFile);
    if (!fs.existsSync(file)) {
      errors.push(`${runtimePlugin.name} missing required file: ${relativeFile}`);
    }
  }

  for (const relativeExecutable of [
    `scripts/${runtimePlugin.script}`,
    `bin/${runtimePlugin.binaryPrefix}-darwin-arm64`,
    `bin/${runtimePlugin.binaryPrefix}-darwin-amd64`
  ]) {
    const file = path.join(runtimePluginRoot, relativeExecutable);
    if (!fs.existsSync(file)) continue;
    const executable = (fs.statSync(file).mode & 0o111) !== 0;
    if (!executable) {
      errors.push(`${runtimePlugin.name} file must be executable: ${relativeExecutable}`);
    }
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
