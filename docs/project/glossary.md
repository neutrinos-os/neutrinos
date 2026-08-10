# Glossary

This is the canonical dictionary for NeutrinOS project terms. Designs and ADRs
decide behavior; this glossary gives their words consistent meanings. A local
design may introduce a provisional term, but a term used across designs should
be promoted here.

Use upstream names unchanged when referring to upstream objects. NeutrinOS
terms describe substrate-independent semantics and must not imply properties
that have not been established.

## Configuration and machine intent

- **fleet inventory**: The authoritative collection of managed machine
  records.
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
- **identity-bound input**: An input fixed by and attributable to a deployment
  identity. Changing it produces a different deployment identity.
- **late-bound input**: A value supplied after deployment identity is
  established under an explicit contract. It does not silently change
  deployment membership.
- **credential**: A late-bound datum delivered through the systemd credentials
  mechanism. A credential may be secret or non-secret.
- **provisioning**: Preparing initially blank or reset storage, trust roots,
  and machine identity. Provisioning is not routine OS configuration.
- **enrollment**: Binding a machine identity to NeutrinOS administrative
  authority and fleet inventory.

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

## Evidence and authority

- **attestation**: A verifiable statement made by an identified authority about
  a subject.
- **provenance**: An attestation describing how build outputs were produced,
  including their inputs, platform, and parameters.
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
