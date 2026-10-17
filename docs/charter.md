# Charter

What rlxfw set out to do, where it stops, what finishing means, and the rules
every release follows. This page is the project's charter, translated on
2026-10-17 from a private planning document dated 2026-08-22 (its fourth
version). The planning documents are not published; [`method.md`](method.md)
§ *Quoting the plan* says how other pages quote them. Where the repository
applies a rule, the rule links there. Where the project stands now is
[`PROGRESS.md`](../PROGRESS.md)'s; this page owns no state.

## The aim

On a 2018 router with a Lexra core and 4 MiB of NOR flash, rebuild a firmware
from the public GPL source and one leaked vendor register manual — its own
kernel configuration, its own drivers, its own userspace and a signed update
chain of its own design — and, with the upstream project's register of test
cases, show item by item where it is stronger than the vendor's firmware, where
it is just as weak, and where it can never be fixed. The items are `R9`'s
register, [`config/fix-cases.toml`](../config/fix-cases.toml), derived from
that upstream register and rendered as [`differential.md`](differential.md);
what cannot be fixed is [`threat-model.md`](threat-model.md) § 11.

## Three levels of success

Each level is a set of gates, and each is a legitimate place to stop: there is
no half-finished state, because wherever a gate stops it leaves a complete thing.

| level | gates | what it delivers |
|---|---|---|
| pass | `R3`, `R5` | a kernel built here booting to a shell; six drivers of its own, the timer first, each with a device-tree binding; the bring-up report's first version |
| solid | adds `R6`, `R7` | an Ethernet driver of its own (`ping`, `iperf3`); a userspace of its own; the manufacturing test |
| top | adds `R8`, `R9`, `P1`–`P3` | the signed update chain; the three-column differential security table; a CVE ledger; the hardening matrix; a demonstration video |

This is what the charter set, not what was met. Each gate's result, and what it
did not establish, is [`GATE-RESULTS.md`](GATE-RESULTS.md)'s, one row each in
[`reports/README.md`](reports/README.md).

## Boundaries

| in scope | out of scope |
|---|---|
| the kernel, drivers, userspace, the update chain and the differential proof | feature parity with the vendor's web interface: only the endpoints `fix-cases.toml` names, and what routing needs |
| an Ethernet driver of its own | a WiFi driver of its own: the GPL drop's `rtl8192cd` is used, and the threat model says so ([`threat-model.md`](threat-model.md) § 8) |
| reading and citing the draft datasheet | committing it ([`CLAUDE.md`](../CLAUDE.md) § Never) |
| writing flash from `0x010000` up, from `R8` on ([`flash.md`](flash.md)) | writing the loader region — a first-stage loader of its own, `R10c`, is deliberately not done — and writing `H601`, which is forbidden permanently |
| any test on this project's own device | any test on a device that is not its own; wireless transmit experiments |

The last row's two exclusions, with tradecraft as the third, are the voluntary
ones in [`method.md`](method.md) § *Deliberately not done*, each with its reason.

## Releases

There is no due date, so the risk is not failing to finish but never finishing:
releases are the project's external clock. Three rules:

1. The repository is public from `v0.1`.
2. Every version is released, with a changelog and its known issues —
   [`CHANGELOG.md`](../CHANGELOG.md) and [`KNOWN-ISSUES.md`](KNOWN-ISSUES.md).
3. Every closed gate gets an entry in [`GATE-RESULTS.md`](GATE-RESULTS.md): a
   one-line version, three claims that stand, each with its evidence, and what
   the gate did not establish. When two consecutive entries name the same thing
   as not established, that thing is the next gate. Until 2026-09-01 the rule
   said *weekly*, and the unit was always the gate ([`log/2026-09.md`](log/2026-09.md),
   2026-09-01, `P4b-2`).

## Disclosure

The pinned reverse-engineering project, [`upstream/`](../upstream), holds
vulnerability reports that are not yet disclosed; its `docs/disclosure.md` at
the pin says which. Publishing a fix publishes the vulnerability, so this
repository writes about the vendor in three tiers:

| tier | rule |
|---|---|
| a class-level fix (*rlxfw's rootfs has no `system()`*) | publishable: it describes rlxfw's design and points at no vendor line |
| a named fix (a vendor address, handler or line) | follows the upstream project's disclosure state: while a report is held, it is not written |
| a reproduction (a request anyone could paste) | never appears in this repository while a report is held |

The upstream project's reports go to TWCERT/CC, and a report's 90-day clock
starts when it is sent; rlxfw may be public before then. Which reports are held
is read in [`threat-model.md`](threat-model.md) § 0.

## The three ways the project fails

| risk | its signal | the counter |
|---|---|---|
| the device dies, or its flash dump is lost | any unexpected flash write; a failing WSL disk | mainline zero flash write ([`flash.md`](flash.md)); an encrypted 3-2-1 backup, restored once (`S0`) |
| refactoring without end | two consecutive working segments with no gate moving | releases as the clock; a gate is the only measure of progress |
| a result certified in an environment more permissive than the device | none, which is what makes it dangerous | codegen and the ISA tested on bare metal only ([`method.md`](method.md)); `hazlint`; `R1f`, the toolchain checked on the silicon |

## House rules

The house rules are [`CLAUDE.md`](../CLAUDE.md)'s, their only owner, and this
page does not restate them; the method they encode is [`method.md`](method.md).

## What this page does not establish

- **That the charter was written on the date given.** The planning documents
  have no history in this repository (量 2026-10-17: `git log --all` restricted
  to their directory prints nothing, and the directory is not a repository of
  its own), so 2026-08-22 is the author's date, not a commit's.
- **That any level was reached, or any boundary held.** Each gate's result is
  [`GATE-RESULTS.md`](GATE-RESULTS.md)'s, and the flash boundaries are enforced
  by the tools [`flash.md`](flash.md) names.
- **That the translation is complete.** Left out: the charter's argument for the
  project's value to a reader, its release schedule's estimates, its daily
  working order, and the four held-report count its disclosure rule cited, which
  the upstream file at the pin no longer matches (`threat-model.md` § 0).
