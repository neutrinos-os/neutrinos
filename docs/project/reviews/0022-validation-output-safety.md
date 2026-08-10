---
id: PR-0022
subject: Validation retained-output safety
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Validation retained-output safety review

## Decision scope

This review challenges the PRE-015 output path after registered test execution.
It proposes closing C-007 from
[PR-0020](0020-validation-runner-hostile-probes.md). It does not satisfy
PRE-015, define long-term quarantine retention, or authorize NeutrinOS product
implementation.

## Summary judgment

Each execution now creates a unique synthetic canary, supplies it only to the
registered child environment, and scans stdout, stderr, result records,
declared artifacts, and the proposed manifest before retention. Conservative
credential markers supplement the exact canary. Unsafe raw files move to a
private sibling quarantine; retained results contain only a placeholder,
finding kind, relative source, and local quarantine path. A finding fails the
run. Sixteen hostile runner probes pass.

The mechanism is suitable for this validation slice. It does not turn pattern
matching into a secret-management boundary: absence and exact environment
allowlists remain the primary defense. New output channels and credential
formats must be registered before they can support a claim.

## Challenges

### C-001: A canary that never reaches a test proves little

- Severity: high
- Claim: scanning for an ambient value stripped before execution cannot detect
  an output leak in a registered test.
- Response: the runner generates a per-run value and injects it under the
  dedicated `NEUTRINOS_VALIDATION_CANARY` child variable. Its value is never
  placed in retained metadata.
- Disposition: resolved in implementation
- Residual risk: purpose-built native runners must continue to use the common
  child environment rather than construct a wider one.

### C-002: Scanning only process logs misses other retained paths

- Severity: critical
- Claim: a safe stdout capture is irrelevant if the same material survives in
  a result record, crash file, serial log, or artifact.
- Response: stdout and stderr are scanned as files; each canonical result line
  and the complete proposed manifest are scanned before writing; every
  non-directory entry beneath the declared artifact root is scanned. Future
  crash and VM serial output must enter one of those registered paths.
- Disposition: resolved for current retained output classes
- Residual risk: adding a new retention root without routing it through the
  scanner reopens C-007.

### C-003: Quarantine can accidentally remain uploadable

- Severity: critical
- Claim: renaming an unsafe file beneath the run directory would still expose
  it to the initial CI artifact upload.
- Response: the quarantine is a separately allocated mode-0700 sibling under
  the system temporary root, never beneath the run directory. The original log
  or artifact becomes a content-free mode-0600 placeholder. `run.json` reports
  the quarantine path and finding metadata, never matched content.
- Disposition: resolved in implementation
- Residual risk: PRE-016 must define local quarantine expiry and disposal; CI
  must upload only the reported run directory.

### C-004: File tricks can bypass or block scanning

- Severity: high
- Claim: following a symlink may read outside the run while a FIFO or device
  can block the scanner indefinitely.
- Response: only regular files are read. Symlinks and other special entries are
  classified as unsafe and quarantined without following them. Scan errors are
  likewise unsafe. The scanner reads bounded chunks with overlap so a marker
  crossing a chunk boundary is still found.
- Disposition: resolved for the current local-filesystem runner
- Residual risk: inability to move an unsafe file makes execution fail but
  still requires CI to suppress upload when the run directory itself cannot be
  made safe.

### C-005: Heuristic secret detection creates false confidence

- Severity: high
- Claim: no finite pattern list detects every credential, and broad patterns
  can quarantine valid diagnostics.
- Response: the exact per-run canary is the deterministic probe. Narrow markers
  for private keys, AWS access keys, GitHub tokens, and bearer authorization
  supplement it. The contract continues to make secret absence primary.
- Disposition: resolved as a bounded claim
- Residual risk: registrations using another synthetic credential shape must
  extend the scanner and hostile probes explicitly.

### C-006: A sanitized result can hide that the test failed safety

- Severity: high
- Claim: replacing raw output without changing result semantics could produce
  a green run.
- Response: the affected test record is reconstructed as failing, names the
  content-free findings, and omits unsafe diagnostic references. The manifest
  records `failure_stage=output_safety`, reports the quarantine path, and the
  command exits 1.
- Disposition: resolved in implementation
- Residual risk: result and manifest schemas remain PRE-016 work.

## Probe observations

Working tree based on `0352c06`, Python 3.14.7, uv 0.12.3:

- `T5-VAL-001`: sixteen probes passed in 0.89 seconds;
- exact canary and conservative credential-marker matches were detected;
- a canary split across scanner chunks and a private-key artifact were moved
  outside the retained run while safe placeholders remained;
- a synthetic registered execution containing the canary failed at
  `output_safety`, retained no canary, and recorded one failing test; and
- the normal hostile-probe run retained `output_safety.passed=true` with no
  quarantine.

These are development observations from a dirty checkout, not qualification or
gate evidence.

## Required confirmations

1. C-007 from PR-0020 is closed for every currently retained output class.
2. The per-run canary is runner-private metadata supplied to registered child
   tests; its value is never evidence.
3. Conservative credential markers supplement but do not replace secret
   absence, environment allowlists, or declared synthetic fixtures.
4. Any unsafe finding fails the affected test and the run; raw content stays
   outside the uploadable run directory.
5. A new retained output root or synthetic credential format must extend the
   scanner and hostile probes before use.
6. Quarantine lifecycle, a failed-quarantine CI suppression rule, the retained
   empty-cache probe, clean profiles, initial CI, PRE-015, and G1 remain open.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. Acceptance approves this bounded
implementation increment, closes C-007 within the stated scope, and confirms
the six items above. It does not accept PRE-015 or G1.
