# Glossary

This is the canonical dictionary for NeutrinOS project terms. Designs and ADRs
decide behavior; this glossary gives their words consistent meanings. A local
design may introduce a provisional term, but a term used across designs should
be promoted here.

Use upstream names unchanged when referring to upstream objects. NeutrinOS
terms describe substrate-independent semantics and must not imply properties
that have not been established.

## Configuration and machine intent

- **fleet inventory**: The authoritative desired-intent collection of managed
  machine records and their referenced role, platform-class, configuration,
  state-contract, and policy definitions.
- **machine name**: A stable human-facing key for one machine record. It is not
  a machine identity, credential, or hardware observation.
- **machine record**: Desired metadata for one managed machine, including its
  identity, role assignment, platform constraints, and machine-scoped
  configuration references.
- **machine identity**: Persistent identity of an enrolled physical or virtual
  machine. It does not change when its OS deployment changes.
- **role**: A named set of behavioral requirements, configuration, health
  criteria, and security objectives, such as `workstation` or `router`.
- **role assignment**: The authorized binding of a machine to a role.
- **platform**: Hardware, firmware, boot environment, and trust facilities that
  exist independently of a NeutrinOS deployment.
- **platform class**: A supported grouping of platform capabilities and
  constraints against which deployment compatibility can be evaluated.
- **platform observation**: A fact observed from SMBIOS, firmware, TPM, CPU,
  storage, or a similar interface. An observation may establish compatibility;
  it does not assign a role or authorize a deployment.
- **configuration source**: A named origin of configuration inputs.
- **configuration scope**: Where a configuration input applies: `common`,
  `role`, or `machine`. In formal text, qualify this term to distinguish it
  from an authorization scope.
- **configuration input**: One concrete declarative or upstream-native input
  supplied by a configuration source.
- **native configuration**: Configuration expressed directly in the format
  consumed by its upstream component, such as a systemd unit or networkd file.
- **configuration composition**: Deterministically combining configuration
  inputs according to their scopes and precedence.
- **configuration precedence**: The explicit conflict order among
  configuration sources. The initial order is `common < role < machine`.
- **resolved configuration**: The complete conflict-resolved configuration
  before it is rendered into OS artifacts.
- **rendered configuration**: Upstream-native files produced from resolved
  configuration.
- **composition record**: Immutable evidence identifying the ordered
  configuration inputs, precedence decisions, transformation tools,
  validations, resolved configuration, and rendered configuration used for a
  deployment variant.
- **identity-bound input**: An input fixed by and attributable to a deployment
  identity. Changing it produces a different deployment identity.
- **late-bound input**: A value supplied after deployment identity is
  established under an explicit contract. It does not silently change
  deployment membership.
- **secret**: A value whose confidentiality must be protected from at least one
  actor in the applicable threat model. A private key, password, or bearer token
  is normally a secret; a public certificate normally is not.
- **credential**: Data or a cryptographic capability used by a subject to prove
  identity, obtain authorization, or configure an authenticated relationship.
  A credential may contain secret and non-secret parts and is not necessarily a
  systemd credential.
- **systemd credential**: An immutable binary datum passed to a systemd-managed
  service activation through the upstream systemd credentials mechanism. It
  may be secret or non-secret; the mechanism does not make its contents an
  authorization decision or an allowed late-bound semantic effect.
- **credential contract**: Identity-bound configuration declaring the exact
  owner, authority, subject, consumer, name, schema and semantic effects,
  delivery, validity, failure, rotation, offline, evidence, and recovery policy
  for a class of late-bound credential instances.
- **credential grant**: An attributable authorization for one exact subject and
  consumer to receive or obtain a credential instance under a credential
  contract. Enrollment identifies the subject but does not itself create every
  credential grant.
- **credential instance**: One versioned and scoped value or proof supplied
  under a credential contract, with explicit issuer, subject, validity, and
  currentness. Its value may be secret even when its identifying metadata is
  not.
- **secret envelope**: A protected representation of secret material addressed
  to declared recipient capability and context. An envelope's encryption does
  not establish authorization, correct consumption, or recoverability.
- **credential realization**: The outcome of attempting to deliver one
  credential instance to one exact consumer activation under its contract,
  recorded without the secret value.
- **provisioning**: Preparing initially blank or reset storage, trust roots,
  and machine identity. Provisioning is not routine OS configuration.
- **installation**: Populating a target with a previously built deployment set
  and the storage/boot structures required to select it. Installation does not
  itself enroll the machine or authorize the deployment.
- **installer artifact**: The exact bootable or executable environment used to
  perform installation. Its destructive capability does not grant release,
  recovery, enrollment, platform-owner, or data-recovery authority.
- **provisioning intent**: An authenticated, versioned, time-bounded record for
  one install, reinstall, disk replacement, identity rotation, reprovision, or
  factory-reset operation. It binds target constraints, permitted mutation,
  preservation, deployment scope, authority steps, and completion behavior.
- **bootstrap hint**: Untrusted or separately authenticated metadata used to
  locate provisioning intent before enrollment. A bootstrap hint does not
  assign a role or authorize a deployment.
- **enrollment**: Binding a machine identity to NeutrinOS administrative
  authority and fleet inventory.
- **enrollment voucher**: A short-lived, authority-effectively single-use
  authorization to submit one enrollment request within an exact machine-record
  and operation scope. A voucher is not a machine credential or approved
  binding.
- **enrollment request**: A fresh proposal containing the voucher, locally
  generated public key, proof of possession, nonce, requested machine record,
  and applicable observations.
- **enrollment approval**: An enrollment-authority decision accepting one exact
  request and assigning its machine identity epoch.
- **enrollment binding**: The current authority-approved association of one
  machine identity key and epoch with one machine record.
- **identity epoch**: An ordered generation of a machine's enrollment identity.
  Rotation or re-enrollment creates a new epoch; rollback cannot restore a
  revoked older epoch.
- **provisioning record**: Attributable evidence of one provisioning intent,
  target, tool and authority actions, installed outputs, failures, and result.
- **provisioning completion**: The joined state showing that installation,
  enrollment, exact normal trial boot, and required handoff checks completed.
  It is not a single magic marker whose absence authorizes replay.
- **reinstall**: Replacement of release-owned deployment artifacts while
  retaining only explicitly selected compatible state and identity semantics.
- **reprovision**: Deliberate execution of a new authenticated provisioning
  intent on a previously provisioned machine.
- **factory reset**: Deliberate destruction of declared machine,
  administrator, user, workload, identity, and secret scopes that returns the
  target to unprovisioned state. It does not enroll a new identity.

The normal composition flow is:

```text
configuration sources
        | composition
        v
resolved configuration
        | rendering and build
        v
deployment artifacts
        | bound by
        v
deployment manifest -> deployment identity
        | plus deployment closure
        v
deployment set
        | booted with platform, state, and late-bound inputs
        v
machine realization
```

## Artifacts and deployments

- **artifact**: Immutable bytes identified by a cryptographic digest and
  intended for testing, publication, or deployment.
- **digest**: The cryptographic content identity of exact bytes. A human
  version is not a substitute for a digest.
- **deployment artifact**: An artifact belonging to a deployment closure.
- **deployment manifest**: The immutable record that binds a deployment's
  complete release-owned artifact closure and its declared constraints.
- **deployment closure**: The complete transitive set of release-owned
  artifacts referenced by a deployment manifest.
- **deployment identity**: The digest of a deployment manifest.
- **deployment set**: A deployment manifest and its complete deployment
  closure. It is the unit of qualification, authorization, staging, selection,
  blessing, fallback, rollback, and withdrawal.
- **deployment variant**: A complete deployment set produced for a particular
  resolved role, platform-class, and machine configuration.
- **machine realization**: A deployment set actually running on a platform
  with its state, declared late-bound inputs, and administrative modifications.
- **release**: A promoted collection of one or more independently identified
  deployment variants and their authorization metadata.
- **release name** or **release version**: A human-readable grouping and
  ordering label. It is not artifact or deployment identity.

Format-specific artifact terms retain their upstream meanings:

- **UKI**: A UAPI Unified Kernel Image: a UEFI PE file combining a boot stub,
  kernel, optional initrd, and related resources.
- **DDI**: A UAPI Discoverable Disk Image: a self-describing GPT disk image.
- **root image**: A DDI or other explicitly named filesystem image used as the
  immutable release-owned root.
- **system extension image** or **sysext**: A UAPI extension image for `/usr`
  or `/opt`.
- **configuration extension image** or **confext**: A UAPI extension image for
  `/etc`.
- **OCI image**, **OCI manifest**, **OCI descriptor**, and **OCI layer**: The
  corresponding OCI Image Specification objects. An OCI layer is a filesystem
  changeset blob, not a configuration scope or generic architectural layer.

## Storage and data protection

- **storage region**: A persistent partition, volume, filesystem, subvolume,
  image store, mount, or explicitly reserved capacity range with declared
  lifecycle purposes. A storage region is not automatically a state owner.
- **storage slot**: A bounded destination capable of holding one version of a
  deployment artifact. A slot name, number, partition label, or position is a
  locator, not artifact or deployment identity.
- **root slot**: A storage slot holding one immutable root image. When dm-verity
  is used, its matching Verity data is part of the deployment closure even if
  stored in a separate slot.
- **root hash**: The trusted top-level dm-verity digest that authenticates one
  exact root data and hash-tree combination. A root hash is an artifact binding,
  not release authorization or qualification.
- **state volume**: A block volume or filesystem holding one or more persistent
  state-contract namespaces with compatible custody, unlock, preservation,
  recovery, and destruction policy.
- **unlock method**: A declared way to obtain or derive the key that activates
  an encrypted state volume, such as TPM2 policy, FIDO2, passphrase, or a
  recovery key.
- **recovery key**: An independently retained high-entropy storage-unlock secret
  used deliberately when the routine unlock method is unavailable. It is not
  recovery-environment authorization or a release-signing key.
- **capacity reserve**: Storage deliberately withheld or protected for a named
  update, fallback, recovery, migration, diagnostic, or layout-evolution
  obligation. Unallocated space is not a reserve unless policy keeps it
  available for that purpose.
- **checkpoint**: An owner-specific consistent point from which state can be
  retried or restored. A filesystem snapshot is only one possible checkpoint
  mechanism and is not an independent backup by itself.

## Package inputs and upstream maintenance

- **package universe**: One declared distribution, release or branch,
  architecture, repository set, trust policy, and dependency-resolution policy
  within which a package closure is solved. It is an input boundary, not the
  identity or runtime lifecycle of NeutrinOS.
- **repository state**: The exact repository metadata and trust context visible
  to one dependency resolution. A mirror URL, date, branch name, or repository
  label alone does not identify a repository state.
- **package input snapshot**: The immutable record and retained object set that
  identifies a repository state, solver policy, complete resolved package
  closure, exact package bytes, source attribution, verification results, and
  project or third-party inputs used by a build.
- **package closure**: The complete set of direct and transitive binary package
  inputs selected for one build variant, including the dependency reasons and
  repository source for every member.
- **input intake**: The controlled transition by which an upstream or
  third-party input is acquired, verified, classified, retained, and made
  eligible for build resolution. Intake eligibility is not deployment
  qualification or release authorization.
- **project-built package**: A package built and maintained by NeutrinOS from
  pinned sources and a reviewed project-owned recipe or patch set. It creates a
  downstream maintenance obligation even when its format matches an upstream
  distribution.
- **third-party package input**: A package, binary, or build recipe outside the
  selected official package universe. Package-manager compatibility or a valid
  third-party signature does not assign NeutrinOS trust or maintenance policy.
- **upstream branch**: A distribution-maintained release or rolling line whose
  update and end-of-life policy governs candidate package inputs. Upstream
  branch support is distinct from NeutrinOS deployment retention.

## Evidence and authority

- **evidence record**: Immutable, content-identified bytes expressing one typed
  claim or observation about exact subjects under a declared format, producer,
  completeness, and verification policy. Record identity does not establish
  truth.
- **evidence-set manifest**: A small immutable record joining evidence-record
  identities for one named purpose and policy. It indexes native claims without
  copying their semantics or becoming deployment identity.
- **attestation**: An evidence record containing a typed statement by an
  identified producer about exact subjects, optionally authenticated through
  an evidence envelope. Authentication establishes attribution, not truth.
- **provenance**: An attestation describing where, when, and how exact outputs
  were produced, including their declared materials, builder, build process,
  parameters, environment, and completeness boundary.
- **SBOM**: A Software Bill of Materials: a subject-bound inventory of software
  components, identities, relationships, ownership, and declared coverage gaps.
  It is not provenance, a vulnerability verdict, or proof of completeness.
- **SBOM coverage gap**: A declared component class, artifact, or relationship
  that the applicable SBOM process could not identify or inspect. A gap is
  unknown coverage, not evidence of absence.
- **build replay**: Re-executing a build with its retained inputs and
  instructions. Success does not imply byte-identical output.
- **bit-reproducible**: A claim that the explicitly named artifacts from builds
  with the declared source, instructions, and environment are byte-for-byte
  identical under the stated comparison.
- **independently reproduced**: A bit-reproducibility result produced by a
  separately identified builder or trust domain. Independence must be stated;
  two runs on one builder do not imply it.
- **vulnerability source snapshot**: Immutable retained advisory or
  vulnerability-source records plus their acquisition identity and time. It is
  input to matching and assessment, not a deployment verdict.
- **vulnerability finding**: A source-attributable candidate match between a
  vulnerability record and an exact component or deployment. It may later be
  confirmed, contradicted, or assessed as not exploitable; it is not deleted by
  that assessment.
- **vulnerability assessment**: An attributable, time- and subject-scoped claim
  about applicability, exploitability, reachability, mitigation, accepted risk,
  or required action for a finding.
- **VEX**: Vulnerability Exploitability eXchange: a machine-readable
  vulnerability assessment in a recognized VEX representation. A negative VEX
  claim is not proof that code is fixed and does not erase its source finding.
- **qualification**: Evaluation of an exact deployment identity against a
  named policy and environment.
- **qualification record**: Attributable evidence recording a qualification
  result and its exact claim boundary.
- **authorization scope**: The machines, roles, channels, operations, or other
  subjects for which an authorization is valid.
- **release authorization**: A signed statement permitting a deployment
  identity to be used within a specified authorization scope and freshness
  policy.
- **release evidence**: Provenance, qualification records, authorizations, and
  related material associated with a deployment.
- **evidence envelope**: A serialized container joining evidence to exact
  native artifact identities. It represents claims but is not itself the
  semantic claim.
- **promotion**: Issuing or activating release authorization. Copying artifact
  bytes is publication, not promotion.
- **publication**: Making artifacts and evidence discoverable or downloadable.
- **channel**: A mutable discovery or policy reference such as `testing` or
  `stable`. A channel is not an identity.
- **withdrawal**: Removing normal authorization for a deployment without
  erasing its bytes or historical evidence.
- **freshness**: Whether current authorization metadata satisfies its time and
  replay policy.
- **authority role** or **signing role**: A named authority responsibility. Do
  not use the unqualified word `role` for this meaning.

## Lifecycle

The normal lifecycle vocabulary is:

```text
discovered -> acquired -> staged -> eligible -> selected
    -> booted -> assessed -> blessed
```

- **discovered**: A deployment identity and its metadata are known to a
  machine or fleet service. Discovery does not establish eligibility.
- **acquired**: Artifact bytes are locally present but inert.
- **staged**: A complete deployment set is locally present and
  integrity-verified without having been selected.
- **eligible**: Qualification, authorization, compatibility, freshness, and
  local-policy gates all pass at evaluation time.
- **selected**: Designated for a subsequent boot.
- **booted deployment**: The deployment identity currently running.
- **trial boot**: A bounded boot of an unblessed deployment.
- **assessed**: Runtime health criteria have been evaluated.
- **bless** or **blessed**: Accept a successfully assessed trial for continued
  normal selection on that machine.
- **default deployment**: The deployment selected when no one-shot or trial
  selection overrides it.
- **retained deployment**: A locally present deployment kept for possible
  future use. Retention does not imply eligibility.
- **fallback**: Automatic selection of a retained eligible deployment after a
  failed boot or health assessment.
- **rollback**: Deliberate selection of an earlier retained deployment through
  the normal authorization path. Rollback does not imply rollback of persistent
  state.
- **recovery**: Entry into an independently authorized recovery environment or
  capability path. Recovery is not automatic fallback.
- **garbage collection**: Removal of unreferenced artifacts according to
  retention policy.

## Rollout control

- **rollout**: The controlled movement of an already authorized release across
  a declared fleet scope. Rollout may restrict who advances and when; it does
  not create release authorization or local eligibility.
- **rollout plan**: An immutable record binding a release authorization and
  promotion evidence set to a fleet inventory snapshot, transition policy,
  ordered cohorts, gates, windows, and stop rules.
- **rollout revision**: An append-only ordered decision that starts, advances,
  pauses, resumes, supersedes, or terminates a rollout plan. It does not mutate
  the plan or earlier revisions.
- **rollout cohort**: A named set of machines evaluated together at one rollout
  stage. Membership is exact or deterministically derived from a frozen fleet
  inventory; a cohort is not deployment identity or a statistical claim.
- **canary**: A rollout cohort intentionally placed early to produce evidence
  before a larger or higher-consequence cohort advances. A canary establishes
  only the behavior its role, platform, and observation policy actually cover.
- **rollout gate**: A declared rule over an exact cohort and observation set
  that permits advance, requires pause, or demands an explicit accepted-risk
  decision.
- **rollout grant**: A bounded decision permitting one named machine or exact
  cohort member to perform a specified rollout action from an exact source to
  an exact target deployment. It cannot replace release authorization or local
  eligibility.
- **rollout observation**: An attributable report binding a machine,
  deployment, boot or transition, policy, producer, result, and time for use by
  a rollout gate.
- **rollout pause**: A decision preventing new acquisition or activation within
  a stated scope and in-flight boundary. A pause is not withdrawal.
- **rollout resume**: A new decision superseding a named pause after recording
  supporting evidence or accepted risk. Elapsed time alone is not resume.
- **transition path**: One or more explicitly permitted edges from exact current
  deployment identity to exact target identity, including applicable state and
  input-baseline compatibility.
- **reboot lease**: Temporary permission to consume an availability slot for a
  reboot. It is not release authorization, rollout permission, or software
  eligibility.
- **pin**: An attributed exception fixing a machine to an exact deployment or
  disabling automatic activation until a review or expiry condition. A pin does
  not imply currentness, support, or immunity from withdrawal.
- **deferral**: An attributed delay of an otherwise eligible rollout action
  until a stated condition or deadline. It does not change deployment identity
  or authorization.

## State and status

- **state**: Data expected to survive deployment replacement. Formal text
  should normally qualify it by owner or lifecycle.
- **state contract**: The declared owner, authority, schema or format,
  compatibility, migration, backup, recovery, reset, and retention behavior of
  a state item or namespace.
- **system model**: The end-to-end relationship among inputs, artifacts,
  machine state, configuration, trust, deployment, and recovery.

Status properties must remain distinct:

- **present**: Bytes exist locally.
- **integrity-verified**: Bytes match an expected digest.
- **authenticated**: A signature validates to an accepted authority.
- **authorized**: Current policy permits an identity for the stated
  authorization scope.
- **qualified**: The required evaluation succeeded for the stated claim
  boundary.
- **compatible**: Platform and state constraints match.
- **eligible**: Every current selection gate passes.
- **healthy**: Runtime health requirements pass.
- **blessed**: A successful trial was accepted.
- **exact**: All release-owned artifacts match the stated deployment identity.
- **locally modified**: Administrator-owned input has changed the machine
  realization outside the deployment closure.
- **current**: Satisfies the explicitly named maintenance or freshness policy.
  Prefer the more precise property when that is what is meant.

## Discouraged ambiguous terms

- Use **layer** only in a qualified upstream term such as **OCI layer**. Use
  configuration source, configuration scope, deployment artifact, project
  surface, or another exact term for other meanings.
- Qualify **image** and **manifest**, for example root image, OCI image, or
  deployment manifest.
- Qualify **scope**, **role**, and **state** when more than one kind is in play.
- Avoid **installed** and **active** for deployment lifecycle status; use
  acquired, staged, selected, booted, or blessed.
- Avoid **latest** as an identity or selection rule. Name the version ordering,
  channel, authorization, or maintenance policy instead.
- Avoid **trusted** unless the trust anchor and guarantee are stated.
- Do not use **signed**, **healthy**, **current**, or **green** as substitutes
  for authenticated, authorized, qualified, eligible, or blessed.
- Avoid the bare noun **target** when it means a managed machine or deployment
  artifact. Use machine, deployment artifact, destination, or another exact
  term. Qualified terms such as systemd target, target disk, and qualification
  target retain their established meanings.

## Prior-art basis

The vocabulary intentionally reuses or adapts terms from:

- the [OCI Image Specification](https://github.com/opencontainers/image-spec),
  especially its definitions of descriptors, manifests, and filesystem
  changeset layers;
- the [UAPI Discoverable Disk Image](https://uapi-group.org/specifications/specs/discoverable_disk_image/),
  [Extension Image](https://uapi-group.org/specifications/specs/extension_image/),
  and [Unified Kernel Image](https://uapi-group.org/specifications/specs/unified_kernel_image/)
  specifications;
- [SLSA terminology](https://slsa.dev/spec/v1.0/terminology) for builds,
  artifacts, and provenance; and
- [The Update Framework specification](https://theupdateframework.github.io/specification/)
  for separating content identity from signed, delegated, versioned, and
  expiring authorization metadata.

TUF's `target file` term is deliberately not adopted because `target` already
has a strong and unrelated meaning in the systemd ecosystem.
