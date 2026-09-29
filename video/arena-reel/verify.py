"""Letter-by-letter check of every command/path shown in the Reel against the brief."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from render import open_page

EXPECTED_COMMANDS = {
    "mkAdd": "/plugin marketplace add https://github.com/irr/arena-mode",
    "install": "/plugin install arena-mode@irrlab.ai",
    "run": '/arena-mode:arena "ta tâche"',
    "shMkAdd": "claude plugin marketplace add https://github.com/irr/arena-mode",
    "shInstall": "claude plugin install arena-mode@irrlab.ai",
    "manualRun": '/arena "ta tâche" n=4 strategy=judge',
}
EXPECTED_PATHS = {
    "src": "skills/arena/SKILL.md",
    "project": ".claude/skills/arena/SKILL.md",
    "user": "~/.claude/skills/arena/SKILL.md",
}

with sync_playwright() as p:
    browser, page = open_page(p)
    cmds = page.evaluate("window.__CMD")
    paths = page.evaluate("window.__PATHS")
    # also check what is actually rendered once typing has finished
    page.evaluate("window.render(19.5)")
    shown_m1 = page.inner_text("#m1-code")
    browser.close()

ok = True
for k, exp in EXPECTED_COMMANDS.items():
    got = " ".join(cmds[k]["lines"])  # visual line breaks are spaces in the real command
    status = "OK " if got == exp else "ERR"
    ok &= got == exp
    print(f"{status} {k:10} {got}")
for k, exp in EXPECTED_PATHS.items():
    status = "OK " if paths[k] == exp else "ERR"
    ok &= paths[k] == exp
    print(f"{status} {k:10} {paths[k]}")
rendered = " ".join(shown_m1.replace("›", " ").split())
print("rendered m1:", rendered)
ok &= rendered == EXPECTED_COMMANDS["mkAdd"] + " " + EXPECTED_COMMANDS["install"]
print("ALL OK" if ok else "MISMATCH")
raise SystemExit(0 if ok else 1)
