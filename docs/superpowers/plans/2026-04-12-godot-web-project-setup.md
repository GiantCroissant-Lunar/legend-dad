# Godot Web Game Project Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up a complete Godot 4.6 web game project with Node.js WebSocket server, dev tooling, and infrastructure for automated browser testing.

**Architecture:** Separate static file server (sirv) and WebSocket server (ws + nodemon) running on different ports. Godot web export served locally with COOP/COEP headers. pnpm workspaces under `project/server/`. Taskfile.yml orchestrates all commands.

**Tech Stack:** Godot 4.6.2, Node.js (ws, sirv-cli, nodemon), Python (download script), pnpm workspaces, Taskfile, biome, ruff, pre-commit, git-cliff

---

## File Structure

```
legend-dad/
├── .gitignore                          # Root gitignore for all project types
├── .pre-commit-config.yaml             # Pre-commit hooks config
├── .editorconfig                       # Editor config for consistent formatting
├── cliff.toml                          # git-cliff changelog config
├── pyproject.toml                      # ruff config for Python
├── Taskfile.yml                        # All dev commands
├── project/
│   ├── hosts/
│   │   └── complete-app/               # (existing) Godot 4.6 project
│   │       └── export_presets.cfg      # Web export preset (created in Task 5)
│   └── server/
│       ├── package.json                # pnpm workspace root
│       ├── pnpm-workspace.yaml         # workspace definition
│       ├── biome.json                  # JS/TS linting config
│       └── packages/
│           └── game-server/
│               ├── package.json        # game-server package
│               ├── nodemon.json        # nodemon config
│               └── src/
│                   └── index.js        # WebSocket + HTTP server entry
├── builds/
│   └── web/                            # Godot web export output (gitignored)
│       └── .gitkeep
├── scripts/
│   └── download_templates.py           # Downloads Godot export templates
└── vault/
    ├── .obsidian/                      # Obsidian config (volatile files gitignored)
    ├── architecture/
    │   └── .gitkeep
    ├── design/
    │   └── .gitkeep
    └── references/
        └── .gitkeep
```

---

### Task 1: Root .gitignore and .editorconfig

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`

- [ ] **Step 1: Create root .gitignore**

```gitignore
# OS
.DS_Store
Thumbs.db

# Godot
project/hosts/complete-app/.godot/

# Builds
builds/web/*
!builds/web/.gitkeep

# Node
node_modules/
*.tgz

# Python
__pycache__/
*.pyc
.venv/

# Obsidian volatile
vault/.obsidian/workspace.json
vault/.obsidian/workspace-mobile.json
vault/.obsidian/plugins/*/data.json

# IDE
.vscode/
.idea/
*.swp
*.swo
```

- [ ] **Step 2: Create .editorconfig**

```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
charset = utf-8

[*.{js,ts,json}]
indent_style = space
indent_size = 2

[*.{py}]
indent_style = space
indent_size = 4

[*.{gd,gdshader}]
indent_style = tab
indent_size = 4

[*.{yml,yaml,toml}]
indent_style = space
indent_size = 2

[Makefile]
indent_style = tab

[*.md]
trim_trailing_whitespace = false
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore .editorconfig
git commit -m "chore: add root .gitignore and .editorconfig"
```

---

### Task 2: Obsidian Vault Scaffold

**Files:**
- Create: `vault/.obsidian/.gitkeep`
- Create: `vault/architecture/.gitkeep`
- Create: `vault/design/.gitkeep`
- Create: `vault/references/.gitkeep`

- [ ] **Step 1: Create vault directory structure with .gitkeep files**

Create the four directories with `.gitkeep` files so git tracks them.

- [ ] **Step 2: Commit**

```bash
git add vault/
git commit -m "chore: scaffold Obsidian vault structure"
```

---

### Task 3: pyproject.toml (ruff config)

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Create pyproject.toml with ruff config**

```toml
[project]
name = "legend-dad"
version = "0.0.1"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 120
src = ["scripts"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "double"
```

- [ ] **Step 2: Verify ruff reads the config**

Run: `ruff check scripts/ --config pyproject.toml`
Expected: No errors (no Python files yet, clean exit)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject.toml with ruff config"
```

---

### Task 4: pnpm Workspace + biome

**Files:**
- Create: `project/server/package.json`
- Create: `project/server/pnpm-workspace.yaml`
- Create: `project/server/biome.json`
- Create: `project/server/packages/game-server/package.json`
- Create: `project/server/packages/game-server/nodemon.json`
- Create: `project/server/packages/game-server/src/index.js`

- [ ] **Step 1: Create workspace root package.json**

File: `project/server/package.json`

```json
{
  "name": "legend-dad-server",
  "private": true,
  "type": "module",
  "scripts": {
    "lint": "biome check .",
    "format": "biome format --write .",
    "lint:fix": "biome check --fix ."
  },
  "devDependencies": {
    "@biomejs/biome": "^1.9.0"
  }
}
```

- [ ] **Step 2: Create pnpm-workspace.yaml**

File: `project/server/pnpm-workspace.yaml`

```yaml
packages:
  - "packages/*"
```

- [ ] **Step 3: Create biome.json**

File: `project/server/biome.json`

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.0/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 120
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "semicolons": "always"
    }
  }
}
```

- [ ] **Step 4: Create game-server package.json**

File: `project/server/packages/game-server/package.json`

```json
{
  "name": "@legend-dad/game-server",
  "version": "0.0.1",
  "private": true,
  "type": "module",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon"
  },
  "dependencies": {
    "ws": "^8.18.0"
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}
```

- [ ] **Step 5: Create nodemon.json**

File: `project/server/packages/game-server/nodemon.json`

```json
{
  "watch": ["src"],
  "ext": "js,json",
  "exec": "node src/index.js"
}
```

- [ ] **Step 6: Create minimal WebSocket server**

File: `project/server/packages/game-server/src/index.js`

```javascript
import { WebSocketServer } from "ws";
import { createServer } from "node:http";

const PORT = parseInt(process.env.PORT || "3000", 10);

const server = createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("legend-dad game server\n");
});

const wss = new WebSocketServer({ server });

wss.on("connection", (ws, req) => {
  console.log(`[ws] client connected from ${req.socket.remoteAddress}`);

  ws.on("message", (data) => {
    console.log(`[ws] received: ${data}`);
    ws.send(JSON.stringify({ type: "echo", payload: data.toString() }));
  });

  ws.on("close", () => {
    console.log("[ws] client disconnected");
  });
});

server.listen(PORT, () => {
  console.log(`[server] listening on http://localhost:${PORT}`);
  console.log(`[ws] WebSocket server ready on ws://localhost:${PORT}`);
});
```

- [ ] **Step 7: Install dependencies**

Run from `project/server/`:
```bash
pnpm install
```

- [ ] **Step 8: Verify biome works**

Run from `project/server/`:
```bash
pnpm run lint
```
Expected: Clean pass, no errors.

- [ ] **Step 9: Verify server starts**

Run from `project/server/packages/game-server/`:
```bash
node src/index.js &
sleep 1
curl -s http://localhost:3000
kill %1
```
Expected: `legend-dad game server`

- [ ] **Step 10: Commit**

```bash
git add project/server/
git commit -m "feat: add pnpm workspace with game-server package and biome"
```

---

### Task 5: Godot Web Export Preset

**Files:**
- Create: `project/hosts/complete-app/export_presets.cfg`

- [ ] **Step 1: Create export_presets.cfg for web export**

File: `project/hosts/complete-app/export_presets.cfg`

```ini
[preset.0]

name="Web"
platform="Web"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="../../../../builds/web/complete-app.html"
patches=PackedStringArray()
encryption_include_filters=""
encryption_exclude_filters=""
seed=0
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
progressive_web_app/offline_page=""
progressive_web_app/display=1
progressive_web_app/orientation=0
progressive_web_app/icon_144x144=""
progressive_web_app/icon_180x180=""
progressive_web_app/icon_512x512=""
progressive_web_app/background_color=Color(0, 0, 0, 1)
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/export_presets.cfg
git commit -m "feat: add Godot web export preset"
```

---

### Task 6: Python Download Templates Script

**Files:**
- Create: `scripts/download_templates.py`

- [ ] **Step 1: Create download_templates.py**

File: `scripts/download_templates.py`

```python
#!/usr/bin/env python3
"""Download Godot 4.6.2 web export templates from GitHub releases."""

import io
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

GODOT_VERSION = "4.6.2"
GODOT_VERSION_TAG = f"{GODOT_VERSION}-stable"
TEMPLATE_FOLDER_NAME = f"{GODOT_VERSION}.stable"

DOWNLOAD_URL = (
    f"https://github.com/godotengine/godot/releases/download/{GODOT_VERSION_TAG}/"
    f"Godot_v{GODOT_VERSION}-stable_export_templates.tpz"
)


def get_template_dir() -> Path:
    """Return OS-appropriate Godot export templates directory."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Godot" / "export_templates" / TEMPLATE_FOLDER_NAME
    if system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Godot" / "export_templates" / TEMPLATE_FOLDER_NAME
    if system == "Linux":
        return Path.home() / ".local" / "share" / "godot" / "export_templates" / TEMPLATE_FOLDER_NAME
    print(f"Unsupported OS: {system}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    template_dir = get_template_dir()

    if template_dir.exists() and any(template_dir.iterdir()):
        print(f"Export templates already exist at {template_dir}")
        print("Delete the directory to re-download.")
        return

    print(f"Downloading export templates from:\n  {DOWNLOAD_URL}")
    print("This may take a few minutes...")

    try:
        response = urllib.request.urlopen(DOWNLOAD_URL)  # noqa: S310
        data = response.read()
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting to {template_dir}...")
    template_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            # Templates are inside a "templates/" folder in the zip
            if member.startswith("templates/") and not member.endswith("/"):
                filename = member.replace("templates/", "", 1)
                target = template_dir / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))

    print("Done! Export templates installed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify ruff passes**

Run: `ruff check scripts/download_templates.py`
Expected: Clean pass.

- [ ] **Step 3: Commit**

```bash
git add scripts/download_templates.py
git commit -m "feat: add Python script to download Godot web export templates"
```

---

### Task 7: Taskfile.yml

**Files:**
- Create: `Taskfile.yml`

- [ ] **Step 1: Create Taskfile.yml**

```yaml
version: "3"

vars:
  GODOT_PATH: '{{.GODOT_PATH | default "/Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot"}}'
  SERVER_DIR: "project/server"
  GAME_SERVER_DIR: "project/server/packages/game-server"
  GODOT_PROJECT_DIR: "project/hosts/complete-app"
  BUILD_DIR: "builds/web"

tasks:
  setup:
    desc: Install all dependencies and download Godot export templates
    cmds:
      - python3 scripts/download_templates.py
      - cd {{.SERVER_DIR}} && pnpm install
      - pre-commit install

  build:
    desc: Export Godot project for web
    cmds:
      - mkdir -p {{.BUILD_DIR}}
      - '{{.GODOT_PATH}} --headless --path {{.GODOT_PROJECT_DIR}} --export-release "Web" ../../../../{{.BUILD_DIR}}/complete-app.html'

  dev:
    desc: Start WebSocket server (nodemon) and static file server in parallel
    deps:
      - dev:ws
      - dev:static

  dev:ws:
    desc: Start WebSocket game server with nodemon
    dir: "{{.GAME_SERVER_DIR}}"
    cmds:
      - pnpm run dev

  dev:static:
    desc: Serve web build with COOP/COEP headers
    cmds:
      - npx sirv-cli {{.BUILD_DIR}} --port 8080 --cors --single --header "Cross-Origin-Opener-Policy=same-origin" --header "Cross-Origin-Embedder-Policy=require-corp"

  serve:
    desc: Serve web build only (no WS server)
    cmds:
      - npx sirv-cli {{.BUILD_DIR}} --port 8080 --cors --single --header "Cross-Origin-Opener-Policy=same-origin" --header "Cross-Origin-Embedder-Policy=require-corp"

  lint:
    desc: Run all linters
    cmds:
      - cd {{.SERVER_DIR}} && pnpm run lint
      - ruff check scripts/

  format:
    desc: Run all formatters
    cmds:
      - cd {{.SERVER_DIR}} && pnpm run format
      - ruff format scripts/

  clean:
    desc: Remove web build output
    cmds:
      - rm -rf {{.BUILD_DIR}}/*
      - touch {{.BUILD_DIR}}/.gitkeep

  changelog:
    desc: Generate changelog with git-cliff
    cmds:
      - git-cliff -o CHANGELOG.md
```

- [ ] **Step 2: Verify Taskfile is valid**

Run: `task --list`
Expected: Lists all tasks with descriptions.

- [ ] **Step 3: Commit**

```bash
git add Taskfile.yml
git commit -m "feat: add Taskfile.yml with dev workflow commands"
```

---

### Task 8: git-cliff Config

**Files:**
- Create: `cliff.toml`

- [ ] **Step 1: Create cliff.toml**

```toml
[changelog]
header = """
# Changelog\n
"""
body = """
{%- macro remote_url() -%}
  https://github.com/GiantCroissant-Lunar/legend-dad
{%- endmacro -%}

{% if version -%}
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else -%}
    ## [Unreleased]
{% endif -%}

{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | striptags | trim | upper_first }}
    {% for commit in commits %}
        - {{ commit.message | upper_first | trim }}\
          {% if commit.github.username %} by @{{ commit.github.username }}{%- endif -%}
          {% if commit.github.pr_number %} in \
            [#{{ commit.github.pr_number }}]({{ self::remote_url() }}/pull/{{ commit.github.pr_number }})\
          {%- endif %}
    {%- endfor %}
{% endfor %}\n
"""
footer = ""
trim = true

[git]
conventional_commits = true
filter_unconventional = true
split_commits = false
commit_parsers = [
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Bug Fixes" },
  { message = "^doc", group = "Documentation" },
  { message = "^perf", group = "Performance" },
  { message = "^refactor", group = "Refactoring" },
  { message = "^style", group = "Styling" },
  { message = "^test", group = "Testing" },
  { message = "^chore", group = "Miscellaneous" },
  { message = "^ci", group = "CI/CD" },
]
filter_commits = false
tag_pattern = "v[0-9].*"
sort_commits = "oldest"
```

- [ ] **Step 2: Verify git-cliff works**

Run: `git-cliff --unreleased`
Expected: Shows unreleased commits formatted.

- [ ] **Step 3: Commit**

```bash
git add cliff.toml
git commit -m "chore: add git-cliff changelog config"
```

---

### Task 9: Pre-commit Config

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=1000"]

  - repo: https://github.com/biomejs/pre-commit
    rev: v0.6.1
    hooks:
      - id: biome-check
        additional_dependencies: ["@biomejs/biome@1.9.0"]
        files: ^project/server/

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.6
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format

  - repo: local
    hooks:
      - id: no-godot-cache
        name: Prevent .godot/ from being committed
        entry: bash -c 'for f in "$@"; do case "$f" in */.godot/*) echo "Blocked: $f"; exit 1;; esac; done' --
        language: system
        pass_filenames: true
```

- [ ] **Step 2: Install pre-commit hooks**

Run: `pre-commit install`
Expected: `pre-commit installed at .git/hooks/pre-commit`

- [ ] **Step 3: Run pre-commit on all files to verify**

Run: `pre-commit run --all-files`
Expected: All hooks pass (some may fix whitespace/newlines — that's fine).

- [ ] **Step 4: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit config with biome, ruff, and safety hooks"
```

---

### Task 10: builds/web/.gitkeep

**Files:**
- Create: `builds/web/.gitkeep`

- [ ] **Step 1: Create .gitkeep**

Create an empty `builds/web/.gitkeep` file so git tracks the directory.

- [ ] **Step 2: Commit**

```bash
git add builds/web/.gitkeep
git commit -m "chore: add builds/web directory with .gitkeep"
```

---

### Task 11: Verification — Pre-commit End-to-End Test

This task verifies pre-commit works by intentionally triggering hooks.

- [ ] **Step 1: Test trailing whitespace hook**

Create a test file with trailing whitespace:
```bash
echo "hello   " > /tmp/test-trailing.txt
cp /tmp/test-trailing.txt scripts/test_lint.py
git add scripts/test_lint.py
git commit -m "test: verify pre-commit catches trailing whitespace"
```
Expected: `trailing-whitespace` hook fixes it automatically, commit succeeds with fixed file.

- [ ] **Step 2: Test ruff hook with a Python lint error**

Create `scripts/test_lint.py` with an unused import:
```python
import os

def hello():
    print("hello")
```

```bash
git add scripts/test_lint.py
git commit -m "test: verify ruff catches lint errors"
```
Expected: ruff `--fix` removes unused import, commit succeeds with fixed file.

- [ ] **Step 3: Test biome hook with a JS formatting issue**

Create `project/server/packages/game-server/src/test_lint.js` with single quotes:
```javascript
const x = 'should be double quotes';
console.log(x);
```

```bash
git add project/server/packages/game-server/src/test_lint.js
git commit -m "test: verify biome catches formatting issues"
```
Expected: biome check flags the single quotes.

- [ ] **Step 4: Clean up test files**

```bash
rm -f scripts/test_lint.py project/server/packages/game-server/src/test_lint.js
git add -A
git commit -m "chore: remove lint verification test files"
```

---

### Task 12: Push to Remote

- [ ] **Step 1: Push all commits**

```bash
git push -u origin main
```
Expected: All commits pushed to `git@github.com:GiantCroissant-Lunar/legend-dad.git`.
