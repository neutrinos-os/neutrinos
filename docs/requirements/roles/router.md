---
status: outline
last_updated: 2026-08-09
---

# Router role

The router is the second physical role. It is selected early because its
headless operation, networking responsibilities, availability needs, and
recovery constraints provide a strong challenge to abstractions first developed
for the workstation.

## Candidate capability areas

- deterministic network configuration under version control
- routing, firewalling, DHCP, DNS, VPN, and forwarding as required by the
  current network
- local console or independent recovery when normal networking is unavailable
- update qualification against representative WAN/LAN topology
- update rollback without relying on the service path being repaired
- configuration backup and restoration
- externally observable health checks for critical network services
- bounded storage and logging behavior
- eventual role-specific kernel evaluation

## Initial constraints

- The router uses the common release and recovery lifecycle unless an accepted
  design demonstrates that a role-specific lifecycle is unavoidable.
- A minimal or no-initrd kernel is a later optimization, not an initial
  requirement.
- Current NixOS configuration is evidence and migration input, not necessarily
  the target configuration language.

## Information needed

- hardware and firmware inventory
- interface topology and naming requirements
- current NixOS configuration and external dependencies
- required protocols and services
- acceptable outage and unattended-recovery behavior
- remote and physical access assumptions
- state that must survive replacement, reset, or hardware failure

