# Glossary

Terms here describe project usage and may be refined by later designs.

- **artifact**: Immutable bytes with a stable content identity, intended for
  testing, publication, or deployment.
- **bless**: Mark a booted deployment as healthy and eligible to remain the
  default.
- **configuration**: Declarative input that selects or specializes system
  behavior; its ownership and deployment mechanism must be stated.
- **deployment identity**: The content identity of an immutable deployment
  manifest binding one complete release-owned artifact set.
- **deployment set**: A deployment manifest and every exact artifact it names;
  the unit of qualification, authorization, selection, blessing, and rollback.
- **deployment variant**: One deployment set built for a declared role,
  platform class, and resolved normal configuration.
- **machine realization**: A deployment set running with accepted late-bound
  values, persistent state, machine policy, identity, and local modifications.
- **release**: A promoted collection of one or more independently identified
  deployment variants and their authorization metadata.
- **role**: A supported specialization such as router or workstation, including
  requirements and qualification tests.
- **state**: Data expected to survive replacement of an OS artifact.
- **system model**: The end-to-end relationship among inputs, artifacts,
  machine state, configuration, trust, deployment, and recovery.
