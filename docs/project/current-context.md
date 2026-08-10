---
status: informative
last_updated: 2026-08-10
source_snapshot_revision: 8dd0669
current_gate: G0-complete
target_gate: G1
active_plan: PLN-0000
---

# Current project context

> Maintained, non-normative orientation aid. Safe to rely on for read-only
> status/orientation; do not traverse its links by default. Before a mutation,
> acceptance, or high-risk claim, verify the governing source. A conflicting
> source wins and this summary must be corrected.

## Current position

NeutrinOS has an accepted architecture-policy baseline and is preparing the G1
gate for one disposable VM-only evidence prototype. G1 is **not satisfied** and
NeutrinOS source implementation is **not authorized**.

[PLN-0000](../plans/0000-pre-implementation-readiness.md) is active only for
repository readiness, documentation, validation, and collaboration
scaffolding. Its next action is to repair the EX-0016 cold-start context route:
the first repair preserved semantics but Codex still opened broad sources and
historical results. Rerun Codex and Claude after the structural repair, then
close PRE-012/PRE-013. The layered test strategy in PRE-014 follows.

The [work register](work-register.md) is the aggregate view of remaining work.
The [decision backlog](decision-backlog.md) owns question state. Neither is
architecture authority.

## Accepted decisions relevant now

- The project name is **NeutrinOS** in prose, **`neutrinos`** in machine-facing
  identifiers, and **`neutrinos-os`** for the GitHub organization
  ([naming decision](naming.md)).
- NeutrinOS is systemd-first; an overlapping non-systemd mechanism carries a
  documented burden of proof ([ADR-0001](../adrs/0001-systemd-first.md)).
- Routine, exceptional, machine, and data authorities remain separate, with an
  independently usable recovery path
  ([ADR-0002](../adrs/0002-separate-authority-and-recovery.md)).
- Fleet intent uses bounded TOML records and exact native configuration, JSON
  Schema validation, and canonical JSON evidence
  ([ADR-0003](../adrs/0003-bounded-fleet-intent-representation.md)).
- Accepted system policy covers deployment lifecycle, configuration, storage
  boundaries, package inputs, supply-chain evidence, rollout, installation,
  credentials, Unix identity, and software-placement boundaries
  ([system requirements](../requirements/system.md)). Exact mechanisms remain
  open where no ADR accepts them.
- PLN-0000's readiness model and fixture/defer classifications are accepted.
  PRE-001, PRE-002, PRE-010, and PRE-011 are satisfied; PRE-018 and G1 are not.

## Leading but unaccepted fixtures

These may support a bounded experiment. They are not permanent architecture:

- direct systemd/UAPI-oriented image composition, likely using mkosi, with
  bootc retained as the required deployment-substrate challenger;
- a declared Fedora stable package snapshot, with a literal Arch snapshot as
  the required package-ecosystem challenger;
- an EROFS root and Btrfs mutable state for later evaluation; the exact storage
  layout, encryption, and recovery mechanism remain open;
- `systemd-sysinstall` as the leading installation mechanism;
- a general distribution kernel with a normal initrd for the first VM fixture;
  and
- an ordinary disposable VM as a test harness, not an accepted microVM product
  model or role.

W-002 microVM lifecycle, W-004 kernel specialization, and workstation, laptop,
router, server/storage, and guest role contracts remain open or explicitly
deferred to later gates. Do not encode their fixture shapes as permanent
architecture.

## Allowed and prohibited work

Currently allowed:

- documentation, repository guidance, validation scaffolding, and other
  readiness changes within active PLN-0000;
- read-only repository and host inspection when the specific task authorizes
  it; and
- documentation-only evaluation with synthetic inputs.

Currently prohibited:

- NeutrinOS source implementation or a reference-VM build under G1;
- mutation of `desktop-jason`, `router`, `misc`, or another physical host;
- use of production credentials, signing keys, enrollment state, recovery
  material, or machine authority;
- treating a candidate fixture, successful probe, or agent summary as an
  accepted decision; and
- autonomous push, merge, release, or publication.

The full mutation boundary and stop conditions live in
[PLN-0000](../plans/0000-pre-implementation-readiness.md).

## Working-tree and validation expectations

Assume a dirty worktree may contain user or another task's work. Inspect it
before editing, preserve unrelated changes, and name them in the handoff.
Concurrent work requires explicit ownership and isolated worktrees as defined
in the root [repository instructions](../../AGENTS.md).

Until PRE-015 supplies canonical entry points, documentation changes must pass:

```sh
git diff --check
```

and the existing internal Markdown-link check:

```sh
perl -MFile::Basename=dirname -MFile::Spec -e 'for my $f (@ARGV) { open my $h, q{<}, $f or die qq{$f: $!\n}; my $code=0; while (<$h>) { if (/^\s*```/) { $code=!$code; next } next if $code; while (/\[[^\]]*\]\(([^)]+)\)/g) { my $p=$1; $p =~ s/#.*//; $p =~ s/^<|>$//g; next if $p eq q{} || $p =~ m{^(?:https?|mailto):}; my $x=File::Spec->rel2abs($p,dirname($f)); print qq{$f -> $1\n} unless -e $x } } }' $(rg --files --hidden -g '*.md' -g '!.git/**')
```

No output from the link check is a pass. These commands are temporary and do
not satisfy PRE-015.

## Context path for a fresh task

1. Read root [AGENTS.md](../../AGENTS.md).
2. Read this file; stop for a read-only orientation/status task.
3. For execution/editing, read the active
   [PLN-0000](../plans/0000-pre-implementation-readiness.md) sections governing
   the exact task.
4. Read the [work register](work-register.md) only for aggregate backlog/gate
   analysis.
5. Open only the authoritative source needed for the exact decision, change,
   conflict, or risk.
6. Consult the [design-session summary](../background/design-session-summary.md)
   or full transcript only for history and provenance.

## Maintenance and verification

Update this file whenever any of the following changes:

- the active gate or active plan;
- an accepted, rejected, superseded, or reopened decision relevant to current
  work;
- a leading mechanism or experimental fixture relevant to current work;
- the allowed or prohibited mutation boundary;
- the canonical validation commands; or
- the one next action.

Set `source_snapshot_revision` to the source revision against which the summary
was checked. This names its inputs, not this file's containing commit, and may
therefore precede HEAD. PRE-012 and PRE-013 remain incomplete until
[EX-0016](../research/exercises/0016-agent-context-and-instruction-loading.md)
passes across the supported clients.
