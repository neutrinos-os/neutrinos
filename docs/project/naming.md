---
status: accepted
last_updated: 2026-08-09
---

# Project naming

## Decision

The canonical human-facing project name is **NeutrinOS**. The canonical
machine-facing identifier is **`neutrinos`**, and the existing GitHub
organization remains **`neutrinos-os`**.

Use the forms consistently:

- `NeutrinOS` in prose, headings, and other display contexts
- `neutrinos` for commands, image names, package namespaces, configuration
  keys, and other lowercase technical identifiers
- `neutrinos-os` for the existing GitHub organization

Do not use `NeutrinOS OS`, `Neutrinos OS`, or alternate capitalization.

## Findings

- [Neutrinos Platforms](https://neutrinos.app/) currently describes
  “Neutrinos” as an operating system, platform, and framework spanning devices.
  This substantially overlaps the category and framing of this project.
- [Neutrinos](https://www.neutrinos.com/) is also the name of an established
  enterprise software company and platform.
- QNX has long used the adjacent “Neutrino” operating-system name; current
  documentation now generally calls the product QNX OS, but the association
  remains visible in its documentation and history.
- Capitalization does not create a distinct spoken name, search term, package
  namespace, domain, or reliable legal identity. Styling the name as
  `NeutrinOS` therefore does not resolve these collisions.
- No trademark or legal clearance has been performed.

## Rationale

The name retains the existing project identity and repository organization,
connects to the atomic-particle theme, and makes the operating-system context
visible without adding a separate “OS” suffix.

The collision risk is acceptable during the personal-fleet phase because the
project makes no public distribution or third-party support commitment. The
display capitalization does not eliminate that risk, so the decision must be
reviewed before a public launch, domain investment, trademark filing, or
third-party package and signing namespace is established.

## Review triggers

- preparation of a generally available public distribution
- external users or contributors becoming a supported audience
- acquisition of project domains or social identities
- creation of third-party package, image, or signing namespaces
- receipt of a credible confusion or legal complaint
