---
id: EX-0007
title: Native configuration and inspection walkthrough
status: complete
date: 2026-08-09
exercise_type: sanitized configuration translation and composition tabletop
evidence_class: local-experience plus analysis-only
related_designs: [DES-0005]
---

# Native configuration and inspection walkthrough

## Purpose and evidence limit

This exercise tests the fleet-intent representation accepted by ADR-0003 against
representative configuration from the current private `nixconfig` checkout.
It asks whether useful intent can remain mostly upstream-native while source
metadata, scope precedence, conflict handling, and inspection stay explicit.

The checkout was inspected locally on 2026-08-09. Secret files were not opened.
Literal public keys, MAC addresses, private addresses, filesystem UUIDs, domain
names, and device assignments are omitted or replaced with obviously
illustrative values. The examples are design fixtures, not runnable NeutrinOS
configuration and not accepted storage or network policy.

## Current-intent observations

The checkout divides imperfectly but recognizably along the accepted scopes:

| Current source | DES-0005 interpretation | Representative intent |
| --- | --- | --- |
| `archetypes/defaultconfig.nix` | Common | systemd-boot policy, baseline packages, SSH, resolved, networkd, locale/time, operator account |
| `archetypes/server.nix` | Shared role source | headless service and secret-consumption policy |
| `systems/router.nix` | Router role plus router machine intent | forwarding, DNS, network topology, firewall, watchdog, services and timers |
| `hardware/router.nix` | Machine realization mixed with discovered state | modules, filesystems, swap, architecture, generated UUID bindings |
| `lib/networking/*.nix` | Project-specific renderer/module library | WAN naming, VLANs, LAN addressing, DHCP, prefix delegation, networkd output |
| `configs/router.nft` | Upstream-native input | nftables policy |

Two observations directly support DES-0005:

1. a networkd setting unavailable through the then-current NixOS module was
   supplied through an `extraConfig` escape; and
2. the router topology required custom typed Nix modules and transformation
   functions before producing native networkd files.

The intended settings remain useful. Requiring a new NeutrinOS option and
renderer for each of them would reproduce the schema-lag problem. The accepted
translation keeps literal networkd, unit, timer, sysctl, module, and nftables
configuration native. Small bounded data is used only where NeutrinOS itself
owns repeated intent or must compose values across scopes.

## Representative authored records

The record boundary accepted by ADR-0003 follows the RES-0005 proposal. A
shortened router machine record is still ordinary data:

```toml
schema = "urn:neutrinos:schema:machine-record:v0"
machine_name = "router"
role = "router"

configuration_sources = [
  "machine/router-interface-intent",
  "machine/router-storage-intent",
  "machine/router-out-of-band-policy",
]

late_bound_contracts = [
  "router-interface-observation",
  "router-provider-delegation",
  "router-service-credentials",
  "router-normal-unlock-capability",
]

state_contracts = [
  "router-machine",
  "router-protocol",
  "router-operational-evidence",
]

health_policy = "router-external"
deployment_policy = "router-cautious-current"

[enrollment]
policy = "physical-owner-plus-out-of-band"
identity_reference = "unassigned"

[platform]
architecture = "x86-64"
allowed_classes = ["x11sdv-4c-tp8f"]
required_capabilities = [
  "uefi",
  "ipmi-device",
  "runtime-watchdog",
  "unattended-normal-reboot",
  "offline-fallback-control-path",
]
```

The role record supplies generic router sources and supported platform classes;
the machine record does not repeat them. The value `unassigned` is a bounded
enrollment state in this illustration, not a machine credential or authority
to enroll.

## Native source manifest

One source-level manifest supplies unambiguous defaults and an exact file list:

```toml
schema = "urn:neutrinos:schema:configuration-source:v0"
name = "machine/router-interface-intent"
scope = "machine"
owner = "neutrinos-release"
consumer = "systemd-networkd"
interpretation = "systemd-networkd-native-v1"
files_root = "files"

files = [
  "usr/lib/systemd/network/10-router-wan.link",
  "usr/lib/systemd/network/20-router-wan.network",
  "usr/lib/systemd/network/30-router-switchteam.netdev",
  "usr/lib/systemd/network/40-router-lan.network",
]
```

Each listed file maps to the same target-relative path below the immutable
root. No owner, consumer, target, or mode is repeated per file. The default
regular-file mode is project policy and appears in resolved output. A symlink,
non-default mode, alternative target, or explicit removal requires an
exceptional object declaration and is visible in review.

The containing Git revision pins co-located files. The authored manifest does
not require a maintainer to paste new digests after every edit; the composition
record hashes all four files and binds the exact revision.

## Literal native inputs

The following sanitized files show the intended authoring surface. Ellipses
and angle-bracket values make these documentation fixtures, not valid build
inputs.

### Kernel and module policy

```ini
# usr/lib/sysctl.d/60-neutrinos-router.conf
net.ipv4.conf.all.forwarding = 1
net.ipv6.conf.all.forwarding = 1
net.core.rmem_max = 4194304
net.core.wmem_max = 4194304
net.netfilter.nf_conntrack_acct = 1
```

```ini
# usr/lib/modprobe.d/60-neutrinos-router-watchdog.conf
options ipmi_watchdog timeout=180
```

These are literal upstream settings. NeutrinOS records their source and exact
destination and applies role policy, but does not create parallel fields for
each sysctl or module parameter.

### Network topology

```ini
# usr/lib/systemd/network/10-router-wan.link
[Match]
PermanentMACAddress=<declared-wan-device-identifier>

[Link]
Name=wan0
```

```ini
# usr/lib/systemd/network/20-router-wan.network
[Match]
Name=wan0

[Link]
RequiredForOnline=routable
RequiredFamilyForOnline=both

[Network]
DHCP=yes
DHCPPrefixDelegation=yes
IPv4Forwarding=yes
IPv6Forwarding=yes
IPv6AcceptRA=yes
IPv6PrivacyExtensions=yes
LLDP=yes
LLMNR=no
MulticastDNS=no

[DHCPv4]
SendRelease=no
UseDNS=no
UseDomains=no
UseHostname=no
UseNTP=no

[DHCPv6]
PrefixDelegationHint=::/60
RapidCommit=yes
SendRelease=no
UseDNS=no
UseDomains=no
UseHostname=no
UseNTP=no
```

`IPv6PrivacyExtensions=` illustrates the central escape requirement: a
supported networkd key reaches output and qualification without waiting for a
NeutrinOS convenience schema. Interface observation may satisfy the declared
mapping, but it cannot choose the router role or invent another mapping.

The networkd manual states that `.network` files are processed
[in alphanumeric order and only the first match is applied](https://github.com/systemd/systemd/blob/main/man/systemd.network.xml).
Consequently, distinct matching files are a semantic interaction even when
their destinations differ. The named consumer policy must check ordered match
fixtures; generic file-collision detection is insufficient.

### Service and timer

```ini
# usr/lib/systemd/system/neutrinos-router-firewall.service
[Unit]
Description=Load the qualified router firewall policy
After=network-online.target
Requires=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/nft --file /usr/lib/neutrinos/router/firewall.nft
ExecReload=/usr/sbin/nft --file /usr/lib/neutrinos/router/firewall.nft
ExecStop=/usr/sbin/nft delete table inet router_firewall

[Install]
WantedBy=multi-user.target
```

```ini
# usr/lib/systemd/system/neutrinos-blocklist-update.timer
[Unit]
Description=Refresh the qualified DNS blocklist input

[Timer]
OnCalendar=00/4:00
RandomizedDelaySec=10m
Persistent=yes

[Install]
WantedBy=timers.target
```

The executable and nftables policy must already be package or release-owned
artifact inputs. The unit is not allowed to download and execute a mutable
program. Whether the blocklist itself is release-owned content or late-bound
service data remains a separate ownership decision; the timer does not answer
it.

Systemd unit drop-ins are merged after the main unit and
[applied in lexical order](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml).
Distinct drop-ins can therefore remain native, but their exact names and
reset/append semantics are part of the consumer policy and qualification.

### Users, volatile paths, mount, and kernel command line

```text
# usr/lib/sysusers.d/neutrinos-observer.conf
u! _neutrinos-observer - "NeutrinOS lifecycle observer" /var/lib/neutrinos /usr/sbin/nologin
```

```text
# usr/lib/tmpfiles.d/neutrinos-observer.conf
d /var/lib/neutrinos/diagnostics 0750 _neutrinos-observer _neutrinos-observer - -
d /run/neutrinos              0755 root                  root                  - -
```

```ini
# usr/lib/systemd/system/var-lib-neutrinos.mount
[Unit]
Description=Illustrative NeutrinOS machine-state mount

[Mount]
What=/dev/disk/by-partlabel/<illustrative-machine-state>
Where=/var/lib/neutrinos
Type=<filesystem-selected-by-DES-0002-and-S-004>
Options=nodev,nosuid
```

The mount unit is only a configuration fixture. It deliberately does not
select a filesystem, partition label, encryption boundary, or final state
layout ahead of S-004.

```text
# build input: kernel command-line token set, rendered into the qualified UKI
quiet rd.systemd.show_status=auto systemd.show_status=auto
```

The kernel command line is a complete build input, not a set of boot-time
fragments assembled from SMBIOS or metadata. A higher scope replaces the
resolved token set through a bounded typed input; the exact final bytes are
bound into the UKI and deployment identity.

Tmpfiles uses the lexicographically earliest file for a duplicated path and
logs other conflicts as errors, while sysusers likewise uses the earliest
entry for a duplicated user or group name. These are documented in the
upstream [tmpfiles](https://github.com/systemd/systemd/blob/main/man/tmpfiles.d.xml)
and [sysusers](https://github.com/systemd/systemd/blob/main/man/sysusers.d.xml)
manual sources. A machine override therefore cannot be implemented by blindly
adding a later file. NeutrinOS must replace a complete lower-scope output,
apply an explicit tombstone, or reject the semantic conflict.

## Scope and conflict fixtures

### Scalar drop-in composition

A common journald source supplies a fleet storage ceiling, the router role
narrows it, and the machine narrows it again for its physical disk budget:

```text
common  -> usr/lib/systemd/journald.conf.d/20-neutrinos-common.conf -> SystemMaxUse=2G
role    -> usr/lib/systemd/journald.conf.d/60-neutrinos-router.conf -> SystemMaxUse=512M
machine -> usr/lib/systemd/journald.conf.d/90-router.conf            -> SystemMaxUse=384M
```

The systemd configuration-file policy is explicitly named, and the filenames
align its later-wins scalar behavior with `common < role < machine`. The
composition record retains all three values and the effective native output.
Post-composition policy still rejects a value below the diagnostic-retention
minimum.

### Complete-file replacement

If common and machine sources both declare the same complete destination, the
machine file replaces the common file before native validation. Two sources in
the same scope declaring that destination fail unless their consumer policy
explicitly defines a native merge. File traversal order never breaks the tie.

### Explicit removal

```toml
[[operations]]
operation = "remove"
output = "file:/usr/lib/systemd/system/neutrinos-optional-observer.service"
reason = "router role uses external availability observation"
policy = "optional-observer-removal"
```

The operation is a first-class tombstone. Omitting the common source from a
machine record does not delete it, and an empty string or boolean is not
interpreted as deletion. Policy decides whether the named output is removable.

### Rejected same-scope native interaction

Two router-role tmpfiles files declaring `/run/neutrinos` are rejected even if
the lines happen to agree: upstream earliest-file behavior is not an approved
same-scope merge policy. The diagnostic names both source records, both files,
the semantic key, and the upstream interpretation rule.

## Consumer interpretation matrix

| Consumer/input | Native interaction that matters | Composition rule | Validation evidence |
| --- | --- | --- | --- |
| systemd unit/drop-in | main file plus lexical drop-ins; scalar replacement and list reset/append vary by directive | Complete-path scope replacement; distinct drop-ins remain native under named policy | `systemd-analyze verify`, rendered unit inspection, boot test |
| systemd-networkd | first matching `.network`; lexical files and drop-ins | Exact paths plus overlap/match fixtures; no generic last-wins claim | native parse/reload checks and modeled-interface tests |
| sysctl.d | later assignments can replace earlier scalar values | Filename policy may align scopes; duplicates remain visible | parse plus expected effective-setting test |
| tmpfiles.d | earliest duplicate path applies; others error | Replace/tombstone one complete output or reject duplicate semantic path | dry-run/image-root validation and boot test |
| sysusers.d | earliest duplicate user/group applies; later entries warn | Reject duplicate semantic identity unless one complete output replaced | dry-run/image-root validation and account-state test |
| nftables | ruleset has its own parser and transaction semantics | Treat policy as literal complete native input unless a separate design proves safe composition | `nft --check` plus namespace/VM traffic tests |
| mount unit | unit and dependency semantics plus storage availability | Complete unit or explicit drop-ins; state contract and S-004 gate remain authoritative | unit verification, image boot, failure/recovery tests |
| kernel command line | token ordering, duplication, and UKI binding affect boot policy | Resolve one typed token set before build; never append from boot metadata | policy validation, UKI inspection, measured boot and negative boot tests |

The matrix is intentionally consumer-specific. “Native” means upstream owns
interpretation, not that NeutrinOS can skip conflict analysis or integrated
qualification.

## Inspection walkthrough

The final command spelling is not selected, but the operator interaction must
support these stable queries.

### Machine summary

```text
$ neutrinos intent show router
inventory:  <revision>
machine:    router
role:       router                     source: machines/router.toml
platform:   x11sdv-4c-tp8f             source: machines/router.toml
sources:    3 common, 3 role, 3 machine
result:     <resolved-configuration-identity>
policy:     pass
```

### Setting to output

```text
$ neutrinos intent explain router --setting systemd.journald.SystemMaxUse
winner:     384M
source:     machine/router-storage-intent
input:      journald.toml:SystemMaxUse
precedence: machine > role > common
overrode:   512M (role/router-availability)
            2G   (common/system-baseline)
policy:     diagnostic-retention-minimum: pass
rendered:   /usr/lib/systemd/journald.conf.d/90-router.conf
```

### Output to sources

```text
$ neutrinos intent trace-output router /usr/lib/systemd/network/20-router-wan.network
consumer:      systemd-networkd
interpretation: systemd-networkd-native-v1
winner:        machine/router-interface-intent
source-bytes:  <digest>
rendered-bytes:<digest>
validators:    native syntax pass; interface fixtures pass; router policy pass
```

### Revision diff

```text
$ neutrinos intent diff router <old-revision> <new-revision>
desired record: unchanged
native files:   20-router-wan.network changed
semantic note:  IPv6PrivacyExtensions added
resolved id:    <old> -> <new>
deployment:     requires build, qualification, and authorization
```

The full immutable composition record can be large; these queries are
projections over it, not a mutable database or a replacement for native
diagnostics.

## Adversarial findings

1. **The metadata burden is bounded at source level.** The representative
   network source needs six declarations plus one exact file list, not repeated
   metadata for every native key.
2. **Literal native configuration removes the schema-lag failure.** The
   networkd escape setting is attributable and testable without a new project
   option.
3. **Native does not mean composable by concatenation.** Networkd, unit
   drop-ins, tmpfiles, and sysusers have materially different ordering and
   collision rules.
4. **Fixed NeutrinOS precedence needs two mechanisms.** Complete output
   replacement and tombstones use project scope semantics; distinct native
   objects use an explicit consumer interpretation policy.
5. **A small renderer remains justified.** Repeated project-owned scalar intent
   and resolved package paths may require bounded generation, but the renderer
   is owned implementation and its exact output is visible.
6. **Inspection can be useful without a universal schema.** A native file can
   be traced by destination and digest even when individual upstream keys are
   not represented in project data.
7. **The example exposes unresolved ownership.** Downloaded blocklists,
   generated lease data, interface bindings, storage identifiers, and unlock
   material still need explicit release, machine, environment, or protocol
   owners. Serialization must not decide those questions accidentally.

## Exercise disposition

DES-0005's native-input, metadata-default, conflict, tombstone, and bidirectional
inspection claims pass at the paper level for the representative router intent.
The exercise does not validate a parser, schema, canonicalizer, renderer, or
native output and does not prove the physical router behavior.

The remaining representation work is a bounded implementation spike using a
non-sensitive fixture corpus. Authenticated first enrollment remains separate
under L-003.
