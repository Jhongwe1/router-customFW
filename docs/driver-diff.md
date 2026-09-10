# The driver diff

**`R5-9`, desk, 2026-09-10 (the fifty-seventh segment). No power, no flash byte,
no device reading.**

`R5` wrote six drivers for this SoC **blind** — `rtl819x-timer`,
`rtl819x-gpio`, `rtl819x-spi` + MTD, `rtl819x-wdt`, upstream `leds-gpio` bound
to my chip, and `rtl819x-keys`. `docs/blind-write-ledger.md` froze, before the
first line of driver source existed, what this repository had already read of
every external implementation. This file is what that was for.

**It is worth writing only if *blind* means something**, and the ledger's § 6
names the one thing that could make it mean nothing. That is what § 1 settles,
and § 1 was written and committed **before either tree was cloned**.

---

## 0. What this file is, and the three things it is not

It compares **my six drivers** against **third-party ports of the same SoC**,
on the two layers `docs/blind-write-ledger.md` § 5 defines. Those definitions
are not restated here; a second copy of a definition is a second owner of it,
and this repository has closed that shape before (`P4b-1`, 2026-09-01).

Briefly, so this page is readable on its own — the owner is the ledger:

* **L1 — fact.** Register addresses, reset values, documented bit positions.
  Three implementations describing **one piece of silicon**. Agreement carries
  no information about independence. This layer is a **cross-check**.
* **L2 — decision.** Divisor semantics, wrap handling, interrupt number,
  which bits are write-1-to-clear, initialisation order, `clocksource`
  `mult`/`shift`, rating and coexistence. **These are choices.** This is the
  layer the ledger protects and the only layer on which a diff means anything.

🔴 **Not ① — a claim that my drivers are better.** A difference on L2 is a
difference. Where the silicon decides which one is right, the experiment that
decides it is named; where it does not, the row says 未定 and stays there.

🔴 **Not ② — a review of the third-party ports.** They are read as evidence
about *decisions*, at the depth § 1 permits and no deeper.

🔴 **Not ③ — independent of the ledger's own limits.** `docs/blind-write-ledger.md`
§ 0 ① states that it is a **lower bound** on contamination: a file read in
2026-08 and never written about is invisible to it. Everything below inherits
that. Two domains are already **not** blind of the vendor and say so in place —
`wdt` (§ 4.10.1 of the ledger, four of seven paths on the decision layer) and
`spi_mtd` (§ 4.5, *the diff's vendor side is spent*).

---

## 1. The derivation check, pre-registered

### 1.1 Why this section is dated, and why it is a commit of its own

`docs/blind-write-ledger.md` § 6, committed **2026-09-02**, states the problem
and imposes the order:

> `driver-diff` compares **me against the third-party ports**. § 4.5 records
> deep reading of the **vendor**. […] **Unless the third-party ports derive
> from the vendor's `arch/rlx`.** If `shibajee`'s or `ggbruno`'s peripheral
> drivers are ports of Realtek's, then reading the vendor is reading their
> ancestor, and the independence is gone without a single third-party file
> having been opened.
>
> When the trees are cloned at `R5-9`, the **first** operation on each is a
> **derivation check** — file headers, copyright lines, SPDX tags, function and
> symbol names against `arch/rlx`'s — performed **before any register map is
> read**, and its result written down before proceeding.

That rule is eight days older than the clone and is in this repository's
history, which is stronger evidence than anything this section could assert
about itself. **What § 1 adds is the operational form** — the exact instrument,
the exact controls, and the verdict rule — and it adds it *before* the data
exists, so the thresholds cannot be chosen to produce an answer.

🔴 **The commit that creates this file contains § 0 and § 1 and nothing else.**
`git log --diff-filter=A -- docs/driver-diff.md` against the clone timestamps
recorded in § 2 is the check, and it is the same shape as the ledger's own
(*committed before any driver source exists*, § 8).

### 1.2 What the check may look at, and what it may not

A derivation check is itself a reading, and a careless one drifts into the
register map it exists to protect. The ledger says so (§ 6, *weak in a stated
way*). The bound is therefore **enforced by the instrument rather than
remembered by the operator**, which is the shape `tools/flashwin.py` already
has for a different forbidden thing.

| may | may not |
|---|---|
| C identifier **names** — functions, macros, structs, enums, typedefs | any **value**: no hex literal, no decimal constant, no bit number |
| file **paths** and directory structure | any **line of source**, in full or in part |
| copyright lines, licence headers, SPDX tags | any **comment body** beyond the copyright block |
| **counts** and set intersections over the above | any register **map**, in any form |

`tools/derivcheck.py` prints identifiers, paths, headers and counts. It has no
code path that prints a source line or a numeric literal, and a case asserts
that on a fixture containing both.

### 1.3 The instrument

For a **reference** tree R and a **candidate** tree C, restricted to a named
set of paths:

1. Extract the identifier set of each — the names a C compiler would see
   defined: `#define` names, function definitions, `struct`/`union`/`enum`
   tags, `typedef` names.
2. Report `|R|`, `|C|`, `|R ∩ C|`.
3. Subtract a **generic baseline** G — identifiers that also occur in the same
   kernel's own `arch/mips` and `include/linux` — and report the
   **distinctive** intersection `|(R ∩ C) \ G|` with the names themselves.
4. Report, separately, the count of files in C whose copyright block names
   Realtek, and the count whose path contains `rlx`.

Step 3 is the one that matters. Two independent ports of Linux to the same SoC
**will** share `init_module`, `platform_driver_register` and `HZ`; they will
not both invent `bsp_tc_init`.

### 1.4 The controls, written before the run

🔴 **A tool reporting *independent* is making a claim.** Two controls, and the
run is void if either fails:

* **Positive control — a known-derived pair must read DERIVED.**
  `src-vendor/wecb-vz-gpl/rtl819x/linux-2.6.30` against
  `src-vendor/rtl819x-toolchain/linux-2.6.30`. `SOURCES.json`'s own entry for
  `wecb-vz-gpl` records that these two *"agree by descent and are ONE vote, not
  two"*. If the instrument cannot see derivation there, every green below is
  worthless.
* **Negative control — an unrelated platform in the same kernel must read
  INDEPENDENT.** `arch/mips/<a non-Realtek platform>` against
  `arch/rlx`, both inside the vendor's own `linux-2.6.30`. Same kernel version,
  same coding era, same subsystem headers, different silicon vendor. If this
  reads DERIVED, the instrument is measuring *generic Linux 2.6.30* and its
  verdicts mean nothing.

⚠️ **Both controls live inside trees this repository has already cloned**, so
they can be run — and were run — **before** either third-party tree arrived.
An instrument validated after the fact is an instrument whose thresholds saw
the data.

### 1.5 The verdict rule, written before the data

Per **tree** and then per **driver domain**:

| verdict | rule |
|---|---|
| **DERIVED** | the candidate contains a directory named `rlx`, **or** ≥ 1 file whose copyright block names Realtek, **or** the distinctive intersection for that domain is non-empty |
| **INDEPENDENT** | none of the three, **and** the domain has an implementation in the candidate at all |
| **ABSENT** | the candidate has no implementation for that domain — no verdict is possible and none is written |

🔴 **What each verdict does to this document, decided now:**

* **DERIVED** for a domain ⇒ that domain's **L2 rows are void** against that
  tree, and the ledger's § 4 entry for the corresponding vendor file is the
  reason. The rows are **not deleted** — they are written and struck, because
  a diff that quietly omits its void rows is a diff whose scope was chosen
  after the fact.
* **INDEPENDENT** ⇒ the domain's L2 rows carry verdicts against that tree.
* **ABSENT** ⇒ the domain is scored against the other tree only, and if both
  are ABSENT the domain has **no diff** and this file says so.

🔴 **The outcome that would make this whole file not worth writing is written
down here, before it is known**: if **both** trees read DERIVED for **all six**
domains, `docs/driver-diff.md` reduces to § 1 plus one sentence, and `R5`'s
`D3` is reported as **not established**. `PROGRESS.md`'s `R5` refutation
condition already says this in the form *"if `R5-0`'s ledger shows the register
maps were already read, `driver-diff.md` **is not written**, and the gate says
so"*. This section is that clause made runnable.

⚠️ **A verdict of INDEPENDENT is not a claim that the port's author never saw
Realtek's code.** It is a claim about what is *in the tree*, which is the only
thing an instrument can reach. The distinction is stated because a reader who
takes INDEPENDENT as *clean-room* is taking more than was measured.

---

*§ 2 onward is written after the clone. Nothing below this line existed when
the commit that created this file was made.*
