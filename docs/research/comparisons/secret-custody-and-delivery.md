---
id: RES-0011
title: Secret custody and credential delivery comparison
status: draft
date: 2026-08-10
source_checked: 2026-08-10
related_designs: [DES-0011]
---

# Secret custody and credential delivery comparison

## Question

Which current mechanisms can protect, transport, and expose late-bound secret
values without becoming NeutrinOS's normal configuration language or requiring
an unjustified always-online control plane?

## Comparison boundary

No single candidate covers the full lifecycle. Evaluate five distinct jobs:

1. custody of plaintext or decryption authority;
2. authorization of an exact machine/consumer to receive an instance;
3. protected transport or at-rest envelope;
4. last-mile exposure to the intended process; and
5. rotation, revocation, recovery, and evidence.

## systemd system and service credentials

### Current upstream behavior

Systemd credentials are immutable binary data blobs exposed as files in a
per-service credential directory at activation. Access is restricted to the
service user; file-system namespacing can hide the directory from other units;
the data is released when the service stops; and systemd attempts to place it
in non-swappable memory. The documented aggregate limit is currently 1 MiB per
service.

Units can load values from files, AF_UNIX sockets, inherited system credentials,
or credential stores with `LoadCredential=`, `LoadCredentialEncrypted=`, and
`ImportCredential=`. `SetCredential=` literals are visible through unit
configuration and are unsuitable for secrets. Services receive the directory
through `$CREDENTIALS_DIRECTORY`; `%d` is available in unit configuration.

System credentials can arrive from a container manager, SMBIOS/fw_cfg for a VM,
the initrd, systemd-stub/UEFI boot environment, kernel command line, or cloud
metadata. These are transport possibilities, not equal trust sources. In
particular, plaintext kernel-command-line values are visible through
`/proc/cmdline`.

### Fit

- Best aligned default last-mile interface under ADR-0001.
- Binary-safe and avoids environment-variable inheritance.
- Activation lifetime and unit sandboxing improve consumer scoping.
- File and AF_UNIX sources allow local sealed storage or a future broker without
  changing the service interface.
- Works naturally for image-based services that should not read arbitrary host
  paths.

### Gaps and risks

- Does not define who may issue or retrieve a secret.
- Does not hide plaintext from root or the consuming process.
- Credentials are immutable during one activation, so rotation needs restart,
  reload, or an application-native channel.
- VM, boot, metadata, and kernel transports have different confidentiality and
  replay properties.
- A privileged common broker can defeat per-unit isolation.
- Generic credential data can become an unqualified configuration channel.

### Disposition

Leading last-mile service interface. It does not select a custody or authority
backend.

Sources:

- <https://systemd.io/CREDENTIALS/>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd.system-credentials.html>

## `systemd-creds` encrypted credentials

### Current upstream behavior

`systemd-creds` encrypts and authenticates credential data with AES-256-GCM.
Keys can derive from a local TPM2, `/var/lib/systemd/credential.secret`, or
both. When both are available the documented default combines them, binding
decryption to the hardware and installation. Decryption normally occurs at
service activation.

The documented null-key mode provides an envelope but no confidentiality or
authenticity. Boot acceptance depends on `systemd.credentials_boot_policy=`;
the upstream default is currently `relaxed`. This makes an explicit NeutrinOS
boot policy necessary rather than reliance on upstream defaults.

TPM-only early-boot credentials, host-key-only systems, PCR binding, and scoped
credential modes have different recovery and portability properties and must
not be collapsed into “encrypted with systemd.”

### Fit

- No additional daemon for local at-rest protection.
- Natural input to `LoadCredentialEncrypted=`.
- Host binding reduces usefulness of copied ciphertext and stolen storage.
- Supports placement in credential stores or appropriate boot locations.

### Gaps and risks

- Default host binding prevents preparation on a different machine.
- Loss of TPM state or the host key can make ciphertext unrecoverable.
- Ciphertext backup is not secret recovery unless the required key capabilities
  and policy are also recoverable.
- Null-key credentials are not protected and boot policy defaults may be too
  permissive.
- At-rest protection is not delivery authorization or revocation.

### Disposition

Leading local encrypted representation when exact recipient, boot policy,
recovery, and replacement semantics fit. Not a fleet envelope or secret
authority by itself.

Sources:

- <https://systemd.io/CREDENTIALS/#encryption>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd-creds.html>
- <https://systemd.io/BUILDING_IMAGES/>

## Administrative envelope with age and SOPS

Age is a small file-encryption format and tool based on explicit recipients and
identities. SOPS encrypts structured values with a data key protected by one or
more KMS/PGP/age recipients; current SOPS key groups can require recovery of
fragments from multiple groups.

### Fit

- Useful for reviewed, offline administrative custody and removable transfer.
- Recipient lists and SOPS key groups can express human or recovery custody.
- No always-online service is required.
- Encrypted material can be version-controlled if metadata disclosure,
  retention, history, and decryption scope are accepted.

### Gaps and risks

- Repository access plus a broadly authorized recipient can expose many values.
- Rotation and recipient removal require re-encryption and history analysis.
- Target-side decryption keys can become shared fleet authority.
- SOPS structured files and templates can invite secret-shaped configuration.
- Neither tool authenticates the local consuming unit or provides activation-
  scoped plaintext automatically.

### Disposition

Candidate administrative custody/offline transport, feeding a separately
authorized local sealing and systemd delivery step. Not selected as the fleet
configuration format or runtime secret interface.

Sources:

- <https://age-encryption.org/v1>
- <https://github.com/FiloSottile/age>
- <https://getsops.io/docs/>
- <https://getsops.io/docs/usage/identities/key-groups/>

## Online secret service and agent

Vault represents the broader class: a machine or agent authenticates to an
online authority, obtains static or dynamic secrets, renews leases, and may
render values to files. Vault Agent can auto-authenticate and its template
facility can fetch, renew, and write values.

### Fit

- Central authorization, revocation, audit, dynamic credentials, and short
  lifetimes can be stronger at scale.
- Automated renewal avoids long-lived static values.
- A narrow broker could source `LoadCredential=` through an AF_UNIX socket or
  stage encrypted data for systemd delivery.

### Gaps and risks

- Server and agent bootstrap, upgrades, backup, unseal/recovery, availability,
  trust, and credential custody are substantial new obligations.
- A shared privileged agent may see every local secret.
- Template rendering is a second configuration language and creates persistent
  files unless tightly constrained.
- Leases and renewal can make network/time/service availability part of role
  availability.
- Operating this for the initial fleet may be less safe than an attended flow.

### Disposition

Challenger only when concrete rotation, dynamic issuance, or fleet-scale needs
justify the control plane. A secret service must feed the same contract and
consumer boundary rather than replacing them.

Sources:

- <https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent>
- <https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent/template>

## Application-native and workload identity

Many protocols can create or renew keys/certificates without handing a static
bearer secret to a daemon. SPIFFE is relevant prior art: its Workload API
streams X.509/JWT identities and trust bundles to locally identified workloads,
with updated full responses used for rotation and revocation propagation.

### Fit

- Separates workload identity from host-wide static files.
- Short-lived, renewable credentials and local caller identification can reduce
  retained plaintext and blast radius.
- An application can adopt new identities without a unit restart.

### Gaps and risks

- Requires an agent, server/control plane, workload attestation, trust-domain
  administration, and application integration.
- It solves workload identity, not arbitrary password/API-key custody.
- Connectivity loss and stale identity behavior still require role policy.
- Excessive for a small fleet absent a concrete workload.

### Disposition

Borrow the separation of node identity, workload authorization, streaming
rotation, and trust bundles. Do not adopt SPIFFE/SPIRE until a real workload and
measured alternative justify it.

Sources:

- <https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_api/>
- <https://spiffe.io/docs/latest/spire-about/spire-concepts/>

## Comparative summary

| Candidate | Custody | Authorization | Offline | Last mile | Rotation | Initial disposition |
| --- | --- | --- | --- | --- | --- | --- |
| systemd credentials | No | Unit declares consumption, not issuance | Yes if source is local | Strong default | New activation or native interface | Lead for services |
| `systemd-creds` blob | Local encrypted representation | No | Yes | Native | Re-encrypt and reactivate | Lead where host binding fits |
| age/SOPS envelope | Administrative/offline | Recipient possession; external policy still needed | Strong | Needs adapter | Re-encrypt/re-deliver | Challenger for custody/transfer |
| Vault-like service | Central/dynamic | Strong if correctly designed | Cached/leased only | Needs agent/adapter | Strong | Scale-driven challenger |
| SPIFFE-like identity | Issued workload identity | Workload attestation/registration | Short-lived cache semantics | Native API | Strong | Workload-driven challenger |

## Research conclusion

The mechanisms compose rather than compete. The least-complex initial path to
exercise is:

```text
administrative custody or issuer
    -> machine/operation-scoped authenticated transfer
    -> local protected representation where needed
    -> systemd credential for one named service activation
```

This conclusion does not select age, SOPS, a custom envelope, an enrollment
transport, or a PKI. EX-0013 must show whether systemd-native local storage plus
attended transfer is sufficient before NeutrinOS adds an online service.
