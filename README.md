# claude-rules

Marc's portable durable rules and onboarding companion for Claude Code sessions. The canonical source. Each project that uses these rules carries a local copy in its own `claude_rules/` directory and syncs back here when a new lesson is earned.

Repo-committed because the iOS Claude Code sandbox does not persist `~/.claude/CLAUDE.md` between sessions, so a personal rules repo is the closest thing the platform currently provides to true cross-session, cross-project persistence.

## What's in here

| file | purpose |
| ---- | ------- |
| **`claude_user_rules.md`** | The durable behavioral rules. Short and direct. Read this first in any new session. Contains the Hat Rule (ask which role you're in, stay in it) plus other always-applies behaviors (hedge unverified claims, treat pushback as data, run adversarial tests, etc.). |
| **`lessons_learned.md`** | Cross-project narrative wisdom log, append-only. Each lesson opens with the moment it was earned and ends with a "sign that this lesson applies" trigger. Read it before starting any deep investigation. Add to it when a new lesson is genuinely earned (not invented). The principles transcend any one project even when the anecdotes don't. |
| **`getting_started_with_claude.md`** | The longer portable companion. Onboarding for newcomers (install, GitHub basics, first session) + 17 distilled working principles + a "for Claude instances" section with concrete behaviors to apply by default. Read this on a flight. Share with friends new to Claude. |
| **`CLAUDE.md.template`** | Drop-in template for the root of any new project. Tells Claude Code's auto-load to read the rules and lessons from `claude_rules/` in the project. |
| **`bootstrap.sh`** | One-shot setup for a new project. Run it from the new project's root and it creates `claude_rules/`, downloads the rule files into it, and installs `CLAUDE.md` from the template. |
| **`claude_rules_sync.py`** | Drift-detection workflow tool. Run from a project's `claude_rules/` directory to compare the local copies against this canonical repo. Reports what's diverged in either direction (local-ahead or live-ahead). Does not modify any files; you do the actual copy + git ops on a desktop. |

## How to use this repo

### Setting up a new project

Two minutes on a desktop. From inside the new project's root (after `git init` or `git clone`):

```bash
curl -fsSL https://raw.githubusercontent.com/marc-leonti/claude-rules/main/bootstrap.sh | bash
```

That creates `claude_rules/` in the project, downloads the rule files into it, and installs `CLAUDE.md` at the project root from the template. Edit `CLAUDE.md` to fill in project-specific bits, commit, push.

From here on, every Claude Code session in that project reads rules from the local `claude_rules/` — no network fetch needed.

### Adding a new lesson (working in any project)

1. In the project's `claude_rules/` directory, edit the relevant file:
   - Behavioral rule? → `claude_user_rules.md`
   - Narrative lesson with anecdote + sign-this-applies? → `lessons_learned.md`
   - Onboarding-relevant distilled principle? → `getting_started_with_claude.md`
   - Project-specific only (doesn't generalize)? → don't put it here; put it in the project's own `CLAUDE.md` instead
2. Commit the change in the project repo.
3. On your desktop, with both repos cloned:
   ```bash
   # Pull both
   cd ~/code/marc-leonti/claude-rules && git pull
   cd ~/code/<project-name> && git pull
   
   # Promote the changed file from project → claude-rules
   cp ~/code/<project-name>/claude_rules/lessons_learned.md ~/code/marc-leonti/claude-rules/lessons_learned.md
   
   # Push claude-rules
   cd ~/code/marc-leonti/claude-rules
   git add . && git commit -m "sync: lesson from <project-name>" && git push
   ```
4. Verify with the sync script in any other project that uses the rules:
   ```bash
   cd ~/code/<other-project> && python3 claude_rules/claude_rules_sync.py
   ```
   It will report `live-ahead` for files where claude-rules is now newer than the project's local copy. Pull those into the other project the same way (cp the other direction, commit, push).

### Checking sync status

From any project's `claude_rules/` directory:

```bash
python3 claude_rules_sync.py
```

It walks the local files, fetches the live versions from this repo, and reports per-file:
- `in sync` — local matches live, no action
- `diverged` — both exist but differ; shows you the diff and tells you to decide which way recent edits should flow
- `local-only` — file exists locally but not in live repo (new file you might want to promote)
- `live-only` — file exists in live but missing from local (new file you should pull down)

The script does not push for you. It just shows what's different. The actual git ops are manual, on your desktop, with whatever tooling you prefer.

## Why version control?

The iOS Claude Code sandbox does not persist `~/.claude/CLAUDE.md` between sessions. Each new session you start from your phone gets a fresh sandbox with a clean home directory. User-level config files do not survive.

Version control is the only reliable durability mechanism the platform currently provides for cross-project, cross-session rules. This repo plays the role that `~/.claude/CLAUDE.md` would play in a desktop / persistent-home-directory environment, and the per-project `claude_rules/` directories play the role of locally-cached snapshots that allow editing without network access.

If iOS Claude Code adds true persistent user-level config in the future, this whole architecture becomes unnecessary — but the file content (the rules themselves) remains useful.

## License

Do whatever you want with the contents. Re-edit, fork, distribute, share. The principles compound when more people apply and refine them.
