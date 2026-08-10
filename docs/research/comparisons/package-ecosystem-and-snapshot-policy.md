---
id: RES-0007
title: Package ecosystem and snapshot policy comparison
status: in-review
date: 2026-08-10
decision_gates: [L-001, L-002, L-007]
---

# Package ecosystem and snapshot policy comparison

## Question

Should the initial NeutrinOS deployment variants consume Fedora stable or Arch
official packages, and what must “pinned package inputs” mean for either choice?

This comparison treats a distribution as an upstream package and maintenance
service. It does not adopt that distribution's installed-host lifecycle.

## Upstream facts

### Common feasibility

The upstream [mkosi project](https://github.com/systemd/mkosi) describes itself
as a wrapper around package managers including DNF and pacman. Both candidates
can therefore feed the same direct systemd/UAPI image-building experiment.
Package-manager support does not prove equivalent repository retention,
security response, script behavior, or artifact output.

### Arch

- The [Arch Linux Archive](https://wiki.archlinux.org/title/Arch_Linux_Archive)
  publishes daily snapshots of official repositories and retains individual
  package versions, with older content eventually moved to a historical
  archive. It explicitly warns against mixing archived and current mirrors.
- Arch's
  [system-maintenance guidance](https://wiki.archlinux.org/title/System_maintenance)
  states that partial upgrades are unsupported because the distribution is a
  rolling, coherently rebuilt package set.
- Official packages use the Arch package-signing hierarchy described in
  [pacman package signing](https://wiki.archlinux.org/title/Pacman/Package_signing).
- The [AUR](https://wiki.archlinux.org/title/Arch_User_Repository) contains
  user-maintained build recipes and explicitly leaves their update and review
  responsibility to the user. It is not an official binary-package tier.
- Arch documents ongoing, not universal, work toward
  [reproducible packages](https://wiki.archlinux.org/title/Reproducible_builds).

### Fedora

- Fedora publishes a new release approximately every six months and maintains
  it for approximately thirteen months according to the
  [Fedora release lifecycle](https://docs.fedoraproject.org/en-US/releases/lifecycle/).
- The [FESCo updates policy](https://docs.fedoraproject.org/en-US/fesco/Updates_Policy/)
  distinguishes Rawhide from stable releases, routes stable candidates through
  Bodhi/updates-testing policy, and generally discourages destabilizing ABI and
  user-experience changes on a stable branch.
- Fedora's
  [packaging guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/)
  require official-package dependencies to be satisfiable in official
  repositories, identify sources and patches in dist-git/source RPM material,
  and build without network access in the Fedora build system.
- Fedora's
  [reproducible-build documentation](https://docs.fedoraproject.org/en-US/reproducible-builds/)
  says source RPMs originate from dist-git recipes and hashed sources, while
  also documenting that distributed signed RPMs are not currently universally
  bit-for-bit reproducible under the strict definition.
- Fedora's default package verification checks package signatures. Repository
  metadata identity and long-term retention still need an explicit NeutrinOS
  boundary; signature validity alone does not prevent freeze or rollback to old
  valid content.

RPM Fusion and AUR are not symmetric. RPM Fusion is a separately governed
binary RPM repository; AUR is a recipe collection. Neither automatically
inherits the official distribution's maintenance, provenance, or qualification
claims merely because its normal tooling can consume it.

## Semantic comparison

| Criterion | Fedora stable | Arch official snapshot |
| --- | --- | --- |
| Upstream change model | Bounded release branch plus stable updates | Continuously moving coherent rolling repositories |
| Security-fix isolation | Often permits a smaller branch-local input delta | Supported refresh normally moves to a newer whole repository state |
| Feature currency | Current but bounded by branch policy and exceptions | Usually close to current upstream |
| Historical repository view | NeutrinOS should preserve exact metadata and bytes; do not assume permanent dated public snapshots | ALA provides dated official-repository snapshots, subject to retention/archive behavior |
| Major transition | Explicit Fedora N-to-N+1 qualification before EOL | Continuous snapshot-to-snapshot transitions; occasional large ecosystem rebuilds |
| Package recipe/source attribution | Source RPM plus dist-git and build-system records | PKGBUILD/package sources and Arch build records |
| Third-party temptation | RPM Fusion, COPR, upstream RPMs | AUR recipes and upstream binaries |
| Owner familiarity | Newer operational model for Jason | Existing long-term familiarity |
| Private overlay pressure | Risk when a stable branch lacks new systemd/kernel features | Risk for AUR-only software and custom kernels |
| Urgent regression surface | Usually branch-local, but not guaranteed small | Potentially all changes since the last qualified snapshot |
| Upstream EOL | Explicit, frequent deadline | No release EOL; old snapshots become stale without an independent maintained branch |

## What a snapshot must mean

A package input snapshot is not merely a date or package manifest. It contains
or immutably references:

- distribution, branch/release, architecture, repositories, priorities, and
  dependency/weak-dependency policy;
- exact repository metadata bytes and digests used by the solver;
- trusted repository/package key identities and verification results;
- the complete resolved binary package closure and exact content digests;
- source package or recipe identities, patches, and available build references;
- solver and package-manager identities plus the resolution transaction;
- project-built and third-party inputs with their separate provenance; and
- retention locations sufficient for offline reconstruction.

The snapshot identity changes if any of these semantic inputs changes. A newer
security assessment can change currentness or support status without changing
the historical snapshot identity.

## Security response comparison

For Fedora, normal response can advance the stable update repository state,
resolve a fresh whole closure, show the package delta, build, and qualify a new
NeutrinOS release. A core rebase or branch migration remains a larger declared
event.

For Arch, normal response advances to a coherent newer archive/repository
state, resolves the entire closure, and qualifies all resulting changes.
Selecting only the fixed package from a newer date while retaining the old
closure contradicts Arch's supported partial-upgrade model unless NeutrinOS
accepts ownership of that derived package universe.

Neither candidate removes NeutrinOS's responsibility to determine whether the
vulnerable code is present and reachable, produce exact artifacts, and run the
minimum emergency gate.

## Third-party boundary

The safe common policy is more important than the repository brand:

```text
third-party recipe or binary repository
        -> finite declared candidate
        -> source/license/maintainer review
        -> pinned literal inputs
        -> isolated build or explicit binary-only exception
        -> NeutrinOS intake identity and provenance
        -> role qualification
```

Blanket enabling is convenient but makes every future repository change an
implicit build input. Per-package intake costs more initially and exposes the
real maintenance owner. EX-0009 must measure whether the number of required
exceptions makes that boundary impractical.

## Recommendation

Use Fedora stable as the leading initial candidate because its maintained
branch and staged-update model better bound security-response churn for a
single maintainer. Preserve exact metadata and packages in a NeutrinOS intake
snapshot because Fedora branch policy is not a historical byte-retention
service.

Keep Arch as a mandatory challenger. Arch should replace Fedora if the literal
reference closures show that Fedora's older components, release migrations, or
third-party/private-overlay count outweigh the cost of qualifying coherent
rolling snapshots.

Do not accept either candidate before EX-0009. Regardless of the result, accept
the same immutable input, source-classification, isolation, currentness, and
retention requirements.

## Evidence still required

- Exact required package/capability closures for VM, workstation, and router.
- Actual input and resulting image sizes.
- Thirty-day representative churn or an equivalent historical sample.
- One routine and one urgent security-fix transaction per candidate.
- Fedora branch-rebase and Arch large-transition qualification estimates.
- Third-party and project-owned package inventories.
- Offline reconstruction after all network repositories are disabled.
