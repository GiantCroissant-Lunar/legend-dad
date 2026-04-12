---
name: agent-browser
description: Browser automation CLI for AI agents. Use when the user needs to interact with websites — navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, testing web apps, or automating any browser task.
user_invocable: true
---
# Browser Automation with agent-browser

Headless browser automation CLI. Fast native Rust binary using Chrome/Chromium via CDP directly.

Install: `npm i -g agent-browser` or `brew install agent-browser` or `cargo install agent-browser`.
First run: `agent-browser install` (downloads Chrome for Testing).
Update: `agent-browser upgrade`.

## Core Workflow

Every browser automation follows this pattern:

1. **Navigate**: `agent-browser open <url>`
2. **Snapshot**: `agent-browser snapshot -i` (get element refs like `@e1`, `@e2`)
3. **Interact**: Use refs to click, fill, select
4. **Re-snapshot**: After navigation or DOM changes, get fresh refs

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# Output: @e1 [input type="email"], @e2 [input type="password"], @e3 [button] "Submit"

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check result
```

## Ref Lifecycle (Critical)

Refs (`@e1`, `@e2`, etc.) are invalidated when the page changes. Always re-snapshot after:

- Clicking links or buttons that navigate
- Form submissions
- Dynamic content loading (dropdowns, modals)

```bash
agent-browser click @e5              # Navigates to new page
agent-browser snapshot -i            # MUST re-snapshot
agent-browser click @e1              # Use new refs
```

## Command Chaining

Chain with `&&` when you don't need intermediate output:

```bash
agent-browser open https://example.com && agent-browser wait --load networkidle && agent-browser snapshot -i
agent-browser fill @e1 "user@example.com" && agent-browser fill @e2 "pass" && agent-browser click @e3
```

Run commands separately when you need to parse output first (e.g., snapshot to discover refs).

## Essential Commands

```bash
# Navigation
agent-browser open <url>              # Navigate (aliases: goto, navigate)
agent-browser back                    # Go back
agent-browser forward                 # Go forward
agent-browser reload                  # Reload page
agent-browser close                   # Close browser (aliases: quit, exit)

# Snapshot
agent-browser snapshot -i             # Interactive elements with refs (recommended)
agent-browser snapshot -i -C          # Include cursor-interactive elements
agent-browser snapshot -c             # Compact output
agent-browser snapshot -d 3           # Limit depth to 3
agent-browser snapshot -s "#selector" # Scope to CSS selector

# Interaction (use @refs from snapshot)
agent-browser click @e1               # Click element
agent-browser click @e1 --new-tab     # Click and open in new tab
agent-browser dblclick @e1            # Double-click
agent-browser fill @e2 "text"         # Clear and type text
agent-browser type @e2 "text"         # Type without clearing
agent-browser select @e1 "option"     # Select dropdown option
agent-browser check @e1               # Check checkbox
agent-browser uncheck @e1             # Uncheck checkbox
agent-browser press Enter             # Press key
agent-browser press Control+a         # Key combination
agent-browser keyboard type "text"    # Type at current focus (no selector)
agent-browser hover @e1               # Hover element
agent-browser scroll down 500         # Scroll page
agent-browser scroll down 500 --selector "div.content"  # Scroll within container
agent-browser drag @e1 @e2            # Drag and drop
agent-browser upload @e1 file.pdf     # Upload files

# Get information
agent-browser get text @e1            # Get element text
agent-browser get html @e1            # Get innerHTML
agent-browser get value @e1           # Get input value
agent-browser get attr @e1 href       # Get attribute
agent-browser get title               # Get page title
agent-browser get url                 # Get current URL
agent-browser get count ".item"       # Count matching elements
agent-browser get styles @e1          # Get computed styles

# Check state
agent-browser is visible @e1          # Check if visible
agent-browser is enabled @e1          # Check if enabled
agent-browser is checked @e1          # Check if checked

# Wait
agent-browser wait @e1                # Wait for element
agent-browser wait --load networkidle # Wait for network idle
agent-browser wait --url "**/page"    # Wait for URL pattern
agent-browser wait --text "Welcome"   # Wait for text to appear
agent-browser wait --fn "window.ready === true"  # Wait for JS condition
agent-browser wait 2000               # Wait milliseconds (last resort)

# Capture
agent-browser screenshot              # Screenshot to temp dir
agent-browser screenshot page.png     # Screenshot to path
agent-browser screenshot --full       # Full page screenshot
agent-browser screenshot --annotate   # Annotated with numbered element labels
agent-browser pdf output.pdf          # Save as PDF

# JavaScript
agent-browser eval 'document.title'           # Simple expressions
agent-browser eval --stdin <<'EOF'            # Complex JS via stdin (recommended)
JSON.stringify(Array.from(document.querySelectorAll("a")).map(a => a.href))
EOF
agent-browser eval -b "<base64>"              # Base64-encoded JS

# Tabs
agent-browser tab                     # List tabs
agent-browser tab new [url]           # New tab
agent-browser tab 2                   # Switch to tab
agent-browser tab close               # Close current tab

# Frames (iframes auto-inlined in snapshots)
agent-browser frame @e3               # Switch to iframe by ref
agent-browser frame "#iframe"         # Switch by CSS selector
agent-browser frame main              # Back to main frame

# Dialogs (alert/confirm/prompt)
agent-browser dialog status           # Check if dialog is open
agent-browser dialog accept           # Accept dialog
agent-browser dialog accept "input"   # Accept prompt with text
agent-browser dialog dismiss          # Dismiss dialog

# Diff (compare page states)
agent-browser diff snapshot                          # Current vs last snapshot
agent-browser diff snapshot --baseline before.txt    # Current vs saved file
agent-browser diff screenshot --baseline before.png  # Visual pixel diff
agent-browser diff url <url1> <url2>                 # Compare two pages

# Network
agent-browser network requests                 # View tracked requests
agent-browser network requests --type xhr,fetch  # Filter by type
agent-browser network route "**/api/*" --abort  # Block requests
agent-browser network har start                # Start HAR recording
agent-browser network har stop ./capture.har   # Stop and save

# Viewport & Device
agent-browser set viewport 1920 1080           # Set viewport size
agent-browser set viewport 1920 1080 2         # 2x retina
agent-browser set device "iPhone 14"           # Emulate device
agent-browser set media dark                   # Dark mode

# Clipboard
agent-browser clipboard read                   # Read clipboard
agent-browser clipboard write "text"           # Write to clipboard
```

## Batch Execution

Execute multiple commands in one invocation:

```bash
echo '[
  ["open", "https://example.com"],
  ["snapshot", "-i"],
  ["click", "@e1"],
  ["screenshot", "result.png"]
]' | agent-browser batch --json

# Stop on first error
agent-browser batch --bail < commands.json
```

## Handling Authentication

| Approach | Best for | Usage |
|---|---|---|
| Persistent profile | Full browser state across restarts | `--profile ~/.myapp` |
| Session persistence | Auto-save/restore cookies + localStorage | `--session-name myapp` |
| Import from browser | Grab auth from running Chrome | `--auto-connect` + `state save` |
| State file | Load previously saved state | `--state ./auth.json` |
| Auth vault | Encrypted credentials, login by name | `auth save` / `auth login` |

### Auth vault (recommended for recurring tasks)

```bash
echo "$PASSWORD" | agent-browser auth save myapp --url https://app.example.com/login --username user --password-stdin
agent-browser auth login myapp
```

### Persistent profile

```bash
agent-browser --profile ~/.myapp open https://app.example.com/login
# ... login once ...
# All future runs: already authenticated
agent-browser --profile ~/.myapp open https://app.example.com/dashboard
```

### Session persistence

```bash
agent-browser --session-name myapp open https://app.example.com/login
# ... login flow ...
agent-browser close  # State auto-saved
# Next time: state auto-restored
agent-browser --session-name myapp open https://app.example.com/dashboard
```

## Annotated Screenshots (Vision Mode)

Overlays numbered labels on interactive elements. Each `[N]` maps to ref `@eN`:

```bash
agent-browser screenshot --annotate
# [1] @e1 button "Submit"
# [2] @e2 link "Home"
# [3] @e3 textbox "Email"
agent-browser click @e2  # Click using ref from annotated screenshot
```

Use when: unlabeled icon buttons, visual-only elements, canvas/charts, spatial reasoning needed.

## Semantic Locators (Alternative to Refs)

```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find placeholder "Search" type "query"
agent-browser find testid "submit-btn" click
```

## Sessions (Parallel Isolation)

```bash
agent-browser --session site1 open https://site-a.com
agent-browser --session site2 open https://site-b.com
agent-browser session list
# Always close when done
agent-browser --session site1 close
```

## Timeouts and Slow Pages

Default timeout: 25 seconds. Override with `AGENT_BROWSER_DEFAULT_TIMEOUT` (ms).

For slow pages, use explicit waits:

```bash
agent-browser wait --load networkidle    # Wait for network to settle
agent-browser wait "#content"            # Wait for specific element
agent-browser wait --fn "document.readyState === 'complete'"
```

## JavaScript Dialogs

Dialogs block all commands until dismissed. If commands start timing out:

```bash
agent-browser dialog status    # Check for pending dialog
agent-browser dialog accept    # Dismiss it
```

## Security (All Opt-In)

```bash
# Content boundaries (recommended for AI agents)
export AGENT_BROWSER_CONTENT_BOUNDARIES=1

# Domain allowlist
export AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com"

# Output limits (prevent context flooding)
export AGENT_BROWSER_MAX_OUTPUT=50000

# Action policy
export AGENT_BROWSER_ACTION_POLICY=./policy.json
```

## Configuration

Create `agent-browser.json` in project root:

```json
{
  "headed": true,
  "proxy": "http://localhost:8080",
  "profile": "./browser-data"
}
```

Priority: `~/.agent-browser/config.json` < `./agent-browser.json` < env vars < CLI flags.

## Key Environment Variables

| Variable | Description |
|---|---|
| `AGENT_BROWSER_SESSION` | Default session name |
| `AGENT_BROWSER_SESSION_NAME` | Auto-save/load state persistence |
| `AGENT_BROWSER_PROFILE` | Persistent browser profile directory |
| `AGENT_BROWSER_HEADED` | Show browser window (`1` to enable) |
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Operation timeout in ms (default: 25000) |
| `AGENT_BROWSER_IDLE_TIMEOUT_MS` | Auto-shutdown daemon after inactivity |
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | Wrap output in boundary markers |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Comma-separated allowed domains |
| `AGENT_BROWSER_MAX_OUTPUT` | Max characters for page output |
| `AGENT_BROWSER_EXECUTABLE_PATH` | Custom browser path |
| `AGENT_BROWSER_ENGINE` | Browser engine: `chrome` (default), `lightpanda` |
| `AGENT_BROWSER_COLOR_SCHEME` | Color scheme: `dark`, `light` |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 64-char hex key for state encryption |

## Common Patterns

### Form Submission

```bash
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser fill @e1 "Jane Doe"
agent-browser fill @e2 "jane@example.com"
agent-browser select @e3 "California"
agent-browser check @e4
agent-browser click @e5
agent-browser wait --load networkidle
```

### Data Extraction

```bash
agent-browser open https://example.com/products
agent-browser snapshot -i --json       # JSON output for parsing
agent-browser get text @e5             # Specific element text
```

### Visual Debugging

```bash
agent-browser --headed open https://example.com
agent-browser highlight @e1
agent-browser inspect                  # Open Chrome DevTools
```

### Connect to Existing Chrome

```bash
agent-browser --auto-connect snapshot  # Auto-discover running Chrome
agent-browser --cdp 9222 snapshot      # Explicit CDP port
```

### iOS Simulator (macOS only)

```bash
agent-browser device list
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com
agent-browser -p ios snapshot -i
agent-browser -p ios tap @e1
agent-browser -p ios close
```

## Gotchas

- **Refs invalidate on page change** — always re-snapshot after navigation, form submit, or dynamic content load.
- **Shell quoting corrupts complex JS** — use `eval --stdin` or `eval -b` for anything beyond simple expressions.
- **Dialogs block everything** — check `dialog status` if commands start timing out unexpectedly.
- **Default timeout is 25s** — setting `AGENT_BROWSER_DEFAULT_TIMEOUT` above 30000 may cause EAGAIN errors.
- **Close sessions when done** — leaked daemon processes persist. Use `agent-browser close`.
- **State files contain tokens** — add to `.gitignore`, delete when no longer needed.

## Attribution

CLI from [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser). Apache-2.0 license.
