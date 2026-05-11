#!/usr/bin/env python3
"""
claude_rules_sync.py — check whether this project's local rules copy is in
sync with the canonical claude-rules repo.

This script is part of the rules-repo distribution. It ships into every
project that uses Marc's claude-rules system, and into the claude-rules
repo itself.

Run it from the directory it lives in. It does not modify any files; it
only reports drift. The actual copying / committing / pushing is done by
you on a desktop with git.

Workflow (desktop-driven, no mobile):
  1. Pull both repos (this project AND marc-leonti/claude-rules).
  2. Run this script in your project's claude_rules/ directory.
  3. Read the report — it tells you which files are diverged.
  4. For each diverged file, decide which way the recent edit should flow:
     - If you edited locally (new lesson earned in this project, etc.):
       cp claude_rules/<file> ../claude-rules/<file>
       cd ../claude-rules && git add . && git commit -m '...' && git push
     - If live is ahead (rules-repo updated from elsewhere):
       cp ../claude-rules/<file> claude_rules/<file>
       cd .. && git add claude_rules/<file> && git commit -m '...' && git push
  5. Re-run this script. Should report "everything in sync" now.

The script does not push for you. It just shows you what's different and
lets you decide direction. Direction matters: pushing the wrong way wipes
out the recent edit.
"""
from __future__ import annotations

import difflib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_OWNER = "marc-leonti"
REPO_NAME = "claude-rules"
BRANCH = "main"

# Files we expect to find in BOTH the local working copy AND the live repo.
TRACKED_FILES = (
    "README.md",
    "claude_user_rules.md",
    "lessons_learned.md",
    "getting_started_with_claude.md",
    "CLAUDE.md.template",
    "claude_rules_sync.py",  # the script tracks itself so versions stay in sync
    "bootstrap.sh",
)


def fetch_live(filename: str) -> tuple[str | None, str]:
    """Return (content, status_label). content is None if fetch failed."""
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{filename}"
    try:
        result = subprocess.run(
            ["curl", "-sS", "-L", "-w", "\n%{http_code}", url],
            capture_output=True, text=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except FileNotFoundError:
        return None, "curl not available"

    if result.returncode != 0:
        return None, f"curl exit {result.returncode}"

    body, _, status = result.stdout.rpartition("\n")
    status = status.strip()
    if status != "200":
        return None, f"HTTP {status}"
    return body, "ok"


def main() -> int:
    local_dir = Path(__file__).resolve().parent

    print(f"=== claude-rules sync check ({datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}) ===")
    print(f"Local: {local_dir}")
    print(f"Live:  github.com/{REPO_OWNER}/{REPO_NAME}@{BRANCH}")
    print()

    in_sync: list[str] = []
    diverged: list[tuple[str, str, str]] = []     # (filename, local_content, live_content)
    local_only: list[str] = []                    # in local but live returns 404
    live_only: list[str] = []                     # in live but missing from local
    failed: list[tuple[str, str]] = []            # (filename, reason)

    for filename in TRACKED_FILES:
        local_path = local_dir / filename
        live_content, status = fetch_live(filename)

        local_exists = local_path.exists()
        live_exists = live_content is not None

        if not local_exists and not live_exists:
            failed.append((filename, "missing from both local and live"))
            continue

        if local_exists and not live_exists:
            if "404" in status:
                local_only.append(filename)
            else:
                failed.append((filename, f"local ok, live fetch failed: {status}"))
            continue

        if live_exists and not local_exists:
            live_only.append(filename)
            continue

        local_content = local_path.read_text(encoding="utf-8")
        if local_content == live_content:
            in_sync.append(filename)
        else:
            diverged.append((filename, local_content, live_content))

    # === SUMMARY ===
    total = len(TRACKED_FILES)
    print("SUMMARY")
    print("-------")
    print(f"  in sync:     {len(in_sync):>2} / {total}")
    print(f"  diverged:    {len(diverged):>2}  (need attention)")
    print(f"  local-only:  {len(local_only):>2}  (in local but not in live repo — promote up)")
    print(f"  live-only:   {len(live_only):>2}  (in live but not in local — pull down)")
    print(f"  failed:      {len(failed):>2}")
    print()

    if in_sync:
        print(f"  In sync: {', '.join(in_sync)}")
        print()
    if failed:
        print("  Failed:")
        for f, reason in failed:
            print(f"    - {f}: {reason}")
        print()

    if not diverged and not local_only and not live_only:
        print("Everything in sync. Nothing to do.")
        return 0

    # === DIVERGED ===
    if diverged:
        print("DIVERGED")
        print("--------")
        print("These files differ between local and live. For each one, decide which")
        print("direction the recent edit should flow, then copy the file accordingly")
        print("on your desktop and push.")
        print()
        for filename, local_content, live_content in diverged:
            print(f"### {filename}")
            local_lines = local_content.splitlines(keepends=True)
            live_lines = live_content.splitlines(keepends=True)
            diff = difflib.unified_diff(
                live_lines, local_lines,
                fromfile=f"live/{filename}", tofile=f"local/{filename}",
                n=3,
            )
            diff_text = "".join(diff)
            if not diff_text:
                print("  (line content identical; trailing whitespace or encoding differs)")
            else:
                lines = diff_text.splitlines()
                shown = lines[:60]
                print("\n".join(shown))
                if len(lines) > 60:
                    print(f"... ({len(lines) - 60} more lines)")
            print()

    # === LOCAL-ONLY ===
    if local_only:
        print("LOCAL-ONLY")
        print("----------")
        print("These files exist in this project but not in the live rules repo.")
        print("To promote (assuming they should be canonical), on desktop:")
        print("  cp <project>/claude_rules/<file> <claude-rules-clone>/<file>")
        print("  cd <claude-rules-clone> && git add . && git commit -m '...' && git push")
        print()
        for filename in local_only:
            print(f"  - {filename}")
        print()

    # === LIVE-ONLY ===
    if live_only:
        print("LIVE-ONLY")
        print("---------")
        print("These files exist in the live rules repo but not in this project.")
        print("To pull them down, on desktop:")
        print("  cp <claude-rules-clone>/<file> <project>/claude_rules/<file>")
        print("  cd <project> && git add claude_rules/<file> && git commit -m '...' && git push")
        print()
        for filename in live_only:
            print(f"  - {filename}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
