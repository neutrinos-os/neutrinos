# NeutrinOS agent index

## Read

- First: [current context](docs/project/current-context.md) — gate, plan, next
  action, constraints. Derived; linked sources win.
- Task scope: active plan + only its relevant links.
- Terms: [glossary](docs/project/glossary.md).
- Decisions: [accepted ADRs](docs/adrs/README.md); questions:
  [backlog](docs/project/decision-backlog.md); aggregate status:
  [work register](docs/project/work-register.md).
- History only when needed: [session summary](docs/background/design-session-summary.md),
  then transcript.

## Authority

- Sole acceptance authority: Jason Tarasovic. Agents draft/challenge/recommend;
  never accept decisions, designs, requirements, ADRs, plans, or gates.
- Accepted records/requirements: policy. Accepted ADRs: architecture. Designs:
  arguments. Research/background: evidence/history. Plans: bounded work
  authority only. Summaries/issues/PRs: non-authoritative.
- Never promote preference, candidate, fixture, transcript remark, experiment,
  or implementation accident into a decision.

## Defaults

- Pre-implementation docs phase. No NeutrinOS source code until plan + gate
  explicitly authorize it.
- systemd-first: [ADR-0001](docs/adrs/0001-systemd-first.md). Overlapping
  alternative requires recorded evidence.
- Bounded, declarative, reviewable, non-Turing-complete operator config; exact
  upstream-native config remains available.
- Separate policy / mechanism / evidence / implementation / rollout authority.
- Use existing IDs, terms, templates, design/review pairs, ADR workflow.

## Safety

- No mutation of `desktop-jason`, `router`, `misc`, other physical/production
  hosts without an accepted plan naming the exact mutation.
- No production signing, Secure Boot, enrollment, recovery, fleet, machine, or
  credential authority in development/tests.
- No push, merge, release, publication, or other remote write without explicit
  user request.
- Scope/authority crossing, accidental deferred decision, unreliable evidence:
  stop; return to review.

## Work

- Before edits: `git status`; preserve unrelated tracked/untracked/staged work.
- Validate via commands in current context. Report checks run/not run.
- Small coherent commits; only after user approval/request; no unrelated work.
- Update source + affected indexes/context/work register together when their
  declared triggers fire.
- Multi-agent only by explicit user request. Per task: owner + file scope +
  isolated worktree/branch. No concurrent same-file edits. Integrator owns
  shared-file conflict resolution.
- Agent memory: non-authoritative; never sole home of decisions/results/next
  action.

## Communication

- Concise by default. Pointers, bullets, sentence fragments. Prose only when it
  improves precision.
- Lead with outcome. Preserve required facts, evidence, caveats, decisions,
  blockers, next action. Cut narration, repetition, generic reassurance.
- Handoff: plan/task; scope; changed/preserved files; checks/evidence;
  accepted vs candidate/open; blockers/risks; exact next action.

