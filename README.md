# NeutrinOS

A systemd-first Linux system for a personal fleet, developed as a reusable
framework. The unit of deployment is a complete, content-identified system
image; machine configuration is bounded and declarative; and every release is
meant to be staged, blessed, and rolled back rather than mutated in place.

**This repository contains no NeutrinOS source code and is not usable as an
operating system.** It is a design record in the pre-implementation phase.
Implementation is not authorized until the G1 gate is accepted.

## Status

| | |
| --- | --- |
| Phase | Pre-implementation; `G0-complete`, preparing `G1` |
| Active plan | [PLN-0000 pre-implementation readiness](docs/plans/0000-pre-implementation-readiness.md) |
| Distribution | Personal fleet and reusable framework; not a public distribution |
| License | [Apache-2.0](LICENSE) |

Reuse is permitted under Apache-2.0. "Not a public distribution" limits
support and compatibility promises, not source visibility: there is no
warranty and no commitment to external users, hardware, or configurations.

## Where to start

- [Documentation index](docs/README.md) — the full design record.
- [Current project context](docs/project/current-context.md) — a
  self-contained snapshot of where the project actually stands. Read this
  before trusting any summary elsewhere.
- [Charter](docs/project/charter.md) and [scope](docs/project/scope.md) — what
  the project is and is not.
- [Architecture decisions](docs/adrs/README.md) — what is settled.
- [Decision backlog](docs/project/decision-backlog.md) — what is not.

Documents marked `draft`, `sketch`, or `proposed` are arguments, not
commitments. Only accepted records and accepted ADRs carry authority.

## Working in this repository

Contributions are not open at this stage; the repository is developed by its
owner, with agents drafting under supervision.

- [`AGENTS.md`](AGENTS.md) is the canonical instruction file for both humans
  and agents. Read it before making any change.
- [`docs/project/repository-hygiene.md`](docs/project/repository-hygiene.md)
  governs layout, identifiers, ignored state, and dependencies.
- [`docs/project/validation.md`](docs/project/validation.md) describes
  bootstrap and the canonical checks.

## Validation

Bootstrap once as described in
[validation usage](docs/project/validation.md#bootstrap), then:

```sh
mise run check:fast
mise run check:complete
```

Behavior is defined by the accepted
[validation execution contract](docs/project/validation-contract.md).
