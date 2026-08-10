---
id: EX-0005
title: Representative deployment manifests and composition tabletop
status: complete
date: 2026-08-09
exercise_type: manifest and lifecycle tabletop
evidence_class: analysis-only
related_designs: [DES-0001, DES-0002, DES-0003]
---

# Representative deployment manifests and composition tabletop

## Purpose and evidence limit

This exercise tests whether DES-0001's deployment-set model can describe the
reference VM, `desktop-jason`, and `router` without either duplicating every OS
artifact per machine or moving checked-in policy into unqualified late-bound
configuration.

The manifests below are semantic records, not a proposed file format. Names
such as `boot`, `root`, and `config` identify responsibilities that a substrate
must bind; they do not require separate files, partitions, images, or a
NeutrinOS-specific manifest implementation. Digests, schemas, package sets,
network values, and qualification results are placeholders until artifacts are
built.

This is analysis-only evidence. It can show that the identity and ownership
model is coherent. It cannot measure build time, storage reuse, test duration,
boot behavior, or power-loss safety.

## Questions and success conditions

The exercise asks:

1. What differs among the VM fixture, workstation, and router deployment sets?
2. Which configuration is immutable release input, which is legitimately
   late-bound, and which remains separately owned state?
3. Can exact machine configuration be bound without rebuilding large shared
   artifacts unnecessarily?
4. Which qualification evidence can be reused, and which must follow each
   literal deployment identity?

The paper model passes if every variant has a complete artifact closure, no
normal policy floats outside its identity, machine identity and secrets remain
separate, and sharing never causes one variant to inherit another's
qualification.

## Schematic manifest contract

Each example uses the same logical fields:

| Field | Purpose |
| --- | --- |
| `schema` | Identifies the interpretation and rejection rules for the manifest. |
| `role` | Names the role whose behavior and health policy are claimed. |
| `platform_scope` | Declares architectures and platform classes on which selection is allowed. |
| `artifacts` | Closes over every exact release-owned boot, root, extension, configuration, firmware, and policy artifact. |
| `resolved_inputs` | Identifies pinned source, package, role, machine, and transformation inputs that determined the artifacts. |
| `late_bound_contracts` | Names independently owned values, their schemas, constraints, and failure behavior. |
| `state_contracts` | Identifies persistent state compatibility and migration rules. |
| `health_policy` | Identifies role-specific boot assessment and blessing rules. |
| `compatibility` | Declares selection, rollback, and cross-role compatibility constraints. |

The content identity of the final manifest is the deployment identity. Platform
signing happens before artifact identities are placed in the manifest.
Qualification and release authorization are detached records created after the
deployment identity exists; putting either result into the manifest would
create an identity cycle.

`release_name`, publication locations, mutable tags, boot-attempt counters,
qualification results, and release-authorization signatures are therefore not
identity-bearing fields in this schematic record.

## Composition candidates

### A. Flatten every variant

Render common, role, machine, and normal configuration into one root plus its
bound boot artifact. Each distinct configuration produces a complete new pair.

Advantages:

- fewest runtime composition and precedence rules;
- easiest claim that boot and root are one literal qualified variant; and
- likely compatible with substrates that expose only one strong native image
  identity.

Costs:

- small configuration changes rebuild and redistribute large artifacts;
- content reuse depends on the build or storage substrate rather than visible
  artifact boundaries; and
- a growing fleet can multiply superficially different roots.

This is the safe fallback when separately stored configuration cannot be
authenticated, selected, rolled back, and garbage-collected with the rest of
the deployment set.

### B. Shared release artifacts plus immutable configuration artifact

Keep large common or role artifacts content-identified and place exact resolved
normal configuration in a smaller immutable artifact. A manifest binds the
literal tuple as one deployment set.

Advantages:

- a machine-policy change creates a new deployment identity without requiring
  unrelated OS bytes to change;
- identical role or platform artifacts can be transferred and retained once;
  and
- configuration provenance and rendered native output remain inspectable.

Costs:

- early boot and the update substrate must prevent a config/root hybrid;
- precedence, compatibility, retention, and recovery span multiple resources;
  and
- every tuple still needs applicable qualification; sharing bytes does not
  make qualification records interchangeable.

This is the preferred working composition target. It is conditional on A-014:
the selected production-supported substrate must enforce complete-set identity
and transactional selection without a custom NeutrinOS updater or object store.

### C. Generic image plus mutable target-side configuration

Build one generic image, then fetch or evaluate current role and machine policy
on the target.

Rejected. It makes normal behavior depend on mutable discovery, rebuilds the
effective OS after qualification, weakens offline rollback, and recreates the
deployment/configuration failure that SYS-014 through SYS-018 were accepted to
avoid.

## Logical factoring model

The exercise distinguishes configuration inputs, derived content, and artifact
bindings without requiring each logical factor to become a physical artifact:

```text
common source and package inputs
              |
              +--> shared base content ----+
              |                             |
role input ---+--> role content ------------+--> deployment manifest
              |                             |      binds exact tuple
machine input +--> immutable normal config -+
              |
platform/root binding --> final boot artifact
```

The boot artifact may need to be unique per deployment if it embeds a root hash,
configuration identity, kernel command line, or platform-specific material.
The root may likewise be physically flattened with role content. Logical
factoring is valuable for provenance and build reuse even when the production
substrate exposes fewer independently stored objects.

A `shared base` is not an independently selectable partial OS. Only a complete
manifest closure is a deployment set.

## Reference VM fixture

The reference VM serves two related purposes:

1. a small VM fixture variant exercises the common install, update, selection,
   assessment, rollback, and recovery machinery; and
2. the qualification harness boots the literal workstation and router
   candidates under modeled hardware before physical rollout.

The fixture does not replace role qualification, and VM success does not prove
physical hardware support.

```yaml
schema: <deployment-manifest-policy>
role: qualification-fixture
platform_scope:
  architecture: x86-64
  classes: [reference-qemu-uefi]
artifacts:
  boot: <signed-boot-artifact-digest>
  root: <minimal-immutable-root-digest>
  config: <vm-fixture-config-digest>
  extensions: []
  os_loaded_firmware: <closed-list-or-empty>
resolved_inputs:
  common: <pinned-common-input-set>
  role: <vm-fixture-role-input>
  machine: <pinned-virtual-hardware-and-config-input>
late_bound_contracts:
  - virtual-hardware-observation
  - optional-vtpm-identity
  - test-injected-network-environment
state_contracts:
  - boot-attempt-and-blessing-state
  - update-diagnostics
  - representative-migration-fixture
health_policy: <vm-lifecycle-health-policy>
compatibility: <vm-selection-and-rollback-policy>
```

The virtual firmware build, variables, vTPM state, and virtual hardware versions
are qualification-environment evidence rather than hidden release inputs.

## Workstation variant: `desktop-jason`

```yaml
schema: <deployment-manifest-policy>
role: workstation
platform_scope:
  architecture: x86-64
  classes: [desktop-jason, reference-qemu-workstation-model]
artifacts:
  boot: <final-signed-workstation-boot-digest>
  root: <workstation-root-digest>
  role_content: <workstation-content-digest-or-flattened>
  config: <desktop-jason-normal-config-digest>
  extensions: <closed-release-owned-list>
  os_loaded_firmware: <amd-gpu-intel-network-and-cpu-payload-list>
resolved_inputs:
  common: <pinned-common-input-set>
  role: <pinned-workstation-role-input>
  machine: <desktop-jason-checked-in-input>
  native_config: <resolved-native-output-identities>
late_bound_contracts:
  - hardware-enumeration-and-supported-topology
  - tpm-bound-normal-unlock-result
  - machine-enrollment-and-host-identity
  - machine-or-user-network-credentials
  - environmental-network-values
state_contracts:
  - machine-identity
  - operational-evidence
  - user-home
  - rootless-container-storage
  - virtual-machine-storage
health_policy: <workstation-boot-and-graphical-session-policy>
compatibility: <workstation-state-and-rollback-policy>
```

### Workstation configuration classification

| Input | Classification | Reason and identity effect |
| --- | --- | --- |
| Enabled base services and graphical session policy | Deployment-bound role configuration | Normal privileged behavior; any change creates another deployment identity. |
| Generic kernel choice, modules, GPU/network firmware and load policy | Release artifact or deployment-bound configuration | Qualified with the literal workstation variant. |
| Supported device/topology constraints and failure behavior | Deployment-bound policy | The accepted class is exact; the observed devices are late-bound evidence. |
| Machine-specific filesystem/mount intent after provisioning | Deployment-bound machine configuration | Normal behavior must not depend on an edited persistent `/etc/fstab`; storage layout itself remains separately provisioned state. |
| Desired hostname, locale, time policy, users, and group policy | Deployment-bound when checked in as normal intent | If an item is instead derived from enrollment identity, that ownership decision must be explicit rather than silently late-bound. |
| TPM observation and normal unlock result | Declared late-bound machine/platform value | Hardware and sealed-secret result cannot be general release bytes; policy and failure behavior remain bound. |
| Wi-Fi, VPN, service, and user credentials | Machine or user state | Secret bytes never enter deployment; references, scopes, consumers, and failure behavior do. |
| DHCP/DNS answers, link state, time, removable devices | Environmental observation | Can affect health but not reconstruct normal policy. |
| `/home`, desktop preferences, applications, containers, and VM disks | User or workload state | Separate lifecycle and status; do not roll back with deployment. |
| Persistent administrative units, modules, boot arguments, or extensions | Administrator override | Outside deployment and marks the machine realization locally modified. |

## Router variant: `router`

```yaml
schema: <deployment-manifest-policy>
role: router
platform_scope:
  architecture: x86-64
  classes: [router-x11sdv, reference-qemu-router-model]
artifacts:
  boot: <final-signed-router-boot-digest>
  root: <router-root-digest>
  role_content: <router-content-digest-or-flattened>
  config: <router-normal-config-digest>
  extensions: <closed-release-owned-list>
  os_loaded_firmware: <intel-network-and-cpu-payload-list>
resolved_inputs:
  common: <pinned-common-input-set>
  role: <pinned-router-role-input>
  machine: <router-checked-in-input>
  native_config: <resolved-network-and-service-output-identities>
late_bound_contracts:
  - physical-interface-observation-and-role-mapping
  - link-and-provider-delegation
  - machine-enrollment-and-host-identity
  - vpn-and-service-credentials
  - hardware-bound-unlock-result-when-supported
state_contracts:
  - machine-identity
  - operational-evidence
  - bounded-network-protocol-state
  - update-and-boot-attempt-state
health_policy: <externally-observed-router-health-policy>
compatibility: <router-state-offline-rollback-and-peer-policy>
```

### Router configuration classification

| Input | Classification | Reason and identity effect |
| --- | --- | --- |
| Interface-role mapping policy | Deployment-bound machine configuration | WAN/LAN meaning and mapping rule are normal policy; observed device identity is a constrained late-bound value. |
| Static or desired addresses, prefixes, VLANs, routes, forwarding, firewall rules | Deployment-bound machine or role configuration | Checked-in non-secret network intent is qualified and cannot float beside a generic image. |
| DHCP, DNS, VPN, monitoring, watchdog, and administration service policy | Deployment-bound configuration | Enabled services, native configuration, ordering, and externally observed health belong to the variant. |
| Kernel, modules, NIC firmware, sysctls, eBPF or packet-processing programs | Release artifact or deployment-bound configuration | These affect privileged forwarding behavior and belong in the complete set. |
| Provider delegation, link state, learned neighbors, current time | Declared late-bound environment or protocol state | Values change operationally under an exact consumption and failure policy. |
| VPN private keys, host keys, service and enrollment credentials | Machine state | Persist and rotate independently; deployment references their scopes but does not contain them. |
| Leases and dynamic protocol state | Explicit machine/workload state contract or ephemeral output | Each protocol decides whether loss is safe; its path does not decide ownership. |
| Logs, boot attempts, update and health evidence | Operational state | Must survive relevant failed boots within bounded storage policy. |
| Local scripts, units, rules, modules, or privileged containers | Administrator override | Supported production policy may reject them; otherwise realization is locally modified. |

The current absence of a TPM does not change the manifest boundary. It affects
whether the `hardware-bound-unlock-result` contract can be satisfied for a
production router with the accepted confidentiality and unattended-boot claims.

## Shared bytes do not imply shared variants

The three examples can reuse content while preserving literal identities:

| Reuse candidate | Likely relationship | Qualification consequence |
| --- | --- | --- |
| Common source/package inputs | Shared provenance input | Input review may be reused; final artifacts still have literal identities. |
| Common base filesystem content | Shared build output, deduplicated object, or flattened output | Common tests can attach to the exact shared artifact, but each manifest tuple still gets selection and integration tests. |
| Generic initial kernel | Potentially shared workstation/router input | Final boot artifacts may differ because initrd, command line, root binding, signing, or platform policy differs. |
| Role content | Shared by machines with identical role needs | Machine configuration differences still create distinct deployment identities. |
| Machine configuration artifact | Shared only when resolved normal configuration is literally identical | Machine identity and secrets can differ without forcing another deployment when their declared late-bound contracts are identical. |
| Qualification environment and test implementation | Shared harness | A passing result transfers only to the exact artifacts and claims exercised. |

Variant count is the number of distinct qualified deployment tuples, not
automatically the number of hosts. Two machines can select one deployment set
when their release-owned bytes, resolved normal configuration, compatibility,
and policies are identical. Enrollment identity, credentials, and observed
hardware values may differ only within the same declared late-bound contracts.

## Configuration-change trace

Consider a one-line checked-in firewall-policy change for `router`:

| Composition | Required work | Identity and safety |
| --- | --- | --- |
| Flattened variant | Re-render/rebuild root and any boot artifact that binds it; create manifest; qualify literal set | Simple runtime boundary, potentially large rebuild and transfer |
| Immutable config artifact | Re-render config artifact; create manifest binding existing compatible root/boot artifacts plus new config; qualify literal tuple | Smaller changed object, but boot must bind config and root atomically |
| Mutable target config | Fetch or evaluate new rule on router | Rejected: behavior changes without a qualified deployment identity |

The second path can reuse unchanged artifact-level evidence, but it cannot skip
the tests affected by the policy change or the end-to-end boot of the literal
new tuple. Evidence reuse must name the unchanged artifact and claim; it cannot
be inferred merely from a common release label.

## Qualification matrix

Each deployment identity receives at least:

1. complete-closure and authorization verification;
2. literal boot and identity reporting on the reference VM where possible;
3. common lifecycle tests for staging, selection, failed boot, rollback, and
   recovery boundaries;
4. role configuration validation and role-specific health tests;
5. affected state-contract compatibility tests; and
6. physical tests for claims the VM cannot establish.

The workstation adds graphical-session and physical device checks. The router
adds representative WAN/LAN topology, externally observed forwarding/services,
watchdog, offline boot/fallback, and independent recovery checks.

An artifact shared byte-for-byte can carry forward evidence that genuinely
depends only on that artifact. Composition, configuration, role behavior,
platform integration, and state compatibility evidence remain attached to the
complete deployment identity or a precisely named broader equivalence class.

## Failure scenarios

| Failure | Required result |
| --- | --- |
| Config artifact from another manifest is present | It remains inert or boot fails binding; no hybrid gains selection eligibility. |
| Root is shared but incompatible with a new config schema | Pre-selection compatibility rejects the tuple; common bytes do not imply compatibility. |
| A machine-specific value is absent | Follow its declared failure policy; do not fetch mutable normal configuration or construct a substitute release. |
| VM passes but a physical device is unsupported | Physical qualification fails and release authorization excludes that target. |
| Router variant is withheld while workstation advances | Workstation may advance under explicit compatibility claims; release name does not fabricate a router artifact. |
| Garbage collection sees one object referenced by several variants | Retain it until no retained deployment closure reaches it. |
| A config-only change is rolled back after state advanced | State compatibility gate applies exactly as for a root change. |

## Conclusions

The manifests are coherent for all three reference uses. They support these
working conclusions:

- use a complete content-identified tuple as the deployment identity even when
  artifacts are shared;
- prefer shared release/role artifacts plus an immutable bound configuration
  artifact when the substrate can enforce the complete lifecycle natively;
- flatten the variant when it cannot;
- never use mutable target-side normal configuration as a sharing shortcut;
- permit one deployment set across multiple machines only when all
  release-owned inputs and late-bound contracts are identical; and
- reuse evidence only at the exact artifact or claim boundary it actually
  tested.

This disposes of DES-0001 review item 3 at the paper level and mitigates C-004.
It supports A-015's plausibility but does not validate its operational cost.
Measured builds and qualification runs remain necessary before accepting the
composition design or choosing a substrate.

## Follow-up evidence

1. Instantiate these records with literal direct systemd/UAPI artifacts and a
   production-supported bootc challenger mapping.
2. Build flattened and immutable-config versions of the same workstation and
   router change; record build time, transferred bytes, retained bytes, and
   end-to-end qualification duration.
3. Prove boot-time binding and interruption safety for the multi-artifact form.
4. Inventory actual native configuration outputs and late-bound schemas.
5. Define thresholds for variant count, qualification duration, and evidence
   reuse that force composition review.
