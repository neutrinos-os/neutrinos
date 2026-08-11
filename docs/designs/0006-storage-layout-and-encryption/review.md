---
design: DES-0006
reviewer: Codex adversarial pass
perspective: failure, security, recovery, operability, alternatives
date: 2026-08-09
amended: 2026-08-11
status: open
---

# Storage layout, immutable root, and encryption review

## Summary judgment

The proposal cleanly separates authenticated public release artifacts from
encrypted persistent state and maps the deployment lifecycle onto standard
systemd/UAPI objects. Its strongest rejection case is operational fragility:
several root/Verity/UKI resources, multiple encrypted volumes, recovery media,
PCR policy, header backups, and fixed partition capacity can create more ways
to strand a one-person fleet than a simpler mutable encrypted root.

Acceptance should ratify boundaries and falsifiable requirements, not declare
the paper mapping proven.

## Challenges

### C-001: Multi-resource A/B can still produce an authenticated hybrid

- Severity: critical
- Claim: a valid signed UKI can point at a valid root from another deployment,
  or bootloader and GPT metadata can select a half-updated tuple.
- Failure or cost if true: the machine runs release-owned bytes that were never
  jointly qualified even though each component passes a local integrity check.
- Required response or experiment: substitute every pairwise-valid UKI, root,
  Verity, config, label, and manifest combination and inject power loss before
  and after every finalization write.
- Author response: slot and version names are explicitly non-authoritative;
  the signed UKI root hash and deployment manifest must bind the literal tuple,
  and UKI entry-point installation occurs last.
- Disposition: mitigated on paper; implementation evidence required.
- Residual risk: firmware-variable and FAT rename behavior may not provide the
  assumed ordering on actual hardware.

### C-002: Fixed partition slots can make the 16 GB router undeployable

- Severity: critical
- Claim: two roots, two hash trees, boot artifacts, recovery, state,
  diagnostics, and reserve may not fit after realistic package growth.
- Failure or cost if true: updates require shrinking the OS unsafely or give up
  the fallback/recovery guarantees exactly where availability matters most.
- Required response or experiment: build representative router artifacts,
  apply the capacity formula with a declared growth horizon, and compare
  EX-0008 layouts R-A and R-B.
- Author response: no byte size or commitment to the 16 GB disk is accepted
  before this evidence; moving the complete lifecycle to the 1 TB disk is a
  first-class option.
- Crux restated 2026-08-11, agreed with the owner. The router is the
  instrument, not the subject. What this challenge falsifies is **SYS-050's
  capacity dependence**: whether "preserve the complete booted deployment plus
  capacity for one complete candidate or eligible fallback" holds on a small
  device, or whether the design must shrink the OS unsafely or drop the
  fallback exactly where availability matters most. Its output is therefore a
  **declared minimum viable device and the formula that produces it**, not a
  verdict about one machine. A design whose guarantees are conditional on an
  undeclared disk size has bound itself to the author's hardware, which the
  owner has said the project must avoid.
- Falsification method, owner direction 2026-08-11: **a VM with a deliberately
  undersized disk, bisected downward until the guarantee breaks.** Capacity
  falsification is monotone -- if a real router artifact set fits in 8 GB then
  16 GB passes a fortiori -- and the size at which it breaks *is* the minimum
  viable device. The disk may be synthetic; the artifact must not be. A real
  router package set, genuinely composed and verity-hashed, or the exercise is
  circular. This also avoids mutating the router at all, which the safety rules
  independently forbid without an accepted plan naming the exact mutation.
- Effect of C-013 on the numbers: smaller than first supposed. `/usr` is nearly
  the whole of an image-based root, so the authenticated artifact did not
  shrink materially. The relief comes instead from layout: under EX-0008 R-A
  the writable root carrying `/var` sits on the 1 TB device, so the small disk
  holds only the ESP, two `/usr` slots, and two hash trees -- all replaced
  wholesale on update, none growing at runtime. The reference `nixconfig`
  router already splits this way, with `/nix` on a separate filesystem and no
  `/var` mount of its own; `/usr` is the direct analogue of `/nix`.
- Not part of this challenge, handed to C-011: under R-A the machine's normal
  boot depends on **two physical disks**, since `/var` is not optional. That is
  an availability property of one machine's hardware, not a test of the
  capacity guarantee, and it belongs with the recovery failure-domain
  challenge. The same dependency already exists on the running NixOS router if
  `/nix` is on the larger disk, so it is inherited rather than introduced.
- Disposition: open. R-A and R-B are retained as instances to be checked
  against the rule rather than argued separately; the owner declined to drop
  either before evidence.
- Modeling assumption, not evidence: the growth horizon applied to measured
  bytes. No VM can produce real package and UKI growth over time. The horizon
  decides the outcome more than the reserve percentage does -- a short horizon
  keeps a small device viable, a long one will not -- and its value is the
  owner's to set. It must be labeled an assumption wherever the result is
  cited.
- Residual risk: a compact initial root can conceal long-term package and UKI
  growth.

### C-003: TPM automatic unlock weakens the intuitive theft claim

- Severity: critical
- Claim: a stolen intact machine can boot an authorized vulnerable release and
  decrypt itself without a person present.
- Failure or cost if true: “encrypted at rest” is presented more strongly than
  the actual protection against offline extraction and boot substitution.
- Required response or experiment: document the exact attacker boundary, test
  withdrawn and substituted releases, and compare unattended TPM2 with
  TPM2+PIN/FIDO2 for the workstation.
- Author response: the design repeats PR-0005's narrow claim and keeps session
  authentication, revocation, and compromise recovery separate.
- Already settled elsewhere, and not reopened here: the permitted claim, fixed
  by PR-0005 C-001 -- hardware-bound unlock protects against offline extraction
  and unauthorized boot substitution under the platform assumption, while
  session authentication and revocation protect the running machine. The router
  is likewise settled by PR-0005: without a proven hardware-bound secret
  facility it may be a development target but does not meet the production
  confidentiality objective.
- Owner ruling, 2026-08-11: the routine unlock policy is **per role, not
  global**.
  - **Workstation (`desktop-jason`): TPM2 + PIN.** It defeats the scenario this
    challenge names, a stolen intact machine that decrypts itself with nobody
    present, and unattended reboot is not a workstation requirement, so the
    cost is a typed secret rather than a lost capability. Unattended TPM2 alone
    was rejected here.
  - **Router and `misc`: unattended TPM2, no human input**, because the owner
    stated on 2026-08-11 that both must reboot unattended. This is exactly the
    pairing PR-0005 says requires a proven hardware-bound secret facility, and
    neither machine has one today. Until they do, both accept the narrow claim
    or carry no powered-off confidentiality claim at all.
- Consequence for `misc`, and the reason its firmware check is decisive rather
  than routine: if Haswell-era PTT presents **TPM 1.2**, `systemd-cryptenroll
  --tpm2` cannot enroll it, and Intel's specification states the D54250WYK
  supports no discrete TPM. A 1.2 answer therefore forecloses unattended
  encrypted boot on that machine permanently rather than inconveniently, and
  `misc` can never be a production-confidentiality target without different
  hardware.
- Enabling conditions, stated so this is not mistaken for an available
  capability: `desktop-jason` advertises TPM 2.0 but its **operation is
  untested**, Secure Boot is **off**, and owner platform keys are **not
  enrolled**. This is a migration target that PR-0005 C-002's mandatory
  exercises gate, not a setting to turn on.
- Consequence for C-005: the PIN joins the recovery-material inventory. A PIN
  that is forgotten is an availability event, so the independently retained
  high-entropy recovery method is load-bearing rather than ceremonial.
- Hardware facts changed 2026-08-11: the documented discrete TPM 2.0 module for
  the router has been **acquired but not installed**. PR-0005 requires treating
  the capability as absent until a module is installed and exercised, so no
  inventory row or confidentiality claim moves yet. Installation is physical
  work on the machine carrying the development network, which is R-054's first
  concrete instance.
- Disposition: **workstation policy resolved 2026-08-11, accepted by Jason
  Tarasovic.** Router unchanged pending module installation and qualification.
- Residual risk: an authorized pre-login vulnerability can expose unlocked
  data. A PIN moves part of the protection into something memorized, which
  fails differently from a sealed secret and fails at the worst time.

### C-004: Signed PCR policy creates another high-value signer

- Severity: critical
- Claim: a policy-signing key that can authorize arbitrary UKI measurements
  can indirectly unlock every volume enrolled to it.
- Failure or cost if true: compromise of an online release workflow becomes
  data-decryption enablement across the fleet.
- Required response or experiment: define policy-key scope, offline/online
  custody, policy reference, rotation, revocation, audit, and the relationship
  to release and platform authorities before enrollment.
- Author response: ADR-0002 prohibits collapsing release and data authority;
  exact policy-key custody remains an S-006 mechanism decision.
- Disposition: open.
- Residual risk: separate policy signing adds ceremony and update failure modes.

### C-005: Recovery keys and LUKS header backups increase theft surface

- Severity: critical
- Claim: an offline recovery key plus usable header backup can bypass all
  platform and measured-boot restrictions.
- Failure or cost if true: storage confidentiality reduces to the physical and
  procedural security of recovery material.
- Required response or experiment: create an inventory and ceremony covering
  separate storage, access, audit, rotation, restore testing, loss, and
  destruction without placing all copies together.
- Author response: recovery material is explicitly independent, never stored
  only on its target, and separately governed; the concrete ceremony remains
  deliberately unresolved.
- Changed by C-003 on 2026-08-11: the recovery inventory gained a third item.
  It is now a high-entropy recovery key per volume, a LUKS2 header backup per
  volume, and a **workstation PIN that can be forgotten**. PR-0005 C-002
  already prohibits hardware-bound unlock as the only recovery path, so the
  recovery key is mandatory rather than optional. The design cannot remove this
  material; it can only decide where it lives and who can reach it.
- The constraints genuinely conflict, which is why this stayed open. ADR-0002
  separates authority from recovery, A-011 assumes an offline copy outside the
  primary local-disaster failure domain, and this challenge's own residual risk
  names the trap: stored together, one theft or one fire ends it; stored apart,
  a single-maintainer restore becomes a multi-location errand at the worst
  possible moment.
- Owner ruling, 2026-08-11: **split the question by authority rather than
  resolving the ceremony here.** DES-0006 owns only the mechanical guarantees a
  storage design can enforce:
  1. every encrypted volume has at least one routine unlock method and one
     independently retained high-entropy recovery method;
  2. a LUKS2 header backup exists per volume, is stored separately from both
     the encrypted device and the recovery key, and is restore-tested rather
     than merely created;
  3. no volume's recovery material is stored on that volume, or on any device
     unlockable by it.
  Creation, custody, access, audit, rotation, loss, and destruction belong to
  DES-0004 under S-006, alongside C-004's signing-key custody, which is the
  same species of question.
- Disposition: **Resolved 2026-08-11 for this design, accepted by Jason
  Tarasovic**, as a recorded handoff rather than a closure. The alternative --
  treating the ceremony as blocking DES-0006's acceptance -- was rejected: it
  would hold a storage design hostage to a key-custody decision that has its
  own gate.
- Residual risk: a sole maintainer can lose either availability or separation
  through one poorly designed backup location. The handoff does not reduce that
  risk, it relocates it, and DES-0006 cannot detect a ceremony that is designed
  and then not followed. The restore test in guarantee 2 is the only part of
  this a storage design can actually verify.

### C-006: Read-only `/etc` can make the system unusable

- Severity: critical
- Claim: upstream tools and services write persistent identity and settings
  under `/etc`; flattening normal config into a read-only root blocks ordinary
  operation.
- Failure or cost if true: the storage design forces a growing custom
  projection system or silently remounts `/etc` writable.
- Required response or experiment: inventory actual workstation/router writes,
  classify every one, and exercise controlled persistent exceptions before
  physical migration.
- Author response: the design explicitly leaves the projection mechanism to
  C-002, reserves an attributable admin-state boundary, and treats unhandled
  writers as unsupported rather than silently weakening the model.
- Restated 2026-08-11, because C-013 removed the premise. `/etc` is no longer
  flattened into an authenticated root; it is a regenerated tree on the
  writable root with signed confexts overlaid. The original failure -- writes
  rejected by a read-only filesystem -- is no longer the main risk. The risk
  moved and sharpened: where a confext is merged, `systemd-confext` makes
  `/etc` read-only and a write fails visibly, which is the acceptable case;
  where **no confext covers the path**, `/etc` is an ordinary writable
  directory, so the write succeeds, the service works, and the change vanishes
  at the next boot. The live question is therefore not whether read-only `/etc`
  blocks operation but whether writable-but-volatile `/etc` **silently discards
  operator and service state**.
- The restatement also exposes a cost: SYS-123 puts every confext under full
  artifact lifecycle, so adding an SSH key or changing a sysctl becomes a
  release-owned artifact with qualification, ordering, rollback, and retention
  attached.
- Owner ruling, 2026-08-11: **fail loudly.** A durable `/etc` write must fail
  when attempted, whether or not a confext covers the path; silent
  non-durability is unacceptable on a system whose claim is attributability.
  A bounded path for testing unqualified configuration is required alongside
  it, non-durable by construction, visibly marked, and either unavailable on
  production physical roles or attributable when used.
- Disposition: **Resolved 2026-08-11 in the storage design, accepted by Jason
  Tarasovic.** DES-0006 now requires that `/etc` present no writable durable
  surface in normal operation and records the experimentation constraint.
- Note on the `C-002` references here and in DES-0006: they denote
  **decision-backlog item C-002** ("How are `/etc`, local overrides, secrets,
  and credentials owned and delivered?"), not challenge C-002 of this review.
  The identifier spaces collide. The pointer is correct and remains the open
  decision; the confext lifecycle it will be answered with belongs to DES-0005.
- Handed on, not closed by this: the confext lifecycle SYS-123 demands, and the
  mechanism satisfying both the fail-loudly guarantee and the experimentation
  path. `confext` currently appears in no design but this one, so C-013 created
  an obligation that the configuration design has not yet absorbed. DES-0005 is
  its home; the governing open decision stays backlog item `C-002`. The experimentation path additionally conflicts with
  `image_policy_confext_strict`, which requires signed extensions, so its scope
  is a production/non-production role distinction of the kind SYS-030 draws.
- Residual risk: exceptions can accumulate until `/etc` is effectively mutable.
  Two new ones. The fail-loudly guarantee has no mechanism yet, so it is a
  requirement on a design that does not exist; and software that writes durable
  `/etc` now fails on a machine where the same write would have silently
  succeeded, which surfaces the unsupported-writer inventory as an operational
  problem rather than a theoretical one.

### C-007: EROFS is novelty without demonstrated value

- Severity: high
- Claim: ext4+dm-verity already supplies a familiar authenticated root, while
  EROFS adds tool and kernel compatibility work.
- Failure or cost if true: the project spends qualification effort on a format
  whose compression or runtime benefits do not matter for three machines.
- Required response or experiment: produce equivalent deterministic EROFS and
  ext4 roots and compare size, build, boot, memory, update, inspection,
  corruption, and recovery behavior.
- Author response: ext4 remains a mandatory challenger and fallback; EROFS is
  not accepted merely because it is read-only.
- Disposition: open.
- Residual risk: measurements may be platform- and package-set-specific.

### C-008: Multiple state volumes multiply failure and recovery work

- Severity: high
- Claim: separate machine and user/workload volumes require more keys, headers,
  backups, mounts, status, and partial-failure paths.
- Failure or cost if true: recovery becomes slower and more error-prone than a
  single encrypted state filesystem.
- Required response or experiment: enumerate actual custody/unlock differences
  and collapse volumes whenever preservation, recovery, and destruction policy
  is identical.
- Author response: the proposal explicitly uses volumes by custody/unlock
  boundary, not by path or every state owner; the workstation's two-volume split
  follows separate physical disks and reprovisioning lifecycles.
- Disposition: mitigated on paper; exercise required.
- Residual risk: later per-user or workload encryption can expand the matrix.

### C-009: Btrfs features may not justify their operating cost everywhere

- Severity: high
- Claim: scrub, quotas, low-space behavior, snapshot retention, send/receive,
  and CoW policy can cost more on a router or small state volume than reflinks
  and subvolumes provide.
- Failure or cost if true: the common default adds recovery and capacity
  incidents to roles that do not use its distinguishing features.
- Required response or experiment: exercise actual workstation and router
  state on Btrfs and ext4, including VM/container CoW, corruption, low space,
  backup, restore, and operator runbooks.
- Author response: Btrfs is the leading candidate because the owner explicitly
  wants filesystem-assisted container and VM workflows; ext4 remains a
  role-specific challenger rather than the project default.
- Disposition: open.
- Residual risk: role-specific filesystem choices increase the qualification
  matrix.

### C-010: Mutable state remains vulnerable to offline tampering

- Severity: high
- Claim: dm-crypt confidentiality and ordinary filesystem checksums do not
  authenticate state against a malicious offline writer.
- Failure or cost if true: an attacker can corrupt or plant executable state
  that is consumed after a valid root boots.
- Required response or experiment: keep the claim narrow, exercise hostile
  state recovery, inventory executable mutable inputs, and measure
  dm-integrity/authenticated-encryption alternatives before rejecting them for
  sensitive roles.
- Author response: the design makes no mutable-authenticity claim and routes
  suspected access to SYS-035 compromise recovery rather than normal mount.
- Disposition: accepted risk for the initial scope, subject to hostile-state
  exercise.
- Residual risk: compromise may be undetectable, so operators can mistakenly
  choose availability recovery.

### C-011: Local recovery shares too much failure domain

- Severity: critical
- Claim: an on-disk recovery UKI and root can be destroyed with the disk, GPT,
  firmware variables, or platform keys it is meant to repair.
- Failure or cost if true: recovery is unavailable during disk replacement or
  platform-authority failure.
- Required response or experiment: exercise at least one independently stored
  recovery medium or IPMI virtual-media path in addition to any convenient
  local recovery artifact.
- Author response: local recovery is optional and never the only independent
  recovery capability; DES-0004 remains authoritative.
- Inherited from C-002 on 2026-08-11: under EX-0008 R-A the router's **normal
  boot depends on two physical disks**. The small device holds the ESP and the
  authenticated `/usr` slots; the large device holds the writable root, and
  `/var` is not optional. Loss of the large disk is therefore not a data
  incident but a boot incident, and it widens rather than narrows the recovery
  failure domain this challenge already contests. It also constrains C-015's
  terminal state: "keep running, degraded and reachable" presumes a writable
  `/var`, which does not exist if the failed device is the one that carries it.
  The dependency is inherited rather than introduced -- the running NixOS
  router has the same shape with `/nix` on a separate filesystem -- but the
  design should state it rather than discover it.
- Disposition: mitigated by design; physical exercise required.
- Residual risk: removable media can be stale or inaccessible when needed.

### C-012: Layout reserve is easy to consume or mis-size

- Severity: high
- Claim: shared free space and flexible state growth can consume the capacity
  promised for staging, diagnostics, or future layout migration.
- Failure or cost if true: an update fails only after acquisition, or recovery
  cannot retain evidence under full-disk pressure.
- Required response or experiment: represent reserve as an explicit protected
  region or enforceable quota, alert before violation, and test full-storage
  behavior.
- Author response: the design makes reserve an owned region and forbids normal
  state growth from silently consuming it; exact mechanism remains open.
- Disposition: open.
- Residual risk: fixed reserve wastes scarce router capacity while flexible
  reserve is harder to guarantee.

### C-013: The authenticated image's scope was never challenged

- Severity: critical
- Raised: 2026-08-11, in a later landscape pass, not part of the 2026-08-09
  adversarial review. C-007 challenged the root *format* and left the root
  *scope* unexamined.
- Claim: the design authenticates a complete root filesystem, including
  flattened `/etc`, while the systemd/UAPI stack it selects under ADR-0001 is
  built around authenticating `/usr` only, with `/etc`, `/var`, and `/home`
  writable. [ParticleOS](https://github.com/systemd/particleos), named by
  RES-0001 as the closest executable reference for the default candidate,
  makes the opposite choice: a verity-signed `erofs` `usr` partition beside a
  `btrfs` root that holds `/var`, with `Encrypt=tpm2` and `FactoryReset=yes`.
  Upstream's stated rationale is that a hermetic OS is definable inside `/usr`,
  and that trees outside it are regenerated by `systemd-sysusers` and
  `systemd-tmpfiles` rather than shipped.
- Failure or cost if true: the design pays the full cost of a read-only root --
  every mutable path must be projected out of state, and every `/etc` writer
  becomes an unsupported class, which is the unresolved C-002/C-006 debt -- to
  buy an integrity increment over `/usr`-only that has never been stated or
  measured. It also puts NeutrinOS off the path its chosen mechanisms are
  designed and tested for, so upstream defaults, `systemd-sysext` mutable-mode
  facilities, and ParticleOS's exercised repart definitions stop being reusable
  and become work.
- Contrary evidence, which is why this is a fork and not a correction: ChromeOS
  and Android both ship whole read-only rootfs plus a separate stateful or
  data partition at very large scale, so the full-root model is field-proven.
  The question is not whether it works. It is whether NeutrinOS's specific
  reason for it -- authenticating exact flattened configuration inside the
  signed artifact -- survives contact with its cost, and whether SYS-049's
  "exact UKI-to-root/Verity binding" was written to require root scope or would
  be satisfied by `/usr` scope plus a separate configuration-integrity claim.
- Required response or experiment: state the integrity delta explicitly -- what
  an attacker or a fault can do against a `/usr`-only layout that a full-root
  layout prevents -- and decide whether that delta is worth the projection and
  `/etc`-exception cost. If the spike under C-007 measures EROFS against ext4
  without also building a `/usr`-only variant, it answers the smaller question
  and leaves this one open.
- Author response: challenge accepted. The full-root scope rested on
  authenticating flattened `/etc` inside the release artifact, and that reason
  does not survive: configuration integrity is required to be deterministic and
  attributable, with cryptographic authentication welcome but not the floor,
  and a signed confext under a strict image policy exceeds that floor without
  putting configuration inside the root image.
- Disposition: **Resolved 2026-08-11 in favor of `/usr`-only scope, accepted by
  Jason Tarasovic.** The authenticated release artifact is `/usr` with its
  Verity pair and signed UKI. Configuration is delivered exclusively by signed
  confexts. The real `/etc` holds nothing durable and is regenerated at boot by
  `systemd-tmpfiles` and `systemd-sysusers`; durable content found there is a
  fault to report, not state to preserve.
- Requirement effect: **none.** SYS-049 requires read-only, authenticated
  "release root content" bound to an identity carried by the boot artifact, not
  a root-scoped filesystem, and its own acceptance evidence already enumerates
  configuration beside root, Verity, and UKI. SYS-090 likewise treats config as
  a distinct deployment-set member. No accepted requirement was amended and G1's
  requirement set is untouched.
- Inherited obligation: SYS-123 governs any mechanism that changes the
  release-owned configuration view, so every confext is a release-owned
  artifact requiring exact content identity, base compatibility, authorization,
  qualification, activation ordering, health, rollback, retention, and
  effective-deployment status. This also forecloses confext mutable modes:
  `Mutable=` write-routing through `/var/lib/extensions.mutable/` is the
  "unattributed mutable administrator layer" SYS-123 forbids, so
  `Mutable=disabled` with `image_policy_confext_strict` is required rather than
  preferred.
- Residual risk: **early boot.** The root partition is now unauthenticated
  state, so anything read before `/usr` is verified -- `fstab`, `crypttab`,
  initrd-stage configuration -- falls outside the integrity boundary. Upstream's
  answers are the signed UKI command line and
  `systemd-confext-initrd`/`systemd-confext-sysroot`, exercised in production by
  ParticleOS, but this is the one respect in which `/usr`-only is weaker than
  full-root and the spike must exercise it rather than assume it. Second
  residual: where per-machine identity comes from is now constrained -- it
  cannot live in `/etc` -- and is left to L-003.

### C-014: Staging never makes the target ineligible before overwriting it

- Severity: critical
- Raised: 2026-08-11, from [RES-0014](../../research/comparisons/embedded-ab-update-field-evidence.md).
  Not part of the 2026-08-09 adversarial review.
- Claim: the failure table already requires that interrupted staging leave
  "inactive partial bytes ineligible", but no step in the staging sequence
  produces that result. Step numbers here are the sequence as it stood when
  this was raised, before the accepted amendment renumbered it. Step 2 chooses
  an inactive slot pair and step 3
  immediately writes. On a first update the claim holds for free, because the
  inactive slot is empty. On a second update that slot holds the previous
  **eligible** deployment -- the retained fallback step 8 promises to keep --
  and the first byte written destroys it while its eligibility marker still
  stands.
- Failure or cost if true: between the first byte of step 3 and its verify,
  the retained fallback is a partial image that the selection mechanism still
  considers a candidate. Boot-attempt exhaustion under SYS-038 could select it.
  This is C-001's authenticated hybrid reached through ordinary operation
  rather than an exotic interruption, and it is what SYS-050 forbids when it
  says partial staging must not "expose a boot entry".
- Prior art: RAUC's documented order is verify the bundle, **mark the target
  slots non-bootable**, then write, precisely so that an interruption mid-write
  cannot leave a slot the bootloader still treats as a candidate.
- Requirement effect: **none.** SYS-050 already forbids the outcome. Note that
  SYS-050 preserves the booted deployment plus *capacity for* one candidate or
  eligible fallback, so overwriting the previous fallback with a new candidate
  is permitted; the defect is the surviving eligibility marker, not the
  overwrite.
- Proposed amendment, awaiting acceptance: insert a step between the current
  steps 2 and 3 of "Staging and selection" --

  > 3. Mark the chosen slot pair ineligible for selection, durably, before
  >    writing any byte into it. The previous occupant stops being a retained
  >    fallback at this point rather than when it is overwritten.

  -- renumbering the remainder, and add a failure-table row: "Ineligibility
  marking interrupted | Target remains ineligible or the marking is not
  observed at all; never a slot marked eligible with foreign bytes in it".
  Durability is the load-bearing word: marking held only in memory leaves the
  window unchanged across power loss.
- Owner ruling, 2026-08-11, on what "durably" must survive. Three levels were
  put to the owner: (1) power loss; (2) power loss plus an unreadable ESP,
  which forbids ineligibility living solely as a filename on the filesystem
  holding the artifacts; (3) both, plus hostile offline modification, meaning
  the marking is authenticated rather than merely present. The ruling is
  **level 3 is the target, level 2 is the accepted fallback, and level 1 is
  acceptable only with a recorded reason** for why level 2 was untenable.
  Ordering matters here: level 1 is the ESP-only marking C-011 challenges as a
  shared failure domain, so landing there must be a stated finding rather than
  a discovery that it was easiest.
- Author response: accepted as drafted.
- Disposition: **Resolved 2026-08-11, accepted by Jason Tarasovic.** The
  amendment is in the design as step 3 of "Staging and selection", with the
  durability levels stated there and a failure-table row for interrupted
  marking. The mechanism is deferred to the substrate spike, which owes an
  answer on level 3's feasibility rather than stopping at the first thing that
  works.
- Residual risk: the mechanism for durable ineligibility is not chosen here and
  interacts with the ESP failure domain raised in C-011 and RES-0014, since
  systemd-boot's counters live as filenames on the same FAT filesystem as the
  artifacts they select. Level 3 additionally interacts with whether the
  bootloader's own attempt counters are trustworthy, which is a larger question
  than staging order and is not opened here.

### C-015: Nothing bounds oscillation between deployments that all fail

- Severity: major
- Raised: 2026-08-11, from [RES-0014](../../research/comparisons/embedded-ab-update-field-evidence.md).
- Claim: the design carries only one branch of SYS-038's exhaustion clause. The
  requirement reads "Exhaustion must select an eligible normal fallback **or
  stop with an attributable diagnosis**"; the design says "boot attempt
  exhaustion may select only a retained eligible normal deployment" and never
  designs the stop. Nothing describes what happens when the deployment selected
  by exhaustion also boots and also fails role-health assessment. Under the
  narrow reading ruled below this is not a requirement violation, because each
  deployment's own accounting is correct; it is a gap in the design's coverage
  of its own failure space.
- Failure or cost if true: two eligible deployments that both boot and both
  fail assessment can alternate indefinitely, each with a fresh attempt
  counter. The machine is powered, unattended, and never converges. On the
  router this is the difference between a diagnosable dead machine and one that
  looks alive over IPMI while cycling.
- Prior art: Mender persists update state across reboots with a
  `state_data_store_count` whose only purpose is to detect state loops and
  force termination into a failure state rather than rebooting again.
- Why an immutable deployment stops working, since the loop looks impossible
  otherwise: assessment is not a function of the image. It evaluates the
  machine in an environment that moves, so the causes that matter are the ones
  **common to both slots** -- an expired certificate, a state schema migrated
  beyond what the older deployment can read, PCR values changed by a firmware
  update so no deployment can unlock state, failing hardware, or a health check
  that depends on reaching something. Fallback only helps when the failure was
  caused by the thing being fallen back from. In every case above it supplies a
  second thing to try, indefinitely.
- Requirement effect: **none.** Owner ruling, 2026-08-11: SYS-038 is read
  **narrowly** -- "every trial boot" governs each deployment's own attempt
  accounting, and the cross-deployment loop is outside it. The requirement is
  unchanged and this behavior is **not required by it**. The amendment below is
  therefore a **design commitment beyond the requirement floor**, adopted
  because the owner directed that the system be designed and built for the
  broader behavior, and it must not be cited as evidence of satisfying SYS-038.
- Field evidence: [RES-0014](../../research/comparisons/embedded-ab-update-field-evidence.md)
  records five implementations converging on the same terminal state -- stop
  selecting, keep running, be loud -- and **none halts the machine**. greenboot
  stops rebooting and reports through logs, MOTD, and `red.d` operator scripts
  in the still-running system. MicroOS branches on whether the snapshot was
  ever known-good. Android prompts rather than resetting unattended. ChromeOS
  alone enters recovery automatically, which SYS-038 forbids and which the
  unattended router makes untenable.
- Proposed amendment, awaiting acceptance: replace the fallback sentence in
  "Root filesystem and `/etc`" with a bounded ladder --

  > Selection driven by exhaustion is itself durably counted, and a deployment
  > that has already been selected by exhaustion and failed assessment is not
  > selected that way again.
  >
  > Response depends on whether the failing deployment has ever passed
  > assessment. A deployment that has never passed is unproven, and exhaustion
  > selects an eligible fallback. A deployment that has passed before indicts
  > the environment rather than the image, so at most one further attempt is
  > made before stopping; falling back cannot address a cause the fallback
  > shares.
  >
  > When no eligible normal deployment remains unselected, automatic selection
  > stops. The machine does not halt: the last deployment continues running,
  > degraded and reachable, and reports an attributable diagnosis naming each
  > deployment tried and its failure. Recovery is not entered automatically, as
  > SYS-038 requires, and the stop is a terminal state for selection only.

  -- and add a failure-table row: "Every eligible deployment boots and fails
  assessment | Automatic selection stops; last deployment keeps running and
  remains reachable; attributable diagnosis names each deployment tried; no
  automatic recovery entry".
- Rejected alternative: a minimal notification image in the ESP, raised by the
  owner as an aside and **not adopted**. It would need a credential to notify
  while running precisely when sealed state may be unavailable, contradicting
  the design position that the ESP holds no secrets; it would sit in the ESP
  failure domain C-011 challenges; and it would add a third signed boot artifact
  and authorization path. greenboot's `red.d` demonstrates that notification
  belongs to the degraded running system, which already has network
  configuration and credentials.
- Author response: accepted as drafted.
- Disposition: **Resolved 2026-08-11, accepted by Jason Tarasovic.** The
  amendment is in the design as "When every eligible deployment fails" under
  "Staging and selection", with a failure-table row. It is recorded there as a
  commitment beyond the requirement floor, not as a reading of SYS-038.
- Residual risk: the exhaustion counter and the known-good record are both
  state, and state is what may be damaged in the scenarios that trigger them.
  Where they live, and whether they survive the failure modes they exist to
  bound, is unresolved. A machine kept running while failing assessment is also
  a machine running in an unassessed condition; what it is permitted to keep
  doing in that state is not defined here.

## Missing alternatives or evidence

- A measured comparison with a single versioned root-image-file store rather
  than partition slots.
- A `/usr`-only authenticated variant built beside the full-root candidate, so
  C-007's format comparison and C-013's scope question are measured together
  rather than one being fixed by assumption while the other is tested.
- Actual mkosi/systemd version availability after L-001 selects package inputs.
- Firmware and bootloader behavior with an ESP-only artifact store and, only if
  capacity requires it, a split ESP/XBOOTLDR layout.
- A concrete self-contained recovery UKI versus recovery root-partition
  comparison.
- Actual TPM2 signed-policy behavior on `desktop-jason` and the proposed router
  module.
- A plaintext-spill audit covering suspend, hibernation, kdump, journal,
  container, VM, and application temporary files.

## Requirements accepted; changes before design acceptance

SYS-048 through SYS-056 were accepted on 2026-08-10. The mechanism design
remains in review and must:

1. Keep root format, recovery packaging, workstation mutable filesystem,
   router target disk, and exact TPM policy explicitly gated by experiments.
2. Add the multi-resource hybrid, capacity exhaustion, recovery-material loss,
   hostile state, `/etc` writer, and full-storage cases to the spike plan,
   together with the second-update overwrite of a retained eligible fallback
   (C-014) and the case where every eligible deployment fails assessment
   (C-015).
3. Do not accept a production router claim until hardware-bound unlock and
   independent console recovery are physically exercised.
