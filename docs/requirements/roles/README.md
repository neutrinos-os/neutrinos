# Role requirements

Role documents define capabilities and externally observable acceptance
criteria, not package lists.

Each role should cover:

- supported hardware or virtual platform
- boot, storage, networking, identity, and security needs
- workloads and resource controls
- installation, update, rollback, backup, and recovery behavior
- degraded and failure modes
- qualification tests
- explicit exclusions

Candidate roles are workstation, laptop, router, server/storage host, and
microVM guest. The initial targets are documented separately:

- [Reference qualification platform](reference-platform.md)
- [Workstation](workstation.md)
- [Router](router.md)

Their selection defines the order of design work, not a claim that they are
already supported.

