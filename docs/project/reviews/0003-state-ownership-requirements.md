---
id: PR-0003
subject: State ownership and rollback requirements
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# State ownership and rollback requirements review

## Scope of acceptance

This decision accepts the policy direction and SYS-019 through SYS-026. It does
not accept DES-0002 as a completed architecture or select a storage,
configuration-delivery, backup, migration, or recovery implementation.

In particular, acceptance means:

- ownership and lifecycle are assigned by state contract, not inferred from a
  path such as `/etc` or `/var`;
- the normal effective `/etc` is reconstructible from identified inputs, with
  individually governed persistent exceptions;
- an OS rollback does not claim to roll back durable non-OS state;
- automatic fallback is offered only across compatible or reversibly
  checkpointed state transitions;
- forward-only destructive migration has a visible commit barrier and a
  maintenance/recovery contract;
- preservation and reset operate on named state owners rather than an
  undifferentiated mutable filesystem; and
- machine identity, secrets, and diagnostic evidence have lifecycles distinct
  from OS release selection.

## Accepted challenges and guardrails

The following challenges remain material and must constrain later designs:

1. Reconstructed `/etc` may require persistent exceptions for ordinary Linux
   software. Exceptions are supported behavior, not evidence that all of
   `/etc` should silently become historical mutable state.
2. A state contract must contain only metadata that drives a gate, operation,
   or recovery decision. NeutrinOS must not create a universal state DSL or a
   second package database.
3. Forward-only migrations are sometimes necessary, including for urgent
   fixes. The explicit maintenance path must remain usable without becoming a
   routine loophole around rollback qualification.
4. Availability recovery and compromise recovery are different operations.
   Preserving state after a failed update does not establish that the state is
   trustworthy after an intrusion.
5. A `locally modified` marker provides attribution but does not by itself
   decide whether rollout should warn, block, or expire the override.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. SYS-019 through SYS-026 are
normative project requirements. DES-0002 remains in review until representative
workstation and router contracts, `/etc` behavior, maintenance migration, and
recovery scenarios demonstrate that the requirements are operable without
creating an unbounded management framework.
