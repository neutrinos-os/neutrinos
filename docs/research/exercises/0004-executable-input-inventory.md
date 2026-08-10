---
id: EX-0004
title: Executable-input ownership and deployment-boundary tabletop
status: complete
date: 2026-08-09
exercise_type: inventory and tabletop
evidence_class: analysis-only
related_designs: [DES-0001, DES-0002, DES-0003, DES-0004]
---

# Executable-input ownership and deployment-boundary tabletop

## Purpose and evidence limit

This exercise tests C-003 from the DES-0001 review and C-002 from the DES-0003
review: whether code and behavior outside the immutable root can silently
inherit the identity, qualification, or trust claims of the selected deployment
set.

It inventories classes of executable input from firmware through user and
workload startup and traces them through the reference VM, workstation, and
router. It is a paper exercise, not an observation of a built NeutrinOS system.
The exact inputs, paths, loader behavior, and enforcement mechanisms must be
verified once representative artifacts exist.

`Executable input` is deliberately broader than an executable file. It is any
code, configuration, data, credential, or mutable selector whose contents can
materially determine which code runs or what privileged behavior it performs.
It includes boot variables, unit files, generators, kernel modules, firewall
policy, and container definitions as well as binaries.

## Question and success condition

The exercise asks:

> Can every input to normal machine behavior be assigned an owner, identity
> treatment, authorization path, lifecycle, and status consequence without
> pretending that the immutable base covers mutable code?

The paper model passes when:

1. all release-owned inputs to privileged normal behavior are in the selected
   deployment set or are outputs deterministically derived from its declared
   inputs;
2. no separately mutable release-owned extension can inherit the deployment's
   qualification;
3. platform, machine, administrator, user, and workload inputs remain distinct
   from release identity and visibly affect the applicable status dimension;
4. rollback cannot silently reactivate an external input whose owner or
   authorization no longer permits it; and
5. recovery does not execute mutable inputs merely by discovering or mounting
   them.

## Governing rule

For a normal deployment, every input that can affect release-owned privileged
behavior must be one of:

- immutable bytes named by the deployment manifest;
- a deterministic runtime output of named release-owned inputs under a named
  interpretation policy; or
- an independently owned, declared late-bound value class whose owner, schema,
  constraints, failure
  behavior, and effective value are visible in the machine realization.

The third category is not permitted for ordinary checked-in non-secret role or
machine policy. It exists for independently owned secrets, hardware facts, and
environmental observations that cannot truthfully be build artifacts.

An input owned by an administrator, user, or workload may remain mutable and
executable. It receives its own authorization and lifecycle and never inherits
base-release qualification. Its presence does not change the immutable
deployment identity, but it can change the machine realization's modification,
support, health, and compromise status.

## Status vocabulary

| Consequence | Meaning |
| --- | --- |
| `deployment changes` | The input is release-owned; changing it requires a new deployment identity and qualification record. |
| `declared late-bound` | The deployment identity is unchanged, but the observed value and applicable policy must be reported as part of the machine realization. |
| `locally modified` | An administrator has deliberately added or replaced system behavior outside the selected deployment. The base can still be reported as exact, but the complete realization cannot be reported as normally qualified. |
| `separate user/workload status` | The base deployment can remain exact while independently managed code has its own identity, authorization, health, and support status. |
| `platform state` | The input is below or beside NeutrinOS release ownership. The release records the supported platform class and observations without claiming the bytes as its own. |
| `compromise unknown` | Exact artifact identity cannot establish whether independently mutable state is benign. A suspected compromise requires the relevant recovery procedure, not merely OS rollback. |

`Exact deployment` therefore means only that the complete selected
release-owned closure matches its identity. It does not mean `unmodified
machine`, `qualified workloads`, or `uncompromised system`.

## Ownership and input inventory

### Platform and pre-release inputs

| Input class | Owner and boundary | Deployment treatment | Authorization and qualification | Lifecycle and status consequence |
| --- | --- | --- | --- | --- |
| CPU behavior, immutable device logic, board wiring | Hardware/platform | Outside deployment; platform compatibility identifies supported class | Hardware qualification and physical inventory, not release signature | Replacement changes platform realization and may require requalification |
| System firmware, UEFI executable and configuration, Secure Boot variables | Platform owner and vendors | Outside deployment unless a future explicit firmware payload is separately governed | Vendor/platform-owner update authority; release qualification records tested versions and settings | Drift changes platform state and can invalidate support or trust claims without changing deployment identity |
| Option ROMs and device-resident firmware | Platform/device owner | Outside deployment when supplied by device; supported versions or measurements are observations | Platform qualification and device update policy | Unknown or changed firmware can make the realization degraded, unsupported, or compromise-unknown |
| CPU microcode or device firmware loaded by the OS | Release when distributed by NeutrinOS | Exact payload belongs in the deployment closure | Qualified and authorized with the literal deployment | Any payload change changes deployment identity |
| UEFI boot entries, boot order, attempt counters, selected deployment pointer | Machine/platform lifecycle state | Mutable selector state outside artifact content; constrained to complete authorized deployment identities | Written only by the boot/update lifecycle; torn writes and unauthorized targets require tests | Changes selection status, not identity; an unknown selector is a boot failure, not discovery authority |

NeutrinOS's boot-to-root claim begins at the configured platform trust anchor. It
does not claim that authenticating a deployment proves vendor firmware benign.
Platform versions and security state remain part of the machine realization so
that this limitation cannot disappear behind `deployment exact`.

### Release-owned boot and system inputs

| Input class | Deployment treatment | Lifecycle and status consequence |
| --- | --- | --- |
| Boot manager, bootloader, add-ons, UKI or equivalent kernel/initrd/cmdline bundle | Every release-owned byte used by normal boot is named; signing precedes content identity | Any replacement or add-on changes or invalidates the selected deployment |
| Kernel command line and early-boot policy | Normal value is embedded in or immutably bound to deployment; break-glass edits are separate admin input | Normal changes create a deployment; an override marks locally modified and may invalidate unlock or eligibility |
| Initrd generators, hooks, credentials policy, and extensions | Exact programs and release-owned inputs are in the closure | External hook injection is rejected or locally modified |
| Immutable root filesystem | Exact image or content identity is required | Substitution makes the set ineligible or boot fail |
| Release-owned `sysext` and `confext` artifacts | Each artifact is named by deployment; absence is explicit | Addition, removal, or change creates another deployment identity |
| Release-owned portable services or privileged containerized system services | Exact root/image, attachment policy, unit configuration, and compatibility are named | Floating references are forbidden; any change creates another deployment identity |
| In-tree and release-distributed kernel modules | Exact modules and dependency metadata are in a named boot or root artifact | Modules are qualified with their kernel; any change creates another deployment identity |
| OS-provided eBPF programs, plugins, interpreters, scripts, and policy or rule sets | Exact code and behavior-defining normal policy belong in the closure | A mutable replacement cannot retain release qualification |
| System units, presets, generators, drop-ins, tmpfiles, sysusers, udev, D-Bus, PAM, and similar privileged configuration | Exact sources or immutable configuration artifact are named and qualified as a resolved whole | Any release-owned change creates another deployment identity |

The mechanism does not decide ownership. A container implementing the router
control plane may be release-owned, while a desktop development container is
workload-owned. A `sysext` used for a local emergency driver may be
administrator-owned even though the same mechanism carries a release extension
elsewhere.

### Runtime construction and machine inputs

| Input class | Owner and deployment treatment | Lifecycle and status consequence |
| --- | --- | --- |
| Rendered `/etc` and generated native configuration | Output reconstructed from deployment-bound normal inputs plus explicitly ordered late-bound and override inputs | Unexplained drift is a failed realization; persistent exceptions retain their actual owner |
| Hardware enumeration, device identity, topology, link state | Machine/platform observation; declared late-bound class with constraints and failure policy | Unsupported or ambiguous values degrade or block support; they do not trigger target-side OS reconstruction |
| Machine identity, enrollment record, host keys, device certificates | Inventoried machine state outside deployment | Rotation or loss changes identity status; OS rollback never restores revoked identity |
| System credentials and secrets | Bytes remain with their machine/admin/user/workload owner; names, source class, scope, delivery policy, and failure behavior are deployment-bound for base services | Actual version is reported without exposing the secret; stale or wrong scope fails its service or machine health |
| Time, leases, DNS answers, discovered peers, external service data | Environment or consumer-owned state | May change health/currentness, never deployment identity by itself |
| Runtime-generated executable artifacts | Owner follows the generator and persistence contract | Persistent or reused output must be identified, invalidated, or reproducibly derived; calling it a cache does not remove it from the trust boundary |

If an output is later consumed as code or privileged policy, its generator,
inputs, cache validity, and ownership must make the result attributable.

### Administrator inputs

| Input class | Deployment treatment | Lifecycle and status consequence |
| --- | --- | --- |
| Persistent unit/drop-in, generator, udev rule, kernel argument, policy, or binary | Outside deployment and explicitly inventoried | Local authorization does not qualify it; realization is locally modified until removal or incorporation into a new deployment |
| Out-of-tree or locally built kernel module | Outside deployment; module signature is not release identity | At minimum locally modified and unsupported for normal qualification; production may reject loading |
| Admin `sysext`, `confext`, portable service, privileged container, eBPF program, or plugin | Separately content-identified and attached explicitly, never resolved from a floating name | Locally modified; status names exact object and attachment scope |
| Transient debugging or break-glass action | Recorded operation outside deployment | Modified until durable effects are proven removed; reboot is not assumed to erase them |
| Locally installed package or writable system-path file | Not part of immutable release | Locally modified or policy violation; collision with release paths blocks an exact-realization claim |

Administrator authorization answers who was permitted to make a change. It
does not qualify the result or prove it safe.

### User and workload inputs

| Input class | Deployment treatment | Lifecycle and status consequence |
| --- | --- | --- |
| User services, desktop autostart, shell profiles, scripts, plugins, per-user applications | User-owned outside base | Separate user status; can compromise a session while base deployment remains exact |
| Development tools and code in `/home` | User or project-workload owned | Not base-qualified; privileged use can also create an admin modification |
| Rootless containers, images, writable layers, volumes, definitions | User/workload owned unless a service is explicitly promoted to release ownership | Separate workload identity, status, and rollback; floating tags are inadequate evidence |
| Privileged application containers or VMs | Workload owned with explicit admin attachment authority unless promoted into base role | Separate workload status; host records privileged attachment and may be degraded or unsupported |
| VM firmware, disks, cloud-init or equivalent inputs | VM-workload owned; guest has its own platform/deployment/state model | Guest identity and health are independent of host base identity |
| Databases, queues, uploaded code, templates, workload policy | Workload owned under a state contract | Separate health, compromise, backup, and rollback; OS fallback does not revert them |

A user-owned executable does not normally mark the base deployment locally
modified. It does prevent status from collapsing base exactness into a claim
that the user's session or whole machine is trustworthy. If user code crosses
an administrative boundary and changes system behavior, the effect is also an
administrator override or compromise, regardless of the file's original owner.

### Recovery inputs

Recovery and installer artifacts use their own authorization and are not
members of a normal deployment set. Under EX-0003, recovery starts without
mounting or executing administrator, user, workload, or mutable machine inputs.
It treats normal mutable content as evidence or potentially hostile data until
an explicit capability-staged operation selects it.

Discovery on disk is not authorization to attach executable state to a repaired
normal deployment. Return to normal requires a selected normal deployment and
the applicable state, enrollment, local-modification, and health gates.

## Reference-role traces

### Reference VM

1. Virtual firmware, UEFI variables, and vTPM state are recorded platform
   inputs in the qualification environment.
2. Deployment binds literal boot, root, release extensions, normal
   configuration, and test policy.
3. Qualification introduces an altered boot variable, extra extension, admin
   unit, user service, and workload container one at a time.
4. Results distinguish rejection, `locally modified`, separate workload
   status, and platform drift rather than changing deployment identity
   indiscriminately.
5. Recovery proves that mounting prior state does not start its units,
   generators, containers, or user services.

**Paper result:** Pass. Actual artifact and loader traces remain required.

### Workstation (`desktop-jason`)

1. Firmware, Secure Boot variables, TPM state, and hardware remain visible
   platform or machine inputs.
2. Release-owned graphical stack, services, modules, udev policy, and system
   extensions belong to the workstation deployment.
3. Checked-in non-secret machine policy is rendered into or named by that
   deployment. TPM-released secrets and actual devices remain declared
   late-bound inputs.
4. Home applications, autostart, rootless containers, and VM disks retain user
   or workload ownership and separate status.
5. A local module, privileged development-container attachment, system unit, or
   boot-argument edit marks the realization locally modified.
6. Deployment fallback leaves user and workload code in place, so it cannot be
   called compromise recovery.

**Paper result:** Pass with an explicit limitation. Base OS identity remains
meaningful, but workstation-wide trust requires separate state and workload
evidence; no single `trusted` indicator is justified.

### Router (`router`)

1. Firmware and trust state remain platform inputs. OS-loaded microcode or NIC
   firmware is release-owned and belongs to deployment.
2. Modules, forwarding/firewall policy, network units, and any container or
   portable service implementing the base router role are release-owned.
3. Exact non-secret interface, route, firewall, and service policy is
   deployment-bound. Link presence, delegated addresses, leases, time, and
   credentials remain late-bound or machine inputs.
4. Persistent local rules, scripts, modules, or privileged containers mark the
   router locally modified; production may reject this state.
5. Fallback selects only a complete deployment and cannot silently load a
   mutable extension or ruleset.
6. Recovery does not activate persistent router configuration or credentials
   merely to inspect it.

**Paper result:** Pass. The actual manifest must confirm there are no hidden
mutable load paths.

## Adversarial scenarios

| Scenario | Expected result | Paper disposition |
| --- | --- | --- |
| Release `sysext` updated under mutable name | Cannot become selectable; identity must match selected deployment | Pass by governing rule |
| Admin adds a correctly signed out-of-tree module | Signature may authorize loading but not confer qualification; reject or mark locally modified | Pass by classification |
| User service survives rollback and relaunches malicious code | Base rollback succeeds but compromise is not claimed repaired; quarantine user state | Pass with explicit non-guarantee |
| Privileged router container follows `latest` | Forbidden for release-owned behavior; exact image and attachment policy belong in deployment | Pass by governing rule |
| Rendered config differs because a persistent fragment was omitted | Attribution fails; realization cannot report exact effective configuration | Pass by failure rule; discovery test required |
| Firmware changes while release artifacts remain identical | Deployment stays the same; platform support/trust status changes | Pass by separate status |
| Recovery discovers normal-state generators and units | They remain data until explicitly selected; mount does not authorize execution | Pass under EX-0003; test required |
| Runtime compiles policy from mutable data and caches it | Data and cache are executable inputs; unknown provenance blocks normal qualification for base behavior | Pass by generated-output rule |

## Conclusions

The exercise resolves DES-0001 C-003 and DES-0003 C-002 at the policy level:

- release ownership, not storage mechanism, decides deployment membership;
- all release-owned privileged inputs belong to the complete deployment
  identity;
- platform inputs remain explicit trust assumptions and observed status;
- administrator inputs are separately authorized and mark local modification;
- user and workload inputs retain independent lifecycle and status;
- exact base identity is never proof of an uncompromised complete machine; and
- recovery does not execute mutable inputs by default.

It does not prove completeness on a real system. A concrete inventory must
trace every loader, search path, generator, extension attachment, and persistent
executable namespace in both substrate candidates and the first VM,
workstation, and router artifacts.

## Follow-up evidence

1. Generate inventories from representative final artifacts and compare them
   with deployment-manifest closure.
2. Trace boot and runtime loaders for inputs outside declared locations.
3. Exercise classification transitions and verify separate deployment,
   platform, modification, workload, and compromise status.
4. Test release-owned extension, portable/container service, module, and
   generated configuration examples on both substrates.
5. Inject admin and user inputs, roll back the OS, and prove they neither
   inherit qualification nor disappear from status.
6. Boot recovery against hostile mutable state and prove inspection triggers no
   code, generator, automount, credential release, or service activation.
