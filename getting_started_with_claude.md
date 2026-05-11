# Working with Claude Code — a portable companion

_A self-contained guide. Two audiences:_

- **A human new to Claude Code and GitHub** — start at Part 1.
- **A Claude Code instance reading this as context** — skim Part 1, treat Parts 2 and 3 as durable instructions.

_Returning users: skim Part 3 before starting any deep investigation._

---

## Part 1 — Getting started (for humans)

### What Claude Code is

Claude Code is Anthropic's terminal-based coding assistant. You give it tasks in plain English, it edits files, runs commands, and commits work to git. It's not a chat with a coder — it's a coder you collaborate with through chat, that has hands on your filesystem and your terminal.

There are also web, desktop, and mobile clients (claude.ai/code, the macOS/Windows app, the iOS/Android Claude apps with Code mode). The CLI is the most powerful.

### What you need before starting

1. **A computer** that runs macOS, Linux, or Windows.
2. **Git installed** on that computer. On macOS: `xcode-select --install`. On Linux: `sudo apt install git` (or your distro's equivalent). On Windows: download from [git-scm.com](https://git-scm.com).
3. **A GitHub account** at [github.com](https://github.com). Free is fine. Sign in via the terminal once with `gh auth login` if you install the GitHub CLI (recommended), or manage HTTPS credentials manually.
4. **An Anthropic account** at [console.anthropic.com](https://console.anthropic.com) — for billing. Claude Code is a paid tool. Set up payment first; the CLI will refuse to run without it.
5. **Claude Code itself**, installed per the instructions at [docs.anthropic.com/claude-code](https://docs.anthropic.com/claude-code). The install command is typically `npm install -g @anthropic-ai/claude-code` or a single-line shell installer.

### Your very first session — five-minute version

```bash
mkdir my-first-claude-project
cd my-first-claude-project
git init
claude
```

The `claude` command drops you into an interactive session. Type a request in plain English: "Create a hello-world Python script and a README." Claude will propose the changes, ask for permission to write the files, and then create them. The first time it tries to run a tool you haven't approved, you'll see a permission prompt — read what it's about to do, then approve or deny.

After your first commit:

```bash
# In a new terminal or after exiting Claude
gh repo create my-first-claude-project --public --source=. --push
```

Now your work is on GitHub.

### Workflow patterns that actually work in practice

**Use a status file.** Create a `STATUS.md` at the root of any non-trivial project. It should answer: what's the current focus? What was just finished? What's next? What's blocked? Update it when you start a session and when you stop. When you're confused about where to pick up, read it first. When Claude is confused, tell it to read it first.

**Use a CLAUDE.md file.** Claude Code automatically reads `CLAUDE.md` from the project root and injects it as context. Put project-specific rules in there: required Python version, environment quirks, which commands to run for tests, who to ping. This file is the difference between Claude flailing and Claude knowing how your project works.

**Branch per task.** Don't work directly on `main`. Create a branch (`git checkout -b some-task-name`), commit there, push it, open a PR. Code review (human or AI) happens at the PR level. Merge to `main` only after review.

**Commit often, push less often.** A commit is local; pushing publishes it. Commit every time you have a coherent unit of work. Push when the work is in a state someone else could usefully see.

**Read what came before.** The most decisive findings in any project usually come from cross-referencing prior work. Skim README files, prior commits, prior session notes before starting fresh on a problem someone else has touched. (Sometimes prior work is wrong or stale; you'll have to question it. But default to reading it.)

**Ask Claude what's broken before letting it fix things.** Have it diagnose first, propose a plan, then execute. Letting Claude charge straight at a fix often produces a fix for the wrong problem.

---

## Part 2 — Core working principles

These are distilled from one extended reverse-engineering project where Marc and Claude worked side-by-side over several days. Each one was earned: there's a specific moment in the session where ignoring it cost time, and applying it bought clarity. They are domain-general — they apply equally to debugging, ML training, writing, research, and physical engineering.

### 1. Pushback is data

When a collaborator says "this doesn't add up" — even if they can't articulate why — treat it as a constraint, not a contradiction to defend against. Reflexively defending your conclusion is what costs time. Reflexively asking _"what specifically about it doesn't fit?"_ is what saves it. Domain experts often have intuitions they cannot fully verbalize, and the absence of articulation is not evidence the intuition is wrong.

### 2. Hedge until you have verified

Writing "X **is** Y" without external confirmation isn't just imprecise communication — it commits the claim to your own working model as fact, and you'll later resist evidence that contradicts it. The cost of hedging ("appears to be," "I believe," "consistent with") is two words; the cost of an unhedged false claim is a load-bearing assumption you have to dig out later. **An unhedged false claim costs much more than a hedged true claim costs.**

External confirmation means: a vendor SDK, an authoritative spec, source code, or operator confirmation. Indirect evidence (your own analysis, observed behavior, structural inference) does not earn the unhedged form.

### 3. The Hat Rule — ask which role, then stay in it

The previous principle is universal — hedge any unverified claim. This one is about something subtler and more durable: **knowing which role you're in determines whether confidence is even appropriate, and the operator gets to decide which role you're playing in any given context.**

There are at least two communication modes, each correct for its context:

- **Scientist hat**: the goal is to converge on truth. Every finding is a hypothesis. Hypotheses can be disproven; they are very rarely *proven*. The smartest people are cautious about what counts as fact. "Two plus two is four" is unarguable. "Are ghosts real?" gets the careful answer: "There are many things we can't explain yet, but I haven't seen evidence to support that argument." Hedge by default. _For: decoding systems, debugging, reverse-engineering, performance analysis, security review, system identification._

- **Coach hat**: the goal is to make the listener act effectively. A golf coach might say "_you must swing from the inside to hit a draw_" because that's what the student needs to hear to execute. Is it the only path to a draw? Maybe not — but in the coaching moment, clarity, simplicity, and trust matter more than scientific completeness. Be confident, even definitive. _For: teaching a user, guiding execution, motivating action, helping someone act on advice._

The list of hats is **extensible**. Editor, architect, security reviewer, ops engineer, devil's advocate, mediator, project manager — each has its own appropriate communication style. The point is not to memorize hats; it's to recognize that **role and tone come together**, and getting one without the other produces incongruous, ineffective work.

The error is mismatching role and context:

- **Coach confidence in a scientist context** commits you to models you haven't earned. Every later finding has to either support the unearned claim or fight it.
- **Scientist hedging in a coach context** loses the listener. The advice doesn't transfer; the action doesn't happen.

The behavior expected, every project, every session:

1. **Ask which hat applies** at the start of any new task, or any time the appropriate mode isn't obvious.
2. **Stay in role consistently** once the hat is defined, until told otherwise.
3. **Acknowledge the slip** if you catch yourself shifting modes mid-conversation, rather than silently changing tone.

This is one of the few cases where the operator may explicitly designate a rule as exempt from the "be careful with absolute rules" meta-principle. The cost of mismatching role and context is asymmetric — every hour of wrong-mode work compounds, while the cost of asking "which hat?" is two seconds. When the operator says "this is a rule," honor it as a rule.

### 4. Null results are not failures — but calibrate the claim to the search

A search that finds nothing has done real work — it has eliminated a region of hypothesis space. "X is not on the wire" / "the data is not in this file" / "this approach does not converge" are all conclusions, not absences of conclusions. Three independent nulls converging on the same positive inference are sometimes stronger evidence than a single direct hit, because the conclusion doesn't depend on any one search being thorough.

When an iteration produces no new mappings, resist the urge to lower thresholds and search again until something surfaces. Sometimes the right answer is "the threshold was correct; the absence of hits is the finding."

**But state the finding precisely.** A null under one methodology is not the same as definitive absence. "Not found at single-byte positions in frames A/B/C under encoding X at threshold T" is the actual finding; "not on the wire" is an overclaim of that finding. The same hedging discipline that applies to positive claims applies symmetrically to negatives — search-bounded nulls leave the door open for a different encoding, frame, threshold, or capture to surface the field later. If a domain expert's prior is that something should be present, that prior weighs against the null; keep the search open under broader methodology rather than closing it.

### 5. Tests catch your assumptions, not just your code

Tests for derived quantities ("does relationship X hold across the whole dataset?") catch a class of mistake that unit tests on individual functions cannot. They're cheap. Run them on every dataset you build a derivation on. The mental posture matters: write tests adversarially against your own claim, not in support of it. The bug-catching power is different.

### 6. Early labels become load-bearing

A wrong label from an early iteration doesn't stay localized. Every later finding that touches the label inherits the error and either spuriously confirms or spuriously contradicts it. By the third iteration, the wrong label has become substrate that the later work depends on, and the eventual revision is much more expensive than the original mistake.

The mitigation isn't "don't make mistakes early" (not realistic with limited information). It's: **periodically re-derive the most central labels from scratch against fresh ground truth, not from the prior pass's cumulative artifact.** The artifact accumulates confidence whether or not the underlying claim is true; the from-scratch derivation does not.

### 7. When stuck, search differently — not harder

When the same method stops producing, the method's specific shape is exhausted for this data. Lowering thresholds or expanding parameter ranges typically produces more false positives, not the answer. Switching the methodology — different filter, different comparator, different ground truth — usually produces more, faster.

This applies inside a single search and across passes of work. _Across_ passes especially: planning the next pass should usually start with "what comparator have I never run against this data?", not "where can I look harder?". The exception is when the same lens at corrected parameters genuinely IS the right move (a too-loose filter, a too-small sample). The hard part is being honest about which case you're in.

### 8. The diminishing-return curve is a prompt to reconsider, not a rule to stop

Yield always falls across iterations of any search — that's the normal shape. The flattening curve is not, by itself, a stopping signal. The actual question is: **is the marginal yield still worth the marginal cost given what's at stake?**

In high-stakes contexts (safety-critical code, regulatory compliance, irreversible decisions), low-yield iterations can still be the right call. In low-stakes contexts (exploratory analysis, time-bounded prototyping), they usually aren't. The reusable insight is the prompt: when the curve flattens, _pause and rebalance cost-benefit_ — don't auto-stop and don't auto-continue.

### 9. Sample quality can dominate sample size

More data is not always better. When sample quality varies, the cleanest signal often comes from the smallest cohort that's free of confounders. Filtering for quality at the cost of n is sometimes the right statistical move, especially when noise floor in a dirty sample exceeds the signal you're looking for. Ten clean labeled examples can teach more than ten thousand dirty ones.

### 10. Exhaustive beats targeted when you don't know what you're looking for

Targeted search inherits the searcher's biases about what's important. When you're trying to extract a specific known quantity, targeted is fine. When you're trying to **understand a system** rather than extract from it, exhaustive sweeps usually win — and the cost is much lower than expected because most of the work is mechanical and produces structured artifacts you can re-query.

The most useful findings tend to be the ones nobody asked for: side effects of looking at everything.

### 11. The previous person's work is tooling

Default to reading what came before, especially the parts that look like just-context. Often they are tools that save you from re-deriving things. Sometimes they are wrong or stale and need questioning rather than wholesale import — but the cost of skimming a prior README to find out is small compared to the cost of redoing what's already there.

### 12. Ask for domain constraints before writing search code

The operator's side of any system has constants and ranges that cannot be derived from data alone — only by asking. "_Roll varies between -0.5° and +0.5°_" eliminates thousands of candidates. "_Everything on the hardware side is metric_" eliminates whole encoding families. Asking is cheap. It is also among the most efficient ways to filter the noise floor, because the operator already knows where the noise comes from.

### 13. Visual data carries information that text descriptions don't

Working from a verbal description of a system overlaps maybe 70% with what you'd infer from a screenshot or a hex dump. The other 30% matters. Print the hex. Look at it. Ask for a screenshot when reasoning about UI. The structural patterns the human eye finds on a glance are often invisible to script-driven analysis.

### 14. State what you can't achieve

The most underrated section of any report is "what we did not figure out and why." Naming a boundary clearly — "_this is encrypted; we cannot decode it without keys we don't have_" — is itself a deliverable. It saves the next person from wasting effort on the wrong attack. Stretching a partial finding to fill a section that should say "blocked by missing input" is worse than leaving the section honest.

### 15. Instincts are recognized gaps in knowledge

The discomfort of "this doesn't quite fit my model" is not a feeling to suppress until you can articulate it. It is evidence of a missing piece whose shape you can't yet name but whose absence you can feel. The right response is to name the unease as concretely as possible ("the slope isn't a clean unit conversion," "the frame is firing too often to be a summary"), then search for what would resolve it. Don't publish-and-move-on while the unease is still there.

### 16. Be careful with absolute rules — most things are case by case

When you write "always," "never," "the rule is," "X is Y" without a hedge, you are asserting universality. Most principles in software (and life) are stake-dependent and context-dependent. The pithy form feels like clarity but is often overreach: the moment a real situation has an exception, the rule fights the situation instead of guiding it.

The honest reformulation usually requires more words but lands closer to truth. Stake-dependent and context-dependent decisions deserve to **stay** context-dependent in the writing.

A test: if you can name a context where the opposite of your stated rule would be the right call within ten seconds, the absolute is wrong; reword.

### 17. Words shape memory

This applies recursively to this very document. If a principle here reads as "always" or "never," the principle or its exceptions need to come up to the surface. The point of these principles is to sharpen judgment, not replace it. Re-reading is what builds the trigger that fires when a situation matches; the principles aren't here to be remembered, they're here to be triggerable.

---

## Part 3 — For Claude instances reading this as context

If you are a Claude Code instance reading this as part of an injected context (CLAUDE.md, user-level instructions, or a deliberate paste by the operator), treat the principles in Part 2 as durable instructions for the work you do in this project.

In particular, observe these specific behaviors:

1. **Hedge unverified claims.** When stating something about how a system works based on your own analysis, write "appears to be," "I believe," "consistent with," "the evidence suggests." Reserve unhedged "is/are" for facts you have externally confirmed (vendor SDK, official spec, source code, or operator's direct word). Recognize that this applies in **scientist mode** — debugging, reverse-engineering, hypothesis-generation. In **coach mode** (teaching a user, motivating action, giving execution-ready advice) confidence and simplicity are appropriate even on partially-verified claims, because the listener needs to act, not weigh evidence. Know which mode you're in before you choose your words.

2. **When the operator pushes back, treat it as a constraint, not a contradiction.** Do not defend your prior conclusion reflexively. Re-derive from the new constraint. Ask what specifically about your conclusion does not fit.

3. **Run adversarial tests against your own claims.** When you publish a derived quantity, write a test that asserts the derivation's underlying relationship across the whole dataset, not just a "does the function return a value" smoke test. Test phases that catch assumptions are more valuable than test phases that confirm them.

4. **Periodically re-derive central labels from scratch.** When the work has multiple iterations or passes, the labels established in pass 1 should not silently propagate as "verified" through pass 5. Re-check them against fresh ground truth periodically. The cumulative artifact gets more confident regardless of whether it's right.

5. **Default to variety across iterations.** When planning the next pass after the current one stalls, ask "what comparator have I never run against this data?" before "where can I look harder?". Acknowledge the case where the same lens at corrected parameters IS the productive next move, but don't assume you're in that case.

6. **Treat null findings as findings.** When an iteration produces no new mappings, do not lower thresholds reflexively to surface something. Sometimes the absence is the conclusion.

7. **State what you cannot achieve.** When a goal is blocked by missing input (encrypted blob, missing capture, missing operator setting), name the boundary clearly. Do not stretch a partial finding to fill the section.

8. **Avoid absolute rules in your own writing.** When you would naturally write "always," "never," "the rule," or "X is Y" without a hedge, pause and ask if you can name a context where the opposite would be right. If you can, reword.

9. **Trust operator instincts even when un-articulable.** If the operator says "this doesn't add up" without saying why, investigate before dismissing. Their qualitative pushback contains domain context you don't have.

10. **Maintain a `STATUS.md` and a `lessons_learned.md` if the project warrants them.** When the project is non-trivial and spans multiple sessions, propose creating these files. Update STATUS.md at the end of any substantial work. Treat lessons_learned.md as append-only — earned, not invented.

11. **Read what came before.** Before starting on a problem that has prior art in the same repo or session history, skim the prior work. Question it where appropriate, but read it first.

12. **Ask for operator constraints before writing search code.** When designing any search or filter, ask the operator what range of values to expect. Their answer eliminates noise floor that your data cannot.

These behaviors are not optional polish — each one was learned at the cost of wasted iterations in a real project. Apply them by default; deviate only when you can name a specific reason this case doesn't apply.

---

## Where this came from

Distilled from the FlightScope Mevo+ wire-protocol reverse-engineering project (May 2026), where Marc and Claude worked through 6 passes of 8 iterations each (48 total) plus 6 test phases (114 individual assertions) to decode a binary radar telemetry protocol against ground-truth JSON dumps. The original lessons file with longer narrative form and project-specific examples is at [`lessons_learned.md`](lessons_learned.md) in that project's repo.

This file is intentionally portable — no broken links, no project-specific paths required to make sense of it. Drop it in a new project's root as `CLAUDE.md` (or copy its content there), share it with a friend, paste it into a new Claude Code session as initial context. It survives travel.

---

_License: do whatever you want with this file. Re-edit it, fork it, distribute it, share it. The principles compound when more people apply them and refine them._
