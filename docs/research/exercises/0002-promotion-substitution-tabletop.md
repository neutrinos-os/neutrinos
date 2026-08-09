---
id: EX-0002
title: Promotion substitution and signer-compromise tabletop
status: complete
date: 2026-08-09
exercise_type: tabletop
evidence_class: analysis-only
related_designs: [DES-0003, DES-0004]
---

# Promotion substitution and signer-compromise tabletop

## Purpose and evidence limit

This exercise tests C-002 from the DES-0004 adversarial review: whether release
authorization and normal platform signing may safely share one routine
promotion environment.

It is a paper exercise. It does not select a token, HSM, signature format,
qualification service, or promotion implementation. `Pass on paper` means the
authority boundaries can stop or contain the stated single compromise. It does
not prove that an eventual product, procedure, or human interface enforces the
boundary.

The exercise does not claim that signatures make malicious source correct or
that tests will detect every backdoor. Build and qualification integrity remain
separate design obligations under L-002 and L-006.

## Question and success condition

DES-0004 originally allowed the distinct normal-platform and release-
authorization keys to share one promotion device. The question is whether
distinct operations and audit records are sufficient when the software asking
for both signatures may be compromised.

The minimum success condition is:

> Compromise of one routine software or signing compartment must not let an
> attacker turn new attacker-chosen bytes into both a platform-accepted boot
> artifact and a normally authorized NeutrinOS release.

This is a single-compromise boundary, not a claim against a malicious maintainer,
malicious hardware below both compartments, or multiple independent systems
being compromised together.

## Promotion objects

The exercise names four objects so that a user interface cannot blur them:

| Object | Meaning | Required binding |
| --- | --- | --- |
| Candidate | Unsigned build output proposed for platform signing | Source, pinned inputs, build provenance, role, and configuration identity |
| Boot artifact | Exact bytes after normal platform signing | Candidate identity and platform-signature identity |
| Qualification record | Results for the literal signed boot artifact and its complete release-owned artifact set | Boot-artifact hashes, test policy and results, role, configuration, and qualification environment |
| Release authorization | Owner approval for normal deployment | Exact boot artifact and artifact set, qualification-record identity, role or channel, compatibility, and policy metadata |

Platform signing precedes literal qualification because it changes the boot
artifact's bytes. Release authorization follows qualification and must name the
qualified bytes. Publication transports this joined set but grants none of the
authorities.

Qualification evidence must be immutable and attributable. The concrete means
by which the release-authorizer validates that evidence is deferred, but data
rendered only by the coordinating promotion host is not independent evidence.

## Threat boundaries

The routine path contains these potentially distinct failure domains:

1. builder and source-input acquisition;
2. promotion coordinator and its user interface;
3. normal-platform signing compartment;
4. qualification environment and evidence store;
5. release-authorization compartment;
6. publication and discovery infrastructure; and
7. the target's staging and selection logic.

The maintainer is a shared human operator. The model aims to prevent malware on
one routine component from silently exercising both signing authorities; it
does not turn one maintainer into two independent reviewers.

## Original shared-host result

Two distinct private keys, commands, PIN prompts, or audit records on one
general-purpose promotion host fail the success condition. A compromise that
persists across both operations can:

1. substitute an attacker artifact for the artifact displayed to the owner;
2. invoke the platform signer over the substituted bytes;
3. fabricate or misrepresent qualification evidence in the same interface;
4. invoke the release signer over the substituted identity; and
5. produce internally consistent local audit records for the attacker's flow.

Adding a second ordinary token to the same untrusted coordinator does not fix
the problem if both tokens blindly sign requests selected by that host. Human
confirmation of a digest displayed only by the compromised host is also not an
independent control.

**Verdict:** The original permission to place both routine authorities in one
ordinary execution environment is rejected.

## Revised minimum boundary

The two routine authorities may share an owner, replacement policy, physical
location, and correlated loss event because neither private key requires a
backup. They must not share a routine compromise boundary during use.

The revised model requires:

1. The normal-platform and release-authorization keys reside in separate
   signing compartments. No ordinary builder, coordinator, qualification
   worker, publication service, or general-purpose promotion host can invoke or
   extract both.
2. The coordinator is treated as untrusted glue. It may assemble requests and
   copy public evidence, but it is not the source of truth for artifact identity
   at both authorization steps.
3. The platform compartment signs a candidate only into a named, inventoried
   candidate context. Its output gains no normal-release status by being
   firmware-acceptable.
4. Qualification tests the literal platform-signed bytes and emits an immutable,
   attributable record bound to those bytes.
5. The release-authorization compartment independently validates the complete
   promotion bundle and the qualification-record binding. A confirmation shown
   only by the coordinator is insufficient.
6. The release operation binds role, channel, configuration compatibility, and
   policy metadata in addition to hashes. It cannot authorize an equivalent
   rebuild, mutable tag, or differently signed artifact.
7. Platform-signed but unreleased candidates are inventoried as hazardous
   intermediate artifacts. Rejection, retention, and destruction status remain
   visible so a compromised release signer cannot silently select an unknown
   pool of candidates.
8. Targets and publication tooling reject mismatched combinations of artifact,
   qualification identity, and release authorization. Withholding and replay
   remain availability and freshness concerns under SYS-037.

The required compartments may eventually be separate devices or independently
enforced signing systems. Product selection is deferred. A claimed partition
must be evaluated by the compromise it survives, not by the number of key files
or prompts it presents.

## Scenario results

### P-001: Builder or source-input path is compromised

**Event:** The builder produces attacker-chosen bytes with plausible provenance.

**Expected containment:**

1. The builder has neither routine private key.
2. Platform signing creates only a candidate, not a release.
3. Qualification operates on the literal signed artifact.
4. Release authorization requires attributable qualification evidence and an
   owner decision for that exact identity.

**Result:** Conditional and outside signer separation alone. The revised model
prevents the builder from self-authorizing, but tests, provenance, review, and
reproducibility must detect or bound a malicious build. A sufficiently subtle
malicious build can still become a deliberately authorized release.

### P-002: Promotion coordinator or its display is compromised

**Event:** Malware controls artifact selection, request assembly, and everything
shown on the ordinary promotion workstation.

**Expected containment:**

1. The coordinator cannot exercise both private keys.
2. The release compartment validates artifact and qualification bindings through
   a channel or policy boundary the coordinator cannot rewrite.
3. Conflicting identities stop promotion and produce evidence outside the
   coordinator's sole control.

**Result:** Pass on paper only under the revised boundary. Blind signers or a
digest confirmed solely on the compromised display fail this scenario.

### P-003: One host can invoke both routine keys

**Event:** A single host reaches the normal-platform and release-authorization
operations, whether the keys are files or two attached tokens.

**Expected containment:** None. The host can request both signatures over a
substituted flow and lie to the maintainer about the identities.

**Result:** Fail. This arrangement is not a conforming implementation of
DES-0004.

### P-004: Normal-platform signing compartment is compromised

**Event:** The attacker can sign arbitrary boot artifacts with the normal
platform leaf but cannot use the release-authorizer.

**Expected containment:**

1. The artifacts are firmware-acceptable but not eligible for normal staging or
   automatic selection.
2. Publication and targets require a matching release authorization.
3. The platform leaf is revoked and replaced through owner-controlled offline
   authority.
4. Every candidate signed during the exposure interval is classified.

**Result:** Pass on paper for remote normal deployment. Physical boot of a
platform-signed artifact and firmware-specific selection behavior remain part of
platform enrollment and physical-host testing.

### P-005: Release-authorization compartment is compromised

**Event:** The attacker can mint release authorizations but cannot create a new
platform-accepted boot artifact.

**Expected containment:**

1. New attacker-chosen bytes cannot satisfy the platform trust anchor.
2. The possible attack set is bounded to already platform-signed candidates.
3. Candidate inventory and retention records identify that set.
4. The release key is revoked and every authorization in the exposure interval
   is classified.

**Result:** Pass on paper for new attacker-chosen bytes, with important residual
risk. The attacker may authorize a rejected, vulnerable, or unintentionally
retained platform-signed candidate. Candidate minimization and inventory are
therefore security controls, not housekeeping.

### P-006: Qualification environment is compromised

**Event:** A qualification worker fabricates passing results for an existing
platform-signed candidate.

**Expected containment:**

1. The qualifier has neither routine signing key.
2. The release operation still requires a deliberate owner authorization.
3. Independent evidence, reruns, or multiple gates may expose inconsistent
   results.

**Result:** Conditional. Authority separation prevents the qualifier from
signing by itself, but false qualification can deceive the owner and the release
compartment. The trust, reproducibility, and authentication of qualification
evidence must be resolved under L-002 and L-006; DES-0004 must not claim to solve
it.

### P-007: Publication or discovery is compromised

**Event:** The registry, mirror, metadata index, or discovery name serves
substituted, incomplete, withheld, or older content.

**Expected containment:**

1. Substitution and mixed-object sets fail identity and authorization checks.
2. Publication cannot create either routine signature.
3. Withholding is reported as unavailable rather than silently repaired with an
   unqualified artifact.
4. Replay is evaluated against retained freshness and withdrawal policy.

**Result:** Pass on paper for substitution and partial publication. Replay and
offline revocation remain open under SYS-037.

### P-008: One signing device is lost or stolen

**Event:** One routine compartment becomes unavailable, with or without evidence
of private-key exposure.

**Expected containment:**

1. The other routine key does not become its backup or replacement.
2. Offline authority replaces the affected delegation or platform leaf.
3. Exposure-window artifacts or authorizations are classified when compromise
   is possible.
4. A new promotion crosses both compartments before publication.

**Result:** Pass on paper. Correlated physical loss of both routine compartments
is acceptable because both are replaceable; correlated compromise during use is
not.

### P-009: The maintainer deliberately authorizes malicious content

**Event:** The sole maintainer knowingly uses both valid authorities to release
malicious bytes.

**Expected containment:** Public evidence attributes the release and supports a
later trust reset, but no second human veto exists.

**Result:** Outside the initial personal-fleet guarantee. Threshold approval or
a second operator would change the project scope and custody model.

### P-010: Two independent routine compartments are compromised

**Event:** The attacker compromises both signers or a lower hardware layer shared
by them.

**Expected containment:** Pause rollout, invoke offline revocation and
replacement, classify the exposure interval, and recover affected machines.

**Result:** Compromise recovery only. The single-compromise prevention claim no
longer applies.

## Alternatives considered

### One host with distinct keys and commands

Rejected. It improves audit semantics and accidental-misuse resistance but does
not survive compromise of the host coordinating both operations.

### Two ordinary tokens attached to the same untrusted host

Rejected as sufficient by itself. Separate private-key storage is useful, but a
host that can obtain both blind signatures can still substitute the complete
flow.

### Separate routine signing compartments in one replacement class

Selected. It prevents one routine signing compromise from creating both halves
of a normally deployable release while keeping loss recovery simple and under
one maintainer.

### Use the offline project root for every release

Rejected. It exposes the authority needed to recover from routine compromise
during every normal and urgent release and turns ordinary maintenance into a
project-governance ceremony.

### Threshold or two-person release authorization

Deferred. It addresses malicious or mistaken sole-maintainer action but is not
operable for the initial personal fleet.

## Findings and design consequence

1. **Logical key separation is not compromise separation.** The execution and
   confirmation paths determine whether one host can exercise both keys.
2. **Loss and compromise need different topology.** The routine keys may share a
   loss event because they are replaceable, but must not share a routine use
   compromise.
3. **Platform-signed candidates are hazardous.** Before release authorization
   they are not normal releases, but compromise of the release key can make one
   eligible. Their inventory and retention must be bounded.
4. **Human confirmation is only as trustworthy as its display and inputs.** A
   second prompt on the same compromised interface is not a second control.
5. **Qualification is a separate trust problem.** Signer separation prevents
   self-authorization but cannot prove that tests or provenance are truthful.
6. **Publication integrity is tractable; freshness is not yet.** Immutable
   identity blocks substitution, while replay and offline withdrawal remain
   under SYS-037.

DES-0004 should retain one routine replacement and availability class but
require two routine signing compromise compartments. Its permission for both
keys to share an ordinary promotion device should be removed. This resolves
C-002 at the design-policy level; implementation and compromise exercises remain
required before production use.

## Follow-up gates

- Select or design two independently enforced routine signing compartments.
- Define the promotion bundle and independent evidence-validation path.
- Specify inventory, retention, rejection, and destruction for platform-signed
  but unreleased candidates.
- Exercise coordinator compromise, each signer compromise, digest substitution,
  and mismatched promotion objects with disposable keys.
- Resolve qualification-evidence trust under L-002 and promotion behavior under
  L-006.
- Apply EX-0003's recovery-capability boundary and complete its physical abuse
  exercises before production enrollment.
