---
id: RES-0016
status: in-review
last_updated: 2026-08-11
evidence_cutoff: 2026-08-11
---

# Maintaining the record corpus: approvals, artifact lifecycle, and a derived graph

## Question

The documentation, decision, and approval corpus is becoming expensive to keep
correct by hand, and the project is only at PLN-0002. What structure would make
approvals, artifact creation and modification, and cross-document state
consistent by construction rather than by diligence?

Recorded 2026-08-11 at owner request so the analysis is not lost. **Nothing
here is proposed for adoption yet**, no tool is selected, and no gate covers
this work. It is background for a decision that has not been framed.

## Why now

Measured on 2026-08-11, before any tooling exists:

| | Count |
| --- | --- |
| Markdown files under `docs/` | 140 |
| Words | ~258,000 |
| Documents carrying an `id:` | 87 |
| Internal document links | ~476 (grep-counted, approximate) |

That is a short book with a citation graph, maintained entirely by hand, at the
second implementation plan of the project. The growth is not anomalous -- it is
what the project's own separation of policy, mechanism, evidence, and
implementation authority produces, and that separation is working. The corpus
is not too large. It is too *unmechanised* for its size.

### The failures are a species, not a scattering

Evidence from a single working day, 2026-08-11, during which PLN-0002-03 was
split into 03a and 03b and two amendments were accepted:

- A task rename required hand-finding references across six files. Nothing
  detected the stale ones; a `grep` written from memory did.
- Documents recording a proposal as "drafted, not accepted" had to be rewritten
  by hand once accepted, in four places, with tense and status leftovers found
  only on a second pass.
- The same status facts are duplicated across the governing plan's task table,
  `current-context.md`, and `work-register.md`, and must be edited together.
  Nothing enforces that.
- An acceptance -- "accepted by Jason Tarasovic on 2026-08-11" -- exists only as
  a sentence typed into prose by an agent. There is no structural difference
  between a real approval and a fabricated one.

None of these was a reasoning error. Every one was **referential integrity or
duplicated state**. That is a mechanical problem with a mechanical answer.

The last item is the serious one. `AGENTS.md` states that agents never accept
decisions, and today that rule is enforced entirely by agent good behaviour.

## Three problems, deliberately separated

Conflating these is how the answer gets over-built.

1. **Referential integrity.** Do referenced IDs exist? Are links live? Is a
   status vocabulary respected? Is every document reachable from an index?
   *Wholly mechanical. Cheapest to fix, and covers most observed failures.*
2. **Derived state.** `work-register.md` and `current-context.md` contain no
   original facts. Every cell restates something owned elsewhere. They go stale
   because restating is manual.
   *Mechanical once (1) exists.*
3. **Event history.** Approvals, artifact creation, artifact modification,
   status transitions. Currently implicit in git history and prose.
   *Not derivable from the documents. Needs a new record.*

Retrieval -- finding the right document -- is **not** on this list. It is not
the observed pain, and `AGENTS.md` deliberately suppresses discovery ("read only
this file + current context. Hard stop."). Semantic search over the whole corpus
would fight that discipline rather than serve it. This is the strongest reason
to keep embeddings out of scope until a retrieval problem is actually observed.

## The line that matters: authored versus derived

The corpus's value is prose that no schema can hold. "The ParticleOS rationale
does not transfer, because our `/etc` is regenerated at every boot" is the whole
worth of [RES-0015](stateless-etc-configuration-delivery.md), and it is not a
field. Any design that pushes authored reasoning into a database either stores
it as opaque blobs -- a content management system with extra steps -- or
pressures the prose to fit a schema, degrading the thing that makes the corpus
useful.

So the line is:

- **Authored, and staying prose in files**: plans, ADRs, designs, research,
  records, reviews. The argument is the artifact.
- **Derived, and safe to generate**: frontmatter fields that restate
  relationships, the aggregate documents (`work-register.md`, index sections of
  `current-context.md`), and the graph itself.

Stated the other way: **do not generate the documents. Generate the
duplication.** This maps onto the project's existing authority separation rather
than cutting across it.

## Generated frontmatter

Owner refinement, 2026-08-11, and better than generating whole documents. The
frontmatter is already the machine-readable projection of each document, and it
is exactly what drifts. Making it generated closes the gap without touching a
word of prose.

The requirement this creates is a clean split within the frontmatter itself,
so a human never hand-edits a generated key and a generator never clobbers an
authored one:

- **Authored keys**: `id`, `title`, `owner`, `status` where status is an act of
  judgment rather than a computed consequence, `governing_plan`.
- **Generated keys**: `blocked_by`, `blocks`, `referenced_by`, `supersedes`
  chains, `last_accepted`, `evidence_for`, and the derived half of
  `last_updated`.

The generated block must be visibly fenced and marked as generated, and the
generator must be idempotent, so a diff that touches it is either a real change
or a bug. Whether generated frontmatter is committed or produced on demand is
open: committing it keeps the corpus self-contained and reviewable in a diff,
which matters here more than usual, at the cost of churn.

## The event ledger

Problem 3 needs a record that does not exist. Approvals, artifact creation, and
artifact modification are events, not states, and reconstructing them from
document diffs is lossy -- a `status:` change from `open` to `accepted` records
that it happened, but not who accepted it, against which review, or on what
evidence.

Shape, kept minimal:

- **Append-only**, one event per entry, never rewritten. A correction is a new
  event that supersedes an old one.
- **Text, not binary** -- JSONL or TOML -- because the reviewable git diff *is*
  the authority mechanism in this project. An acceptance that cannot be read in
  a commit is not an acceptance. This constraint eliminates every embedded
  database as a system of record, independent of quality.
- **Events at minimum**: `accepted`, `rejected`, `superseded`, `reopened`,
  `created`, `modified`, `blocked`, `unblocked`, each with actor, timestamp,
  subject ID, and the governing review or plan.
- **Acceptance is a distinct, attributable act.** This is what converts
  `AGENTS.md`'s rule from a behavioural norm into something with a structural
  trace. It does not by itself prevent an agent writing an `accepted` event, and
  a design that wants real enforcement needs something an agent cannot produce
  -- a signature, or a step outside the agent's reach. Worth stating as an open
  question rather than assuming the ledger solves it.

## Queries worth having

The point of the graph, and the part that justifies it over a linter. Drawn
from questions actually asked during PLN-0001 and PLN-0002:

- What is this plan blocked on, transitively?
- What does this decision block? What breaks if it is reopened?
- What references this ID? (The task-rename failure above.)
- What is `accepted` but has no evidence recorded against it?
- What is being *relied on* while still `open` or `candidate`?
- What changed since the last gate?
- **Which candidate fixtures have been used repeatedly without a decision?**

The last one deserves emphasis. PR-0029 C-005 and PR-0030 C-006 both name the
same failure: a fixture becomes a decision by working repeatedly, unremarked.
The project currently defends against it with vigilance and prose warnings. A
graph that counts uses of a candidate against the absence of an accepting ADR
could **detect it mechanically**. That is a project-specific capability with no
off-the-shelf equivalent, and it is the strongest argument in this document for
building something rather than importing something.

## What any answer must preserve

Constraints from `AGENTS.md`, and the reason a general-purpose knowledge tool is
unlikely to fit unmodified:

- Reviewable git diffs remain the authority mechanism.
- Bounded cold-context reading. A tool that encourages traversal defeats the
  read discipline that keeps agent context honest.
- Agents never accept. Tooling must make acceptance harder to fake, not easier
  to type.
- Non-Turing-complete, declarative, reviewable configuration -- the project's own
  default, which should apply to its own tooling.
- Minimal dependencies. `jsonschema` is currently the repository's only runtime
  dependency and that is a property worth keeping.

## Implementation shapes, none selected

| Shape | Fits | Cost |
| --- | --- | --- |
| Validator only, plain Python over frontmatter and links, wired into `check:fast` | Problem 1 entirely | Small; no new dependencies; the validation harness already exists |
| Validator plus generator for aggregates and generated frontmatter | Problems 1 and 2 | Moderate; needs the authored/generated split settled first |
| Append-only text event ledger plus CLI | Problem 3 | Moderate; new record type, new discipline |
| Embedded graph database as derived index | Query ergonomics | Real dependency; at 87 nodes and ~476 edges a dictionary is sufficient |
| Embedded graph database as source of truth | — | **Rejected on the git-diff constraint above**, not on quality |

An embedded graph database was examined on 2026-08-11 as a concrete example
rather than as a candidate. The finding that generalises: on-disk binary storage
disqualifies any such tool as the *system of record* here, while the corpus is
far too small for its performance properties to matter as a *derived index*.
Both halves of that argument are independent of which product is examined.

Vector search and embeddings are out of scope for the reasons in "Three
problems" above. The plausible future home for them is cross-session **agent
memory** over transcripts and history -- a different corpus, at a different
scale, that is not git-tracked and where the objections here do not apply.

## Risks

- **This is tool-building, mid-plan.** PLN-0002 is active and blocked on an
  upstream outage, which makes an infrastructure detour unusually attractive
  right now. The validator is small enough not to be one; a full graph CLI is
  not.
- **Recursion.** Adopting tooling to manage the decision corpus is itself a
  decision requiring declared inputs, a plan, and evidence. That is not an
  argument against it, but the work should be planned rather than absorbed.
- **Over-fitting to today's failures.** The observed pain is one day of
  evidence, however sharp. Growth to G3 or G4 may change which of the three
  problems dominates.
- **Generated frontmatter is a schema commitment.** Once tasks and documents
  have machine-readable relationships, changing the relationship model becomes a
  migration.

## Not decided

No tool, no shape, no schedule. The one thing this document does recommend, and
recommends only as a first step to be judged on its own: **the validator**,
because it addresses the entire observed failure class, costs nothing in
dependencies, fits the existing `check:fast` contract, and is useful whether or
not anything further is ever built.
