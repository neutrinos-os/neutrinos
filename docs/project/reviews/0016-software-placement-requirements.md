---
id: PR-0016
subject: Software placement and execution-boundary requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Software placement and execution-boundary requirements review

## Decision scope

This review asks whether SYS-121 through SYS-132 should become normative before
NeutrinOS selects exact user tools, desktop applications, Flatpak scope/remotes,
mise backends, project-container tooling, sysext use, OCI runtime policy, or the
microVM mechanism.

It reviews DES-0013 and proposed EX-0015. Acceptance would establish ownership
and lifecycle boundaries, not accept the leading mechanisms.

## Summary judgment

The requirements should be accepted after owner review. They prevent an
immutable OS from concealing uncontrolled mutation in user and workload stores,
while avoiding the opposite mistake of coupling every personal tool to the OS
release.

The decisive rule is that promised role and recovery capability belongs to the
release. Everything else may update independently only when its owner, access,
state, and support consequences remain explicit.

## Proposed requirement disposition

### SYS-121: every component has one accountable placement

An exact component is joined to a semantic placement class, owner, source,
execution boundary, state, updates, recovery, evidence, and support effect.
Package format alone cannot assign the class.

### SYS-122: role and recovery dependencies are release-owned

Boot, unattended role behavior, policy enforcement, host health/update, and
recovery cannot depend on mutable user, project, application, workload, guest,
or network-only state.

### SYS-123: host extensions retain release obligations

Any sysext or equivalent host hierarchy extension is compatibility-bound,
authorized, qualified, and transactionally visible as release-owned software;
it is not a personal package layer.

### SYS-124: user baselines cannot become hidden host configuration

User tools remain interactive, non-critical, reconstructible, source-bounded,
and independently current. Their manifests, hooks, shims, and command
precedence are inspectable.

### SYS-125: project environments are revision-bound executable inputs

Projects own their toolchains and declare direct/container/guest execution.
Newly encountered configuration is not silently trusted or executed.

### SYS-126: application security follows effective permissions

Desktop application origin, identity, installation owner, effective static and
dynamic access, state, update, rollback, and maintenance determine the claim;
the packaging label does not.

### SYS-127: workloads require more than image identity

Exact artifact identity joins runtime configuration, mappings, attachments,
credentials, state, health, update, backup, and retirement. Mutable container
history is not represented as a rebuilt artifact.

### SYS-128: guests retain a complete guest lifecycle

A stronger kernel/OS boundary is used only for a declared need and retains its
own artifact, patch, identity, storage, network, credential, health, and
recovery responsibilities.

### SYS-129: executable and activation resolution is deterministic

All command and activation paths reveal candidate realizations and selection.
Mutable lower-authority paths cannot shadow release software for privileged or
unattended consumers.

### SYS-130: update and rollback claims stop at update domains

Each class reports currentness and recovery independently. Cross-domain
compatibility must be joined explicitly; OS rollback cannot claim application,
workload, or guest state rollback.

### SYS-131: placement changes are stateful migrations

Moving a component between classes transfers owner, authority, state,
credentials, precedence, update, and support through a verified cutover with a
return path.

### SYS-132: inventory joins classes without flattening assurance

Machine status can traverse component, realization, privilege, state,
currentness, vulnerability, evidence, and owner across all classes while
preserving native diagnostics and coverage gaps.

## Guardrails from adversarial review

### Minimal host is subordinate to a recoverable role

Image size does not justify moving required diagnostic or recovery capability
to a user-controlled online installer.

### Immutable root is not immutable machine

User tools, Flatpaks, container stores, volumes, and guests are intentionally
mutable domains. They require independent inventory and recovery truth.

### Sandbox and container are claims to prove

Whole-home mounts, sockets, devices, D-Bus, host execution, credentials, and
the shared kernel can erase the expected boundary.

### Developer convenience is not hostile-code isolation

Toolbx-style integration may be exactly right for a trusted project while being
the wrong boundary for an untrusted checkout.

### One joined status is not one support promise

Visibility across the machine must not imply NeutrinOS release qualification
or maintenance ownership for user and third-party components.

## Strongest alternatives rejected at policy level

### Put every executable in the OS image

Rejected because it couples user/project iteration to release rollout and
creates unnecessary variants without improving ownership of unrelated data.

### Put everything non-core in containers

Rejected because a format does not resolve desktop integration, project trust,
state, runtime access, update, or guest-kernel requirements.

### Let each tool choose its own installation method

Rejected as a supported default. It creates unbounded trust roots, update
agents, command precedence, state paths, and recovery procedures.

### Treat anything outside the image as unsupported and invisible

Rejected. Users will run software, and visibility is required for diagnosis and
security response. Ownership-aware inventory can report it without granting a
release support promise.

## Required implementation evidence

Acceptance establishes policy only. DES-0013 still requires:

1. representative workstation and router placement inventories;
2. role-critical offline/absence recovery;
3. mise and project-trust evaluation;
4. Flatpak origin, permission, portal, update, rollback, and backup results;
5. Toolbx/container integration and ownership results;
6. exact OCI versus mutable-container evidence;
7. command and activation shadowing tests;
8. cross-domain rollback and compatibility tests;
9. interrupted placement migration; and
10. measured operating cost.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-121 through SYS-132 are
normative policy boundaries. DES-0013 remains in review until EX-0015 supports
exact user, project, desktop-application, workload, extension, and exception
choices.
