---
id: RES-0002
status: in-review
last_updated: 2026-08-09
source_repository: JTarasovic/nixconfig
decision_gates: [P-001, C-001]
---

# NixOS configuration and deployment retrospective

## Question

Does the owner's operating experience with NixOS identify material
requirements that the existing-system comparison must include?

## Summary judgment

Yes. The objection is not simply unfamiliar syntax or a preference for another
package manager. The source of truth intended to describe machines became a
substantial program in Nix, the module abstraction did not expose all required
upstream behavior, and deployment required a separate Nix-based orchestration
layer. This is directly contrary to the desired operator model for NeutrinOS.

A NixOS image appliance could improve artifact delivery, but it would not
remove Nix evaluation and the NixOS module system from the human-authored
machine model. Adopting NixOS while hiding it behind a new NeutrinOS DSL would
recreate the abstraction and maintenance problem one layer higher.

This experience was sufficient to propose rejecting NixOS as NeutrinOS's
primary configuration and deployment framework. SYS-014 through SYS-018 were
subsequently accepted in PR-0002, making that disposition final.

## Evidence source and limits

This retrospective uses:

- the project owner's account on 2026-08-09;
- the local private `nixconfig` repository and its `main` history; and
- representative current files, without copying secrets or machine-private
  values into this repository.

The repository records one operator's experience with a demanding router and
small personal fleet. It is strong product-requirement evidence for this
personal-fleet project, but it is not evidence that NixOS is generally
defective or unsuitable for other operators.

## Owner account

The intended outcome was to keep understandable machine configurations under
version control. In practice:

- too much time was spent fighting Nix as a language;
- deployments were painful;
- required settings were not always exposed through the NixOS module DSL, so
  use depended on upstream module work or local workarounds; and
- the repository became a body of Turing-complete code rather than a bounded
  description of the machines.

The underlying concern is inspectability and operational control: understanding
the effective machine should not require mentally evaluating a general-purpose
program and its abstraction framework.

## Repository observations

### Concentrated integration work

The repository contains 82 commits on `main`. Sixty-four occurred between
2023-08-17 and 2023-09-16, including 14 `fix:`, four `refactor:`, 19 `chore:`,
and 24 `feat:` subjects. Counts do not prove excessive complexity, but the
subjects show that a large share of early effort went to stabilizing the
configuration framework and deployment rather than merely recording desired
machine state.

Representative commits include:

| Commit | Subject | What it indicates |
| --- | --- | --- |
| `4524683` | `feat: add deployment` | Deployment introduced another flake input and integration surface. |
| `35b50c8` | `feat: fix up deploys` | Deployment immediately required structural rework across nine files. |
| `8e7d428` | `fix: remove netbootxyz so systems will boot properly` | A valid-looking composition still produced an unusable system. |
| `5b5e857` | `feat: modularize network` | Network intent led to a custom module layer spanning eleven changed files. |
| `899cb11` | `feat: modularize router lan iface config` | Router LAN behavior required another substantial local abstraction. |
| `ede6dbe` | `fix: use correct propogation syntax` | Correctness depended on framework-specific expression details. |
| `adcb326` | `fix: quote property to bring team online` | A quoting detail in generated configuration affected network availability. |
| `64cd1c6` | `chore: refactor to use flake-parts` | The repository underwent a 540-line framework migration. |
| `5123160`–`0b80578` | four module-migration commits | Formatting, shell, packages, and system composition each became flake modules. |
| `3c89929` | `ci: create initial ci` | Evaluation checks arrived after the initial configuration and deployment work. |

The later history contains recurring flake, action, and package-input upgrades.
That maintenance may be reasonable in a Nix project, but it is cost added by
the chosen configuration and deployment ecosystem.

### The resulting source of truth is a software project

The current tree has roughly 1,586 lines across 24 tracked `.nix` files for two
systems. It includes:

- flake inputs and output composition;
- a `deploy-rs` node generator;
- custom archetypes;
- locally defined networking modules and option schemas;
- custom packages and checks; and
- machine, hardware, secrets, and service integration.

Line count is not a quality measure. The material observation is that the
operator must understand functions, recursive attribute sets, module merging,
defaults and overrides, dynamic attributes, flake inputs, and evaluation
context to understand or change the fleet.

### Missing abstractions create two unsatisfactory paths

The repository demonstrates both paths available when a setting is not
adequately modeled:

1. build and maintain a custom typed NixOS module; or
2. inject native text or lower-level attribute structures through escape
   hatches such as `environment.etc`, raw nftables rules, systemd service
   definitions, and `extraConfig`.

For example, the shared default configuration includes a setting marked
`TODO(jdt): add this upstream`, while the router combines NixOS service options,
raw nftables text, native systemd properties, and a checked-in nftables file.
The escape hatches are valuable, but their existence weakens the proposition
that a comprehensive typed DSL should mediate the underlying system.

## Derived candidate requirements

### Data-first machine intent

The normal source of truth for a machine or role should consist of bounded,
reviewable data and upstream-native configuration files. Understanding the
declared intent must not require evaluating a general-purpose programming
language.

Build tools may be implemented in general-purpose languages. The constraint is
on the operator-facing input contract, not on implementation technology.

### Native configuration is first-class

When an upstream component has a stable native configuration format, that
format should remain usable directly. NeutrinOS should add composition,
ownership, validation, and qualification around it rather than reproduce every
setting in a universal project DSL.

### Schemas must not become capability gates

Project schemas should govern values NeutrinOS must reason about across roles,
machines, or lifecycle stages. A missing convenience schema must not require
waiting for NeutrinOS to expose an otherwise supported upstream setting.
Pass-through or native-file mechanisms must remain explicit, attributable, and
testable.

### Composition must be bounded and observable

Role inheritance, defaults, and machine overrides need deterministic
precedence. The fully composed input and resulting native configuration must be
inspectable without reverse-engineering evaluation order or implicit module
merges.

### Deployment consumes qualified artifacts

The deployment operation should select and activate a previously built and
qualified release artifact. It should not turn a target machine into the place
where an arbitrary configuration program is evaluated or where an
unqualified equivalent system is reconstructed.

### Failure must be attributable

Validation and deployment errors should identify the responsible input,
machine or role layer, generated output, and lifecycle stage. A user should not
need specialist knowledge of the composition engine to locate an ordinary
configuration error.

## Adversarial challenge

A router with VLANs, prefix delegation, multiple network domains, staged
firewalls, DNS policy, discovery proxies, and monitoring is intrinsically
complex. Replacing Nix expressions with YAML or TOML does not remove that
complexity. Native configuration files can duplicate values, lack cross-file
validation, and expose unstable upstream details. Some conditional composition
will eventually be necessary.

The lesson is therefore **not** “configuration must contain no logic.” The
stronger and more testable boundary is:

- checked-in machine intent is bounded data or native configuration;
- reusable transformation logic is project implementation, separately tested
  and versioned;
- generated results are inspectable artifacts; and
- extending convenience schemas never gates use of an upstream capability.

If NeutrinOS grows an open-ended template language, pervasive conditionals, or
a module system that users must program, this objection has not been solved.

## Effect on RES-0001

NixOS remains technically strong in declarative composition, image creation,
and VM testing. It is no longer an unanswered functional competitor, however:
its primary authoring and evaluation model conflicts with accepted requirements
derived from actual use. A NixOS appliance changes artifact delivery but does
not resolve this conflict.

The project may still borrow testing patterns and lessons from NixOS. Using Nix
as a hidden image builder would require a separate future justification because
it would add an ecosystem without supplying the operator-facing model.
