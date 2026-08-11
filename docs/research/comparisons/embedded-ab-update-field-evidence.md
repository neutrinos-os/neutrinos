---
id: RES-0014
status: complete
last_updated: 2026-08-11
evidence_cutoff: 2026-08-11
decision_gates: [S-004, L-003, L-004]
---

# Embedded A/B updater field evidence

## Question

The update substrate is already selected: SYS-030 and RES-0002 put NeutrinOS on
the systemd/UAPI path, and RES-0001 found no justification for building a new
one. **This comparison reopens none of that.**

It asks a narrower question. RAUC, SWUpdate, Mender, Ubuntu Core, ChromeOS, and
Android have collectively shipped A/B updates to very large numbers of devices
that lose power at inconvenient moments and cannot be recovered by hand. What
did they learn about staging, interruption, capacity, and recovery that
NeutrinOS would otherwise learn by discovering it?

The output is a list of failure modes to design against and to inject in the
storage spike, not a mechanism recommendation.

## Evidence limitations

Read them before using anything below.

- **This is documentation-derived, not measured.** Nothing here was reproduced
  on our hardware. Every item is a claim by a project about its own behavior.
- **Most of these systems target embedded bootloaders** -- U-Boot, Barebox,
  SoC ROM code -- not UEFI with systemd-boot. Several mechanisms have no
  transferable form, and a few of the sharpest lessons are *about* bootloader
  environment storage that UEFI handles differently.
- **None of them combine dm-verity with signed configuration extensions**, so
  the confext half of the C-013 decision has no prior art here.
- Project claims about their own atomicity were not independently verified and
  are recorded as claims.

## What transfers

### Mark the target ineligible before writing the first byte

RAUC's documented order is: verify the bundle, **mark the target slots
non-bootable**, then write. The marking precedes the write so that an
interruption mid-write cannot leave a partially written slot that the
bootloader still considers a candidate.

DES-0006's staging sequence protects the booted deployment and verifies the
staged bytes while they remain unselected, but it does not say that the target
is made explicitly ineligible *before* writing begins. On a fresh disk that
distinction is invisible; on a second update, the inactive slot still holds the
previous eligible deployment, and the first byte written destroys it while its
eligibility marker may still stand.

**Directly relevant to C-001.** This is a concrete ordering fix, cheap to
adopt, and independently worth a failure injection.

### Boot-selection state must not live inside the thing it selects

RAUC states the constraint plainly: persistent state for fallback logic must be
stored **outside the bootloader partition**, or updating the bootloader
destroys the state that decides what boots.

NeutrinOS's boot counting is planned through systemd-boot's native mechanism,
which encodes counters in **filenames on the ESP** -- the same filesystem that
holds the UKIs being counted, the bootloader itself, and the firmware fallback
path. That is a single FAT filesystem holding artifacts, selection state, and
recovery entry point at once.

This is not an argument to change mechanism. It is an argument that ESP
corruption and ESP-full are first-class failure cases for us in a way they are
not for a system with counters in a redundant U-Boot environment, and that the
XBOOTLDR question in DES-0006 has a failure-isolation dimension the design
currently frames mostly as capacity.

**ChromeOS is the contrasting design worth knowing**: priority, tries, and
successful flags live in **GPT partition attributes**, not in a filesystem.
Firmware picks the highest-priority kernel partition, requires
`successful == 1` or `tries > 0`, and demotes priority to 0 when both reach
zero. Selection state therefore survives filesystem damage on the thing being
selected.

### Updating the bootloader is the irreducible single point of failure

Every project says some version of this. SWUpdate: bootloader update is
"generally a one-way process and highly hardware-specific"; if it breaks, the
board does not boot. RAUC: the selection mechanism cannot itself be redundant.

RAUC's mitigations are prior art worth knowing even though they are
partition-table tricks rather than UEFI mechanisms: switching an **MBR or GPT
first-partition entry between two halves of a reserved region** to make an ESP
or boot-partition replacement atomic, and writing the unused of two fixed
locations first where SoC ROM code scans in a defined order.

DES-0006 treats bootloader update as an "exceptional" operation and says little
else. That is the right instinct and an insufficient design.

### Verify by reading back, not by trusting the write

SWUpdate recommends SHA-256 verification per artifact and calls the CPIO CRC
check weak. Android goes further: after an A/B update, `update_verifier` **reads
every block of the dm-verity devices** before marking the slot successful,
rather than waiting for a user's first access to a bad block.

For NeutrinOS this sharpens DES-0006's "verify literal identities and root hash
while they remain unselected" into something specific and testable: a full
verity read of the staged `/usr` image, not just a digest of what was
transferred. The distinction matters exactly when storage is failing, which is
the case the check exists for.

### Small storage forces an honest choice between fallback and retry

SWUpdate's two strategies are the clearest statement of the capacity trade:

- **Double-copy (A/B)** always leaves a working copy, and requires each copy to
  be under half of available storage.
- **Single-copy** runs the updater from RAM and rewrites in place. It guarantees
  the system can **retry** an update, not that it can **fall back** to the
  previous version.

The router's ~16 GB system disk is exactly where this bites, and EX-0008 leaves
two physical layouts in competition. The lesson is not "pick single-copy" -- it
would contradict SYS-050 -- but that if two complete `/usr` slots plus recovery
plus reserve do not fit, the alternatives are a bigger disk or a weaker
guarantee, and no clever layout produces a third option.

SWUpdate's related caveats: streaming installs avoid temporary copies but
remove the safeguard of validating a complete artifact before touching storage,
and it explicitly recommends **not** streaming the bootloader.

### Rollback needs a loop breaker

Mender persists update state in a key-value database across reboots and carries
a `state_data_store_count` specifically to **detect state loops** and force
termination into a failure state rather than rebooting forever.

DES-0006 has boot-attempt exhaustion selecting an eligible fallback, but no
concept of a system oscillating between two deployments that each fail
assessment differently, or of a rollback that itself fails to complete. A
bounded, attributable dead end is a requirement, not a nicety.

Mender also **refuses to commit** when its `upgrade_available` flag is not what
a successful new-slot boot would have left, which is a cheap sanity check that
the reboot went where the update intended.

### Recovery is a separate storage problem, not just a separate authorization

SWUpdate: updating the updater is only safe with two copies of it, and a rescue
system should live on **separate storage**. This is the same failure domain
C-011 already challenges DES-0006 on, arrived at independently from field
experience.

Ubuntu Core's `recover` mode is the most interesting precedent for us. It boots
a recovery system into an **ephemeral tmpfs** and copies only a narrow,
enumerated set of values -- network configuration and `etc/machine-id` -- from
the host's data partition, rather than mounting that partition into the
recovery environment. It also keeps an `ubuntu-save` partition that persists
across refreshes and factory reset.

That is close to an existence proof for the shape C-013 just committed us to:
per-machine identity as a small enumerated set projected into a regenerated
`/etc`, and recovery that reads named values instead of trusting a state
volume. It is worth studying under **L-003** rather than being reasoned about
from first principles.

### Boot-time verification that the machine booted what was selected

Ubuntu Core marks a new kernel or base as a "try" in `modeenv`, and on the next
boot snapd **compares the snap actually booted against the expected one**,
treating a mismatch as a failed installation rather than as success.

This is DES-0006's step 6 -- independently bind the actual UKI, root, and Verity
bytes to the selected deployment identity -- implemented in a shipping system,
and confirmation that the step is load-bearing rather than paranoid.

## What does not transfer

- **Bootloader environment redundancy** (`CONFIG_ENV_OFFSET_REDUND`, EFI Boot
  Guard's redundant copies, Barebox `bootchooser` state) has no direct UEFI
  analogue in our path. The underlying requirement -- selection state written
  atomically and stored redundantly -- does transfer, and we currently satisfy
  it with FAT filenames.
- **eMMC boot-partition and SoC ROM scanning tricks** are irrelevant to x86
  UEFI hardware.
- Mender's and RAUC's **server and campaign models** are out of scope; fleet
  rollout is RES-0009's subject.
- Ubuntu Core's **snap packaging model** is not under consideration; only its
  boot state machine and recovery-mode data handling are cited here.

## Consequences for NeutrinOS

Proposed additions to the storage spike's failure matrix, none of which the
current DES-0006 verification list covers:

1. Interrupt a write to the inactive `/usr` slot **after** the previous
   deployment in that slot has been partially overwritten, and confirm the slot
   is ineligible rather than merely stale.
2. Corrupt or fill the ESP and confirm that boot counting, fallback selection,
   and recovery entry degrade attributably rather than jointly.
3. Read back the complete staged verity device before blessing, and inject a
   bad block that a digest-of-transfer check would miss.
4. Force a deployment that boots but fails assessment on **both** slots and
   confirm the system reaches a bounded, attributable dead end instead of
   oscillating.
5. Exercise the router capacity case with two complete `/usr` slots, recovery,
   and reserve, and record whether the honest outcome is a larger disk or a
   weaker retained-fallback guarantee.

Proposed design responses, for the owner rather than taken here:

- Add explicit target-ineligibility marking before staging writes to DES-0006's
  staging sequence (C-001).
- Give bootloader update its own design treatment rather than the word
  "exceptional" (C-011 adjacent).
- Add a rollback loop breaker with an attributable terminal state.
- Reframe the XBOOTLDR question to include failure isolation, not only capacity.
- Study Ubuntu Core `recover` mode under L-003 as prior art for projecting a
  narrow enumerated identity set into a regenerated `/etc`.

## Sources

- [RAUC](https://rauc.io/) update procedure, slot groups, bootloader interaction
- [SWUpdate](https://sbabic.github.io/swupdate/) double/single-copy strategies,
  bootloader environment atomicity, streaming caveats
- [Mender](https://mender.io/) state machine, state-loop detection, commit
  refusal semantics
- [Ubuntu Core / snapd](https://github.com/canonical/snapd) `modeenv` try
  state, rollback detection, `recover` and `factory-reset` modes, `ubuntu-save`
- [ChromiumOS disk format](https://www.chromium.org/chromium-os/developer-library/reference/device/disk-format/)
  GPT kernel priority/tries/successful attributes
- [Android A/B updates](https://source.android.com/docs/core/ota/ab/ab_implement)
  boot control HAL, `update_verifier` full verity read before marking success
