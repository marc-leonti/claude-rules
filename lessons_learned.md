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

## A test that would pass on the old code isn't coverage of the change

When I rewrote `decode_d4` to read attack-angle as `i24BE@90-92` instead of the legacy `i16BE@91-92`, I added three tests with names like `test_attack_angle_i24_sign_extends_negative`. Each test set the new high byte to `0xFF` and asserted the decoded value. They all passed. They were green next to the merged change. The reviewer pointed out that `0xFF` is exactly the natural i16 sign-extension of every vector I'd chosen — the **legacy decoder produces the identical result on those vectors.** The tests asserted nothing the change had introduced. They were green by inheritance, not by exercise.

The same pattern showed up in a second test of mine: `test_decode_shot_from_buffer_prefers_d4_club_path_over_ed` only called the per-frame decoders, never `decode_shot_from_buffer` itself. Removing the line of merge-precedence code I'd written wouldn't have failed it.

The general form: **when adding tests for a code change, the diagnostic question isn't "does the test pass?" — it's "would this test pass on the old code?"** If yes, the test is decorative. The vector / control flow / target function has to differ enough that the legacy implementation produces a different value or a different path.

The mechanical version is concrete:

- For an encoding change, choose vectors where the new and old encoding produce **different** outputs (for `i16` → `i24`, pick magnitudes outside the i16 range; for `u16` → `u24` overflow, pick a value above the u16 ceiling).
- For a control-flow change (a new precedence rule, a new fallback path), call **the function that owns the new control flow**, not the helpers it composes.
- When in doubt, run the test against pre-change code (`git stash`, `git checkout HEAD~1`, etc.) and check that it fails. If it doesn't, the test isn't testing the change.

This is a stricter form of the existing rule "Run tests adversarially against your own claims" in [`claude_user_rules.md`](claude_user_rules.md). The adversarial framing catches missing assertions; this catches missing differentiation. They're complementary: a test can be adversarial on its assertion (assert the relationship, not "returned non-None") and still vacuous on its vector (input doesn't distinguish new from old).

A reviewer caught both forms in PR #131. I shipped them green because the test-name half of the contract said the right thing — only when someone with fresh eyes asked "does this vector actually differentiate the change?" did the gap show up. The discipline is to ask that question on the way in, not wait for someone else to ask on the way out.

> **Sign that this lesson applies:** I just wrote a test for a code change. Before committing, I cannot answer "what specific output of the legacy code would have failed this test?" Add a vector or control-flow path that distinguishes them, or rename the test to acknowledge its narrower scope.

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

Before this project I'd treated `captures/session_17/` and `captures/session_18/` as historical context — interesting reading, but my work was on Session_FSGolf. That was wrong.

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

## Lazy proxies that silently set their target to None are the worst kind of breakage

> _Added 2026-05-13 after the first end-to-end live hardware test. The Vision Pipeline crashed on the first shot with `TypeError: 'NoneType' object is not callable` at `_mp_pose.Pose(...)`. The cause was that mediapipe 0.10.21+ dropped the `mediapipe.solutions` namespace and replaced the lazy attribute proxy with `None` instead of raising on access._

The class of failure: a library exposes an attribute via a lazy/proxy mechanism; a future version removes the attribute but does not raise on access — it returns `None`. Any consumer that wrote `cls = lazy.X; instance = cls(...)` now fails at the call site, far from the import, with a generic-looking `TypeError`. The stack trace points at the call site, not the missing attribute.

The investigation cost is steeper than a regular ImportError: you can't grep for the missing name in your code (it's still there), the import line still "works," and the failure only surfaces under code paths that actually instantiate the class.

Three habits that catch this earlier:

- **Validate lazy proxies at module-import time, not at first use.** If your code depends on `mediapipe.solutions.pose.Pose` being a class, write `assert callable(mediapipe.solutions.pose.Pose)` (or a quick `isinstance(mediapipe.solutions.pose.Pose, type)`) at the top of the module. The whole consumer module then refuses to load if the dependency is the wrong shape, with an error that names the offender.
- **Pin upstream versions whose major-version cadence drops APIs.** mediapipe ships breaking changes on minor versions (0.10.20 → 0.10.21 dropped `solutions`). PIN `mediapipe<0.10.21` in setup docs the moment you see this pattern, not after the next install breaks.
- **When you upgrade a library and it suddenly errors mid-runtime, check the changelog for proxy/lazy-import changes specifically.** They're easy to miss in release notes because they aren't "breaking changes" in the classic sense — the import still resolves.

Generalises beyond mediapipe: any library with `__getattr__`-driven module-level laziness can do this. PyTorch's deprecated APIs, transformers' tokenizer aliases, and pip-resolver-substituted fallbacks have all hit this shape historically.

> **Sign that this lesson applies:** I'm getting a `TypeError: 'NoneType' object is not callable` on a name that exists at the import I wrote, and the cause might be that the library quietly retired the attribute. Walk the import chain by hand: `print(type(mod.foo.bar))` at module import. If it's `<class 'NoneType'>`, the proxy silently failed.

---

## Auto-modes silently trade throughput for stability — pin them when throughput matters

> _Added 2026-05-13 after the first FLIR Blackfly S indoor session. Camera ran at ~9 FPS in 700-lux indoor lighting; the spec was 200+ FPS at the configured resolution. Default `ExposureAuto=Continuous` had silently dialed exposure up to ~100 ms per frame to compensate for dim light._

Hardware in "auto" mode optimizes for the property the manufacturer thinks the customer wants — usually image quality or stability. When throughput / latency / determinism is what you want, that automatic trade goes the wrong way and never tells you. The symptom is "the system is running, just slow." There's no error, no warning, no log line.

For FLIR cameras specifically, the four knobs that bite are: `ExposureAuto`, `GainAuto`, `AcquisitionFrameRateEnable` (must be True to honor `AcquisitionFrameRate`), and `BlackLevelAuto`. Default-off, manually configured: predictable performance. Defaults-on: the camera will quietly drop FPS in dim light, raise gain in bright light, and clip black levels in scenes with wide dynamic range.

The pattern generalises:

- **Storage**: auto-tiering silently moves hot data to slow tiers when free space gets tight; latency degrades but no alert fires.
- **CDN / autoscaler**: auto-throttling on rate-limit triggers; requests succeed (200s) but at 10x the expected p99 latency.
- **GPU drivers**: thermal throttling drops clock speed silently; benchmarks read 30% lower than spec with no error code.

The lesson is not "always disable auto-modes." Many auto-modes are exactly right (auto white-balance for general photography, ABS in cars). It's: **if a system's behavior depends on a quantity that auto-modes secretly adjust, the auto-mode is the prime suspect for any "running but slow" symptom.** Pin to manual values in the configurations that matter to performance, log the actual configured values on startup so the operator can see what's in effect, and treat "auto" as opt-in rather than default for production paths.

> **Sign that this lesson applies:** the hardware/system is "working" but at a performance level far below its spec, and no error or warning is being raised. Before debugging the obvious, dump every config knob that has an `Auto`-prefixed variant and check what value the system actually settled on.

---

## When a trigger fires NEAR an event rather than strictly BEFORE it, extract a symmetric window around the trigger

> _Added 2026-05-13 after `src/assembler.py` was re-architected to take a `post_trigger_s` parameter (commit `51fe123`); revised the same day after the deeper finding (commits `8f00e32` + `2225ae7`) that the "wire-level D3 trigger" was a misread of the protocol — the D3 cluster fires ~1 s **after** each shot's D4/EF lands, not at-or-near impact. We now anchor on EF-chunk receive time instead; the asymmetric (pre, post) window argument still applies because the new anchor is ~1.5 s post-impact._

A common mental model: a "trigger" announces the start of an event, the event then unfolds in the post-trigger window, and the pre-trigger window is uninteresting. Many hardware protocols don't work that way. The trigger is whatever bit of state the device latches to mark a moment — sometimes that's at the leading edge, sometimes at the centre of the event, sometimes at the trailing edge, sometimes the trigger fires multiple times across one event, and sometimes the thing the codebase calls "the trigger" is actually a post-event acknowledgement (the Mevo+ D3 cluster turned out to be exactly that).

If the documentation doesn't say where the trigger fires relative to the event, default to: **assume the trigger fires somewhere inside (or after) the event, and extract a symmetric (pre, post) window around it.** Sizing the post-window costs you only a brief blocking wait at extraction time; sizing it to zero costs you the impact frames.

The CaddieAI-specific shape is now: `pre_trigger_s=2.5, post_trigger_s=0.3` for swing analysis, anchored at EF-chunk receive time (~1.5 s after ball impact). The pre side captures the backswing and early downswing; the 300 ms post side captures a bit of follow-through tail.

Generalises to any "extract data around event-time" pattern:

- Database CDC consumers that subscribe to a transaction-commit event: the commit timestamp is the end of the transaction, not the middle — the prior writes happened in the previous N ms.
- Profile/trace analysis: a marker dropped at "function entry" doesn't bracket the call's stack-frame allocation, which started earlier.
- Audio onset detection: the algorithmic "onset" frame is usually a few ms into the actual transient.

> **Sign that this lesson applies:** I'm building a frame-extraction / event-window / replay-buffer system and I'm tempted to make post-window length = 0 because "the event hasn't happened yet by the time the trigger arrives." Stop and verify with the actual protocol what the trigger means; defaulting to a small symmetric window costs nothing and recovers from being wrong.

---

## A latch that silently retains its previous value is worse than a latch that surfaces "missing"

> _Added 2026-05-13 after the D3-latch redesign in `sniffer/decoders.py` (commit `95262fd`); the redesign turned out to be patching the wrong root cause (the wire premise that D3 was the trigger was itself wrong — see "Verify wire-protocol comments against the wire before building tracking on top of them" below). The lesson framing about silent-stale-state still stands, just with cleaner attribution: the per-D3-frame design didn't fix the symptom in the live ClusterA run because the records being tracked weren't shot triggers in the first place._

Stateful "latest observed value" caches have a failure mode that's easy to miss in normal operation: if the source ever skips a refresh, the cache happily returns the previous value. There is no signal to the consumer that the value is stale. The system continues running, but every downstream calculation that uses the cached value is now wrong, with no error.

Two architectural choices help:

- **Make missing data explicit, not silent.** Replace the single mutable latch with per-event records that can be looked up independently for each consumer. When the consumer asks "what's the timestamp for shot N?" the lookup either finds a record or returns `None`. `None` is loud — it traverses the rest of the pipeline as an obvious gap (and in CaddieAI's case triggers a parse-time fallback). A stale value is silent — it looks fine until something downstream notices the drift.
- **Couple state lifecycle to the event that consumes it.** If the latch is "the timestamp for the NEXT shot," reset it after that shot is emitted. The previous design never reset — that's what made the staleness compound.

This generalises wherever a single mutable value caches "the most recent X observed":

- Caches that hold the latest device measurement (temperature, voltage, RPM): if the device transient-fails on its next update, the consumer sees the old reading and may act on it.
- "Last known good state" stores in distributed systems: if the periodic refresh fails silently, every requestor for hours reads stale state.
- LRU-cache-like memoization where the source of truth is a streaming feed rather than a deterministic function — missed updates leave the wrong value cached.

The fix isn't always to remove the cache; sometimes you just need a freshness timestamp alongside the value and a consumer-side staleness gate. CaddieAI's `poc.py` does exactly that for the workaround path: it reads the latch, computes age, and falls back if the age exceeds 1 s. Either approach beats silently returning the stale value.

> **Sign that this lesson applies:** I'm about to design or maintain a `_latest_X` instance attribute that's overwritten unconditionally on update. Ask: what happens if the source skips an update? If the consumer would get a value that "looks right" but is wrong, redesign — either to per-event records, or to value + freshness timestamp with a consumer-side staleness check.

---

## Mixing time sources is fine if you're explicit about which one drives correctness

> _Added 2026-05-13 in passing during the D3-latch fix. The status line in `poc.py` mixes `time.monotonic_ns()` (for elapsed-since-D3 calculations, where monotonicity matters) and `time.time()` (for the wall-clock display, where the operator just wants a human-readable timestamp). The two read slightly different "now" values within the same `_print_record` call — fine, because they're displayed to different audiences (the elapsed delta is for correctness checks; the wall-clock timestamp is for the human log)._

There's a common reflex to treat "mixing time sources is bad" as an absolute rule. It isn't. The actual rule is more nuanced: **time sources have different invariants (monotonic vs wall-clock vs hardware-clock), and you should pick the one whose invariants match the correctness property you depend on for that calculation.** Mixing two sources in the same code path is fine when each is used for the property it provides.

Common pairs:

- `time.monotonic_ns()` for **elapsed** computations (because it can't run backward). `time.time()` for **wall-clock display** (because the operator wants 14:32:18, not "monotonic clock value 109834... ns").
- `os.times()[4]` (wall-clock) for **scheduling** (cron-like jitter is fine). `time.perf_counter()` for **benchmark deltas** (highest resolution).
- Hardware timestamps from a frame buffer (PySpin's `system_time_ns`) for **event-to-event ordering within a single capture session**. System monotonic clock for **comparison to user-space events**.

The wrong move is using a wall-clock for elapsed (because NTP can step backward) or a monotonic clock for display (because the user can't interpret it). The right move is using both, in the same render, with each value derived from the appropriate source.

The asymmetry: confusion arises when the SAME value gets computed two ways via different clocks and they disagree. As long as each value is computed from exactly one clock and the consumer knows which clock it came from, the mix is safe.

> **Sign that this lesson applies:** I'm about to refactor a piece of code to use "one clock everywhere for consistency" and I'm not sure why. Check what each clock reading is doing: if elapsed and display are different concerns served by different clocks, leave them mixed.

---

## Verify wire-protocol comments against the wire before building tracking on top of them

> _Added 2026-05-13 after the D3-latch saga. `wire_decode.py` had a one-line comment dating back to the proxy days: `D3_TYPE = 0xD3   # shot-event trigger`. That comment was the foundation of two architectural designs (proxy's `_last_d3_received_ns` latch, then the sniffer's per-D3-frame `_d3_records` redesign) and one passing-mention lesson in this file ("trigger fires NEAR an event"). When the live ClusterA capture showed d3_age_ms running 11–141 s, the diagnosis pivoted from "fix the tracking" to "audit the premise." Offline replay against three independent capture fixtures revealed the wire pattern is consistently `D4 → EF → 4×D3 → idle → D4 → EF → 4×D3 → ...` — D3 fires AFTER each shot. The trigger premise was wrong from the start. Two architectural designs and two debugging sessions were spent building tracking on a misread comment._

It is easy to read a comment like `0xD3   # shot trigger` and treat it as a primary source. It isn't. The comment is some earlier engineer's interpretation of the wire, possibly written before today's fixtures existed, possibly written from one capture that doesn't generalise, possibly inherited verbatim from an upstream project. The wire itself is the only primary source.

**Before building infrastructure on top of a wire-semantic claim, run the actual bytes through a parser and look at the interleaving.** It takes about ten minutes — open the PCAP, dump frame-type + offset in order, look for the pattern. Five minutes of empirical work prevents days of architectural rework.

Specific tells that a wire-protocol comment is unverified:

- It uses a single-word descriptor like "trigger" / "ack" / "ready" with no offset / timing / repetition info. The wire reality usually has nuance the descriptor flattens.
- It's a 60+ character one-liner adjacent to a constant declaration. Long-form, evidence-bearing wire comments tend to live in docstrings or sibling `.md` files, not inline near the constant.
- The comment predates any capture file in the repo (check `git blame` against `ls captures/`).
- The codebase has two layers of "tracking infrastructure" attempting to compensate for unexplained behaviour at runtime — that's usually the load-bearing comment lying.

The fix isn't to distrust every comment. It's to **verify any comment you're about to build state on**, the same way you'd verify any external claim you're about to depend on. The cheaper the verification, the higher the bar should be for skipping it — and for wire data captured in a PCAP, the verification cost is one ad-hoc script.

> **Sign that this lesson applies:** I'm about to write code that latches / tracks / records `received_X_time_ns` for some wire frame type, and my justification is "the comment in the parser says X is the trigger." Stop and replay one capture through `parse_stream` to see where X actually sits in the per-shot frame interleaving. If X is post-event rather than pre-event, the entire tracking model is wrong.

---

## Build narrow modules, compose them upward

> _Added 2026-05-14 after the autonomous arc that seeded `src/coaching/` with 10 modules across one long work session. The modules — `club_inference`, `session_analysis`, `shot_commentary`, `tour_comparison`, `session_compare`, `trend_analysis`, `brain`, `markdown_report`, `llm_prompt`, `llm_client` — each do one thing on `ParsedShot` or `SessionSummary`. None calls another sibling module except through the `brain` orchestrator. Tests are independent per module. CLI tools (`coaching_replay`, `compare_sessions`, `list_sessions`, `session_markdown_report`, `trend_report`, `coaching_brain`) are thin wrappers that import the modules they need._

The default shape when you're building "the coaching brain" is one big module that does everything. That's the natural reading of the spec — "a coaching system" sounds like one thing. The arc above did the opposite: kept each module under ~300 lines, narrow input contract (consume `ParsedShot` or `list[ParsedShot]`), narrow output (one dataclass), independently testable, no shared state.

Why it worked:

- **Each module's tests proved its piece in isolation.** When the integration broke (the per-shot smash-factor calculation differed between the wire-decoded path and the FSConnect-log path), the failure surfaced at exactly one boundary, with a clear `assertAlmostEqual` failure mentioning the metric. Compared to a single 1500-line "CoachingEngine" class where the failure mode would be "the test for the whole engine doesn't pass" — useless localization.

- **Composition was free at the consumer layer.** The brain module (`brain.assemble_session_report`) is 50 lines because it only needs to call the four data-producing modules and bundle their outputs. The CLI tools are thin because the underlying modules already produce the data they need.

- **The LLM prompt assembly didn't need to know about any of the rules.** `llm_prompt` reads the structured outputs from the other modules and builds a prompt out of them. If a new rule lands, the prompt updates automatically because it iterates over `commentary.notes` and `tour_deltas` — no per-rule code in the prompt assembler.

- **Adding a new module is cheap.** `trend_analysis` was added after the other five were in. It consumes `SessionSummary` (the same type `session_analysis` produces) — no changes to anything upstream. The CLI tool for it (`trend_report.py`) was 150 lines. New module: 1 day of work; new feature visible to the operator: same day.

The cost of the discipline is more files. The benefit is that *every* file is small enough to read in full when investigating an issue, and the integration surface is the dataclass boundary, not method signatures across a god-class.

> **Sign that this lesson applies:** I'm about to build a feature that's described as "the X system" or "the X brain." Resist the singular "system." List the discrete data transformations involved (X type → Y type) and build one module per transformation. The orchestrator that strings them together comes LAST and is usually 50 lines.

---

## When a "reverse-engineering gap" turns out to have a side-channel, take the side-channel

> _Added 2026-05-14 after the autonomous arc that landed `src/telemetry/fsconnect_log.py`. CaddieAI had spent weeks treating HI/VI (face impact location) as a hard wire-RE problem — the project field-map and ironsight WIRE.md both confirmed it's NULL across every catalogued per-shot wire message. The proposed path forward was an MJPEG-over-port-8080 CV pipeline (extract per-shot video frames, run face-impact detection on them). Hours of work, no progress against the gap. While building an FSConnect-log parser for a separate purpose (the parked `DescentV` / `clubLowPoint` derivations couldn't be done from wire data alone), it turned out the FSConnect plugin emits a per-shot JSON record with **114 fields including `clubFaceImpactLocation` populated on 90 of 103 shots**. HI/VI was on disk locally the whole time — just not on the wire._

The lesson is about the **architecture assumption**, not about FSConnect specifically. CaddieAI had a clean conceptual model: "the sniffer reads the wire, the wire feeds the decoder, the decoder feeds the assembler." That model implicitly treats anything not on the wire as unavailable. But the local PC running GSPro has many data sources — log files, registry entries, FSConnect's debug stream — that are equally "free" to consume.

Specific cases this generalises to:

- An API doesn't expose a field, but the desktop app's debug log writes it on every event.
- A device's wire protocol is sparse, but a sibling protocol on a different port carries the missing fields.
- A library doesn't surface a metric, but its source includes it as a private attribute you can read.
- An external service's response omits something its own dashboard renders — the dashboard's API likely has it.

The architectural cost of consuming a side-channel: usually one parser module and a clear note in the docs about where the data really came from (provenance matters for production reliability — the side-channel can change format without a versioned API contract). The architectural benefit: side-step a multi-week RE / CV / inference task.

**This is not "always prefer the side-channel."** The wire path is usually higher-performance, lower-latency, more reliable, and version-stable. But when the wire path is BLOCKED on something the side-channel just gives you, take the side-channel; document the provenance; ship.

> **Sign that this lesson applies:** I've been treating a field as "missing from our data sources" for more than a week. List every process running on the same machine that could plausibly have generated or consumed that field at any point. For each, check whether it writes a log, exposes a debug interface, has an exportable history, or uses a sibling network channel. A field "missing from the wire" might be sitting in a 1.6 MB text file on the same SSD.

---

## The operator's seeds are illustrations, not evidence

> _Added 2026-06-12 from the CaddieAI trend-coaching design session. Marc: "I try to be careful about planting seeds that create bias and push you in a direction... When I tell you my ideas and ask for your thoughts or opinions, I don't want you to just tell me it looks great. I want you to consider those ideas, do some research on your own, tell me where I might be wrong or offer an alternative that might work better... And be sure to resist being biased because I planted that seed."_

Two failures in one session earned this. Marc asked for an "aspirational hardware wish list" and offered a hypothetical framing - "if a pressure plate would be more useful than more cameras, maybe I should invest in that instead." My supposedly independent wish list contained a pressure plate instead of a third camera. Separately, he told a deliberately fictional story (an imaginary coach named Bob, with invented coaching advice he explicitly didn't know was sound) to illustrate the *kind* of product behavior he wanted - and I wrote the fiction's specifics into a canonical design doc as if they were a validated fault model and proven coaching language.

The mechanism: an operator's example defines the SHAPE of the answer they want, not its content. When the example comes back to them inside my "analysis," their speculation has been laundered into something that looks independently derived. The echo is invisible from the inside - both outputs felt reasoned while I produced them.

The de-bias audit that followed showed the failure isn't *using* seeds - it's not *checking* them:

- The pressure plate (his seed) **survived** independent verification: a peer-reviewed systematic review confirms ground-reaction-force patterns associate with clubhead speed and skill. Keeping it was right; my original justification (quoting fictional Bob) was not.
- My camera recommendation (shaped by his "how many cameras" frame) **failed** the audit: a $0 software alternative existed - monocular 3D pose lifting, commercially proven for exactly this use case - that the seeded frame had hidden from consideration entirely.
- The fiction-as-spec error had a cheap fix with real consequences: label the story as fiction in the doc, extract only its *shape* as the requirement, and add a validation gate for the invented content.

The protocol that comes out of this, applied per consequential decision (Marc's explicit proportionality caveat: no analysis paralysis, and "you don't always need to name at least one alternative... but definitely check to see"):

1. **Strip the seed and re-derive** from base evidence - literature, repo data, a web search. If the only support for a conclusion is the operator's own framing, it isn't supported yet.
2. **Check for alternatives outside the offered frame.** Name one only when it's genuinely worth naming.
3. **When the seeded idea survives, say so and show what it survived.** "Your hypothetical holds up, and here's the independent evidence" is more useful to the operator than either reflexive agreement or reflexive contrarianism.
4. **Label fictions as fiction** in anything canonical. An operator's illustrative story can be a great spec for the *shape* of a system while being zero evidence about the domain.

This is the complement to "On Pushback" (the first lesson in this file): pushback is data, but agreement-shaped seeds are NOT data - they're framing. The two lessons share a root: the operator's words always tell you what kind of answer is wanted; only evidence tells you what the answer is.

> **Sign that this lesson applies:** my recommendation contains the operator's own example handed back to him, or I'm citing the operator's story/scenario as support for a design choice, or I notice I haven't consulted any source other than the conversation itself before agreeing.

---

## A note on re-reading

These lessons are worth nothing if I read them once. The point of putting them down is to read them often enough that the recognition becomes faster — that the "sign that this lesson applies" lines start to fire automatically when the corresponding situation comes up. I notice I'm explaining why a conclusion is right; Lesson 1 fires; I stop and ask what specifically doesn't fit. I notice a search is stuck on lower thresholds; Lesson 6 fires; I switch methods.

That's the pattern. The lessons aren't here to be remembered; they're here to be triggerable. Re-reading is what builds the trigger.

---

_Document started 2026-05-04 after the FS Golf Session 24 deep-decode project. Lessons added when a new one is earned, not invented. Three lessons added 2026-05-05 after passes 5 + 6 (early-labels-become-load-bearing, across-pass-lens-rotation, diminishing-returns-as-prompt-not-rule). One meta-lesson added 2026-05-05 after Marc caught the diminishing-returns lesson framed as an absolute rule (be-careful-with-absolute-rules). Scientist-vs-coach mode lesson added 2026-05-05 after Marc caught me writing "the drift IS" when the honest verb was "could be" — a mode mismatch between the analysis context and the language used. Five lessons added 2026-05-13 after the first end-to-end live hardware test exposed (1) silent lazy-proxy breakage in mediapipe 0.10.21+, (2) FLIR auto-exposure throttling in dim indoor light, (3) the asymmetric (pre, post) frame-extraction window required by D3-near-impact wire-triggers, (4) the silent-stale-value failure mode of the original single-D3-latch design, and (5) the safe mixing of `time.monotonic_ns()` and `time.time()` in the same display when each drives a different concern. Two of those (3) and (4) revised the same day after the ClusterA live capture exposed the deeper root cause: the wire D3 was never the trigger at all — it's a post-shot frame cluster. Sixth 2026-05-13 lesson added at that point: verify wire-protocol comments against captures before building tracking on top of them. Two lessons added 2026-05-14 after the autonomous coaching-module arc (build narrow modules; take the side-channel). One lesson added 2026-06-12 after Marc caught his own planted seeds echoing back through a hardware wish list and a fictional coaching story landing in a canonical design doc as if it were evidence (operator seeds are illustrations, not evidence)._
