---
status: active
last_updated: 2026-08-11
governing_plan: PLN-0001
---

# Reference-VM slice evidence bundle

PLN-0001-08. The slice's records cite evidence spread across a build root, three
output directories, and validation run directories in a temporary path that a
reboot removes. This records what was gathered into one retained bundle, what
was deliberately left out, and how to rebuild anything the bundle only names.

The bundle is **not in the repository**. The hygiene contract's binary and 1 MiB
bounds bind here, so a bundle records identity and reconstruction rather than
bytes.

| Property | Value |
| --- | --- |
| Location | `~/.cache/neutrinos/slice/evidence/pln-0001-08/` |
| Size | 6310 KiB, 64 files |
| Collected at | 2026-08-11, source revision `34b9364` |
| Collector | `src/slice/collect-evidence.py` |
| Integrity | `MANIFEST.sha256`, one SHA-256 per file |
| Unsafe-output scan | Clean, zero findings |

## What it contains

- **`composition/`** — the declaration, its schema, and the mechanism as
  committed: `input-set.toml`, `compose.sh`, `mkosi.conf`,
  `retain-repository.py`. Plus the resolved 104-package manifest, the retention
  record, and the declared repository's `repomd.xml`. A record that cites these
  by path becomes unreadable the moment the checkout moves on.
- **`identity/`** — `digests.json` with every output digest from the networked
  build and the offline rebuild, the UKI read from each image's ESP, and the
  three extracted-tree manifests, gzipped.
- **`validation/`** — both canonical profile runs in full, results and logs:
  `fast` at 8 passing, `complete` at 12 passing, zero failing, zero blocked.
- **`index.json`** — the above as one machine-readable record, including the
  source revision and the scan result.

## What it does not contain, and why

Disk images, UKIs, kernels, and initrds are named by digest only. They are
reconstructible from the declared inputs, which is the claim the slice exists to
make; carrying 1.3 GiB per build to prove it would contradict the claim rather
than support it. The retained repository's 121 packages are likewise identified
by `retained.json` and the repository's own signed metadata. Extracted trees
are represented by their manifests, since the trees are derived from the images.
PLN-0001-06's fault injections keep their own bundle at
`evidence/pln-0001-06/`, 320 KiB, and are referenced rather than copied.

## Closing measurement: three builds, one tree

The bundle records one measurement not made before. The root filesystem was
extracted from three separately produced disk images:

1. the 2026-08-10 offline reconstruction (PLN-0001-07),
2. the 2026-08-11 networked build, with the package cache moved inside the
   build root, and
3. the 2026-08-11 offline rebuild resolving only from the retained repository.

All three trees are **byte-identical: 13240 entries, one shared manifest digest
`a47841ac...`**, across mode, ownership, symlink target, size, and per-file
content. Both images' ESPs carry the same UKI, `575c847d...`. The three `.raw`
digests differ, for the two reasons the
[composition record](slice-composition-record.md) identifies and neither of
which is reachable from configuration.

This is the strongest form of the slice's central claim available here: not that
one build is reproducible, but that the shipped tree is invariant across a
network-attached build and two offline reconstructions performed a day apart
from separately assembled inputs.

## Reconstructing what the bundle only names

```sh
# Artifact, with the network. Retention runs as part of it.
./src/slice/compose.sh --force build

# Artifact, with the network removed, from the retained repository.
./src/slice/compose.sh \
    --local-mirror=file://"$HOME"/.cache/neutrinos/slice/inputs/repository \
    --output-directory="$HOME"/.cache/neutrinos/slice/out-offline --force build

# Evidence, after both profiles have been run.
python3 src/slice/collect-evidence.py --build-root=... \
    --fast-run=... --complete-run=... --tree-manifest=... --destination=...
```

Tree extraction is not a committed tool. It is a byte-range copy of the root
partition followed by `btrfs restore` inside a user namespace, described in the
[reconstruction record](slice-reconstruction-record.md), which also states its
limits -- excluded timestamps and unattested `security.*` xattrs.

## What this bundle does not establish

- **Retention is not durability.** The bundle sits in one user's cache
  directory on one host. Nothing replicates it, and PLN-0001 makes no claim
  about evidence retention beyond the life of this build root. R-005's bound is
  respected by keeping identity rather than bytes; where the bytes must live
  long-term is not a question this slice answers.
- **A green profile is not qualification.** Twenty passing results across two
  profiles record that the checks the slice defines pass on this host. Three of
  the requirements they trace to are accepted at `Partial`, and the plan's
  candidate fixtures remain candidates.
- **R-007's disposition was met differently than written.** The risk asked for
  reconstruction "with the network removed and the cache cleared". The offline
  rebuild resolves from the retained repository, which is a cache in the
  mechanical sense -- but it is also the declared input, validated
  package-by-package against the declared repository's published index by both
  retention and `T3-SLICE-002`. What makes the result non-hollow is that
  validation, not an empty directory.
