# NeutrinOS agent index

## Read

- Read-only status/orientation/report: read only this file +
  [current context](docs/project/current-context.md). Hard stop.
- Exception: when the user explicitly names or asks to verify one authority,
  open only that source (example: ADR-0001 for systemd-first).
- A request for citations or loaded-instruction files does not authorize source
  discovery. Cite paths from current context; report only files actually read.
- Read-only task: do not run validation commands. Report requirements only.
- Execution/edit: active plan + only sources governing the exact change/risk.
- Never cold-read `docs/research/results/`, session history, or every linked
  source. Use only for an explicit evidence/history task.
- On-demand: [terms](docs/project/glossary.md); [ADRs](docs/adrs/README.md);
  [questions](docs/project/decision-backlog.md); [aggregate](docs/project/work-register.md).

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
- After edits: `mise run check:fast`; run additional checks required by the
  governing plan. Bootstrap/details: [validation](docs/project/validation.md).
  Report checks run/not run.
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
