# NeutrinOS agent index

## The test

Before starting work, answer both:

1. **Does this move toward a machine that installs, boots, updates and rolls
   back?** Six of the seven [charter](docs/project/charter.md) criteria need
   one. "No" means it is a preference with a document attached.
2. **What does it cost to reverse?** A rebuild is cheap: default it and move on.
   A physical visit to a real machine is not; that is where care and
   measurement belong.

Rigour scales with **reversibility, not with how foundational a choice feels**.
The `/usr` filesystem format consumed a plan, a review, fourteen tasks and
54,000 words; it is `Format=` in one repart file, selected by
`NEUTRINOS_SLICE_ARM`. Do not repeat that shape.

**Prefer working code over prose.** A document must name what it unblocks.

## Read

- [charter](docs/project/charter.md) and [principles](docs/project/principles.md):
  ~1,000 words together, the standing brief. Read when the question is what to
  do next.
- [current context](docs/project/current-context.md): where the build actually
  is, how to build and boot it, what is missing, what has already cost time.
- On demand: [terms](docs/project/glossary.md); [ADRs](docs/adrs/README.md);
  [questions](docs/project/decision-backlog.md);
  [risks](docs/project/risk-register.md).
- Never cold-read `docs/research/results/`, session history, or every linked
  source. Those are for an explicit evidence or history task.
- Cite only paths actually read.

## Defaults

- **Build it.** Writing NeutrinOS source needs no plan, gate or sign-off.
  Disposable VMs and scratch disks are the working environment and a rebuild is
  the undo.
- systemd-first: [ADR-0001](docs/adrs/0001-systemd-first.md). An overlapping
  alternative requires recorded evidence.
- Bounded, declarative, reviewable, non-Turing-complete operator config; exact
  upstream-native config remains available.
- Use existing IDs, terms, templates and the ADR workflow. Record a decision
  when it is made, not in advance of making it.
- Working code beats a candidate label. If a fixture has survived long enough to
  be load-bearing, write the ADR or replace it.

## Safety

These are about damage that is not a rebuild away.

- No mutation of `desktop-jason`, `router`, `misc` or any other physical or
  production host. VMs and spare disks only.
- No production signing, Secure Boot enrollment, recovery, fleet or credential
  material in development or tests. Synthetic fixtures only.
- No push, merge, release or publication without an explicit request.

## Work

- Before edits: `git status`; preserve unrelated tracked, untracked and staged
  work.
- After edits: `mise run check:fast`. Report what ran and what did not.
  Bootstrap and details: [validation](docs/project/validation.md).
- Editing `tools/validation/`: `mise run check:complete`, not `check:fast`.
  Every VM and fixture check is `complete`-only, so `fast` cannot see the code
  being changed. Do not edit the tree while it runs; it asserts repository state
  is unchanged, and an edit mid-run trips that assertion.
- Small coherent commits, on request; no unrelated work folded in.
- Update the source and `current-context.md` together when what that file says
  stops being true. Keep it under 1,100 words; detail goes to the owning record.
- Multi-agent only by explicit request. Per task: owner + file scope + isolated
  worktree or branch. No concurrent same-file edits.
- Agent memory is non-authoritative; never the sole home of a result or a next
  action.
- **NEVER `pgrep`, `pkill`, or `ps | grep`.** No exception, no last resort. A
  name pattern is not a process identity: the searching command's own argv
  contains the pattern, so a wait loop matches itself and never exits while the
  work it watches has already finished. Wait on the background task and read its
  output when notified; in a shell, hold the pid you started (`cmd & pid=$!;
  wait "$pid"`); to wait on a condition, test the condition. If none of those
  fit, restructure the work.
- MUST NOT block the turn over 90s. Anything expected to run longer (VM
  matrices, `check:complete`, composition) runs in the background; keep working.

## Language

Binding. These words let a false claim pass review; the fail-open findings are
the same defect in mechanism.

- Never **signed**, **healthy**, **current**, **green** in place of
  authenticated, authorized, qualified, eligible, blessed.
- Never **trusted** without naming the anchor and the guarantee.
- Never bare **root**: name the release artifact, its `/usr` slot, the writable
  root partition, or the verity root hash.
- Never **latest** as identity or selection rule: name the version ordering,
  channel, authorization, or maintenance policy.
- Qualify **image**, **manifest**, **scope**, **role**, **state**, **target**.
  **layer** only inside an upstream term (OCI layer).
- Deployment status is acquired, staged, selected, booted, blessed — not
  installed or active.
- Use upstream names unchanged for upstream objects. A NeutrinOS term must not
  imply a property that has not been established.
- Full dictionary on demand: [glossary](docs/project/glossary.md).

## Communication

- Concise by default. Pointers, bullets, sentence fragments. Prose only when it
  improves precision.
- Lead with outcome. Preserve required facts, evidence, caveats, blockers, next
  action. Cut narration, repetition, generic reassurance.
- Handoff: what changed; what was preserved; checks run and their result; what
  is measured versus assumed; blockers; exact next action.
