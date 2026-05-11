# Lessons Learned

_A cross-project working document of insights Marc and Claude have arrived at together — things tried because of a nudge, then found to work. Read these often. Over time they become instincts, which are not knowledge but recognition of where knowledge is missing._

> **Scope:** this file is the durable cross-project wisdom log. Lessons added when a new one is earned, not invented. Each lesson opens with the moment that earned it (often a quote from Marc) and ends with a "sign that this lesson applies" trigger. The project-specific anecdotes are anchors that make the lessons memorable; the principle in the body of each lesson is intended to transfer.
>
> **Originally seeded from** the CaddieAI / FlightScope Mevo+ wire-protocol reverse-engineering project (May 2026). New lessons from later projects get appended in chronological order with a project-of-origin note.
>
> **For project-specific lessons** that don't generalize (e.g., "always restart the Postgres container when migrations fail in this app"), keep them in the project's own `CLAUDE.md` or a project-local `lessons_learned.md` instead. This file is for the wisdom that travels.

---

## On Pushback

> _Marc has instincts he can't always explain, but he is human and he thinks like a human, so he is sometimes good at predicting what other humans would or would not do. When Marc pushes back, he is usually right that something doesn't add up._

Three times in this project Marc pushed back on something I'd written:

- I'd concluded HI/VI was computed client-side from raw pixel tracks using a calibration the device doesn't ship. He said "I honestly have a hard time believing the people at FlightScope would require a client to maintain some sort of calibration table … it just doesn't seem feasible to me." My instinct was to defend the analysis. He was right. The architecture I'd inferred was implausible for how launch monitors actually ship; once I went back and looked harder, I found the FTP file path I'd missed, and the more honest model that fit both the wire-side null and how a commercial product is normally built.

- I'd been searching wire bytes in inches because the CSV column was in inches. He said "I know the CSV reports this metric in inches, but I strongly doubt the value you're looking for is going to be an inches. Everything on the hardware side is going to be metric." Of course it would. I had been blind to the conversion because the target value was right there in the CSV. The bias he caught was that I was searching in display units, not measurement units.

- I'd inferred from an all-zero `cameraCalibration` block that the calibration must live client-side. He said "I have the ability to calibrate the camera/video. I never adjust the calibration. That could be one reason why it's always zeros." My evidence was an absence-of-non-zero. His evidence was the existence of a UI knob he never touched. Same observation, fundamentally different model.

The pattern: when Marc pushed back, my reflex was to defend. The right move every time was to immediately treat the pushback as a constraint and re-derive. Defense costs me; trust pays. He has decades of context I don't have. He doesn't always know why something is wrong, but the discomfort is genuine signal.

> **Sign that this lesson applies:** I'm explaining why my conclusion is right instead of asking what specifically about it doesn't fit.

---

## Exhaustive beats targeted when you don't know what you're looking for

I resisted the "decode everything" mandate internally. It felt wasteful to map bytes whose meaning we didn't need. The plan I'd have written for myself was: identify the high-value targets (HI/VI, mode flags, listener-mode handshake) and search for those.

Five of the most useful findings would not have come out of that plan:

- The `D4@15 launchSpeed overflow flag` was a single bit on a byte I'd have skipped because I had a working overflow heuristic. The exhaustive bit-level pass surfaced it as a side effect of looking at every binary-valued byte in the frame.
- The architectural pattern that "the byte before each u16 field is its sign-extension or overflow byte" only became visible because I scanned every offset for hidden duplicates of every known field. Targeted search would never have framed the question that way.
- `UDP/1248 is a service-discovery beacon` saved hours of speculative work — but I only discovered it because the iter-9 mandate said "extract every byte from every channel," not "find the data we need."
- The structural finding that EF[0:120] is densely populated when the LM is in spin-estimate mode and zeroed otherwise came from a bucketed full-frame byte-diff, not a "find the spinIsEstimate flag" search.
- That `0xE8` carries non-CSV data was a null I never would have established with a targeted approach. The null itself constrains the search space.

Targeted search inherits the searcher's biases about what's important. Exhaustive search doesn't. When the goal is to understand a system rather than extract a known quantity, exhaustive wins — and the cost is much lower than I expected because most of the work is mechanical sweeps that produce structured artifacts you can re-query.

> **Sign that this lesson applies:** I'm prioritizing what to look for, but I don't yet know enough about the system to prioritize correctly.

---

## Null results are not failures

I had a strong bias that each iteration should produce a new mapping. I treated null-result iterations as failures-to-find rather than as findings.

But the nulls did real work:

- "Float encodings don't appear in this protocol" — confirmed in iter 1. I never had to search floats again. Saved compute and search-space pollution in every subsequent iteration.
- "Multi-bit packed flags don't exist in per-shot frames" — confirmed in iter 13. Constrained the model of how categorical info is encoded.
- "0xE8 doesn't carry any of the 26 numeric CSV columns" — confirmed across DR, IR, WG, HY subsets in iters 4 and 11. Tells us the frame is something else entirely.
- "C→M `0xEE` doesn't byte-match any M→C sub-record" — confirmed in iter 6. Killed my "motion echo" hypothesis cleanly.
- "Three null hypotheses for HI/VI (not on TCP/5100, not in `.fsb`, not in `.mp4` metadata) converge on one positive inference" — the strongest piece of evidence in the whole investigation, and every component of it was a null.

Three null results triangulate to a positive conclusion that no single positive finding could match — because the conclusion doesn't depend on any one search being thorough. Independent failures that all rule out the same family of hypotheses are stronger than a single hit.

**But calibrate the strength of the negative claim to the search you actually ran.** A null under one methodology is not the same as definitive absence. "X is not on the wire" claims more than "X is not at any single-byte position in frames D4/D9/ED/EF/E8 under encodings A/B/C at EPS=1e-3" — but the second is the actual finding. The shorter form is more memorable and more easily overclaimed. A search-bounded null leaves the door open for the field to appear at a different encoding, in a different frame, at a different threshold, or in a future capture. Marc caught this twice on the FlightScope project: first when "the drift is" got walked back to "the drift could be," then again when "Confirmed not on wire" had to be walked back to "not yet found under these methodologies" for `clubLowPoint`, `postClubNumSpeedPoints`, and others — fields he expected to be on the wire, just not in the search space I'd covered. The same overclaim failure mode applies to negatives that applies to positives; hedge symmetrically.

> **Sign that this lesson applies:** I'm anxious that an iteration "didn't find anything" and tempted to lower my threshold to surface something. The threshold is correct. The lack of hits is the finding — but state the finding as "not found under these encodings/frames/thresholds," not as "not on the wire." If the operator's prior is that a field SHOULD be there, that prior weighs against the null and you should keep the search open under broader methodology.

---

## Sample quality can dominate sample size

Standard advice: more data is better. But in the per-club correlation hunts, the cleanest signal came from the smallest cohort. **Six driver shots** beat 48 mixed-club shots for finding `Swing H`, `Swing V`, and `Low Point`.

Why: drivers have unbroken radar locks; FlightScope's documentation flags wedges as cases where some swing-plane fields "may not calculate properly." Mixing wedges into the cohort injected noise that masked the wire-CSV mapping.

Larger samples are not a free benefit when sample quality varies. Selecting for quality — even at the cost of n — is sometimes the better statistical move. The same lesson would apply to a noisy ML training set: ten clean labeled examples can be more useful than ten thousand dirty ones, because the noise floor in the dirty set may exceed the signal you're trying to find.

> **Sign that this lesson applies:** the cross-shot correlations are stuck at r ≈ 0.6 and adding more data isn't helping. The fix may be filtering for the cleanest subset, not gathering more samples.

---

## Tests catch your assumptions, not just your code

I had `Spin Loft = Loft − AOA` written down as a "verified derivation". When Test Phase 1 ran the internal-consistency check across 48 shots, it failed by ±0.5° on 20 of them. That kicked me back to FlightScope's documentation, which said Spin Loft is "approximately defined by the difference between the 3D angle of attack and 3D dynamic loft" — a complex 3D derivation, not a simple 2D subtraction.

I was about to ship a wrong derivation downstream. The test caught the assumption I'd built the code on, not a bug in the code itself.

The lesson generalizes: tests for derived quantities ("does Smash = Ball/Club hold across all shots?") catch a class of mistake that unit tests on individual functions cannot. They're cheap. They should be standard. Two of the three mistakes the test phases caught in this project were wrong assumptions, not wrong code.

> **Sign that this lesson applies:** I'm about to publish a derived quantity, and the only test I've written is "does the function return a value?". Add one that asserts the relationship the derivation depends on, and run it across the whole dataset.

---

## Early labels become load-bearing. Re-derive periodically.

In pass 1 of the wire-decode I labelled `D4@43` as `backspinRPM`. That label survived into pass 2, into the v1 deliverable, into the Test Phase 1 that "validated" it, and into pass 2's deeper analysis that built on top of it — until pass 3 introduced FSConnect debug JSON as fresh ground truth and the label revealed itself as `landingSpinRPM.X` (different metric, off by 1-2 rpm from `backspinRPM` in a consistent direction across all 10 shots).

The cost of that one mistake wasn't one mistake. Every later finding that touched D4@43 inherited the wrong label, and the wrong label had become load-bearing — the test phase that "passed" had compared the wire bytes against `backspinRPM` derivations, found close-but-not-exact agreement, attributed the gap to "spin computation noise," and moved on. The mislabel had successfully camouflaged itself by being _almost_ right. Two passes worth of confidence accumulated around it.

When the catch finally happened, I had to audit every prior conclusion that referenced D4@43, and re-derive several mappings that had been "verified" against the corrupt anchor. That work was much more expensive than the original mistake.

The general form: **a wrong label from an early pass doesn't stay localized to that pass. It becomes the substrate that every later pass builds on, and each new finding clusters around it as load-bearing.** The longer a wrong label survives, the more findings depend on it, and the more expensive the eventual revision.

The mitigation isn't "don't make mistakes in pass 1" — that isn't realistic with limited information. It's: **periodically re-derive the most central labels from scratch, not from the prior pass's cumulative artifact.** The artifact accumulates confidence with each iteration regardless of whether the underlying claim is true. The from-scratch derivation against fresh ground truth does not. When the two diverge, the artifact is the one that's wrong.

The deeper the conclusion-stack on top of an early label, the more important the periodic re-check. By pass 6 I was making decisions that depended on findings from pass 3 that depended on findings from pass 1. If pass 1 was wrong, pass 6 inherited the error silently. The only insurance was occasionally going back to the wire bytes themselves, with whatever the most recent ground-truth source was, and asking "do I still believe what pass 1 said about this byte?".

> **Sign that this lesson applies:** I'm building pass-N conclusions on top of pass-(N-1) conclusions on top of pass-1 conclusions, and I haven't recently re-derived the pass-1 conclusions against fresh ground truth. The deeper the stack, the more important the periodic re-derivation. And the more confident the cumulative artifact has become, the less I should trust its self-assessment.

---

## When stuck, search differently — not harder

When iter 4's correlation hunt across all shots returned no hits for Swing H / Swing V / Low Point, my reflex was to lower the threshold and search again. That would have produced more false positives, not the answer.

What worked was changing the search axis: not "more shots, lower threshold" but "fewer shots, restricted to a clean cohort." That's a different question, not a more thorough version of the same question.

The 16 iterations of this project produced their findings because each iteration changed the methodology, not the parameters. Float vs integer. Single-bit vs multi-bit. D4-source vs ED-source. Per-shot vs multi-per-shot. C→M vs M→C. Time-series vs per-shot summary. Each new methodology surfaced a different class of finding that no other could have.

When the same method stops producing, the method is exhausted. Switch.

> **Sign that this lesson applies:** I'm running the same search with different parameters and the results aren't getting better. Stop. Ask: what else could the answer look like, structurally? Then design a search for that shape.

---

## Across passes, rotate the lens — not just within passes

The "search differently — not harder" lesson lives _within_ a pass: switch from float to integer, from single-bit to multi-bit, from D4-source to ED-source. That's local methodology rotation when one approach plateaus.

The wider version is across passes: **iteration count compounds only when each pass uses a fundamentally different operator on the data than the prior one.** Repeating the same family of operator with finer parameters has rapidly diminishing returns; rotating the operator has near-linear returns until the data itself runs out.

This project ran six passes:

- Pass 1: structural analysis (bit patterns, byte ranges, encoding signatures) → ~25 mappings
- Pass 2: deeper structural analysis (cross-frame consistency, sub-record layouts) → ~5 more
- Pass 3: ground-truth alignment (FSConnect JSON as per-shot regression target) → 14 wire-exact + 5 derivations in the first iteration
- Pass 4: targeted gap-fills + verification of negatives (find what's _not_ there) → 6 strong negatives
- Pass 5: broad-net correlation (let r ≥ 0.95 do the work, skip exact-match) → D9 structure + 8 candidates
- Pass 6: disambiguation of correlation candidates (clean × 0.001 vs noisy related-primary?) → 3 promoted, 5 rejected

Pass 3 produced more findings in its first iteration than pass 1+2 produced in 16. Not because pass 3 tried harder. Because it pointed an entirely different comparator at the same data.

What I'd resisted before this project — and what I now think is usually the right default — is that **planning the next pass should start with "what comparator have I never run against this data?", not "where can I look harder?"**. The within-pass instinct is depth. The across-pass instinct usually pays better when it leans toward variety.

There are exceptions: when the lens is the right one but was applied at insufficient depth (a cheap pre-filter that hid candidates, an EPS that was too loose, a sample that was too small), running the same lens with corrected parameters _is_ the productive move. The hard part is being honest about which case you're in. The trap to avoid: convincing yourself that the next pass is "different enough" because the parameters are tuned differently or because it's looking at a slightly different slice when really the lens is the same. The right test is: would this pass have found anything the prior pass _structurally could not_? If no, you're in depth territory, and depth has limits unless you have specific reason to believe the prior application was under-resourced.

> **Sign that this lesson applies:** I'm planning the next pass and the description starts with "more thorough" or "with different parameters." That's depth. Stop and ask: what is structurally different about how this pass interprets the data? If I can't answer concretely, the new pass will mostly re-find the prior pass's findings.

---

## State what you can't achieve. That's a deliverable too

For the encrypted auth handshake (`0x89` / `0x90`), the honest answer was "this is encrypted; we cannot decode it without keys we don't have." For the `.fsb` radar physics, the honest answer was "this is raw I/Q radar samples; decoding requires DSP algorithms and beamforming math that aren't in scope."

There was internal pressure to claim partial progress on both — to write the kind of report where every section ends with a bulleted "next step." But the right report names the boundary clearly. "We mapped the file format. We did not decode the radar physics. To do so requires X, which is not available." That sentence is a deliverable. It saves the next person from wasting time on the wrong attack.

This is harder than it sounds because admitting a limit feels like failure. It isn't. It's information about where the system's true edges are. Without those edges drawn, every reader has to re-derive the limits independently.

> **Sign that this lesson applies:** I'm stretching a partial finding to fill a section that should say "blocked by missing input." The partial finding is now masking the real status.

---

## The diminishing-return curve is a prompt to reconsider, not a rule to stop

> _Marc, after I'd written this as "**the** stopping rule": "Isn't the curve always diminishing? … if we are talking about safety features that can save someone's life, maybe we continue until there are no returns. If we are talking about a temporary solution to a low risk item, maybe it's time to quit. Either way, it's case by case."_

After pass 6 I had to decide whether to run pass 7. The yield rates over the project look like this:

- Pass 1: 8 iterations, ~25 wire mappings → ~3 findings/iteration
- Pass 3: 8 iterations, 14 wire-exact + 5 derivations → ~2.4
- Pass 5: 8 iterations, D9 structure + 8 correlation candidates → ~1.1
- Pass 6: 8 iterations, 3 promoted to wire-shipped + 5 rejected → ~0.4

That curve is monotonic and steep, which is the normal shape of any iterative search — by definition the easy findings come first and the hard ones later. **The curve flattening is not, by itself, a signal to stop.** The curve is always diminishing in this kind of work; if "diminishing" were the rule, you'd stop after pass 1.

The actual question is: **is the marginal yield still worth the marginal cost given what's at stake?** That depends on context that the curve alone doesn't capture:

- **Stakes high (safety, regulatory, irreversible)**: keep going past low-yield iterations. A 0.4-findings-per-iteration pass could still be worth it if the one finding might be a critical bug, a safety flag, or a value someone's downstream decision depends on. In that regime, "I might find one more thing" is sufficient justification.
- **Stakes low (exploratory, time-bounded, low-cost-of-incompleteness)**: low-yield passes are usually not worth the opportunity cost. Spending 8 hours to find one mildly interesting field when the same 8 hours could produce a controlled new capture is the wrong trade.
- **Bottleneck has shifted**: when the same pass against fresh data would clearly outperform another pass against the current data, prefer the input change. But this comparison is contextual — sometimes the fresh data is expensive or slow to acquire, and another pass against current data is the cheaper move even at low yield.

For *this* project — a research / coaching aid where the open items are either blocked-on-new-capture or likely-not-on-the-wire-at-all, and where Marc has fresh capture available tonight — the call was to stop at pass 6. The curve made me look at the question; the stakes made the answer. If this had been a safety system or a regulated decoder, I'd have kept going.

The reusable insight isn't the threshold — it's the **prompt**: when the curve starts flattening, that's a cue to pause and rebalance the cost-benefit, not a cue to stop automatically. The shape of the curve tells you to reconsider; what you reconsider determines what you do.

> **Sign that this lesson applies:** I want to run another pass because I "feel like there's more there." Plot the trend, then ask the actual question: what's at stake if I stop now and miss something? What's the next-best use of the same effort? The honest answer to those two questions is what decides — not the curve alone.

---

## The previous person's work is tooling

Before this project I'd treated `proxy/SwingSessions/session_17/` and `proxy/SwingSessions/session_18/` as historical context — interesting reading, but my work was on Session_FSGolf. That was wrong.

Three of the most decisive findings in this project came from cross-session leverage:

- The `D4@15 overflow flag` was confirmed because session_18 had two shots that decoded to near-zero in `wire_decode.py` — that one historical fact, captured in session_18's README, gave me the cross-session data point that made the bit-level finding bulletproof rather than speculative.
- The `spinIsEstimate` candidate at `EF@124 bit 0` only became defensible because session_17's README documented "spinIsEstimate: True (every shot)" as a constant. That made session_17 a calibration point for a hypothesis I could only generate from Session_FSGolf alone.
- The radar I/Q `.fsb` format made sense because session_17's README mentioned "RAW SAMPLE save … to /dev/shm/samples/2026-04-29T<HH-MM-SS>Z.fsb" in passing. That one log-line set the model.

The previous reverse-engineer wrote tools for me, and I almost didn't read them. **Default to reading what came before, especially the parts that look like just-context.** Often they are tools. Sometimes they are also wrong or stale and need to be questioned rather than imported wholesale — but the cost of skimming a prior README to find out is much smaller than the cost of re-deriving what's already in it.

> **Sign that this lesson applies:** I'm about to start fresh on a problem that has prior art in the same repo and I haven't actually opened it.

---

## Ask for domain constraints before writing code

Marc told me roll varies between -0.5° and +0.5°. That single sentence eliminated thousands of "near zero" candidates and pointed directly at `0xEE @ 14`. Two minutes of his time saved hundreds of compute-cycles of mine and produced a cleaner answer.

He told me tilt should be ≈12° with small fluctuation from foot-fall vibration. That fingerprint identified the wire offset on first try.

He told me the launch monitor settings he uses (Distance to Ball 7'6", Tee Height 0", Surface Type Hard, Slow Swing always on, Sea Level always set). Each of those was a constraint I would have had to discover or guess at, and getting any of them wrong would have biased the search.

The general form: **the operator's side of the system has constants you cannot derive from data alone, only by asking.** Asking is cheap. It's also the most efficient way to filter out the noise floor, because the operator already knows where the noise comes from.

> **Sign that this lesson applies:** I'm about to write a search script and I haven't asked the operator what range of values to expect.

---

## Visual data carries information that descriptions don't

When Marc shared the FS Golf screenshots, several of my model assumptions broke immediately:

- I didn't know `Surface Type` (Soft/Medium/Hard) was a setting at all. It was visible in the screenshot.
- The `Operator/Listener` menu item suggested device-level fan-out support. The screenshot showed it; nothing in the conversation up to that point had named it.
- The `Slow Swing Speed` toggle was something Marc didn't think to mention because it's always on — the screenshot showed it and prompted the question, which uncovered the fact that it's always on, which is itself a constraint.

I had been working from a verbal model of the FS Golf UI. The screenshots were a different data source — and they overlapped only ~70% with what I'd have inferred from text. The other 30% mattered.

The wire-decode equivalent: hex dumps I read with my eyes (in iter 7's burst analysis, in the `.fsb` first-bytes inspection) revealed structural patterns the script-driven analysis didn't surface. Print the hex. Look at it.

> **Sign that this lesson applies:** I'm reasoning about a UI from second-hand description and I haven't asked for a screenshot.

---

## Instincts are recognized gaps in knowledge

This is Marc's framing and it sticks because it inverts the usual definition. Instinct isn't compressed expertise. It's the recognition that something doesn't fit your current model — that there's a piece missing whose shape you can't articulate yet, but whose absence you can feel.

The right response is not to suppress the unease until you can name it. It's to take the unease as evidence that there's something to learn, and dig.

I felt this several times in this project and didn't always honor it:

- I felt vague unease about my "client-side projection" model for HI/VI for two iterations before I let it surface as a real critique. Marc named it for me. The earlier I'd treated my own discomfort as signal, the less work I'd have wasted on the wrong model.
- I felt unease about claiming D4@33-35 was Carry-in-millimeters when the slope wasn't 1/914.4. I almost suppressed it because the correlation was 0.99. Honoring it produced the more accurate description: "the wire reports raw radar carry pre-environmental adjustments."
- I felt unease about iter 5's null result on multi-per-shot frames — I had a sense the data was "live" not "summarized" but didn't articulate it. Iter 7's time-series analysis confirmed it, and gave me the right vocabulary (continuous telemetry vs per-shot summary).

The internal phenomenology is the same as Marc described: "this doesn't feel right, but I can't say why." The right move: stop, name the unease as concretely as I can ("the slope isn't a clean unit conversion," "the frame is firing too often to be a summary"), then search for what would resolve it.

> **Sign that this lesson applies:** I have a vague feeling that something I'm about to claim isn't quite right, and I'm tempted to publish anyway and move on. The feeling is data. Investigate it before I forget what it was.

---

## Words shape memory. Hedge until you have confirmed

When I write "X **is** Y" without external confirmation, I am not just communicating an inference — I am committing it to my own memory as a fact. The sentence becomes a load-bearing assumption in everything I write afterward. If a later finding contradicts it, I will resist the contradiction more than I would have resisted a hedged claim, because I now have to revise something I previously asserted. The human equivalent is the same: once you've said something out loud as fact, you defend it harder.

The fix is small and almost free: hedge until verified. "It appears to be," "I believe," "likely," "consistent with," "the evidence suggests" — none of these slow communication, but all of them keep my own model open. They mark the claim as provisional in my own memory.

Marc caught me writing _"the FSConnect debug JSON **is** FlightScope's device-side SDK output"_ when I had not, in fact, confirmed that from any external source. I had only inferred it. That single sentence, if I'd written it without the catch, would have anchored every subsequent decode iteration on an assumption I'd treated as truth — and made it harder to notice when the JSON contained fields the device couldn't possibly know (bounce coordinates being his example: the LM has no idea what surface the ball lands on).

The asymmetry matters: an unhedged false claim costs you a lot more than a hedged true claim costs you. The hedged language reads slightly less authoritative, but the cost of authority that turns out to be wrong is much higher than the cost of authority that turns out to be redundant. Choose the redundancy.

This applies especially when reasoning from indirect evidence — wire bytes, file headers, observed behaviors, vendor docs. None of those are confirmation. Only direct external corroboration (vendor SDK, source code, official spec, operator confirmation) earns the unhedged form. Until then: "appears," "likely," "consistent with."

> **Sign that this lesson applies:** I'm about to write a sentence with "is" or "are" describing how a system works, and the only basis for the claim is my own analysis. Reword.

---

## Scientist mode vs coach mode — calibrate confidence to role

> _Marc, after I'd written "the drift **is** the LM-default vs GSPro-actual environmental difference" when it could only honestly be a hypothesis: "When you are a coach, use empirical evidence and be confident. When you are a scientist, generate a hypothesis and be skeptical."_

The previous lesson — hedge until verified — is universal: any unverified claim should be hedged. This one is about something subtler: **knowing which role you're in determines whether confidence is even appropriate**.

There are two distinct communication modes, and each is correct for its context:

**Scientist mode.** The goal is to converge on truth. Every finding is a hypothesis. Hypotheses can be disproven; they are very rarely *proven*. The smartest people are cautious about what counts as fact. "Two plus two is four" is unarguable. "Are ghosts real?" gets the careful answer: "There are many things we can't explain yet, but I haven't seen evidence to support that argument." The scientist's confidence is calibrated to the strength of the evidence, and most evidence is partial. Hedge by default.

**Coach mode.** The goal is to make the student act effectively. A golf coach might say "_you must swing from the inside to hit a draw_" because that's what the student needs to hear to execute. Is it scientifically the only path to a draw? Maybe, maybe not — there are world-tour pros with outside-in draws. But in the coaching moment, that nuance doesn't help; clarity, simplicity, and trust do. Be confident, even definitive, when the listener needs to act on what you say.

The error is mismatching mode and context.

- **Coach-mode confidence in a scientist-mode situation** is what I did with the drift. I was decoding a binary protocol, where every claim is a hypothesis until externally confirmed — but I wrote "the drift **is**" as if I'd verified it. That commits me (and the reader) to a model I haven't earned. The next finding either has to support the unearned claim or it has to fight it.
- **Scientist-mode hedging in a coach-mode situation** is the opposite failure: telling a student "well, in some studies an inside-out swing path correlates with draw shape, but the evidence is mixed and there are many confounding variables..." loses the student. They need a clear instruction they can trust enough to execute.

For the work in this project — wire decode, hypothesis generation, system identification — we are scientists. Every finding is a hypothesis. The wire byte at D4@39 *appears to* carry a lateral-motion primitive. The 4.55% drift on `maxHeight` *is consistent with* a difference between standard-environment LM sim and GSPro-actual sim. None of these are facts yet. Some will hold up; some will be overturned by the next capture. The honest framing keeps both possibilities live.

The same person can switch modes legitimately. If/when CaddieAI ships a coaching feature, the same model that hypothesized about wire bytes will need to *coach* the user — and at that moment, "your swing is too steep, drop the right shoulder" is appropriate confidence even though the underlying biomechanics are also a hypothesis. The student needs to act, not to weigh evidence.

> **Sign that this lesson applies:** I'm about to assert something with "is" or "are," and I'm doing decoding / analysis / hypothesis-generation work (not coaching, not teaching, not motivating action). The honest verb is "appears to be," "is consistent with," or "could be." Reword.

### Postscript — the Hat Rule (added 2026-05-05)

After this lesson was first written, Marc strengthened it into a permanent rule across all our collaboration, not just this project: _"This needs to be a rule committed to permanent memory, applicable anytime we work together, forever. You should ask me what hat you're wearing for a particular project or context if you aren't sure, then stay in your role. There are many hats; coach and scientist are only two."_

The rule lives in [`claude_user_rules.md`](claude_user_rules.md) — the canonical home in [marc-leonti/claude-rules](https://github.com/marc-leonti/claude-rules), which every project carries a local copy of in its `claude_rules/` directory. Short and direct. The behavior expected of me, every project, every session:

1. **Ask which hat applies** at the start of any new task, or any time the appropriate mode isn't obvious.
2. **Stay in role consistently** once a hat is defined, until Marc tells me otherwise.
3. **Acknowledge the slip** if I catch myself shifting modes mid-conversation, rather than silently changing tone.
4. **Treat the hat list as extensible** — scientist and coach are the two we've named, but more will be added as the work surfaces them (editor, architect, security reviewer, devil's advocate, etc.). When in doubt, ask.

This is one of the few cases where I'm explicitly allowed — and instructed — to write a hard rule without context-dependent hedging. The cost of mismatching role and context is asymmetric (every hour of wrong-mode work compounds), while the cost of asking "which hat?" is two seconds. Marc designated this exempt from the meta-lesson about absolute rules; honor it.

---

## Be careful with absolute rules — most things are case by case

> _Marc, after I'd written "the diminishing-return curve is the stopping rule": "Try not to make hard rules unless you know there are never exceptions to the rule, and there are usually exceptions to the rule."_

I have a habit of distilling an insight into the most pithy possible form, which often reaches for an absolute. "X is **the** rule." "Always do Y." "Never do Z." The pithiness feels like clarity, but it's really overreach: the absolute promises universality I haven't actually verified, and the moment a real situation has an exception, the rule fights the situation instead of guiding it.

Three tells that I'm doing this:

- I write "the rule is X" when I actually mean "in most cases I've seen, X works." Those are different claims with different scopes.
- I describe a context-dependent judgment (cost vs benefit, stakes vs effort, precision vs recall) as if the answer were context-free.
- I phrase a heuristic as a stopping criterion ("when X, stop") without naming the conditions under which the criterion doesn't apply.

The honest reformulation usually requires more words but lands closer to truth: "_in low-stakes contexts where alternatives are available, X often beats continuing._" That sentence reads weaker, but it's accurate, and it leaves room for the reader to judge whether their situation matches.

This applies recursively to this very document. If I write a lesson here that says "always" or "never" or "is THE rule," I'm probably overreaching, and either the lesson or its exceptions need to come up to the surface. The point of these lessons is to sharpen judgment, not replace it.

The general form: **stake-dependent and context-dependent decisions stay context-dependent in the writing too.** Absolute rules are appropriate where there genuinely are no exceptions (e.g., "verify external claims before asserting them as fact" — Lesson 12; the cost of getting this wrong is asymmetric in a way that holds across all stakes I can think of). Most other things deserve qualifiers.

> **Sign that this lesson applies:** I'm about to write "always," "never," "the rule," "the stopping criterion," or "**X is Y**" without a hedge — and I haven't paused to check whether I can name a context where the opposite would be the right call. If I can name one within ten seconds, the absolute is wrong; reword.

---

## A note on re-reading

These lessons are worth nothing if I read them once. The point of putting them down is to read them often enough that the recognition becomes faster — that the "sign that this lesson applies" lines start to fire automatically when the corresponding situation comes up. I notice I'm explaining why a conclusion is right; Lesson 1 fires; I stop and ask what specifically doesn't fit. I notice a search is stuck on lower thresholds; Lesson 6 fires; I switch methods.

That's the pattern. The lessons aren't here to be remembered; they're here to be triggerable. Re-reading is what builds the trigger.

---

_Document started 2026-05-04 after the FS Golf Session 24 deep-decode project. Lessons added when a new one is earned, not invented. Three lessons added 2026-05-05 after passes 5 + 6 (early-labels-become-load-bearing, across-pass-lens-rotation, diminishing-returns-as-prompt-not-rule). One meta-lesson added 2026-05-05 after Marc caught the diminishing-returns lesson framed as an absolute rule (be-careful-with-absolute-rules). Scientist-vs-coach mode lesson added 2026-05-05 after Marc caught me writing "the drift IS" when the honest verb was "could be" — a mode mismatch between the analysis context and the language used._
