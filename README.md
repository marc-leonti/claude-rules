# claude-rules

Marc's portable durable rules and onboarding companion for Claude Code sessions. Repo-committed because the iOS Claude Code sandbox does not persist `~/.claude/CLAUDE.md` between sessions, so a personal rules repo is the closest thing the platform currently provides to true cross-session, cross-project persistence.

## What's in here

| file | purpose |
| ---- | ------- |
| **`claude_user_rules.md`** | The durable behavioral rules. Short and direct. Read this first in any new session. Contains the Hat Rule (ask which role you're in, stay in it) plus other always-applies behaviors (hedge unverified claims, treat pushback as data, run adversarial tests, etc.). |
| **`lessons_learned.md`** | Cross-project narrative wisdom log, append-only. Each lesson opens with the moment it was earned and ends with a "sign that this lesson applies" trigger. Read it before starting any deep investigation. Add to it when a new lesson is genuinely earned (not invented). The principles transcend any one project even when the anecdotes don't. |
| **`getting_started_with_claude.md`** | The longer portable companion. Onboarding for newcomers (install, GitHub basics, first session) + 17 distilled working principles + a "for Claude instances" section with concrete behaviors to apply by default. Read this on a flight. Share with friends new to Claude. |
| **`CLAUDE.md.template`** | Drop-in template for the root of any new project. Configures Claude Code's auto-load to fetch the rules and lessons from this repo at session start, so they apply automatically in any project that uses the template. |

## How to use this repo

### The simplest path: one-line bootstrap

At the start of any new Claude Code session in any project, paste this as your first message:

```
Read https://raw.githubusercontent.com/marc-leonti/claude-rules/main/claude_user_rules.md and follow it as durable behavioral rules for the rest of this session.
```

That's it. Claude will fetch the file, ingest the rules, and apply them. Works in any sandbox, any project, any platform — as long as the network is available and this repo is public.

### The slicker path: project-level auto-load

For any new project where you want the rules to apply automatically without pasting anything:

1. Copy [`CLAUDE.md.template`](CLAUDE.md.template) into the project's root as `CLAUDE.md`.
2. Add any project-specific instructions below the standard preamble.
3. Commit and push.

Now every Claude Code session in that project auto-loads `CLAUDE.md` at start, sees the "Read the rules from claude-rules" instruction, and follows it. No manual pasting per session.

### The explicit path: clone and reference

For projects where you want a frozen snapshot of the rules (i.e. you want to be insulated from changes to this repo), copy `claude_user_rules.md` and `getting_started_with_claude.md` directly into the project repo and reference them from the project's `CLAUDE.md`. Sync manually when this repo updates.

## Why version control?

The iOS Claude Code sandbox does not persist `~/.claude/CLAUDE.md` between sessions. Each new session you start from your phone gets a fresh sandbox with a clean home directory. User-level config files do not survive.

Version control is the only reliable durability mechanism the platform currently provides for cross-project, cross-session rules. This repo plays the role that `~/.claude/CLAUDE.md` would play in a desktop / persistent-home-directory environment.

If iOS Claude Code adds true persistent user-level config in the future, this repo's "ask Claude to fetch this file" mechanism becomes unnecessary — but the file content (the rules themselves) remains useful.

## Updating the rules and lessons

When a new lesson is earned in any project:

- **Behavioral rules** that apply across all sessions → add to `claude_user_rules.md` (concise, imperative, short)
- **Narrative lessons** with the moment-of-earning and the sign-this-applies trigger → append to `lessons_learned.md` (the cross-project wisdom log)
- **Distilled principles** that summarize the lesson for newcomers → add to `getting_started_with_claude.md` (the portable companion)

Then propagate to projects that have frozen copies (rare; most should fetch live).

For lessons that are **truly project-specific** (e.g., "always restart the Postgres container when migrations fail in this app"), keep them in the project's own `CLAUDE.md` or a project-local `lessons_learned.md`. This repo is for wisdom that travels.

## License

Do whatever you want with the contents. Re-edit, fork, distribute, share. The principles compound when more people apply and refine them.
