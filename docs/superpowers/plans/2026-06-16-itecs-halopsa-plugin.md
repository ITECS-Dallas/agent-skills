# ITECS HaloPSA Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the existing read-only GO-MCP HaloPSA connector as `itecs-halopsa` in the existing ITECS Agent Skills marketplace.

**Architecture:** Keep the sibling `GO-MCP/connectors/halopsa` checkout as implementation source of truth. Build Darwin binaries into `plugins/itecs-halopsa/bin/`, launch them with `plugins/itecs-halopsa/scripts/run-halopsa-mcp`, and register the plugin through `.agents/plugins/marketplace.json`.

**Tech Stack:** Codex plugin manifest JSON, Codex plugin `.mcp.json`, Go MCP stdio server, Node validation script, GitHub private marketplace repo.

---

### Task 1: Validation Contract

**Files:**
- Modify: `scripts/validate.mjs`

- [x] **Step 1: Add validator checks for `itecs-halopsa`**

Require marketplace registration, plugin manifest, `.mcp.json`, launcher script, HaloPSA skill, and Darwin binaries.

- [x] **Step 2: Run validator to verify it fails before plugin files exist**

Run: `node scripts/validate.mjs`

Expected: FAIL with missing `itecs-halopsa` marketplace entry, manifest, `.mcp.json`, wrapper, skill, and binaries.

### Task 2: Plugin Files

**Files:**
- Create: `plugins/itecs-halopsa/.codex-plugin/plugin.json`
- Create: `plugins/itecs-halopsa/.mcp.json`
- Create: `plugins/itecs-halopsa/README.md`
- Create: `plugins/itecs-halopsa/skills/halopsa-mcp/SKILL.md`
- Create: `plugins/itecs-halopsa/skills/halopsa-mcp/agents/openai.yaml`
- Create: `plugins/itecs-halopsa/scripts/run-halopsa-mcp`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `README.md`

- [x] **Step 1: Add plugin manifest**

Create a manifest named `itecs-halopsa` with `skills: "./skills/"` and `mcpServers: "./.mcp.json"`.

- [x] **Step 2: Add MCP server config**

Configure `mcpServers.halopsa.command` as `./scripts/run-halopsa-mcp` and `cwd` as `"."`.

- [x] **Step 3: Add wrapper**

The wrapper must choose the correct bundled Darwin binary by `uname -m`, read config from `HALOPSA_MCP_CONFIG` or `~/.codex/halopsa-mcp/config.json`, and fail with a clear message if the config file is absent.

- [x] **Step 4: Add operating docs and skill**

Document all eleven current HaloPSA tools, read-only boundaries, local config path, install commands, and smoke-test commands.

- [x] **Step 5: Register marketplace plugin**

Add `itecs-halopsa` to `.agents/plugins/marketplace.json` with `policy.installation: "AVAILABLE"` and `policy.authentication: "ON_INSTALL"`.

### Task 3: Build Binaries

**Files:**
- Create: `plugins/itecs-halopsa/bin/halopsa-mcp-darwin-arm64`
- Create: `plugins/itecs-halopsa/bin/halopsa-mcp-darwin-amd64`

- [x] **Step 1: Run GO-MCP HaloPSA tests**

Run: `go test ./...` from the sibling `GO-MCP/connectors/halopsa` checkout.

- [x] **Step 2: Compile Darwin binaries**

Run:

```bash
AGENT_SKILLS_ROOT="$(cd ../agent-skills && pwd -P)"
GOOS=darwin GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o "$AGENT_SKILLS_ROOT/plugins/itecs-halopsa/bin/halopsa-mcp-darwin-arm64" ./cmd/mcp
GOOS=darwin GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o "$AGENT_SKILLS_ROOT/plugins/itecs-halopsa/bin/halopsa-mcp-darwin-amd64" ./cmd/mcp
```

- [x] **Step 3: Mark wrapper and binaries executable**

Run: `chmod +x plugins/itecs-halopsa/scripts/run-halopsa-mcp plugins/itecs-halopsa/bin/halopsa-mcp-darwin-*`.

### Task 4: Final Verification

**Files:**
- Verify all changed files.

- [x] **Step 1: Run agent-skills validator**

Run: `node scripts/validate.mjs`

Expected: PASS.

- [x] **Step 2: Run plugin-creator validator**

Run: `python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/itecs-halopsa`

Expected: PASS.

- [x] **Step 3: Run MCP listfeatures smoke**

Run the GO SDK `listfeatures` client against the bundled plugin binary with `~/.codex/halopsa-mcp/config.json`.

Expected: output includes all eleven current HaloPSA tools.

- [x] **Step 4: Inspect Git diff and stage intentionally**

Run: `git status --short --branch`, `git diff --check`, and `git diff --stat`.

Stage only the plugin packaging, validation, docs, and related existing ITECS marketplace updates.
