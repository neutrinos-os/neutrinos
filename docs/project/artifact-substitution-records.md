---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-10
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# Negative evidence for the `/usr` artifact

PLN-0002-10. **Independently valid, correctly signed release members substituted
into an authenticated artifact, with the mechanism that rejected each one and
the diagnostic that names it recorded per cell.** Seven cells per arm, each
booted under two firmware states: 32 boots, two arms, one tree state.
**Accepted 2026-08-15 by Jason Tarasovic**, with the carried risks at the foot
of this document accepted as part of it.

This is the plan's last measurement task and the only remaining one that could
move C-007. **It does not move it**: every result below is identical on EROFS
and ext4, down to the wording of the diagnostics. Substitution behaviour is a
property of dm-verity, the GPT identity scheme and systemd's activation path,
and the filesystem inside the image contributes nothing to it. Four of C-007's
eight criteria now separate the arms not at all.

**This record recommends nothing.** PLN-0002-13 answers C-007.

Figures are in `$NEUTRINOS_SLICE_BUILD_ROOT/evidence/pln0002-10/substitution.json`
with the console of all 32 boots retained beside it under `serial/`, written by
`src/slice/measure-substitution.py`.

## The prediction this task was given, and what happened instead

The plan predicted this task would fail open. Half of that prediction is wrong
and the half that is right is worse than it was stated.

**Every image substitution failed closed.** All eight — a valid `/usr` and its
Verity tree together, in both the content and identity shapes, and each of the
two alone — stopped in the initrd and reached `emergency.target` with `/usr`
unmounted. Under both firmware states, on both arms. Nothing reached userspace,
so nothing ran off a substituted image.

**Every signature substitution failed open.** All six — a valid signature by an
unenrolled authority, and a valid signature by the *enrolled* authority over a
root hash that is not this image's — booted to `running` with zero failed
units. Under both firmware states, on both arms. This is the new result and it
is stated precisely below, because "the signature is not enforced" is the
already-known finding and is not what was measured here.

## What was substituted

Donors are PLN-0002-06's content and seed variants: independently valid
artifacts, built from the same tree state, signed by the **enrolled** verity
key. That is PR-0030 C-004's requirement — a substitute that fails to mount
proves nothing, because it never reached the binding. A cell that boots here
means integrity failed to bind; it cannot mean a signature was missing.

| Cell | What moved | Everything else |
| --- | --- | --- |
| `baseline` | nothing | the unmodified primary |
| `pair-content` | the donor's whole disk -- `/usr`, Verity tree, signature partition, and their GPT identities -- under the primary's ESP and therefore the primary's signed UKI | -- |
| `pair-seed` | as above, from the seed variant: identical tree, different identity | -- |
| `usr-only` | the seed variant's `/usr` bytes, into the primary's slot under the primary's GPT identity | the primary's Verity tree and UKI |
| `verity-only` | the seed variant's Verity tree bytes, likewise | the primary's `/usr` and UKI |
| `sig-foreign` | the seed variant's signature partition: a valid enrolled-signer signature over a **different** root hash | the primary's image and UKI |
| `sig-wrong-key` | the primary's **own** root hash, re-signed by a second synthetic authority that is in no machine's `db` | the primary's image and UKI |
| `sig-rebuilt-enrolled` | the primary's own root hash, re-signed by the **enrolled** authority -- the control | the primary's image and UKI |

The control cell exists because this harness rebuilds the signature blob rather
than copying it, and its encoding is not byte-identical to `systemd-repart`'s:
repart reaches OpenSSL through its API and emits the SHA-256 `digestAlgorithm`
with an explicit NULL parameter where the command line omits it. Four bytes,
semantically identical, both verify. Without the control, a wrong-key cell that
behaved unusually could not be attributed to the signer rather than to those
four bytes. It behaves exactly as the artifact's own blob does.

**The identity being substituted lives in the GPT, not only in the bytes.**
`systemd-repart` derives the `/usr` partition UUID from the first half of the
root hash and the Verity partition UUID from the second half — visible in all
six artifacts, e.g. root hash `d0f7f411…be732d4d…` against UUIDs `D0F7F411-…`
and `BE732D4D-…`. So the pair cells substitute the donor's whole disk under the
primary's ESP rather than splicing donor partitions into the primary's table,
which would have silently retained the primary's identity in the field the
binding actually uses.

## Three mechanisms rejected the image, and each names itself

The plan asked for a diagnostic that discriminates a root-hash mismatch from a
signature failure from a mount failure. There are three, and they are distinct:

| Cell | Diagnostic | What rejected it |
| --- | --- | --- |
| `pair-content`, `pair-seed` | `Using data device /dev/disk/by-partuuid/d0f7f411-…` then `Dependency failed for sysroot-usr.mount` | **device resolution**. The initrd looks up the partition whose UUID the root hash names; on a donor disk it does not exist, so verity is never reached |
| `usr-only` | `device-mapper: verity: 253:2: data block 0 is corrupted` | **the root hash over the data** |
| `verity-only` | `device-mapper: verity: 253:2: metadata block 1 is corrupted` | **the root hash over the hash tree** |

All three end at `emergency.target` with `/usr` unmounted and the root account
locked, so the failure is terminal rather than degraded.

**The pair cells are rejected earlier than expected, and that is worth stating
plainly.** They fail at device lookup, not at verification: the UKI names a root
hash, the root hash names two partition UUIDs, and a substituted deployment
carries its own. The binding therefore holds *twice* — once through the GPT
identity scheme and once through verity — and only the first is exercised when a
whole deployment is swapped. `usr-only` and `verity-only` are the cells that
exercise the second, which is why they are in the matrix even though the pair
cells look like the more complete substitution.

## The signature is verified, and its verification is not a gate

This is the finding. It is not the same as the one already recorded under
`S-005`, and it is stronger.

Under **plain OVMF**, every boot — including the untouched baseline — logs
`Root hash verification failed` four times and boots anyway. The kernel refuses
a signature it has no key for and `systemd-veritysetup` retries without it. That
is the known fail-open, and on its own it reads as "the mechanism was not
configured".

Under the **enrolled firmware** the mechanism *is* configured and does work:
`integrity: Loaded X.509 cert 'NeutrinOS verity, synthetic'` appears in the
keyring and the `Root hash verification failed` messages are **gone**, on every
enrolled boot. Signed activation happens.

And under that same enrolled firmware:

| Cell | Signature | Result |
| --- | --- | --- |
| `sig-rebuilt-enrolled` | valid, enrolled signer, correct root hash | boots -- expected |
| `sig-wrong-key` | valid, **unenrolled** signer, correct root hash | **boots**, `running`, zero failed units |
| `sig-foreign` | valid, **enrolled** signer, **wrong root hash** | **boots**, `running`, zero failed units |

So the configuration question this task was told to settle has an answer, and it
is not the comfortable one. The signature is not merely unverified for want of a
key: **it is verified where it can be, and the outcome of that verification does
not gate anything.** An untrusted signer and a signature that covers a different
image both fall back to unsigned activation, silently, and the machine reports
success. Enrolling the signer changes which code path runs and changes no
outcome that this task can observe.

`sig-foreign` is the sharper of the two. A signature partition whose `rootHash`
field names an image that is not present, signed by the authority the firmware
trusts, is accepted into a normal boot.

**The enrolled arm is stronger than anything the artifact produces by itself,
and that has to be said or the result reads as milder than it is.** The six
artifacts ship their own auto-enrolment keys in the ESP — `PK.auth`, `KEK.auth`,
`db.auth` under `\loader\keys\auto`, from `SecureBoot=yes` — so on capable
firmware with a store in setup mode they enrol themselves. But that `db` carries
**only `CN=NeutrinOS image, synthetic`**, the UKI signer. The verity signer is
not in it. The enrolled arm here uses the `T4-CONFEXT-001` fixture, whose `db`
carries the image signer, the verity signer, and the platform key, and which
exists only because that check needed it.

So the configuration under which the signature is verified and still gates
nothing is a **better** configuration than any machine this artifact would reach
on its own. A machine that self-enrolled would sit in the plain arm's position —
signature refused for want of a key, unsigned fallback, boot — while looking
fully enrolled.

## Cells of C-001's cross product

C-001 requires a cross product, not a sample. What this task covers:

| Substituted member | Covered | By |
| --- | --- | --- |
| `/usr` image, same format, valid, enrolled signer | yes | `usr-only`, and `pair-*` at the identity layer |
| Verity tree, valid, enrolled signer | yes | `verity-only` |
| `/usr` + Verity as a valid pair, content differing | yes | `pair-content` |
| `/usr` + Verity as a valid pair, identity differing | yes | `pair-seed` |
| Verity signature, valid, wrong authority | yes | `sig-wrong-key` |
| Verity signature, valid authority, wrong root hash | yes | `sig-foreign` |
| Confext, valid, unenrolled signer | yes, signature dimension only | `T4-CONFEXT-001` |

What carries forward, uncovered:

- **UKI substitution.** A donor UKI on the primary's disk is not measured. It is
  the mirror of `pair-*` and is expected to fail at the same device lookup, but
  expectation is what this task exists to replace.
- **Slot label substitution, and every cell needing A/B slots.** PLN-0002 builds
  one slot per arm by design; no selection, staging, or finalization exists to
  substitute against.
- **Power loss before and after each finalization write**, which C-001 requires
  on every cell. Nothing here is interrupted; there is no finalization write in
  this plan to interrupt.
- **Physical roles**, and with them C-001's own residual risk — firmware-variable
  and FAT rename ordering, which a VM cannot settle.
- **The manifest.** See below.
- **Confext substitution on any dimension but the signature**: content, path
  ownership, and base compatibility are untested.

## The manifest cell has no boot, and that is the result

`neutrinos-slice.manifest` is a build sidecar. It is written beside the artifact
by mkosi, it is consumed by `retain-repository.py` and by the fixture build, and
**it is not on the disk**: not in the ESP, not in `/usr`, not in any partition of
any of the six artifacts. Nothing at boot reads it.

So there is no manifest-substitution boot to run. Substituting it changes no
byte the machine ever sees, which means the manifest is not an input to the
boot-integrity gate and cannot be made one by testing it. This is recorded as a
covered-by-reasoning cell rather than a measured one, and it is a real answer to
the plan's line item rather than an omission: **if the manifest is meant to be a
release-owned member under C-013, it is not currently delivered as one.** That is
a question for DES-0006 and it is not this task's to answer.

## What this record does not claim

- **No recommendation.** Four criteria now tie; one criterion, or four, does not
  decide C-007.
- **No claim about a configured enforcement point.** What was measured is the
  artifact as PLN-0002-06 froze it, under a `db` that trusts the verity signer.
  A NeutrinOS that wants a bad signature to fail closed must add that itself;
  where upstream puts it — the TPM unseal, not the mount — is `S-005` and out of
  this plan's scope.
- **No availability or recovery claim.** The eight image cells reach emergency
  mode. Whether that is the right terminal state, and what a machine should do
  from there, is PLN-0002-12.
- **Nothing about lazy verification.** The image cells fail at activation, before
  any read pattern matters. PLN-0002-09 owns the lazy-verification behaviour and
  its finding is unchanged.
- **No physical-role claim.** Disposable VMs, synthetic keys, plain OVMF and an
  enrolment fixture built in the build root.
- **No format claim.** Every cell behaved identically on both arms.

## Carried risks

- **The synthetic signing material expires 2026-09-11.** These boots are inside
  that window. Anything re-measured afterwards measures expired enrolment
  material.
- **The ParticleOS command-line ruling of 2026-08-12 is still open**, and
  settling it in its own favour rebuilds the artifact set and voids these
  records with the rest.
- **`T4-CONFEXT-001` remains unreachable through `mise run`**, because
  `sandbox.deny_env` strips its declared fixture directory. The confext cell
  above is covered by a check that has to be invoked directly.
