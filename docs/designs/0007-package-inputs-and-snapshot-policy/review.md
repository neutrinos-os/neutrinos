---
design: DES-0007
reviewer: Codex
perspective: security, operations, failure, maintainability, alternatives
date: 2026-08-10
status: open
---

# Adversarial review

## Summary judgment

The package-input boundary is necessary and the Fedora-first proposal is
plausible. Its strongest advantage is operational: stable-branch fixes can be
qualified without automatically absorbing the full churn of a rolling
repository. Its strongest reason for rejection is equally operational: Fedora
branch migration, snapshot retention, RPM policy, and missing current features
may create more private distribution work than dated Arch snapshots.

The mechanism-independent requirements are accepted. Do not accept the Fedora
selection until EX-0009 measures literal closures and two representative update
workflows.

## Challenges

### C-001: Fedora is being selected from policy, not actual closures

- Severity: critical
- Claim: maintained branches sound safer, but required systemd, kernel,
  workstation, or router packages may be absent, old, patched incompatibly, or
  available only through third parties.
- Failure or cost if true: NeutrinOS immediately grows a private RPM overlay and
  loses the maintenance advantage used to justify Fedora.
- Required response or experiment: build equivalent reference closures and
  list every missing capability, custom build, patch, and third-party import.
- Author response: Fedora remains proposed and EX-0009 is a blocking gate.
- Disposition: open.
- Residual risk: initial closure success does not predict future feature needs.

### C-002: The intake snapshot becomes a home-grown repository service

- Severity: high
- Claim: preserving repository metadata, package bytes, signatures, source
  attribution, and dependency evidence may reproduce a large part of Pulp or
  another repository manager.
- Failure or cost if true: storage and tooling complexity exceeds the value of
  using upstream binary packages.
- Required response or experiment: implement the exercise with the smallest
  content-addressed object set and compare it with an existing snapshot/mirror
  tool before designing a service.
- Author response: the design selects a logical retention boundary, not custom
  server software or a publication protocol.
- Disposition: mitigated on paper; exercise required.
- Residual risk: Fedora's lack of a dated public repository view may force more
  metadata preservation than Arch ALA.

### C-003: Six-month Fedora rebases become forced project deadlines

- Severity: critical
- Claim: a roughly thirteen-month support window gives one maintainer little
  margin if a branch migration exposes state, boot, or package regressions.
- Failure or cost if true: machines run unsupported or urgent migration work
  displaces security and recovery work.
- Required response or experiment: tabletop N-to-N+1 qualification with a
  calendar, overlap budget, failure fallback, and measured owner hours.
- Author response: one current branch and an early migration trigger keep the
  obligation visible; they do not prove it affordable.
- Disposition: open.
- Residual risk: upstream schedule slips and personal availability correlate
  poorly.

### C-004: Stable branches can delay required upstream fixes

- Severity: high
- Claim: an important systemd or kernel behavior may exist upstream but not in
  the selected Fedora branch, while Arch already packages it.
- Failure or cost if true: NeutrinOS must backport, rebase a core package, defer
  an architectural feature, or migrate branches early.
- Required response or experiment: define the actual capability floor and test
  it against both candidates; do not substitute version-number preference.
- Author response: capability gates, not “newest,” drive branch selection.
- Disposition: open.
- Residual risk: later systemd-first decisions can change the floor.

### C-005: “Official only” can make the workstation incomplete

- Severity: high
- Claim: codecs, firmware, hardware support, or user-facing applications may
  require RPM Fusion, COPR, or upstream binaries.
- Failure or cost if true: the policy either blocks real work or accumulates
  ad-hoc exceptions after the architecture is accepted.
- Required response or experiment: inventory the actual workstation's OS-owned
  needs separately from user applications and exercise at least one source and
  one binary-only exception.
- Author response: the finite import boundary permits justified exceptions
  without granting a whole repository transitive trust.
- Disposition: open.
- Residual risk: per-package intake can cost more review time than repository
  trust for a large set.

### C-006: Source builds quietly create a downstream distribution

- Severity: critical
- Claim: project-built RPMs will accumulate patches, toolchain constraints,
  security ownership, and dependency transitions.
- Failure or cost if true: the project repeats the maintenance burden it was
  designed to avoid.
- Required response or experiment: every owned RPM needs an upstream/removal
  condition and the candidate comparison must count ongoing owner work, not
  only whether a package can be built once.
- Author response: owned overlays are exceptional and unbounded ownership is a
  rejection criterion.
- Disposition: mitigated by policy; enforcement evidence required.
- Residual risk: strategically important patches are difficult to remove.

### C-007: Package signatures are overread as supply-chain provenance

- Severity: critical
- Claim: a valid signature authenticates the upstream packaging authority but
  does not prove source correspondence, builder integrity, absence of malware,
  freshness, or project qualification.
- Failure or cost if true: compromised but signed content is promoted as safe.
- Required response or experiment: expose signature, source attribution,
  rebuild/reproducibility status, vulnerability status, and qualification as
  independent fields and test their disagreeing combinations.
- Author response: the design explicitly separates these claims.
- Disposition: resolved in model; implementation test required.
- Residual risk: operators may still over-trust the simplest green status.

### C-008: Package installation executes untrusted code

- Severity: critical
- Claim: RPM scriptlets, triggers, macros, dependency generators, and project
  recipes execute during image construction and can steal credentials or alter
  output outside an expected file manifest.
- Failure or cost if true: a package-input compromise becomes a release-key or
  fleet compromise.
- Required response or experiment: isolate acquisition/build/composition from
  signing, remove secrets and ambient network, record script output, and
  inject a hostile test package.
- Author response: the proposed builder boundary adopts these controls.
- Disposition: mitigated on paper; exercise required.
- Residual risk: compromised build tooling can falsify the recorded output.

### C-009: One package universe can be false simplicity

- Severity: medium
- Claim: a tiny microVM or future storage role may be materially better served
  by a different upstream.
- Failure or cost if true: commonality increases image size, kernel divergence,
  or unsupported local builds.
- Required response or experiment: keep the deployment model distribution-
  neutral and require measured role value before adding a second universe.
- Author response: the choice is initial scope, not a universal invariant.
- Disposition: mitigated.
- Residual risk: adding a second universe later expands every supply-chain gate.

### C-010: Snapshot immutability hides staleness

- Severity: critical
- Claim: a perfectly retained repository state can contain known vulnerable
  packages and appear healthy because its bytes and signatures still verify.
- Failure or cost if true: reproducibility becomes a false currentness signal.
- Required response or experiment: test an old valid snapshot with a newly
  applicable advisory and require distinct stale/current/support status.
- Author response: SYS-060 makes the distinction normative if accepted.
- Disposition: resolved in model; status exercise required.
- Residual risk: upstream advisory data may be delayed or incomplete.

## Missing alternatives or evidence

- Actual Fedora versus Arch package lists for the three initial variants.
- Current systemd, kernel, mkosi, EROFS, Btrfs, TPM, and virtualization feature
  availability rather than version-only comparison.
- A minimal existing tool for immutable RPM intake and offline reconstruction.
- Representative Fedora security-update and branch-migration evidence.
- Representative Arch archive refresh and rolling-regression evidence.
- Actual third-party requirements from the workstation capability design.
- Storage costs for binary packages, metadata, source evidence, and debug data.

## Requirements accepted; changes before design acceptance

SYS-057 through SYS-064 were accepted on 2026-08-10. The ecosystem and
mechanism design remains in review and must:

1. Execute EX-0009 with literal role closures and record owner time.
2. Define the initial capability floor before comparing package versions.
3. Demonstrate offline reconstruction without a mutable upstream URL.
4. Exercise hostile build code and keep release signing outside its boundary.
5. Produce the ecosystem-selection ADR only after the challenger results.
