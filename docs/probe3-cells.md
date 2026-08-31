# `probe3` — the cell table

**Written 2026-08-26, desk, no power. `R1h-0`.** Every expected value and every
refutation condition below was written **before** the cell it belongs to, and
every expected value names the capture or the artefact it came from. That rule
exists because this project has broken it twice — `D2c` derived an expected
value from a stale map, and `E10d` derived one from the very map the cell was
testing — and both times the cell could not fail.

**Two columns, not one.** Every cell carries *expected under qemu* separately
from *expected on the device*, because `probe1` cell 1 came back **`02` FRESH
under qemu and `01` STALE on silicon** (量, `bench/2026-08-25/H1b.log:9`), and
that opposition is the reason the experiment means anything. **A qemu run that
looks like the device is the run to distrust.**

---

## 0. What this file owns, and what it does not

| | |
|---|---|
| **owns** | what each `probe3` cell does, what it is expected to return on each of the two machines, what would refute it, and what it measures |
| **does not own** | *where I am* (`PROGRESS.md`), the cache model itself (`notes/cache-model.md`), the four decisions `R1-gate` made (`docs/rlx-cache-and-cp0.md`), any number **except one** (`SPEC.md` indexes them) — 🔴 **§ 6.3's derivation of `TC0CNT`'s 14,286,057 Hz rate is owned here**, because it is derived here and `SPEC.md` `CLK-17` points back at this file for it; every other number in this file is a quotation, **and what the operator types** — that is `R1h-2`'s runsheet section, ⏸ **deferred 2026-08-26 to `R3`'s seating preparation**, and a separate step on purpose |
| **is not** | the payload. `R1h-1` builds that, under the `hazlint` gate, with one qemu mutation per cell |

`R1h` exists to settle four things (`PROGRESS.md` § Step list): ⓐ cache size /
line size / associativity **measured**; ⓑ does the D-cache allocate on read and
can anything invalidate a clean line; ⓒ does this core retire the MIPS-II
`cache` instruction; ⓓ write-through vs write-back-without-write-allocate, and
are `Status.IsC`/`SwC` implemented as bits. Every cell below is tagged with the
one it serves.

---

## 1. 🔴 Two things changed today, and both change the design

### 1.1 The prediction and the mechanism were about different caches

`PROGRESS.md` § Now describes ⓐ as *"the eviction walk — sweep N for the size,
sweep S for the line size, the pattern for the associativity"*, and gives it
*"a prediction to refute rather than a blank: D-cache 8 KiB, line 16 B, read out
of this unit's own kernel"*.

**Those are two different caches.** The mechanism the walk is built on —
*a store written into the instruction stream is not seen* — is `probe1` cell 1
and cell 5, and it measures the **I-cache** (量, `bench/2026-08-25/H1b.log:9-12`,
`01` STALE on all four victims). The prediction cut from this unit's kernel —
`sltiu … 0x4000` at `0x8000CAAC`/`0x8000CBE0`/`0x8000CCD4`, read through
`cache-rlx.c` as `cpu_dcache_size`, and eight `cache` ops at stride `0x10` — is
about the **D-cache** and only the D-cache (讀, `notes/cache-model.md`
§ *Cache geometry*).

So the walk as described could not have refuted the prediction that was written
for it. `probe3` carries **two walks**: Group W on the I side, where the
mechanism is measured, and Group V on the D side, where the prediction lives and
the mechanism is the thing Group C is testing. **Group V is armed at run time by
Group C's own result** — see § 7.

**And while correcting that, one more correction, in the other direction.** The
brief for this step said the I-cache size has no source at all. It has the
*strongest* sourcing of the three numbers — see § 6.3. **What has no source of
any kind, anywhere, is the associativity of either cache.** That is the cell
that stays blank if its walk fails.

### 1.2 🔴 There is a 16 KiB instruction scratchpad on this part, and it is exactly the size of the I-cache

Nothing committed in this repository has ever mentioned it. It is a first-order
threat to ⓐ, and it was found today by asking what `CCTL 0x010`/`0x020` are.

**They are not cache commands. `0x010` is `IMEM0FILL` and `0x020` is
`IMEM0OFF`** — the lifecycle controls for a local instruction scratchpad — and
four sources say so, two of which are independent of each other:

| | source | what it gives | class |
|:-:|---|---|---|
| 1 | **`arch/rlx/include/asm/rlxregs.h:630-638`**, in **all three GPL drops this project holds** | `CCTL_IMEM0FILL 0x00000010`, `CCTL_IMEM0OFF 0x00000020`, and the rest of the register: `DInval 0x1`, `IInval 0x2`, `IMEM0ON 0x40`, `DWB 0x100`, `DWBInval 0x200`, `DMEM0ON 0x400`, `DMEM0OFF 0x800` | 讀. ⚠️ **One source, not three** — the three files are byte-identical, md5 `623d85d7d39efd1906e8b6b842e60e82`, and they share the Realtek SDK ancestor `cache-rlx.c` came from |
| 2 | **Lexra LX4189 Data Sheet Rel 1.9 § 5.2**, *"Cache Control Register: CCTL"* | the same two bit positions, plus the semantics in prose: *"A transition from 0 to 1 on IMEMFill causes the LMI to initiate a series of line read operations to fill the IMEM contents… The processor stalls while the entire IMEM contents are filled"*; *"A transition from 0 to 1 on IMEMOff causes the LMI to clear its internal IMEM valid bit. Subsequent cacheable fetches from the IMEM region will be serviced by the instruction cache"* | 讀, **vendor doc, and independent of 1** — Lexra is the core vendor, Realtek the integrator. ⚠️ LX4189 is a **write-through** part with no `DWB`/`DWBInval` bits at all, so bits 8–9 of its map are Reserved and live here: **the two maps are provably not identical**, and bits 6–7 differ between sources too. `0x010`/`0x020` are the only bits on which every source agrees without contradiction |
| 3 | **`refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` § 1 p.1 and § 2** | *"a 16Kbyte I-Cache, 8Kbyte D-Cache, 16Kbyte I-MEM, and 8Kbyte D-MEM are provided"* — the scratchpads **exist on this family, and their sizes** | 讀, vendor doc, **already in this repo**, and already quoted verbatim in `SOURCES.json:195`. ⚠️ **but read § 1.3 before quoting it** |
| 4 | 🔴 **this unit's own kernel, `0x80002210`–`0x80002300`** | the **behaviour**, and it matches the names exactly | 讀, on an artefact cut from this device |

Source 4 is the one that turns a name into an explanation. Disassembled from
`$FWRE_WORK/rebuild/b4c-desk/vmlinux-rederived.bin` (sha256 `cf0d60a8…`; chain of
custody in `notes/cache-model.md`):

```
80002210  mfc0  t0,$12
8000221c  lui   at,0x8000
80002220  or    t0,t0,at          ; Status |= CU3  -- so CP3 is reachable
80002224  mtc0  t0,$12
80002230  mtc0  zero,$20          ; CCTL = 0        <- the 0->1 edge, deliberately
8000223c  li    t0,32
80002240  mtc0  t0,$20            ; CCTL = 0x020  IMEM0OFF
8000224c  mtc0  zero,$20
80002258  li    t0,514
8000225c  mtc0  t0,$20            ; CCTL = 0x202  DWBInval | IInval
80002268  lui   t0,0x802c
8000226c  addiu t0,t0,-32768      ; 0x802B8000
80002270  lui   t1,0xfff
80002274  ori   t1,t1,0xc000      ; 0x0FFFC000   -- a 16 KiB-aligned 28-bit mask
80002278  and   t0,t0,t1          ; 0x002B8000   -- physical
8000227c  mtc3  t0,$0             ; CP3 $0 = IMEMBASE
80002288  addiu t0,t0,16383       ; +0x3FFF      -- 16 KiB
8000228c  mtc3  t0,$1             ; CP3 $1 = IMEMTOP
80002298  mtc0  zero,$20
800022a4  li    t0,16
800022a8  mtc0  t0,$20            ; CCTL = 0x010  IMEM0FILL   <- fill it
800022b4  lui   t0,0x802c         ; 0x802C0000
800022bc  lui   t1,0x802d
800022c0  addiu t1,t1,-16384      ; 0x802CC000
800022c4  beq   t0,t1,0x800022f4  ; skip if the region is empty
800022cc  lui   t1,0xfff
800022d0  ori   t1,t1,0xe000      ; 0x0FFFE000   -- an 8 KiB-aligned mask
800022d4  and   t0,t0,t1          ; 0x002C0000
800022d8  mtc3  t0,$4             ; CP3 $4 = DMEMBASE
800022e4  addiu t0,t0,8191        ; +0x1FFF      -- 8 KiB
800022e8  mtc3  t0,$5             ; CP3 $5 = DMEMTOP
800022f4  mtc0  zero,$20
80002300  jr    ra
```

**Every element corroborates every other.** The first window it programs is
**16,384 bytes**, which is the datasheet's I-MEM size; the second is **8,192
bytes**, the datasheet's D-MEM size; the CP3 register numbers are 0/1/4/5, which
is what the third-party `lxregs.h` names `IMEMBASE`/`IMEMTOP`/`DMEMBASE`/
`DMEMTOP`; the CCTL writes are **clear-then-set**, which is what an
edge-triggered control needs and what the LX4189 doc says it is; and `CU3` is set
immediately before the first `mtc3`. `notes/cache-model.md` already records this
same address span for the CCTL writes, and reads it as *"part of this SoC's reset
sequence, reproduced by two codebases, and it says nothing about what they
mean."* It says what they mean.

🔴 **And the loader does not do any of it.** A scan of `stage2.bin` for primary
opcode `0x13` (COP3) returns **97 words, all of them data**: every one is at or
above `0x8040A5B8`, which is where `SPEC.md` `CPU-26` already places the start of
the loader's data region (`0x8040A5C0` = `BootStateEvent[3][8]`), and every one
decodes as ASCII (`4c4f540a` = `"LOT\n"`, `4e49435f` = `"NIC_"`, `4d583235` =
`"MX25"`). **Zero COP3 instructions in the loader's code.** So the loader issues
`IMEM0OFF` and `IMEM0FILL` **without programming BASE/TOP at all** — over
whatever range reset left.

⚠️ **The control on that zero is weaker than this project's usual, and saying so
is the point.** The same scanner finds the four clean `mtc3`s in the kernel, so it
can see a real COP3 instruction — but that control is on a *different file*.
There is no known COP3 in `stage2.bin` for it to rediscover, because there is
none. The zero is a zero; the instrument was demonstrated elsewhere.

**🔴 Why this threatens ⓐ.** *"When IMEM is invalid, all cacheable fetches from
the IMEM region will be serviced by the instruction cache"* (讀, LX4189 § 5.2) —
read the other way round, **while it is valid they are not.** If `probe3`'s
victim arena lands inside the loader-prompt IMEM window, the eviction walk
measures a 16 KiB scratchpad and reports it as a 16 KiB I-cache. **The two are
the same size, so no size measurement can tell them apart.** Three cells answer
this and all three are new: Group M reads the window, Group W's `w-imem` re-runs
the walk with the scratchpad switched off, and § 9 makes it a condition on the
whole table.

⚠️ **One retrospective comfort, and it is only that.** `probe1` cell 2 applied
`CCTL 0x002` (`IInval`) and read `02` FRESH ×2 (量, `H1b.log:15-16`). `IInval`
invalidates the I-cache; per the same LX4189 section `DInval` explicitly leaves
the DMEM alone, so 推 `IInval` leaves the IMEM alone too, and a victim inside a
live IMEM would have stayed STALE under cell 2. **So `probe1`'s victims were
probably not in the IMEM window** — 推, about `probe1`'s addresses, and it
transfers to none of `probe3`'s.

### 1.3 ⚠️ The datasheet in `refs/` documents a variant this unit is recorded as NOT being

**This qualifier applies to every expected value below that cites a Realtek
datasheet, and it was nearly left out of this file.** `SOURCES.json`'s own entry
for `ds-rtl8196e-vex` carries it verbatim:

> *"It is the -VE1/2/3 variant, which has embedded DRAM by MCM. **THIS UNIT HAS
> EXTERNAL SDRAM (Winbond W9825G6KH) and is therefore NOT this part.**"*

That is 量 on this unit — `MEM-01`, the package silkscreen of the Winbond part.
And `CPU-02` (量) reads the SoC's own marking as `RTL8196E · I510VG1 · GF23
TAIWAN`, **with no variant suffix at all**, so neither datasheet's part number is
confirmed here.

**What survives, stated exactly:**

- The geometry and the CPU name appear in **two different Realtek documents about
  two different variants** — the leaked `-VE1/2/3-CG` draft in `refs/`, and the
  **public `RTL8196E-CG`** datasheet already listed in `SOURCES.json`
  `reference_only` for precisely this reason (*"a second document (not the same
  one) on the naming question"*). Two documents agreeing across variants is worth
  more than one document.
- **Family membership is 量 and is not in doubt**: `CPU-01`, ×3 — the package, the
  boot banner, and the bootcode's own comparison of `0xB8000000` against
  `0x8196E000`.
- 🔴 **It is still a statement about a family, not a measurement of this die**,
  which is the whole reason ⓐ is a gate. The datasheet moves the geometry from
  *one third-party vote* to *two vendor documents plus a third-party dtsi plus a
  build constant* — **and every one of those is a belief about silicon, not a
  reading of it.**

⚠️ **And it cuts the other way for `CPU-46`.** The I-MEM/D-MEM sizes rest on the
same two documents — but **this unit's own kernel programming `+0x3FFF` and
`+0x1FFF` into `CP3 $0`/`$1` and `$4`/`$5` is cut from this device**, and it
agrees with them. That is the leg that does not depend on the variant.

### 1.4 🔴 The core vendor's datasheet is in hand now, and it refutes four things in this table

**Added 2026-08-26, `R1h-1`.** § 1.2 cited *"Lexra LX4189 Data Sheet Rel 1.9
§ 5.2"* from `SOURCES.json`'s `reference_only` list, where the entry ends
*"NOT DOWNLOADED INTO `refs/`: cited only. If it is ever fetched it moves to
`documents` WITH a sha256."* It was fetched. `SOURCES.json` moved it, with
`sha256 6afb1415…`; the PDF itself is **not committed** — it is someone else's
property and `CLAUDE.md` forbids it — and lives in `$FWRE_WORK/rebuild/
refs-external/`.

⚠️ **The standing caveat, and it got sharper.** § 1.2 already recorded that the
LX4189 is a write-through part with no `DWB`/`DWBInval`, so its CCTL map and this
SoC's are provably not identical. **Table 2 makes it worse and better at once:
the LX4189's entire CP0 register list is 8, 12, 13, 14, 15, 20 — no `Index`, no
`Random`, no `EntryHi`/`EntryLo`. IT HAS NO TLB.** This die has 32 TLB entries
(量 `CPU-08`, corroborated by `Random` reading 5…29 inside 0…31 on `probe2`'s
census). So the LX4189 is **a sibling and demonstrably not this part**, every
line below is 讀 about a related core, and none of it is a reading of this
silicon. What it *is* worth is that it comes from the **core vendor**, where
everything else here comes from the integrator or from a third party.

| | what the document says | what it changes here |
|:-:|---|---|
| ① | § 5.2, verbatim: *"if the affected memory location has an alias in uncacheable (KSEG1) space … perform an uncached read of the affected memory locations. **If the location is resident in the data cache it will be invalidated.**"* and *"**Note that a write to a KSEG1 address has no affect on the contents of the data cache.**"* | 🔴 **`c-E0` and `c-E2` were broken and would have refuted `CCTL 0x100` by accident.** They were written to continue from `c-E`'s state; `c-E`'s own last step is an uncached load of the target, which by ① invalidates the line — so by the time `c-E2` issued its `DWB` there would be **no dirty line left**, its `P0` reading would have been recorded as *"`0x100` does not write back"*, and that is a refutation produced by the running order. **Each of the three E cells now runs its own whole sequence.** ② also gives `c-A` its first expected value: an uncached *write* does not disturb a resident line, so **`l2 = P0`, a stale line**, 讀 ×1 |
| ② | the same two sentences | 🆕 **cell `c-G` exists because of them.** ⓑ asks what on this core can invalidate a clean line; the core vendor's answer is *an uncached read*, with no `CCTL` at all. It costs five loads and no new instruction, and if it holds here `R6` gets a per-line invalidate primitive for the price of a load. See § 6.5 |
| ③ | § 5.1: *"configurable for a 16, 32, 64, or 128-byte cache line size"*; § 5.6: *"the cache obtains a cache line (4, 8, 16, or 32 words)"* | 🔴 **`w-line`'s void gate was in the wrong place.** It probed to `+192` and called a STALE run reaching there *"past any plausible line"* — **128 bytes is a legal line on this family**, so that gate would have recorded a real 128-byte line as a void measurement. The probe list now runs to `+320` and the void gate is at `+256` |
| ④ | § 5.1 Table 18: `ICACHE` is *"Direct mapped or two-way set associative"*; `DCACHE` is *"Direct mapped data cache"* and Table 25 offers no other option | 🔴 **Associativity is no longer *"留白 — no source of any kind, anywhere"*.** The I side's search space is **{1, 2}** and the D side's prediction is **direct-mapped**. `w-assoc`/`v-assoc` go from a blind sweep to a prediction with a refutation condition: **a walk that returns K = 4 refutes this bloodline** |

**And two things it gives that are not corrections.**

- 🔴 **`PRID` is `0x0000c401` for the LX4189** (Table 2). This unit reads
  `PRId = 0x0000CD01` (量, `R1g-4b`). That is **one point on the Lexra `PRId`
  map and the first this project has had** — it says `0xCD01` is not an LX4189
  and nothing more. `CLAUDE.md`'s ban stands: **it is a datum, not the
  assignment table**, and `RLX4181`/`RLX5281` remain unwritable.
  🔄 **2026-08-27: the assignment table turned up, in a GPL drop already on
  disk.** `arch/rlx/include/asm/cpu.h` maps `PRID_IMP_RLX4181 = 0xcd00`, so
  `0x0000CD01` is **RLX4181 rev 1** and `RLX5281` (`0xdc01`) is excluded. The
  sentence above is left as written because it was the correct judgement on the
  evidence it had, and because what it insisted on — a table rather than a datum
  — is exactly what arrived. `notes/vendor-kernel-isa.md` §5 carries the three
  weaknesses that travel with it.
- § 3.4.2: *"Other exceptions, BEV = 0 → `0x8000_0080`"* — a **fourth**
  independent source for the vector, from the core vendor, agreeing with this
  unit's own `trap_init`, the vendor bootcode's comment, and
  `arch/rlx/kernel/traps.c:691`. Nothing changes; it is recorded because a
  fourth agreeing source is worth knowing about when the wrong address had
  reached seven committed sites as recently as 2026-08-25.

---

## 2. The instruments `probe3` stands on

Everything below is reused rather than invented. Each row names the measurement
that licenses it, so an argument about a cell can be traced to a capture in one
step.

| | instrument | what licenses it |
|:-:|---|---|
| **M1** | a store into the instruction stream is not seen by the I-cache | 量 `bench/2026-08-25/H1b.log:9-12` — `probe1` cell 1 (cached store) **and cell 5 (uncached store)**, `01` STALE on all four victims, `ex=000011a1` against `ma=240222b2`. 🔴 **`probe3`'s I-side cells use the uncached store**, i.e. cell 5's leg, which takes the D-cache out of the I side entirely |
| **M2** | `CCTL 0x002` alone makes a rewritten instruction visible | 量 same captures, cells 2/3/6, `02` FRESH on six victims; re-measured 2026-08-25b by `probe2` on a **different address range and a different store path** (`install.bad=0`, `break` trapped and returned). This is `probe3`'s **re-arm** between walk steps, and it is what lets one arena be reused |
| **M3** | an exception at `0x80000080` reaches an installed handler and returns | 量 `bench/2026-08-25b/H2a.log` — `break.count=1`, `cause=00000024` (ExcCode 9 `Bp`), `break.epc=80500270`, `install.bad=0`, `restore.mismatch=0`, `H2h-utlb` byte-identical to the same seating's `H0c` |
| **M3′** | the handler is **ExcCode-agnostic** | 讀 `tools/rlxprobe/exc.S:68-114 (rlx_exc_entry:)`: it stores `Cause`, stores `EPC`, increments a count, returns to `EPC+4` via `jr $26 / rfe`. **No test of `Cause`, no conditional branch, one control transfer.** Corroborated on the emitted `probe2` image: 22 words, zero branches. ⚠️ **The gap, stated:** no exception other than `Bp` has ever been delivered on this die under this handler. The code path is provably identical; that it *behaves* identically for ExcCode 10 is 推. Cell `x-ri` closes it |
| **M3″** | `EPC+4` is unconditional, and wrong in a branch delay slot | 讀 `exc.S:41-44 (It adds 4 to EPC unconditionally)` and `exc.S:92 (addiu $26, $26, 4)`. **Constraint on every `probe3` cell: no probed instruction may sit in a delay slot**, and `Cause` is recorded whole so `BD` is visible if it happens anyway |
| **M4** | CP0 20 is a **write-only** command register that reads zero | 量 `CPU-39` — `probe1`'s `XCT0` row read `00000000`, and `probe2`'s row `0xa0` read `00000000` with `nowrite=0` across all 256 rows proving `mfc0` always writes `rt`. **Two consequences:** a `CCTL` command's effect is the only observable; and a read-modify-write of `CCTL` degenerates to a plain write on this die, so `probe1`'s clear/write/clear (讀, `cache.S:70-81 (rlx_cctl:)`) already produces the 0→1 edge the LX4189 doc requires |
| **M5** | `Status.IsC` does not isolate; stores issued while it is set reach DRAM | 量 `probe1` cell 4, `07` CORRUPT ×2, `240222b2 → 000222b2` and `03e00008 → 00e00008`. **Constraint: no `probe3` cell may execute a store while `IsC` is set.** Cell `s-isc` sets it with no memory reference between set and clear |
| **M6** | the KSEG0/KSEG1 alias works for **stores that miss** and for uncached read-back | 量 `probe1` cells 1 vs 5 (`ma` identical) and every `mb`/`ma` field. ⚠️ **What is NOT established is exactly what Group C tests**: that an uncached store leaves a *resident* D-line alone |
| **M7** | DRAM keeps its contents across the payload's own reset, and across a short power-off | 量 `MEM-10` (2-word canary, three warm resets), `MEM-15` (548-byte chosen-value block — **and it did NOT survive ~3.9 h**). **Consequence: `probe3` poisons its result block *and* initialises its arena before the first cell**, or a leftover arena reads exactly like a live one |
| **M8** | the loader re-stages `0x80500000` on a watchdog reset | 量 `R1g-4b` — a second `J 80500000` booted the vendor kernel. **`probe3` gets its own upload** and cannot share `R3`'s |
| **M9** | `TC0CNT` at `0xB8003108` is readable and TC0 is running at the prompt | 量 `REG-07` (one reading, `0x0010B960`, mid-count), `REG-09` (`TCCNR = 0xC0000000` → TC0En=1, TC0Mode=1), `CLK-04` (the loader's tick advances at 100.0018 Hz over a 2,080 s baseline, which requires the counter to count). ⚠️ **n=1 on the register itself** — cell `P1` closes that at the prompt for free |

---

## 3. The address map `probe3` uses

🔴 **Only one span of DRAM on this device has positive evidence of being free at
the loader prompt**, and it is not the largest one. `0x80A00000`–`0x80AF1002`
held a 987,138-byte image across a complete TFTP upload **and** download,
byte-identical, with the loader's own network stack live throughout (量, `G4`,
2026-08-24d, sha256 `396561a0…45a03e90`). Everywhere else the case is *"nothing
has read it"* — and `MEM-14` is this device's own counterexample: `0x81000000`
was exactly that kind of address until three captures showed the boot path
writes it on **every** boot.

**So `probe3` stays inside the proven span** — 🔄 **and since 2026-09-01
that sentence needs its qualifier, because Group F reads two addresses that are
not DRAM at all.**

| | |
|---|---|
| **every WRITE this payload makes** | is inside `0x80A00000`–`0x80AF1002`, and that is unchanged. The arena, the result block and the poison margin are the whole list |
| **every DRAM READ** | likewise |
| 🆕 **Group F's reads** | `0xBD000000` and `0xBFC00000` — two windows onto the SPI flash, outside DRAM and outside the proven span, and **reading is not writing**. § 6.8 owns them, § 6.8.0 records that nothing here has read either of them outside Linux, and `f-alias`/`f-live` are that assumption turned into two cells that can fail |

⚠️ **The distinction is load-bearing and it is why this row is a row.** `MAP-17`'s
band is about *what may be written without destroying something*; a load cannot
destroy anything, and the risk it carries is different in kind — a bus that
never answers, which is what the exception handler and the running order at § 7
are for.

| | window | what | evidence |
|:-:|---|---|---|
| | `0x80A00000`–`0x80A0027F` | `probe1`'s result block, 160 poisoned words | 量, `bench/2026-08-25/H1c.log`. **Preserved** — `probe3` must not touch it |
| | `0x80A01000`–`0x80A01CC3` | `probe2`'s result block, 817 poisoned words | 量, `bench/2026-08-25b/H2g.log`. **Preserved** |
| **RB** | `0x80A02000` + | 🆕 **`probe3`'s result block.** Above both, inside the proven span | a choice; refuted by cell `P3` |
| **ARENA** | `0x80A10000`–`0x80A8FFFF`, 512 KiB | 🆕 **the victim / data arena**, runtime-generated. Big enough for a 12-count sweep at 16 KiB stride and for a 64 KiB working set | inside the proven span; `0x80A78000` is the one point inside it read directly (`G0-mid`, 16 words: no pointer, no self-reference, no period) |
| | `0x80AF1002` | top of the proven span | 量, `G4` |
| | `0x80B00000`–`0x80BFFFFF` | `RLX_GEOM_BASE`. **Not used** — `GEOM=1` is dead (`CPU-25`) and this window has never been read | — |

**Why the arena is generated at run time.** `probe1`'s `victims.S` is 16 slots at
`0x400` stride = 16 KiB of `.text` (讀, `rlxdefs.h:31-32 (#define RLX_VICTIM_STRIDE 0x400)`). A stride sweep to
16 KiB × 12 counts needs 192 KiB and a 64 KiB working set needs 64 KiB;
assembling that is a quarter-megabyte payload whose `hazlint` population is
mostly `nop`. Generating it costs an uncached store loop plus **one
`CCTL 0x002`** — which rests on **M2**, which is measured. The payload says so in
its own header: *the arena's first execution is licensed by `probe1` cells
2/3/6.*

**Why the walk loops run from KSEG1.** `victims.S` already admits the one thing
its 7 KiB pair gap cannot exclude: *"This does NOT exclude eviction by the driver
code that runs between the two calls."* Entering the walk through
`rlx_call2_uncached` makes the driver's own instruction fetch uncached, so **the
only thing in the I-cache is the victims**. The build is `-mno-abicalls -fno-pic
-G0`, so every address the loop forms is absolute whatever segment it runs in
(讀; `RUNSHEET.md:974` already establishes this for `probe1`'s `flags` bit 0).

**The victim primitive is two words, not three.**

```
+0:  jr    $31                     <- the guard word; must always read 03e00008
+4:  addiu $2, $0, IMM             <- delay slot, and THE PATCHED WORD
```

`probe1`'s victim is three words with the patched word first and the guard at
`+4`; this inverts it. The reason is resolution: **an 8-byte victim can be placed
at 8-byte stride, so Group W can see an 8-byte line.** A 3-word victim cannot go
below 16 bytes, and at 16 bytes *"the line is 16 B"* and *"the line is 8 B or
4 B"* are the same reading. The guard moves to `+0` and becomes the word that
must never change, which is strictly better than `probe1`'s: the guard is now the
control-flow word itself.

⚠️ `.set noreorder`, and the delay slot is filled by hand. `addiu` is not a load,
so the exposed load-delay slot does not apply; `hazlint` gates the build anyway.

---

## 4. Encoding and budget, written before the cells

**The wire is 3840 bytes/s** (38400 8N1, 10 bits/byte; 算, and it reproduces
`H1c`'s measured 1,671 B and `H2g`'s measured 9,661 B).

🔴 **`--esc-after 60` is not a cap on the report, but the report lives inside
it.** The capture spans `J` → payload runs and reports → the payload's own
`rlx_reset` → reboot → the ~4.9 s ESC window (`LDR-15`) → the prompt. Miss the
ESC window and the vendor kernel boots: **one power cycle.** Arithmetic:
`(60 − 5.616) × 3840 = 208,834` bytes of report before the window is eaten —
⚠️ **and `5.616` is carried from the `§ B4` budget box rather than derived here;
`LDR-15`'s ESC window is 4.886 s and the remaining 0.730 s is named nowhere in
this repository. It is marked or it does not stand.** **At `probe1`'s 104-byte
row shape, `104V + 191 ≤ 208,834` gives V ≤ 2,006 — a wall, not a guideline**,
and 2,048 full rows are `104×2048 + 191 = 213,183`, an overrun of 4,349 bytes =
**1.13 s**. *(The 191 is the banner and header; drop it and the wall moves to
2,008. Both terms are stated so the number can be checked rather than trusted.)* The operator would not see an overrun;
they would see the vendor kernel boot, which reads as *"the payload hung"*.

🔴 **The read-back has a ceiling of evidence.** The largest `DW` ever executed on
this device is **820 printed words / 9,661 bytes** (量, `H2g`). Above ~1,000
words two things are untested at once: whether the loader's `DW` accepts a
4-digit decimal length, and whether anything in its print loop caps the run.
`reply_DW(addr,N) = len(cmd) + 2 + 47×ceil(N/4) + 9` (讀, `LDR-07`; the constants
are fitted over 91 captures by `tools/reply-size.py`, not counted in a terminal),
and **the round-up is upward — a length given too small never announces itself.**

**The encoding, and why.**

| | UART | RAM read-back | inside measured evidence? |
|---|---|---|---|
| one full `probe1`-shape row per victim | 104 B each — 213 KB at V=2048 | `DW … 16433`, a 5-digit length | ❌ overruns the ESC window, and is 20× past any `DW` this loader has executed |
| 1-bit STALE/FRESH bitmap | 0.34 B/victim with line framing | tiny | ❌ **and it is worse than cheap.** `probe1` defines **seven** verdicts, and cell 4 came back `07` CORRUPT on both victims — the entire evidence that `Status.IsC` does not isolate. A 1-bit map would have scored those two as a cache result |
| 🔴 **nibble bitmap in RAM + summary on UART + 16 named full rows on both channels** | 🔄 **BUILT AND MEASURED 2026-08-26: 5,893 bytes / 126 lines under qemu** (量, `qemu/2026-08-26/probe3.txt`, sha256 `e6035718…`, and the `.build` file beside it records both), against the 2,177 B this row estimated before the payload existed. The estimate was low because it counted 16 rows plus a banner and no per-point summary; the payload emits one line per sweep point across three sweeps, one per CP3 register, and one per Group C cell. **The device run will be LONGER** — Group V is void under qemu and will run on silicon — 推 ≈ 7 KB / 1.9 s. Both are far under § 4's own wall of 208,834 B. 🔴 **V is NOT the payload's total.** Summed over § 6 the victim *instances* are well over 12,000. The block is **reused between sweep points**, so **which point survives to the read-back is a decision**: it is the **boundary point** — the first with any FRESH, whose PATTERN is what carries associativity and aliasing — and the largest point if there is no boundary. It is written by a **second, single-point run**, so both runs' counts are in the block and a disagreement between them is visible rather than silently resolved. `H_BMP_POINT` and `H_BMP_COUNT` name it, and **the payload writes its own surviving-victim count into the header** so the desk can compare it against the length it actually read | 🔄 **`DW 80A02000 641` = 7,593 B / 1.98 s** — 79 % of `H2g`'s already-executed 9,661 B, and three digits, so it does not depend on the untested question of whether the loader takes a four-digit length. **433 was this row's estimate before the cells were laid out**; the block is 64 header + 192 cell results + 16 × 8 rows + 256 bitmap words + the seal, and `Makefile`'s `RB_WORDS_probe3`, `probe3.c`'s `RB_WORDS` and a compile-time assertion in `probe3.c` all carry it. 🔄 **2026-08-31 (seventeenth session): 641 → 707, `DW 80A02000 707` = 8,345 B / 2.17 s, 86 % of `H2g`.** 🔄 **2026-09-01 (eighteenth): 707 → 718, `DW 80A02000 718` = 8,486 B / 2.21 s, 88 % of `H2g`** — Group F took eleven result words.** The block is now 64 header + **194** cell results + 16 × 8 rows + 256 **scratchpad** bitmap words + **64 retained** bitmap words + the seal. Two changes, and the second is the one this row's own sentence about *"which point survives to the read-back"* required: `O_BMPK` is a region with **one writer**, `O_BMP` stays the scratchpad seven cells share, and Group W's `M(T)` ladder took the two new result words. The three mirrors are unchanged in kind — `Makefile`'s `RB_WORDS_probe3`, `probe3.c`'s `RB_WORDS`, the compile-time assertion — and `tools/test-rlxprobe.sh` recomputes the total from the C, now including `RB_BMPKW` | ✅ **every number is under something this loader has already done** |

🆕 **2026-08-29, `R1h-3`: `LDR-07`'s round-up hands back the over-run control
for free, and this section did not know it.** The block is `RB_WORDS = 641`
words and the payload poisons `RB_POISON_W = 641 + 8 = 649` of them, the margin
existing *"so a run that wrote PAST its own block shows data where poison was
predicted"* (讀, `probe3.c:131 (#define RB_POISON_W (RB_WORDS + 8u))`). **`DW 80A02000 641` prints `4 × ceil(641/4)` =
644 words**, so `w641`, `w642` and `w643` — three of the eight margin words —
come back on the last reply line, at `0x80A02A04`/`08`/`0C`, beside the seal at
`0x80A02A00`. **The margin check therefore needs no second command**, and its
expected value is `DEADC0DE` three times. Reading the remaining five costs one
`DW 80A02A04 8` (118 B) and is worth sending only if those three are not poison.
⚠️ **`DEADC0DE` is also on `P2`'s refutation list** as a known magic, so the same
constant is the arena's *negative* control before the run and the block's
*positive* control after it — and from the second seating onward a `DEADC0DE` in
`P2` stops being unambiguous, because a previous run's block surviving the
power-off (M7) reads identically. `bench/2026-08-30/PREDICTIONS-B5-block0.md`
§12 carries the reasoning and the three-way seal check that goes with it.
🔄 **2026-08-31: the layout moved and the free margin shrank from three words to
one. The paragraph above is left as written because it is what the 641-word
block did.** `RB_WORDS` is **718**, `RB_POISON_W` is 726, and `DW 80A02000 718`
prints `4 × ceil(718/4)` = **720** words — so `w718` at `0x80A02B38` and `w719`
at `0x80A02B3C` come back beside the seal at `0x80A02B34`. *(707 returned one
such word and 641 returned three; each was the remainder falling out that way.)*

🆕 **And that stopped being luck on 2026-09-01.** `probe3.c` carries
`rb_readback_shows_poison`, a compile-time assertion that **refuses to build a
layout whose `RB_WORDS` is a multiple of four** — such a block returns no poison
word at all and the over-run control stops existing without saying so.
`tools/test-rlxprobe.sh` `SM3b` is the mutation that proves it fires (asserting
on the assertion's NAME, since `SM3` already shows a bad layout does not build)
and `SM3c` is its population control.

🔴 **That is not a weakened control, and the reason is worth stating rather than
assumed.** A payload that writes past its own block writes **upward from the
seal**, so `w707` is the *first* word any over-run reaches; `w708`–`w710` could
only add evidence about an over-run of two words or more, which `w707` has
already caught. The three-word version was `641 mod 4 == 1` and nothing had
chosen it. Reading the remaining seven still costs one `DW 80A02B0C 8`.

⚠️ **What this does cost is a check on the reply's own length.** Three poison
words at a known offset made the last reply line self-identifying; one does not.
The compensation is that `tools/rbcheck.py` now parses `H_LAYOUT_RES/ROWS/BMP/
BMPK/SEAL` **out of the block** instead of hardcoding 384 and 640, so a capture
of either layout is readable without the tool being told which it is — and
`C2`, the control that fires when `--words` reads the seal at the wrong offset,
is what catches the case this margin used to.


**So: four bits per victim** — the seven verdicts plus `0` = *never written*,
which is the only lossless bitmap and the only one with a negative control inside
it. Sixteen full rows carry the boundary brackets and the controls, on **both**
channels, so `H1c`'s word-for-word cross-check survives.

⚠️ **Every bitmap line — on whichever channel carries it — carries its own start index.** Without it one
lost line silently deletes eight victims and shifts the rest; with it a truncated
capture is recoverable. **Do not ship a bitmap line without an index.**

⚠️ **And the sixteen rows are not decoration.** A bitmap cannot carry
`mb`/`ma`/`g` — the raw before / after / guard words that let a verdict be
**re-derived at the desk if the verdict logic is later found wrong**. `probe1`'s
own history is exactly that: the audit found `rlx_call0` never wrote `$2`, and
every trapped row's `v` was carrying a loop counter. Raw fields survive a bad
verdict function. A bitmap does not.

🔴 **AND HERE IS WHAT THE BUILT VERSION LOSES ANYWAY, STATED RATHER THAN LEFT TO
BE NOTICED.** The walk classifies in assembly with a full register file and has
none left to keep `ex` — the value the victim actually returned — in. So in the
sixteen rows **`ex` is RECONSTRUCTED from the verdict nibble** and the row says
so; `ma` and `g` are uncached reads of DRAM taken after the pass, and DRAM does
not move, so those two are raw. What is kept instead is the one case where the
nibble and the value can disagree about anything: **the raw value of the first
victim in each pass whose return matched neither constant** goes in the walk's
control block, and a return equal to the prime gets its own verdict
(`V_VOIDPRIME`, nibble 4) rather than being folded into *weird*. A reader who
wants `ex` for a victim that read STALE or FRESH can compute it; a reader who
wants it for one that read neither has it for the first such victim and a count
for the rest.

---

## 5. Group P — preflight, at the prompt, before anything is uploaded

Four cells, **eight commands** (`P1` is sent twice, `P2` is four `DW`s). **No upload, no `J`, zero risk to the device, and every one of them removes an
assumption a later cell would otherwise carry.** They belong to `R1h-2`'s (⏸ now written at `R3`'s seating prep, § 10b)
runsheet section; they are listed here because three cells below are conditional
on them.

> **Written before the cells.** `P1` is expected to show a *changed* `TC0CNT`;
> equal readings kill Group T outright. `P2` is expected to show bias garbage
> with no pointer, no self-reference, no period and no run of zeros; anything
> else moves the arena. `P3` is expected to return 23,527 bytes; a
> `Unknown command !` means the `DW` read-back must stay under 1,000 words and
> the encoding in § 4 is the only one that fits. **`P0` must show `00000000`, or
> nothing is uploaded at all.**

| cell | command | expected on the device (and its source) | refuted by |
|---|---|---|---|
| **`P0`** | `DW 8040D4A0 1` — the autoburn word, read **before** the `put` | word 1 = `00000000`. 讀+量, `H1a`/`G2`; this is `R0`'s flash-write control and it is not optional | **anything else. Stop. Nothing is uploaded.** |
| **`P1`** | `DW B8003108 1`, **twice, seconds apart** | 🔴 `LDR-07` rounds the word count up to a multiple of 4, so this one command prints **four** words — `TC0CNT`, `TC1CNT`, `TCCNR`, `TCIR`. Expect `TC0CNT` **different** between the two reads; `TC1CNT = 00000000`, `TCCNR = C0000000` **and `TCIR = 80000000`** unchanged (量, `REG-08`/`REG-09`/`REG-10`, `bench/2026-08-23/E.log:15`) — **four words come back and four are pre-registered**, or a change in the fourth passes unremarked in the cell whose whole purpose is raising `REG-07` off n = 1 | **equal `TC0CNT`** → the register is frozen, not a live mirror of the counter, and **Group T does not ship**. `TCCNR ≠ C0000000` → something writes it after `timer_init` and M9 is wrong |
| | | ⚠️ **This is not a rate measurement and must never be written up as one.** The counter wraps every 9.9998 ms; two console reads are seconds apart, so the delta is uniform mod 142,858 and carries no rate information. At 38400 the command echo alone exceeds one wrap | |
| **`P2`** | `DW 80A02000 16`, `DW 80A10000 16`, `DW 80A50000 16`, `DW 80A8FFC0 16` — head of the result block and head / middle / tail of the arena | high-entropy bias garbage. 量 `MEM-16`: uninitialised DRAM on this board is 89.5 % reproducible across a 16 h power-off against a **measured** null of 55.98 %, so it looks like structure and is not | 🔴 **any of: a word equal to its own address or to another address in the window** (`MEM-11`'s signature — uninitialised DRAM cannot produce its own address); **any aligned pointer-shaped word** `80xxxxxx`/`81xxxxxx`/`A0xxxxxx`/`B8xxxxxx` (`G0`'s pre-written condition, verbatim: *"any one pointer-shaped word and the address is re-picked"*); **a repeating period**; **sixteen zero bytes** (on this board zeros are not power-on bias); **any known magic** — `5A5AA5A5`, `00000144`, `DEADC0DE`, `524C5831`, `524C5832` |
| **`P3`** | `DW 80A00000 2000` | **23,527 bytes, 6.13 s** (算, `LDR-07`; `len("DW 80A00000 2000")=16`, `+2 +47×500 +9`) | `Unknown command !` (≈44 B) or a short whole-line reply → **the loader will not take a 4-digit decimal length**, and every read-back in this payload must stay ≤ 999 words. ⚠️ This is the one preflight cell that costs real seconds; it is also the only thing standing between § 4's arithmetic and a read-back that silently truncates |

---

## 6. The cells

Every group opens with its predictions and refutation conditions **written
first**. Every expected value names its artefact. Where there is no source, the
cell says **留白** and does not invent one.

### 6.1 Group M — where the scratchpads are

**Settles: the precondition for ⓐ.** Without it, a walk that returns 16 KiB
cannot say which 16 KiB structure it measured.

> **Written before the cells.**
>
> **There is no prediction for the device, and that is the finding.** The loader
> contains **zero COP3 instructions** (§ 1.2), so at the prompt `IMEMBASE`/
> `IMEMTOP` hold **whatever reset left**, and nothing in any source says what
> that is. 🔴 **The kernel's values — `0x002B8000`/`0x002BBFFF` and
> `0x002C0000`/`0x002C1FFF` — are NOT a prediction for this cell.** They are what
> a different codebase chose after the loader had already handed over. Quoting
> them here as an expected value would be `E10d` a third time.
>
> **否證 M.** If `mfc3` traps with `CU3` already set, CP3 is not reachable from a
> payload and the scratchpad windows stay 未定 — in which case every geometry
> number in this payload carries the I-MEM residual explicitly, and `w-imem`
> becomes the only handle on it.

| cell | what it does | expected under qemu (source) | expected on the device (source) | refuted by |
|---|---|---|---|---|
| **`m-cu3`** | read `Status`, `or` `0x80000000` (`CU3`), write back, three `nop`, read back, **restore immediately**. No load or store in between | 🔴 **`before = 00000000`, `set = 00000000` — bit 31 does NOT stick.** 量(qemu) 2026-08-26, `qemu/2026-08-26/probe3.txt`. Malta's 24Kf masks `CU3` out of a `Status` write, and the same run proves the write path itself works: `CLEAR_BEV=1` cleared `BEV` through the same routine. **So qemu is a machine where a defined `Status` bit is masked, which is the positive control on this cell's mechanism** | bit 31 set in the read-back. 讀, this unit's kernel `0x8000221C`–`0x80002224` sets exactly this bit before its first `mtc3`, so the vendor judged it necessary in kernel mode; 讀 LX4189 § 3.4.1's `STATUS` figure puts `CU(3:0)` at 31–28 and § 2.4 says a Coprocessor Unusable exception follows a CP0-family access with the usability bit clear | bit 31 clear in the read-back → `CU3` is not implemented as a bit, and `m-imem`'s result must be read as *"CP3 answered without `CU3`"* |
| **`m-imem`** | 🔴 **set `CU3` again and hold it across the whole cell** — `m-cu3` restored `Status`, and `mfc3` with `CU3` clear traps **by construction**, which would be recorded as *CP3 unreachable* and would be an artefact of the running order. Then `mfc3` CP3 `$0`,`$1`,`$4`,`$5` (and `$2`,`$3`,`$6`,`$7`), **each read twice with two different primes**, with the `Status` read-back written to the block beside each result so that *trapped with `CU3` set* and *trapped with `CU3` clear* are separable at the desk. Restore `Status` at the end | 🔴 **all eight trap, `Cause = 0x1000042C` → `ExcCode = 0x0B` (Coprocessor Unusable), `m.traps = 000000ff`.** 量(qemu) 2026-08-26. ⚠️ **And on qemu the two explanations are CONFOUNDED**: `m-cu3` measured that `CU3` cannot be set there, so *CP3 is absent* and *`CU3` is masked* produce the identical reading, and the payload prints that it cannot separate them. **What the qemu leg does buy is real: sixteen non-`Bp` exceptions delivered to this handler and returned from, before the device ever sees one** — `x-ri`'s `ExcCode = 0x0A` is the other place | 留白. A base/top pair whose difference is `0x3FFF` would corroborate a 16 KiB IMEM; `0` in both would mean the window is unconfigured. ⚠️ **The LX4189 does NOT corroborate the CP3 numbering**: its IMEM/DMEM base and top are hardwired configuration pins (`CFG_IWBASE[31:10]`, `CFG_IWTOP[17:10]`, § 5.4) with no CP3 registers at all, so this SoC's core exposes something the core vendor's document does not describe. One source (the third-party `lxregs.h`) plus this unit's own kernel behaviour | **each read equal to its own prime → the destination was never written** — `F50b`'s failure, and the whole reason there are two primes; **both differing from their primes but from each other → unstable**; **both differing from their primes and equal → a value**. A trap → CP3 unreachable, see 否證 M |
| | ⚠️ **the two-prime read is `probe2`'s rule, not caution.** `F50b` spent a seating on *"reads zero"* being indistinguishable from *"the destination was never written"*, and `rlx_call0_primed` is what separated them (量, `nowrite=0` across 256 rows) | | | |

**What `m-imem` buys the rest of the payload.** The arena is generated at run
time, so the payload can **read the windows first and place the arena outside
them**, and record the choice in the result block. That is strictly better than
choosing at build time and hoping.

### 6.2 Group W — the I-side eviction walk

**Settles ⓐ for the I side.**

> **Written before the cells.**
>
> | | prediction | source, and its weakness |
> |---|---|---|
> | I-cache size | **16 KiB** | 讀 ×3, and one is a vendor doc **already in this repo**: `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` § 1 p.1 / § 2 / block diagram (*"16Kbyte I-Cache"*), already quoted at `SOURCES.json:195`; Realtek's own `arch/rlx/soc-rtl8196e/bspcpu.h`; and the third-party `rtl8196e.dtsi` (`i-cache-size = <16384>`). 🔴 **Read § 1.3 first**: that datasheet documents the `-VE1/2/3` variant, which `SOURCES.json` records this unit as **not being** (embedded DRAM by MCM vs this unit's external W9825G6KH, `MEM-01`, 量). The same claim is in the **public `RTL8196E-CG`** datasheet, a second Realtek document; family membership is 量 ×3 (`CPU-01`). **Two vendor documents about two variants of a family this die belongs to — not a reading of this die** |
> | I line size | **16 B** | 讀 ×1, third-party only — the dtsi. 🔴 **The datasheet gives sizes and no line size**: grep for *"cache line"*, *"line size"*, *"associat"* over all 11,467 extracted lines returns only switch-MAC-table hits. And the 16 B read out of this unit's kernel is **the D side** — eight `cache` ops at stride `0x10`, and the I side of that build has no per-line op at all |
> | associativity | 🔄 **NARROWED 2026-08-26 to {1, 2}, and the *"no source of any kind, anywhere"* form is withdrawn.** LX4189 § 5.1 Table 18: the `ICACHE` LMI is *"Direct mapped or two-way set associative"*, and § 5.3 describes the two-way form's LRU and lock bits in detail. So the I side has exactly two candidates | 讀 ×1, **core vendor, and a different part** — read § 1.4 before quoting it: the LX4189 has no TLB and this die has 32 entries (量 `CPU-08`). Not in the Realtek datasheet, not in `bspcpu.h`, not in the dtsi, not in any GPL drop. **`w-assoc` returning K = 4 refutes this bloodline**, which is more than the cell could do yesterday |
>
> **否證 ⓐ, restated as the payload will check it.** At the smallest working set
> — 1 KiB, smaller than any plausible cache — **every victim must come back
> `01` STALE**. One `02` FRESH there and the walk is not measuring capacity
> eviction: **the size number is void, not approximate.**
>
> 🔴 **And the positive control, which `否證 ⓐ` does not state and which
> `CLAUDE.md` requires.** At the largest working set — 64 KiB, larger than any
> plausible I-cache on a 4 MiB device — **most victims must come back FRESH**.
> A walk that returns all-STALE everywhere has not proved the cache is huge; it
> has proved it cannot evict, and *that* tool cannot fail. **Both controls are
> checked before any boundary is reported.**
>
> 🔴 **The qemu column for this entire group is a constant.** 量(qemu) this
> session: a victim executed, patched through KSEG0, re-executed reads
> `000022b2`; patched through **KSEG1**, it also reads `000022b2`. TCG keys
> translation-block invalidation on the **physical** address and both windows
> unmap to the same page, so the alias buys nothing under qemu.
> **Every W cell is FRESH under qemu at every N and every S, so there is no
> boundary to find** — and **否證 ⓐ's negative control is *guaranteed to fail*
> under qemu.** `R1h-1`'s harness must not assert it, or the suite goes red for
> the right reason at the wrong time.

| cell | what it does | expected under qemu | expected on the device | refuted by |
|---|---|---|---|---|
| **`w-line`** | in one 1 KiB-aligned block: execute `V0` at `+0`; then **uncached-store** NEW into **`V0`'s own patched word** and into probe victims at 🔄 **`+8, +16, +24, +32, +48, +64, +96, +128, +160, +192, +256, +320`**; then execute each | all FRESH (量(qemu) 2026-08-26, `w.line.bits=22222222`, `bits2=22222000` — thirteen probes, every one `V_FRESH`) | **`+8` STALE, `+16` FRESH** → a 16-byte line. The run of STALE starting at `+8` is the fetch granularity | 🔴 **`V0` itself FRESH → the block is void.** It was demonstrably fetched, so at any line size ≥ 4 B it MUST read STALE: it is the **must-fire** control, and without it *all FRESH* is indistinguishable from an 8-byte line, a patch that missed, and a dead re-arm. ⚠️ **Under the new two-word victim `V0`'s patched word is at `+4` and its GUARD is at `+0`** — the first draft said *"`+4` FRESH"* meaning `V0`, and that phrasing is `probe1`'s layout, which is inverted here. 🔄 **STALE reaching `+256` → void, NOT `+192`**: LX4189 § 5.1 makes **128 bytes a legal line size on this family**, so the old gate would have recorded a real 128-byte line as a void measurement. **All FRESH (with `V0` STALE) → the line is ≤ 8 B, recorded 未定 rather than as a number** — `V0` fills `+0..+7`, so no probe lies inside its line |
| **`w-line0`** | the same block layout in a second, distant block, with **`V0` never executed** | all FRESH | 🔴 **all FRESH.** This is the negative control: nothing was fetched, so nothing can be stale | any STALE → the patch is not landing, or the arena is contaminated, and `w-line` is void |
| **`w-back`** | a third block with `V0` at `+136` (deliberately **not** 16 B-aligned); probes at `+112, +120, +128, +144, +152, +168` | all FRESH | 🔴 **`+128` STALE and `+144` FRESH** if the line is 16 B — i.e. the STALE set is exactly `[128,144)`, the line *containing* `+136`. **STALE extending backwards is the signature of a line fill; forward-only is prefetch**, and this cell is the only thing that separates them | STALE only forward of `+136` → `w-line`'s number is a prefetch depth, not a line size. 🔴 ⚠️ **`w-back` alone cannot separate `L = 32` from `L = 16` plus one next-line prefetch**: `+136` sits in the **lower** half of the 32 B block `[128,160)`, so both hypotheses stale exactly `[128,144+16)` and neither null fires. **`w-back2` is what separates them.** All FRESH → `L ≤ 8`, 未定 |
| **`w-back2`** 🆕 | a fourth block with `V0` at **`+152`** — the **upper** half of a 32 B-aligned block; patch `+156` (its own word, the must-fire) and probe `+128, +136, +144, +160, +168, +176` | all FRESH | **`L = 32`** stales `[128,160)`: `+128`/`+136`/`+144` STALE, `+160`/`+168`/`+176` FRESH. **`L = 16` + one next-line prefetch** stales `[144,176)`: `+128`/`+136` FRESH, `+144`/`+160`/`+168` STALE. **The two readings are disjoint, and that is the whole cell** | any other pattern → the fill granularity is neither, and `w-line`'s number is void |
| **`w-size`** | for W ∈ {1, 2, 4, 8, 16, 32, 64} KiB: fill the working set with victims at 32 B stride, execute all in order, uncached-patch all, execute all again, count FRESH | all FRESH at every W | **all STALE up to 16 KiB; FRESH appears at 32 KiB.** Source as above — 讀 ×3 for 16 KiB | **any FRESH at 1 KiB** → 否證 ⓐ, size void. **No FRESH at 64 KiB** → the walk cannot evict, positive control failed, size void |
| **`w-assoc`** | 🔴 **parameters chosen at run time from `w-size`'s answer C.** For T ∈ {C/8, C/4, C/2, C} and M ∈ 1…12: M victims at stride T, execute, patch, execute. The smallest T at which a small M evicts gives the way size; K = M−1 | all FRESH | **留白 — no source.** The cell reports (T, M) and the write-up derives K 🔄 **2026-08-31: it reports the whole ladder, not just the argmin** — `w.assoc.mt`, one byte per stride, plus `w.assoc.mtcap`. §6.2a has the predictions and the reason only ONE of the four bytes discriminates | `w-size` void → `w-assoc` is not run and says so in the block. 🔴 **Two controls of its own, both free: M = 1 at every T MUST read all-STALE** (one victim cannot self-evict), **and the largest M at the smallest T MUST show FRESH.** Neither firing means (T, M) is a number with nothing behind it. **T and M are recorded as absolute byte values beside the C they were derived from**, because `w-assoc` runs on `w-size`'s *unqualified* C — if `w-imem` later differs, `w-assoc` is 未定 and its T was the scratchpad's |
| **`w-imem`** | 🔴 `CCTL 0x020` (`IMEM0OFF`), then **`w-size` again, unchanged** | all FRESH both times | **identical to `w-size`** → **either** the arena was never in the IMEM window **or** `CCTL 0x020` did nothing. 🔴 **CP0 20 is write-only and reads zero (M4), so no cell in this payload can confirm a `CCTL` command was accepted** — *identical* is also the no-op reading. It is a pass **only** where `m-imem` returned a window and the arena is provably outside it; everywhere else it is **未定**. **If `m-imem` returned a window, one extra victim block goes INSIDE it**: that block MUST change across the `0x020` write, and without it this cell has no must-fire | 🔴 **different** → the first `w-size` was measuring the scratchpad. **That is a result, not a failure**: the difference is the IMEM geometry, and `w-imem`'s run is the I-cache one |

⚠️ **`w-imem` is the one cell that writes a `CCTL` command this project had ruled
out.** The rule was drawn because the command had **no name** (`notes/cache-model.md`:
*"this project does not write an unnamed command to a cache controller on a
one-device budget"*). As of § 1.2 it has one, from four sources, and it is the
only instrument that separates a 16 KiB cache from a 16 KiB scratchpad of the
same size. **`0x010` (`IMEM0FILL`) stays out** — it stalls the core through a
full 16 KiB line-read burst, and nothing on this unit has issued it after the
prompt. `IMEM0OFF` clears one valid bit; the payload ends in `rlx_reset` and the
loader re-runs its whole reset sequence, so the restore is the reboot.

#### 6.2a 🆕 2026-08-31 — what Group W reports that it did not, and the predictions, written before the seating

Two instruments, both from `R3-9`'s carried-forward rows. **Neither adds a cell**
— they change what the two cells that already ran are able to *say*.

##### ① The `M(T)` ladder, `w.assoc.mt`

`w-assoc` swept four strides and reported only the winner. The other three
readings were discarded, and a stride at which **nothing in 1…12 evicted** left
no trace at all — *nothing evicted* and *this stride was never swept* were the
same observation, which is this file's own *a tool reporting 0 is making a
claim* in a search loop. One word now carries all four, one byte each, MSB
first: `0` = swept and nothing evicted, `1`…`12` = the smallest M that did,
`0xFE` = stride below the minimum, `0xFF` = not reached because the `M = 1`
control aborted the sweep. `w.assoc.mtcap` carries, per stride, the M at which
the arena refused — `w.assoc.capped` counts those and a count cannot say where.

🔴 **The reason this is worth two words is that the winner does not
discriminate and one loser does.** 讀, for `C` = 16 KiB with 16-byte lines,
comparing two-way (512 sets) against direct-mapped (1,024 sets):

| stride | set advance, 2-way | set advance, DM | M, 2-way | M, DM |
|---|---:|---:|:-:|:-:|
| `C/8` = 2,048 | 128 of 512 | 128 of 1,024 | **9** | **9** |
| `C/4` = 4,096 | 256 of 512 | 256 of 1,024 | **5** | **5** |
| `C/2` = 8,192 | 512 ≡ 0 | 512 of 1,024 | **3** | **3** |
| `C` = 16,384 | 1,024 ≡ 0 | 1,024 ≡ 0 | **3** | **2** |

> **PREDICTED: `w.assoc.mt = 09 05 03 03`.** Direct-mapped predicts
> `09 05 03 02`. **One byte carries the whole difference** and the other three
> are shared — so the ladder is one discriminator reported four ways, not four
> pieces of evidence, and a write-up that counts it as four is wrong.
>
> 🔴 **AND THIS DERIVATION IS NOT NEW HERE — `docs/rlx-cache-and-cp0.md` § *the
> argument for two-way* has had it since 2026-08-29, and the two agree.** That
> file tabulates M at 4096 / 8192 / 16384 for FIVE hypotheses — 8 KiB 2-way,
> 16 KiB 1-way, 16 KiB 2-way, 16 KiB 4-way, 32 KiB 2-way — and reads
> `(8192, 3)` as unique to 16 KiB two-way; the rows above reproduce its 2-way
> `5, 3, 3` and its direct-mapped `5, 3, 2` independently, and add the `C/8`
> column it does not carry. **So what `w.assoc.mt` changes is not the argument
> but where it lives**: the argument was reconstructed at the desk from a single
> reported argmin, and the ladder puts the evidence for it in the block. Quote
> that file for the hypothesis space; quote this section for what the payload
> now emits.

>
> **PREDICTED: `w.assoc.mtcap = 00 00 00 00`.** `A_ASSOC_SPAN` is `0x38000` =
> 229,376 B and the largest request is 12 × 16,384 = 196,608 B, so the arena
> refuses nothing. 量 2026-08-29 `w.assoc.capped=00000000` agrees, and the two
> are computed by different code from the same span.
>
> **REFUTATION.** Any byte outside {2, 3, 5, 9, 0xFE} at its own stride, or a
> ladder that is not monotonically non-increasing in T, and the eviction model
> behind `CPU-25` is wrong rather than the associativity. A `0` at `C/2` or `C`
> would mean 12 victims all mapping to one set evicted nothing — which refutes
> the whole walk, not the geometry.

⚠️ **What the ladder does NOT do: it is not new evidence.** 量 2026-08-29
already reported `w.assoc.tm = (8192, 3)`, and the search keeps the *strictly
smaller* M, so a direct-mapped part would have reported `(16384, 2)`. **The
2026-08-29 reading already excluded direct-mapped.** What it did not do is let a
reader see that: the exclusion ran on an argument about the search's
tie-breaking, and the block held nothing to check it against. The ladder makes
the same exclusion readable. **`CPU-25` does not become more certain; it becomes
checkable**, and the difference is stated because inflating one into the other
is exactly the move this file exists to prevent.

##### ② The retained bitmap, `O_BMPK`

The block advertised the boundary point's *pattern* as surviving to the
read-back. It did not — § *The retained bitmap does not survive to the
read-back* below has the measurement. The scratchpad has seven users and the
last of them wins. `O_BMPK` is a 64-word copy taken the instant the boundary
point's own counts are computed, and `H_BMP_KEPT` says how much of the point it
holds.

🔴 **What the pattern buys, and it is the second route to the same answer.**
At the boundary point the victims are 32 B apart, so the set index advances by
**two** per victim. Under two-way (512 sets) victims **k and k+256 share a
set**; under direct-mapped (1,024 sets) every victim of the 512 has its own set
and no two ever share.

> **PREDICTED, two-way**: the FRESH victims arrive in `{k, k+256}` **pairs**.
> When something outside the sweep (the walk's own instruction fetches) occupies
> a third line in set *s*, both victims of that set thrash and both miss on the
> re-execution. 量 2026-08-29 `bmp.rerun.fresh = 20` — so **ten pairs**.
>
> **PREDICTED, direct-mapped**: the same 20 FRESH arrive as **isolated
> singletons**, because a conflict in one victim's set says nothing about the
> victim 256 away.
>
> **REFUTATION, and it is the reason this is worth a region.** 20 FRESH split as
> 10 pairs versus 20 singletons is a difference no summary count can show, and
> the two hypotheses give the *same* count. **If the FRESH victims are neither
> — some paired, some not — the pairing model is wrong and the ladder above is
> the only route left.** An odd `bmp.rerun.fresh` refutes pure pairing
> immediately; 20 is even, which is a necessary condition the 2026-08-29 run
> already passes and nothing noticed.

⚠️ **`bmp.kept` is capped at 512 nibbles and the cap is not free of assumption.**
It is exactly `bnd_count` at the 16 KiB boundary 量 2026-08-29, two pairing
periods under the two-way hypothesis and one under direct-mapped. A boundary
above 16 KiB truncates — and a boundary above 16 KiB has already refuted
`CPU-25`'s size, so the truncation only bites in a run whose headline has
changed. **`tools/rbcheck.py` C17…C23 check the region against
`H_BMP_FRESH`**, which is the payload's own count of the same victims: two
numbers over one region, computed by different code at different times, which
is the only thing that can catch a snapshot taken at the wrong moment.

##### What both cost

**`RB_WORDS` 641 → 707**, `DW 80A02000 707`, 8,345 bytes, **+0.19 s** on the
read-back. `hazlint` **0 violations in 874 loads** (804 before). Nothing on the
wire changes shape; no cell was added, removed or reordered; `flags` and the
`.bss` size are unmoved.

⚠️ **Those are the two instruments' own numbers and they are left as written.**
The payload moved again on 2026-09-01 — Group F, § 6.8 — so the *image* is now
`RB_WORDS` **718**, `DW 80A02000 718`, 8,486 bytes, `hazlint` **0 violations in
946 loads**. This paragraph says what the retained bitmap and the `M(T)` ladder
cost, which is a different question from what the payload weighs today, and
overwriting it would lose the first to answer the second.


⚠️ **The re-arm between every measurement point is `CCTL 0x002` (M2) plus a
rewrite of the arena to OLD.** That is one measured instrument used many times.
🔴 **Neither `w-line0` nor the 1 KiB control can detect a broken M2, and the
first draft of this file said they could** — `w-line0` never fetched anything, so
a failed invalidate leaves nothing behind; and a stale line left in place reads
**STALE**, which is the 1 KiB control's own expected value. **The detector is
free and it is the arming execution's own reading**: after the rewrite to OLD,
each victim's first execution MUST return OLD, and a victim returning NEW there
proves the invalidate did not take. **The sweep also runs ascending in W**, so a
FRESH victim at a large point cannot contaminate a smaller one.

### 6.3 Group T — the timer, and what it can and cannot buy

**Settles: nothing in `R1h` by itself. It is a second, independent mechanism for
ⓐ and ⓑ, and it is `R5-0`'s reconnaissance taken on a seating already paid for.**

> **Written before the cells.**
>
> 🔴 **`TC0CNT`'s count field is bits 31:4, not the whole word, and every read
> must be shifted right by 4 before it is used as a tick count.** 量, `REG-05`:
> this unit's `TC0DATA` reads `0x0022E0A0` = `142,858 << 4`, exactly the
> compiled-in image value, so the shift is measured on silicon rather than
> assumed; `REG-07`'s single reading of `TC0CNT`, `0x0010B960`, is `0x0010B96` =
> 68,502 counts. Bits 3:0 are Reserved and read zero. **A payload that subtracts
> raw words reports ticks × 16 and a wrap 16× too late** — and every number in
> this group would be wrong by that factor with nothing detecting it.
>
> **Single-access timing is impossible on this device and this is not marginal.**
> `TC0CNT` increments at **14,286,057 Hz** — 推, from two 量 inputs and nothing
> else: `CLK-04`'s measured tick of 100.0018 Hz × `REG-05`'s measured
> `TC0DATA = 142,858`. One tick is **69.9983 ns**, and a DRAM access is
> 0.43–1.43 ticks. The quantisation is the size of the quantity. **Loop-of-N
> only.**
>
> 🔴 **Do not use 14.9650 MHz.** That is `CLK-08b`'s **watchdog** clock, a
> different clock on the same die, 4.75 % away, and `CLK-08b` explicitly refuted
> `f_timer/14` as the watchdog's rate. Using it puts a 4.75 % error into every
> number here. 🔴 **And `SPEC.md` `CLK-02`'s name is wrong against the datasheet
> it cites**: `CLK-02` is labelled *計時器基底時脈*, but D § 8.2.8 defines
> *"Base clock = System_clock (Peripheral Lexra Bus)/N"* — so 200.0049 MHz is the
> divider **input** and 14.286 MHz is the **base clock**. Whoever reads the two
> side by side inverts a factor of 14.
>
> **The wrap is 142,858 ticks = 9.9998 ms, and the modulus is not a power of
> two**, so `after − before` masked to 28 bits is wrong. `if (d < 0) d += 142858`,
> valid for one wrap only. Every window in this payload stays under 3 ms.
>
> **否證 T.** `t-live` returning two equal readings kills the group. `t-cal`
> returning 0 means TC0 stopped under the payload and every timing cell is void
> and says so. A constant independent of the iteration count means the loop was
> elided or the bracket is measuring only itself.

> 🔴 **THE WHOLE qemu COLUMN OF THIS GROUP IS NOW ONE READING, AND IT IS NOT
> "未定" AND NOT "FROZEN".** 量(qemu) 2026-08-26, `qemu/2026-08-26/probe3.txt`:
> **every read of `0xB8003108` returns `FFFFFFFF`** — Malta has nothing mapped
> there and an unmapped uncached read returns all ones. The value is neither
> prime, so the load demonstrably *did* write its destination; the register is
> not frozen, it is **absent**. Every bracket therefore reports `0`, and the
> payload prints `Group T VOID -- TC0CNT reads all ones twice: there is no timer
> at that address on this machine`. *Nothing is there* and *the register is
> frozen* are different claims about a machine and the payload separates them.
> **The harness may assert the self-void on qemu; it may not assert any tick
> count there.**

| cell | what it does | expected under qemu | expected on the device (source) | refuted by |
|---|---|---|---|---|
| **`t-live`** | two `lw` from `0xB8003108`, both primed, **separated by a short calibrated loop of ≫ 1 tick** — back to back they may be closer than the 69.9983 ns LSB (`t-ovh` says that latency is unmeasured), and *equal* would then be the reading of a perfectly live counter | 🔴 **`FFFFFFFF` on both the back-to-back and the separated pair** (量(qemu)); the group self-voids and says which of the three reasons it is | **different values.** 量 `REG-09` (`TC0En=1`, `TC0Mode=1`) + `CLK-04` (the tick advances, which requires counting) | equal **on the separated pair** → frozen register, group void. ⚠️ **Equal on a back-to-back pair is not a refutation and does not void the group.** Second < first without a wrap → the read disturbs it (the `PSRP` bit 8 read-to-clear precedent, 量 `NET-11`) |
| **`t-ovh`** | K back-to-back reads for **K = 1, 100, 1000, 4000**; regress. K = 1 and K = 2 differ by less than the 1-tick LSB and carry no leverage — a two-point fit plus noise | 🔴 **`0` at every K** (量(qemu)) — the bracket subtracts `FFFFFFFF` from `FFFFFFFF` | 留白 — **no file in this repo contains a measurement of an uncached KSEG1 register-read latency.** Slope = cost per ITERATION in ticks (one uncached read plus three ALU/branch, which is the loop the payload actually emits); intercept = bracket overhead | **the K = 4000 reading failing to scale when K doubles** → the bracket is measuring itself. ⚠️ **A slope of exactly 0 cannot occur under tick quantisation and is therefore not a refutation** — the first draft of this row named it as one, which is a condition that cannot fire |
| **`t-cal`** | bracket the existing 3-instruction loop at **two** counts, **140,800 and 70,400** — 否證 T's *constant independent of the iteration count* limb cannot be evaluated at one point, and **the ratio is what separates *the loop was elided* from *TC0 stopped***, both of which report ≈ 0 at a single count. That is `probe1`'s `GEOM` defect exactly: one number, two reasons | 🔴 **`0` at both counts** (量(qemu)) | **14,286 ticks.** 算 from 量 `CLK-03` (`f/CPI = 1.408e8` iter/s, n=1, `bench/2026-08-25/H1b.timing`) × 14,286,057 Hz. 10.0 % of the wrap — no wrap, comfortable | 0 → TC0 stopped under the payload. ~2× or ~0.5× → **CPI is not 3, and this cell has just separated what `CLK-03` could not** (400 MHz × 6 cycles vs 200 MHz × 3) |
| **`t-hit`** | 🔴 **a 4 KiB working set — half the predicted D-cache — traversed 32 times at 16 B stride**, once through KSEG0 and once through KSEG1, each bracketed, with **one warming pass discarded**. **The iteration count carries N, the footprint does not**: after the warming pass every cached access is a hit, so the KSEG0 leg measures **residency** rather than miss latency. ⚠️ **A single sweep of a working set larger than the cache measures miss latency in both windows and is not a residency instrument** — 4096 loads at 32 B stride would touch 128 KiB once, i.e. 4,096 compulsory misses, and *equal* would then be the expected reading on correct silicon | 🔴 **`0` for the warming pass and both legs** (量(qemu)) | 留白. 推: the uncached loop is several times the cached one. N=4096 gives 1,760–5,850 ticks of signal against a 1-tick LSB | equal → either the timer is not counting (contradicts `t-cal`) or KSEG0 is not cached, which would refute M1 by a route with no cache cell in it |

🔴 **What `t-hit` is really for, and it is the sharpest thing in this payload.**
Cell `c-A`'s negative reading is a **disjunction**: *no read-allocate*, *the
alias is snooped*, or *the line was evicted*. Eviction is excluded by the
two-victims-far-apart trick. **The remaining two are not separable by any
experiment that observes only through the alias** — see § 6.5. A *timing* signal
observes residency without going through the alias at all, so it is the only
route on this device that could split them. `t-hit` at 70 ns resolution over
4096 iterations is a coarse version of that route, and whether it is good enough
is exactly what `t-ovh` decides.

### 6.4 Group H — the handler, and Group X — the `cache` instruction

**Settles ⓒ, and gives `CPU-04` its first capability measurement.**

> **Written before the cells.**
>
> 🔴 **qemu cannot answer ⓒ in either direction, and its answer will look like a
> confirmation.** 量(qemu) this session: `cache 0x10`, `0x11`, `0x15`, `0x19`,
> `0x1b` all retire with `n=0`, and so do **all 32 values of the op field**,
> including ones MIPS32 leaves undefined. **qemu does not decode the op field at
> all.** If the device also retires, the qemu run will read as agreement and will
> be nothing of the kind.
>
> **The MIPS32 encoding and the Lexra names coincide on four of five** (讀(ext)
> for the MIPS32 side, 讀 `cache-rlx.c` for the Lexra side): `0x10` = Hit
> Invalidate I = `IInval`; `0x11` = Hit Invalidate D = `DInval`; `0x15` = Hit
> Writeback Invalidate D = `DWBInval`; `0x19` = Hit Writeback D = `DWB`.
> 🔴 **`0x1b` does not**: MIPS32 decodes it as Hit Writeback **Secondary**, and
> Lexra calls it `DWB_IInval`, a composite MIPS32 has no encoding for. It is also
> the one op with **zero occurrences** in this unit's kernel, so the binary cannot
> adjudicate it. **`0x1b` is not in this payload** — issuing a secondary-cache op
> on a part with no secondary cache is a cell whose refutation condition cannot be
> written honestly today.
>
> **否證 ⓒ, from `PROGRESS.md`, and the payload obeys it literally:** a `cache`
> instruction that neither retires nor traps — the payload hangs — refutes the
> handler, not the instruction. **`probe3` writes each cell result to the block
> BEFORE issuing the instruction**, exactly as `probe1` does.

| cell | what it does | expected under qemu (source) | expected on the device (source) | refuted by |
|---|---|---|---|---|
| **`h-brk`** | re-run `probe2`'s `break` control after installing and reading back the handler | `count=1`, `cause` ExcCode 9 — **only with `CLEAR_BEV=1` and `RET_ERET=1`**, because qemu enters with `Status.BEV=1` (量(qemu), `status.entry=00400000`) | `count=1`, `cause=00000024`. 量 `bench/2026-08-25b/H2a.log` | `count=0` → the handler did not take and **every X and M cell is void**. This is the gate for the whole group |
| **`x-ri`** | execute `0x0000000E` (SPECIAL, function `0x0E`) | 🔴 **traps, `ExcCode = 0x0A`.** 量(qemu) this session, two runs | 🔴 **留白, and the honesty is the point: no Lexra ISA document exists in this repository, so no encoding can be shown reserved on this core.** `refs/README.md` lists two Realtek datasheets and nothing else, and the RTL8196E one says *"Supports MIPS-1 ISA, MIPS16 ISA"* — MIPS16 needs `JALX` at opcode `0x1D`, so *"MIPS-I, therefore reserved"* is not a safe blanket. 量: **zero occurrences in `stage2.bin`**, with the scanner control being the two `rfe`s it does find | it **retires** → this core implements something there. That is a finding, and it leaves the RI path unproven — but **`h-brk` alone already licenses `x-11`**, because the handler branches on nothing (M3′) |
| | ⚠️ **Do not use `rfe` (`0x42000010`) as the RI control.** It is RI on qemu (量) and a **valid instruction on this core** — `exc.S` builds the device return path on it and `stage2.bin` contains two. It is the **inverse** control: it must retire on the device and trap on qemu | | | |
| | ⚠️ 量(qemu): the obvious picks do **not** trap — `0x78000000` (opcode `0x1E`), `0x00000005`, `0x70000000`, `0x7C000000` all retire, and `mfc2` gives RI rather than CpU. Anyone choosing a reserved-*looking* encoding from a table would have chosen one of these | | | |
| **`x-11`** | write the row, then execute **one** `cache 0x11, 0(base)` with `base` pointing at a `probe3`-owned scratch word; read `exc_rec[0]`, `Cause`, `EPC`, and the scratch word and its two neighbours, before and after | **retires, `n=0`** (量(qemu)). **Vacuous** | 留白 — the disjunction is the answer. 讀: this unit's kernel holds **37** D-side `cache` ops at `0x8000CA40`–`0x8000CD4C`, so the build believes they execute; *"in the binary"* is not *"executes"* | **the scratch word or a neighbour changed** → `0x2F` decodes as something else on this core, and the cell is void for ⓒ but is itself a finding. `Cause.BD` set → M3″, the instruction was in a delay slot, cell void |
| **`x-10`** | the same for `cache 0x10, 0(base)`, then a **functional leg that re-establishes its own baseline here**: execute two victims in one **fresh** block, patch both, treat **one** with `cache 0x10`, execute both. 🔴 **The untreated twin MUST still read STALE.** Without it, *the victim went FRESH* names six intervening stages of `CCTL 0x002`/`0x020`/`0x100`/`0x200`/`0x001` as readily as it names `cache 0x10` | retires, `n=0`. Vacuous | 留白. 讀: **zero** I-side ops in the whole kernel image, which is the shape `cache-rlx.c` produces for its RLX4181/5181 half | see `x-11`. If it retires but the victim stays STALE, it is implemented as a no-op — a third outcome neither `PROGRESS.md` nor `SPEC.md` had a slot for |
| **`x-15`, `x-19`** | conditional: **run only if `x-11` retired**, same protocol | retire | 留白 | **see `x-11`**: the scratch word or a neighbour changed → the op decodes as something else; `Cause.BD` set → M3″, cell void. ⚠️ **Gating on `x-11` answers ⓒ for one op and reports it for a family** — qemu does not decode the op field at all, so *uniform decoding* is precisely the assumption not to make |

🔴 **What `x-10` does and does not say about `CPU-04`.** `cache-rlx.c` gives the
D-side ops to RLX4181/5181/4281/5281 and the I-side ops to **4281/5281 only**;
this unit's kernel has zero I-side ops. So `x-10`'s outcome is a **capability**
measurement on silicon, and it is the first one this project will have. **It
still does not name the core.** `PRId = 0x0000CD01` is 量 and unmapped; the split
in `cache-rlx.c` is the *build's* belief about its own silicon. `CLAUDE.md`'s ban
stands and this cell does not lift it — see § 8.

### 6.5 Group C — coherence

**Settles ⓑ and ⓓ①.** The mechanism is the KSEG0/KSEG1 alias standing in for a
bus master, and **the proxy is a model, not the thing.**

> **Written before the cells.**
>
> | | prediction | source, and the vote on the other side |
> |---|---|---|
> | `c-E`: write-through or write-back | **write-back** — the cached store is held and the uncached read-back returns the OLD value | 讀 ×1: **both** GPL drops carry `CONFIG_ARCH_CACHE_WBC=y` in all five `boards/rtl8196e` variants. ⚠️ **One vote, not two** — the drops share an ancestor. 🔴 **And `probe1`'s six cells are consistent with write-through**: all six stores landed on lines the D-cache did not hold, where write-through and write-back-without-write-allocate give the identical reading. This is a genuine 50/50 with one source on each side |
> | `c-A`: is there a stale line | 🔄 **`l2 = P0`, a stale line — the 留白 is withdrawn 2026-08-26.** LX4189 § 5.2: *"**Note that a write to a KSEG1 address has no affect on the contents of the data cache.**"* If a resident clean line is untouched by an uncached store, the second cached load returns the OLD value | 讀 ×1, core vendor, **and a different part** — § 1.4. Nothing in any Realtek source speaks to read-allocation on this core, and the LX4189 sentence presumes the line is resident, which is what `c-A`'s own step 2 is doing |
> | `c-F`: does `CCTL 0x100` invalidate | **no** — `DWB` writes back and does not invalidate, so a stale line survives it | 讀 ×2: `cache-rlx.c`'s encoding table (`0x100 = DWB`) and `rlxregs.h:635` (`CCTL_DWB`). ⚠️ **Same SDK ancestor — one vote.** This unit's kernel issues it at `0x8000CA94`/`0x8000CAC0`; **its loader never does**, and **no source in this repository has ever recorded its effect** |
> | `c-B`: does `CCTL 0x200` invalidate | **yes** | 讀 ×2 (`DWB_Inval`), and this unit's loader issues it at `0x804066CC` |
> | `c-C`: does `CCTL 0x001` invalidate | **yes** | 讀 ×2 (`DInval`); this unit's kernel issues it at `0x8000CA24`, **its loader never does** |
>
> 🔴 **`c-E` is `c-A`'s positive control in only one of the two branches.**
> `docs/rlx-cache-and-cp0.md` § ② carries this in its narrowed form and owns it;
> **`PROGRESS.md`'s 否證 ⓑ still states it unconditionally and is the copy to
> fix.** What `probe3` adds is the cell that decides which branch obtains. If `c-E` shows a held
> store, the line was **resident**, so read-allocate is real and `c-A`'s *fresh*
> cannot mean *no read-allocate* — it means snooped (eviction being excluded by
> the far-apart pair). **If `c-E` shows write-through, it proves nothing about
> residency**, and `c-A`'s *fresh* stays a two-way disjunction. § ② claims E makes
> A interpretable full stop; that holds in the write-back branch only, and the
> write-up must not repeat the unconditional form.
>
> 🔴 **And in the write-through branch the two survivors are not separable from
> here at all.** *No read-allocate* and *the alias is snooped* differ only for a
> **real** bus master; every observation this payload can take goes through the
> alias. **For `R6`'s purpose they are equivalent** — under both, a cached read
> after a device write returns fresh data — *provided* a real DMA write looks like
> an uncached CPU store from the cache's side, which is the proxy assumption and
> cannot be tested without the engine. **`R6` re-tests it with the real engine
> before relying on it, and this file says so rather than letting the equivalence
> pass as a proof.** `t-hit` is the one instrument here that does not go through
> the alias.
>
> 🔴 **The qemu column for this whole group collapses to one reading.** 量(qemu)
> this session: TCG models no D-cache; `alias.load2` returns the **second** value
> (no stale line) and `alias.cellE` is **immediately visible** (no dirty line);
> `mfc0`/`mtc0 $20` retire with no effect; `cache 0x11`/`0x15` are no-ops.
> **A = A′ = B = C = D = E under qemu.** 否證 ⓑ is *inapplicable* under qemu, not
> merely unmet.

All cells use two targets in the arena, `probe1`'s trick against eviction, and a
guard word beside each. 🔴 **The separation is stated in the payload and is
deliberately not a power of two.** *Far apart* defeats **line sharing**; it does
not defeat **set conflict**, which happens at multiples of (cache size / ways) —
and both of those are exactly what Group V is there to measure, with
associativity 留白. **`c-A` therefore runs at two different separations**, so an
eviction artefact shows up as a disagreement between them rather than as a
negative result that would void Group C and Group V together.

| cell | what it does | expected under qemu | expected on the device | refuted by |
|---|---|---|---|---|
| **`c-E`** ⓓ① | uncached-store `P0`; **cached-load** X (this is the allocate); **cached-store** `P1` — a write **hit** on a resident line, the case no `probe1` cell exercised; **uncached-load** X | `P1` — "immediately visible", i.e. it always looks write-through (量(qemu)) | **`P0`** → write-back, the store is dirty in the D-cache | **`P1`** → write-through **or** the cached load never allocated (no read-allocate, so the cached store was a write **miss**) **or** the uncached load snoops. 🔴 **`P1` means write-through only if `c-A` established read-allocate positively** — write-through and write-back-without-write-allocate are exactly the pair ⓓ① exists to separate, and on a miss they give the identical reading. Otherwise `c-E` is recorded `void — residency not established`, and `CONFIG_ARCH_CACHE_WBC=y` is not refuted from a void |
| **`c-E0`** 🆕 | 🔴 **the write-buffer control, and it runs before `c-E2`.** 🔄 **It runs `c-E`'s WHOLE sequence again from its own uncached store — it does NOT continue from `c-E`'s state**, see § 1.4 ①. Then 64 uncached reads of an unrelated address (`TC0CNT`, whose line is nowhere near the target) before the measuring load | `P1` (量(qemu) 2026-08-26, `c E0 l3=5a5a0002`) | **`P0`** → the line is genuinely dirty, and only now can `c-E2` attribute a change to `CCTL 0x100`. The buffer this controls for is documented: LX4189 § 5.6, *"Writes that are serviced by the data cache may require extra time to be serviced by the LBC if its write buffer is full"* | **`P1`** → `c-E`'s `P0` was a **posted cached store the uncached load overtook**, not a dirty line. The write-policy verdict is void and `c-E2` does not run — after a `DWB` and a second load the buffer has drained under both hypotheses, so **`c-E2` alone is a cell that cannot fail** |
| **`c-E2`** | 🔄 **`c-E`'s whole sequence again, self-contained**, then `CCTL 0x100` (`DWB`), then uncached-load X | `P1` (量(qemu) 2026-08-26) | **`P1`** if `c-E` read `P0` → the line *was* dirty, and `CCTL 0x100`'s effect is measured for the first time anywhere | still `P0` → `0x100` does not write back, and its name is wrong on this die. 🔴 **AND THE VERSION OF THIS CELL THAT CONTINUED FROM `c-E` WOULD HAVE REPORTED THAT FOR THE WRONG REASON**: `c-E`'s own final uncached load invalidates the line (LX4189 § 5.2), so there would be no dirty line left for the `DWB` to write back and the cell would have refuted the command by an artefact of the running order. § 1.4 ① |
| **`c-A0`** | 🔴 **the negative control, and it runs first.** uncached-store `P0`; **no load**; uncached-store `P1`; cached-load X | `P1` | **`P1`** | `P0` → something else is stale and **every cell in this group is void** |
| **`c-A`** ⓑ | uncached-store `P0`; cached-load X (→ `l1`); uncached-store `P1` — the stand-in for the engine; cached-load X (→ `l2`); uncached-load X | `l2 = P1` (量(qemu), `alias.load2=aaaa0002`) | 留白. **`l2 = P0`** → a stale line exists: **the DMA-stale case reproduced with no DMA engine.** `l2 = P1` → no stale line, and the disjunction above applies | `l1 ≠ P0` → the first store did not land; the final uncached load ≠ `P1` → the second did not. Either voids the cell before its verdict is read |
| **`c-F`** | `c-A` with `CCTL 0x100` between the store and the second load | `l2 = P1` | **`l2 = P0`** — a write-back does not invalidate, so the stale line survives | `l2 = P1` → `0x100` invalidates too, and **`c-C` loses its safety precondition** (below) |
| **`c-B`** | `c-A` with `CCTL 0x200` | `l2 = P1` | **`l2 = P1`** — `DWB_Inval` invalidates | `l2 = P0` → `0x200` does not invalidate a clean line, and ⓑ's shortlist loses its best candidate |
| **`c-C`** | `c-A` with `CCTL 0x001` | `l2 = P1` | **`l2 = P1`** | `l2 = P0` |
| **`c-D`** | `c-A` with one `cache 0x11` over the line. **Conditional on `x-11` retiring** | `l2 = P1` (the op is a no-op) | **`l2 = P1`** if `x-11` retired and `0x11` really is `DInval` | `l2 = P0` → it retires and does nothing, which is `x-10`'s third outcome on the D side |
| **`c-G`** 🆕 ⓑ | 🔴 **the core vendor says an uncached READ invalidates a resident line, and nothing here had tested it.** uncached-store `P0`; cached-load X (→ `l1`, the allocate); uncached-store `P1`; **uncached-load X** (→ `l2`) — the claimed invalidator; cached-load X (→ `l3`) | `l3 = P1` (量(qemu) 2026-08-26, `c G VOID` — it is gated behind `c-A`, which is negative there, so qemu answers it in neither direction, exactly like `c-A` itself) | **`l3 = P1`** → the uncached read invalidated the line. 讀 ×1, LX4189 § 5.2: *"perform an uncached read of the affected memory locations. If the location is resident in the data cache it will be invalidated."* ⚠️ § 1.4's caveat applies in full | **`l3 = P0`** → this core does not do what the core vendor's document says its family does, and ⓑ's shortlist loses a candidate that costs one load. 🔴 **Readable only where `c-A` was positive**: with no stale line there is nothing to invalidate and both outcomes read the same, so it is gated with `c-B`/`c-C`/`c-F` |

🔴 **`c-B` and `c-C` are unfalsifiable if `c-A` is negative, and the payload must
say so rather than report a pass.** With no stale line to invalidate, every
treatment returns `l2 = P1` whether it works or not. **If `c-A` reads `l2 = P1`,
the payload writes `c-B`/`c-C`/`c-D`/`c-F` into the block as `void — no stale
line to act on`, and `c-E`/`c-E0`/`c-E2` as `void — residency not established`,
and reports no verdict for any of them.** 🔴 **The dependency runs both ways and
the first draft of this file had it one-way**: `c-E` assumes its own step 2
allocated, and that is exactly what `c-A` measures. A cell that returns the right
answer for the wrong reason is exactly what `R1g-1` pre-registered against.

🔴 **A safety note that is also a measurement.** `CCTL 0x001` (`DInval`)
invalidates the **whole** D-cache **without writing back**, so any dirty line the
payload owns is lost — including its own stack, if `c-E` came back write-back.
🔴 **The mitigation has to be INSIDE `c-C`'s own leaf routine, and the version
of this paragraph that said otherwise would have cost the power cycle.**
`rlx_call2_uncached` spills `$31` onto a **KSEG0** stack (讀, `cache.S:363-365 (rlx_call2_uncached:)`
— `addiu $29,$29,-8 / sw $31,0($29)`; `start.S:21-24 (lui $29, %hi(_stack_top))` and `rlxprobe.lds:83-87 (The stack lives above .bss)`
put `_stack_top` past `.bss`). Under the write-back branch that spill is a dirty
line; `DInval` discards it **without writeback**; the epilogue's `lw $31,0($29)`
then reads pre-writeback DRAM and `jr $31` goes to a wild address — the loader's
permanent hang, with no handler that can help.

**So: `CCTL 0x100` (`DWB`) and `CCTL 0x001` (`DInval`) are two consecutive
`mtc0`s inside one leaf routine** — no call, no return, no result-block write
between them — with `$31` held in a register across both, entered through KSEG1,
register-only, no stack reference at all.

🔴 **`c-F` is NOT that mitigation.** It is a separate cell and `c-B` runs between
it and `c-C` (§ 7 stage 6), so every frame pushed after `c-F` is dirty again by
the time `c-C` fires. What `c-F` *is*, is the measurement of whether `0x100`
writes back at all — **and if it reports that it does not, `c-C` does not run.**

### 6.6 Group V — the D-side eviction walk, armed at run time

**Settles ⓐ for the D side — the half that carries the prediction.**

> **Written before the cells.**
>
> | | prediction | source, and its strength |
> |---|---|---|
> | D-cache size | **8 KiB** | 讀 ×3, and they do not share an ancestor on this point: `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` § 1 / § 2 / block diagram (*"8Kbyte D-Cache"*) — ⚠️ **§ 1.3**, a variant this unit is recorded as not being, corroborated by the public `-CG` datasheet; **this unit's own kernel** — `sltiu … 0x4000` at `0x8000CAAC`/`0x8000CBE0`/`0x8000CCD4` and `sltiu … 0x2001` at `0x8000CA18`, read through `cache-rlx.c` as `cpu_dcache_size` and `× 2`; the third-party dtsi |
> | D line size | **16 B** | 🔴 **the strongest of the three, and it needs no source to interpret it**: eight `cache` ops at stride `0x10` covering exactly 128 bytes in this unit's own kernel *is* a line-size assumption whatever any document says |
> | associativity | 🔄 **direct-mapped, 2026-08-26.** LX4189 § 5.1 Table 18 gives the `DCACHE` LMI exactly one form — *"Direct mapped data cache"* — and Table 25's seven configurations are all *"direct mapped"*. Unlike the I side there is no second candidate | 讀 ×1, **core vendor, and a different part** (§ 1.4: the LX4189 has no TLB and this die has 32 entries). **`v-assoc` returning K > 1 refutes this bloodline** |
>
> ⚠️ **All of it is what a build and a draft datasheet *believe* about this
> silicon.** It is a prediction with a refutation condition, and it is only worth
> writing because it is written before the walk.
>
> 🔴 **Group V is armed by `c-A`.** Its observation channel — *an uncached write
> is invisible to a resident clean line* — **is** `c-A`'s positive reading. If
> `c-A` is negative, every V cell returns FRESH at every size, which is
> indistinguishable from *there is no D-cache*. **The payload checks `c-A` and,
> if it is negative, writes Group V into the block as `void — c-A negative`, with
> the reason, and does not run it.** That is the self-gating the whole running
> order is built around.
>
> **否證 ⓐ (D side)** is `w-size`'s, restated: every target STALE at the smallest
> working set, most FRESH at the largest, or the size is void rather than
> approximate.

| cell | what it does | expected under qemu | expected on the device | refuted by |
|---|---|---|---|---|
| **`v-line`** | cached-load the word at `+0`; **uncached-store** NEW at `+0` itself **and** at `+4, +8, +12, +16, +20, +24, +32, +64`; cached-load each | all FRESH — no D-cache modelled (量(qemu)) | **`+4, +8, +12` STALE; `+16` FRESH** → a 16-byte line. 🔴 **4-byte resolution — finer than the I side**, because a data word is 4 bytes and a victim function is 8 | 🔴 **`+0` FRESH → the block is void**: `+0` was demonstrably loaded, so it MUST read STALE — the must-fire, and Group V runs only when `c-A` was positive, so the control is already licensed. `+64` STALE → the STALE run exceeds any plausible line and the number is void |
| **`v-size`** | for W ∈ {1, 2, 4, 8, 16, 32} KiB, **one target per 16 B — `v-line`'s predicted line, and re-derived from `v-line`'s *measured* value before the sweep runs if it differs**: cached-load the whole set, uncached-store NEW over all of it, cached-load again, count FRESH | all FRESH | **all STALE up to 8 KiB; FRESH appears at 16 KiB** | any FRESH at 1 KiB, or no FRESH at 32 KiB — same two controls as `w-size` |
| **`v-assoc`** | as `w-assoc`, parameters from `v-size` | all FRESH | 留白 | `v-size` void |
| **`v-dmem`** | 🔴 **placement, not a treatment.** The D-side arena is chosen at run time to sit **outside** the `DMEMBASE`/`DMEMTOP` window `m-imem` read | — | — | if `m-imem` trapped, the window is unknown and every V number carries the D-MEM residual explicitly. **There is no `DMEM0OFF` cell**: `0x800` has one source and this payload does not write a command on one source |

### 6.7 Group S — is `Status.IsC` implemented as a bit

**Settles ⓓ②.** `SPEC.md` `CPU-19` 殘留 named `probe2` as the experiment; `probe2`
contains **no `mtc0` to CP0 12 anywhere**, by its own audit requirement — so that
experiment ran and did not include this. It is re-pointed here.

> **Written before the cells.**
>
> 🔴 **THE CONTROL BIT IS DECIDED, AND IT IS TWO BITS: 6 AND 24.** `R1h-0` left
> this 留白 with an instruction to name it with a source. The source turned out
> to be the **core vendor's own document**, fetched 2026-08-26 — LX4189 Data
> Sheet Rel 1.9 § 3.4.1, the `STATUS` register figure:
>
> ```
>  31-28    27-23   22     21-16   15-8      7-6   5    4    3    2    1    0
>  CU(3:0)    0     BEV      0     IM(7:0)    0   KUo  IEo  KUp  IEp  KUc  IEc
> ```
>
> > *"The 0 fields are ignored on write and are 0 on read. It is recommended
> > that the user explicitly write them to 0 to insure compatibility with future
> > versions of the LX4189."*
>
> | bit | LX4189 | R3000 | MIPS32 |
> |:-:|---|---|---|
> | **6** | inside the `0` field 7–6 | **reserved** — `arch/rlx/include/asm/rlxregs.h:97` carries the comment *"bits 6 & 7 are reserved on R[23]000"*, in **Realtek's own header for this architecture port** | `SX`, which enables 64-bit **supervisor** addressing and exists only on MIPS64 |
> | **24** | inside the `0` field 27–23 | **reserved** (the 24–23 run) | `MX`, the **DSP ASE** presence bit, a MIPS32r2 feature |
>
> `Config.M = 0` is 量 on this die (`probe2`, `bench/2026-08-25b/H2a.log`), so it
> is not a MIPS32 core and neither MIPS32 field can mean anything here.
> ⚠️ **Strictly, neither bit is *absent* from the MIPS32 figure** — both are
> drawn there, as 64-bit and ASE fields. The honest statement is *"reserved in
> the R3000 figure, a 64-bit/ASE field in the MIPS32 one, and inside a
> written-as-zero field in the core vendor's own"*, and that is what the write-up
> must say rather than the shorter claim.
>
> 🔴 **TWO of them rather than one, and that is not belt and braces**: a single
> control bit cannot see a **partial** write mask. Bits 6 and 24 sit at opposite
> ends of the register, so a mask that is not one contiguous decode shows up as
> the two disagreeing with each other — a reading no single bit could produce.
>
> 🔴 **AND THE DEVICE COLUMN IS NO LONGER 留白 EITHER.** The same LX4189 figure
> puts **bit 16 itself** inside the `0` field 21–16: on that part `IsC` and `SwC`
> do not exist at all. So the prediction is **bit 16 reads back CLEAR**, 讀 ×1,
> from a Lexra part. ⚠️ **The LX4189 is not this core** — its Table 2 lists CP0
> registers 8/12/13/14/15/20 and nothing else, so it has **no TLB**, and this die
> has 32 TLB entries (量 `CPU-08`; `Random` moved 5…29 inside 0…31). It is a
> sibling, not this part, and one vote from a sibling is what this prediction is.
>
> *(Kept as written:)* `c-r3k.c` uses `IsC`, but this SoC builds `arch/rlx/`,
> whose `cache-rlx.c` uses `CCTL` instead, so the vendor's own usage is weak
> evidence at best.
>
> **否證 S.** What is 量 already is **behaviour**: stores issued while `IsC` was
> set reached DRAM (`probe1` cell 4, `07` CORRUPT ×2). This cell reads the
> **bit**. The two are different claims and the write-up may not merge them.

| cell | what it does | expected under qemu | expected on the device | refuted by |
|---|---|---|---|---|
| **`s-isc`** | entered through KSEG1: read `Status`, set **`0x01010040`** — `IsC` (bit 16) together with the two control bits 6 and 24 — write, three `nop`, **read back**, restore, three `nop`. 🔴 **No load and no store between set and clear** — M5 | 🔴 **`before = 00000000`, `set = 00000000`, `restored = 00000000`; verdict word `0`.** 量(qemu) 2026-08-26, `qemu/2026-08-26/probe3.txt`. All three bits are masked on Malta's 24Kf, and the same run proves `Status` writes land there (`CLEAR_BEV` cleared `BEV` through the same routine). **So qemu is a worked example of a core WITH a write mask, which is the positive control on this cell's mechanism** | **bit 16 CLEAR and both control bits clear** — 讀 ×1, LX4189 § 3.4.1, and it agrees with `probe1` cell 4's behaviour. The 2×2 the payload reports: **16 set, control clear** → `IsC` is decoded and non-functional (M5). 🔴 **control bits set** → `Status` has no write mask, *bit 16 sticks* carries no information, and the cell reports **未定**. **16 clear, control clear** → not implemented as a bit, and cell 4's CORRUPT is fully explained — and `m-cu3` having stuck a bit earlier in the run is what makes that a measurement rather than *"the write did not land"*. **The two control bits disagreeing** → a partial write mask, which no single control bit could have shown | the restore not returning `Status` to its entry value → the cell has changed machine state it does not own, and everything after it is suspect |

🔴 **`SwC` is not in this payload, and the reason is specific.** `SwC` swaps the
I and D caches, and **what instruction fetch does while they are swapped is the
one thing this core has no documentation for** — `cache.S` already flags it. On a
core measured **not** to honour `IsC`, R3000 semantics cannot be used to argue
`SwC` is safe. ⓓ② closes on `IsC` alone and says so.

### 6.8 🆕 2026-09-01 — Group F, the memory-mapped SPI window, and it is the only instrument that can close `FW-34`

**Why it is in this payload rather than at the loader prompt.** `SPEC.md` §17's
remaining `FW-34` row asks whether the memory-mapped window prefetches a
sequential fetch stream. The seventeenth session withdrew the `FLR` cell that
was booked for it, and it did so on the strength of a disassembly rather than a
preference: `LDR-42` — the loader's `FLR` reads through `SFDR` programmed I/O
and its only mention of `0xBD000000` is a `printf` argument, so **no loader
command can measure the window at all**. `notes/kernel-build.md` §20.6 names
what is left: a bare-metal payload with a calibrated timer, and this project
has exactly one.

#### 6.8.0 🔴 What this repository does NOT already know, which is the reason for two of the four cells

**Nothing here has ever read through `0xBD000000` outside Linux.** `FLS-11` and
`MAP-12` both mark the value **量**, and the evidence both of them cite is the
loader printing `offset 0x003f0000<0xbd3f0000>` in its `FLW` message. §20's
`lui` census is what makes that citation fail: `0xbd00` occurs **exactly once**
in the whole loader and it is that `printf` argument, so what the device
emitted is a compile-time constant of the loader's, not a read. It is the same
shape as `icache: 16kB/16B` in `CPU-25` — a build constant wearing a
measurement's clothes — and the real 量 arrived on 2026-08-31 from somewhere
else entirely: `FW-34`'s four `busybox wc -lc` runs took 4,194,304 bytes
through `map->virt = 0xbd000000`, under Linux. **Both rows are corrected in the
same commit as this section.**

So this group may not assume the window is decoded at the loader prompt, and
`f-alias` and `f-live` are that assumption turned into two cells that can fail.

**And `0xBFC00000` is a second window, not the same one.** §19.7.2's ≤9× rests
on the sentence *"every instruction fetch of that loop is itself an uncached
read of the SPI device the loop is reading"* — stage 1 executes at
`0xBFC001D0`. That is a different physical decode (`0x1FC00000`) from
`0xBD000000` (`0x1D000000`), and **no cell in this repository has ever compared
them**. Timing only `0xBD000000` would leave *the two windows behave alike* in
the load-bearing position, unmeasured. Group F times both.

#### 6.8.1 The cells

Four cells, one new assembly primitive, **no command issued to the SPI
controller** — every access is a load, and `SFCR`/`SFCSR`/`SFDR` are never
written.

| cell | what it does | why it is not the obvious thing |
|---|---|---|
| **`f-sfcr`** | one uncached `lw` of `SFCR` (`0xB8001200`) | the divider is what turns ticks into SPI clocks, and until now the model carried `REG-13`'s **`0x3FC00000`** from a reading taken at the prompt on another day. This measures it **inside the run whose ticks it explains** |
| **`f-alias`** | the first 16 words of `0xBD000000` against the first 16 of `0xBFC00000`, pairwise | **the liveness control that needs no committed flash byte.** Two independent address decodes returning sixteen identical non-trivial words is a property no floating bus produces, and only the COUNT of mismatches enters the block — no flash content does |
| **`f-live`** | of words 1…15 at each window, how many differ from word 0 | separates *dead, and it reads as a constant* from *live*. A count of shape, not a copy of content |
| **`f-time`** | `rlx_tc_stride` over three address spaces × two strides, plus the first leg repeated last | the ratio is clock-independent and the absolute rate is clock-dependent; **neither alone is worth the words** and § 6.8.3 says why |

**`f-time`'s six legs, and they differ only in `base` and `stride`.** N = 1,024
loads each; the address advances by `stride` and is masked to a **64 KiB**
span, so the footprint is bounded whatever the stride is and both windows are
touched identically.

| leg | base | stride | span |
|---|---|---:|---|
| `f.win.seq` | `0xBD000000` | 4 | 4 KiB |
| `f.win.str` | `0xBD000000` | 1,024 | 64 KiB, 64 addresses, 16 revisits |
| `f.boot.seq` | `0xBFC00000` | 4 | 4 KiB |
| `f.boot.str` | `0xBFC00000` | 1,024 | 64 KiB |
| `f.dram.seq` | `ARENA + 0x20000`, KSEG1 | 4 | 4 KiB |
| `f.dram.str` | `ARENA + 0x20000`, KSEG1 | 1,024 | 64 KiB |
| `f.win.seq2` | `0xBD000000` | 4 | the FIRST leg again, run LAST |

🔴 **The DRAM legs are not decoration and they are not a floor.** They are the
same loop over memory whose behaviour is known, so they bound the loop's own
contribution — and, more importantly, **a strided DRAM read crosses SDRAM rows
and is expected to be slower than a sequential one on its own account**. That
confound is the whole reason the verdict below is a ratio of ratios rather than
a ratio.

#### 6.8.2 PREDICTED, written before the seating

推, every term named. Tick = **69.9983 ns** (`CLK-17`). SPI clock =
`CLK-02`'s **200.0049 MHz** ÷ `REG-13`'s DIV **4** = 50.0012 MHz, so one SPI
clock is 20.00 ns. A `Fast Read` re-issued per word is `cmd(8) + addr(24) +
dummy(8) + data(32)` = **72 clocks = 1.440 µs = 20.57 ticks**; held open, 32
clocks = **9.14 ticks**. The loop is six instructions, so at `CLK-01`'s 400 MHz
with CPI 1–3 it adds **0.21–0.64 ticks** per access — a minority term in every
band, which is why the CPI ambiguity does not have to be resolved first.

> **PREDICTED `f.win.str` ≈ 21,300–21,700 ticks** (1.49–1.52 ms), because a
> 1,024-byte stride defeats any buffer this controller plausibly has.
> **`f.win.seq` is the reading.** If it lands in the same band the window
> serves every access as its own transaction; at ≈ 9,800 it holds the read
> open; at ≈ 5,900–6,800 it buffers 16 B; at ≈ 3,100–4,500, 32 B.
>
> **PREDICTED `f.sfcr = 3FC00000`** (量 `REG-13`, at the prompt).
> **PREDICTED `f.alias = 00000000`** — the two windows are the same flash.
> **PREDICTED `f.live` both bytes ≥ 10** — flash offset 0 is loader code, and
> `nop` being `0x00000000` is exactly why the cell counts *differs from word 0*
> rather than *is not zero*.
> **PREDICTED `f.faults = 00000000`.**

**THE VERDICT, as bands on `R = f.win.str / f.win.seq`, written first:**

| `R` | what it establishes |
|---|---|
| **≤ 1.15** | **no buffering.** `FW-34`'s last row CLOSES: §19.7.2's ≤9× is 9× |
| **1.15 – 1.8** | indeterminate, and it is reported as that |
| **≥ 1.8** | the window buffers; implied burst ≈ **4 R bytes**, rounded to a power of two. `FW-34` NARROWS and does not close — see § 6.8.3 |

**And the control on the verdict**: `f.dram.str / f.dram.seq` must be
**strictly less** than `R`. If the DRAM ratio is as large, the difference
belongs to the loop or to SDRAM row misses and this cell says nothing about the
window at all.

**The absolute cross-check, which is a second question the same six words
answer.** `f.win.str / 1024`:

| ticks/access | what it establishes |
|---:|---|
| **20.6 ± 15 %** | 72 clocks at DIV 4 **and** the datasheet's *DRAM Clock* is `CLK-02`'s 200 MHz. §20.5 says nothing in this repository has ever asserted that identification; this is the first thing that tests it. Three facts at once — the cell does not separate them |
| **≈ 82** | DIV 16, the reset default, is still in force when `probe3` runs |
| **≈ 9** | the STRIDED leg is buffered too: the 64 KiB mask is inside the buffer and `R` is void, not small |
| anything else | not attributable |

⚠️ **This does not replace §20.5's `FLR` cell and must not be written up as
doing so.** `LDR-42` is that `FLR` reads through `SFDR` and this group reads
through the memory-mapped window: **two ports of one controller**. A `20.6`
here constrains §20.5's bands; it does not measure them.

#### 6.8.3 🔴 REFUTATION, and the asymmetry that has to be written into the answer

**Six conditions, each naming an outcome that would prove this wrong:**

1. **`f.faults ≠ 0`** — a load in this group trapped, and the handler's own time
   is inside the bracket. **Every tick in the group is void**, not merely
   suspect.
2. **`f.alias ≠ 0`** — the two windows are not one view. §19.7.2's *"the same
   SPI device the loop is reading"* loses its basis, and it is then `f.boot.*`
   and not `f.win.*` that bounds the ≤9×.
3. **either byte of `f.live` = 0** — that window returned sixteen identical
   words. A floating bus, not flash; every tick for that window describes a
   dead decode.
4. **`|f.win.seq2 − f.win.seq| > 10 % of f.win.seq`** — the instrument is not
   repeatable across the group it sits at the end of, and no ratio computed
   from it is worth reading.
5. **`f.win.str < f.dram.str`** — the window is faster than uncached DRAM,
   which nothing in this model allows. The framework is wrong, not one term.
6. **`f.sfcr ≠ 3FC00000`** — the divider is not what `REG-13` read at the
   prompt. The absolute table above has to be recomputed before any of it is
   quoted, and `f.sfcr` is what it is recomputed from.
7. 🔴 **any leg below `f.dram.str`, or a `f.win.str` under ~5,000 ticks** — a
   reading that has WRAPPED aliases to a small number, and every ratio computed
   from it is then arithmetic on a number that is not a duration.

🔴 **THE WRAP MARGIN, and Group F is the first cell in this payload that does
not fit inside the window § 6.3's own comment describes.** `TC0CNT` wraps every
**142,858 ticks = 9.9998 ms**, `tc_ticks` is valid for **one wrap only**, and
the file's timer comment says *"every window in this payload stays under 3 ms"*.
Group F's predicted band is 1.5 ms — but the worst case this model ALLOWS is
DIV 16 (the reset default, if something has written `SFCR` back) at 82.3
ticks/access, which is **84,275 ticks = 5.9 ms**: safe, at **59 %** of one wrap,
and a margin of 1.7× rather than 3×.

**What that costs and what it does not.** It does not move any band: 5.9 ms is
inside one wrap and `tc_ticks` handles it. What it costs is the head-room the
rest of the payload has, so **`f.sfcr` is read FIRST in the group and is the
thing to read first at the desk**: `3FC00000` says DIV 4 and the 1.5 ms band
applies. If a future `F_COUNT` is raised, the arithmetic above is what has to be
redone, and `1024 × 82.3 = 84,275` is the number to redo it from.

🔴 **THE ASYMMETRY, and `SPEC.md` §17's row must be written this way.** This
group times **data-side `lw`**. §19.7.2's amplification is **instruction-fetch
side**. The two meet because stage 1 executes in KSEG1, so its fetches are
single-word uncached bus reads exactly like these loads — but *exactly like* is
an argument, not a measurement, and the conclusion inherits the difference:

* **`R ≤ 1.15` CLOSES `FW-34`.** Nothing is buffered for a single-word read
  from this window, and an uncached instruction fetch is one.
* **`R ≥ 1.8` only NARROWS it.** The window buffers data reads; whether the
  instruction-fetch stream is served the same burst is not measured here, and
  the honest statement is a smaller upper bound with the mechanism named.

⚠️ **What this cannot see**, stated rather than left to be discovered:

* A buffer of **64 KiB or more** would be inside the mask and both legs would
  be fast. That is what the `≈ 9` row of the absolute table is for; an SPI
  window with a 64 KiB buffer on a part whose D-cache is 8 KiB is implausible,
  and *implausible* is the strength of the claim.
* The **first** access of each leg is a miss under every hypothesis and is
  inside the bracket. At N = 1,024 it is ≤ 0.1 % of any band and no band is
  narrower than 30 %.
* It says nothing about **writes**. `R5b` goes through `SFDR`; see §20.5.

#### 6.8.4 Where it runs, and what a fault there costs

**Stage 10, after Group S and before the restore** — `progress` `0xA8`,
appended between `P_ISC` (`0xA0`) and `P_RESTORED` (`0xB0`) rather than
renumbering, for the same reason header words 52, 53 and 54 were appended: a block
whose progress marks were renumbered cannot be compared to an older one.

It is last because it is **the first time this payload reads an address space
outside DRAM and the SoC register block**, and § 7's order is by that question
and no other. Everything Groups H through S measured is already in the block
when it starts, so a fault — or a bus that never answers — costs this group and
nothing before it. The handler installed at stage 1 is what makes a fault a
recorded outcome instead of the loader's permanent hang, and **no load in this
group sits in a branch delay slot**, which is `exc.S:41-44 (It adds 4 to EPC
unconditionally)`'s standing constraint.

---

## 7. Running order, and what survives a fault at each point

**Risk order, not numeric order** — `probe1`'s rule, and `RUNSHEET.md:974`
already warns that a reader who assumes otherwise misreads every row. **Every
cell writes its result to the block before the next one starts**, and word 2 is
`probe2`'s monotone progress marker, so a block recovered after a hang says
where the run stopped instead of leaving it to be inferred from what is missing.

| # | stage | progress | what is new here | what a fault costs |
|--:|---|---|---|---|
| 0 | poison the result block; **initialise the arena**; header; banner; `pc`/`rb`/`flags` stale-build checks | `0x10` | nothing — `probe1`'s opening, plus the arena (M7) | everything, and the block reads poisoned, which is a different observation from the previous run's data |
| 1 | 🔴 **Group H** — install the handler, read all 44 words back through KSEG1, `h-brk` | `0x20` | nothing — `probe2`'s, measured end to end | 🔴 **the gate, and it moved to the front for a reason.** It used to be stage 4, which left stages 1–3 — including the `CCTL 0x020` write, the first command this project issues that its own loader does not issue after reset — running with **no handler installed**, where any fault reaches the loader's permanent hang. It costs nothing new — it is `probe2`'s, measured — so there is no reason for it to run second. `h-brk` failing voids Groups M and X, and they do not run |
| 2 | **Group T** — `t-live`, `t-ovh`, `t-cal`, `t-hit` | `0x30` | one `lw` from a documented read-only SoC register | the timing group only. Placed first because it is the cheapest thing in the payload and, if it works, everything after it *could* carry timing |
| 3 | **Group W** — `w-line0`, `w-line`, `w-back`, `w-back2`, `w-size`, `w-assoc` | `0x40` | nothing: uncached stores, cached fetches, `CCTL 0x002`. **Every instruction here has already executed on this silicon** | ⓐ's I side |
| 4 | **`w-imem`** — `CCTL 0x020`, then `w-size` again | `0x50` | 🔴 the first `CCTL` command this project has written that its own loader does not issue **after** reset. Named by four sources (§ 1.2); the main W reading is already in the block | the IMEM discriminator only |
| 5 | **Group M** — `m-cu3`, `m-imem` | `0x60` | `mtc0` to CP0 12 (`CU3`, restored immediately) and `mfc3`. **A trap here is an expected outcome, not a failure** | the scratchpad windows; every geometry number then carries the I-MEM residual explicitly |
| 6 | **Group C** — `c-A0`, `c-A`, `c-A2`, `c-E`, `c-E0`, `c-E2`, `c-F`, `c-B`, `c-C`, `c-G` | `0x70` | `CCTL 0x100` is new from our side; `0x001` is new from our side; both are named and both are issued by this unit's own kernel | ⓑ and ⓓ① |
| 7 | **Group V** — armed iff `c-A` showed a stale line, and placed outside the D-MEM window | `0x80` | nothing beyond Group C | ⓐ's D side |
| 8 | **Group X** — `x-ri`, `x-11`, `c-D`, `x-10` and its functional leg, then `x-15`/`x-19` if `x-11` retired | `0x90` | 🔴 **the first `cache` instruction this project has ever executed.** Everything else is already in the block | ⓒ, and nothing before it |
| 9 | **Group S** — `s-isc` | `0xA0` | `mtc0` to CP0 12 setting a bit measured **not** to work | ⓓ②, and it is last because it has the least source support of anything here |
| 10 | 🆕 **Group F** — `f-sfcr`, `f-alias`, `f-live`, then `f-time`'s seven legs | `0xA8` | 🔴 **the first time this payload reads an address space outside DRAM and the SoC register block.** Two windows onto the SPI flash, and nothing here has read either of them outside Linux — `FLS-11`'s `量` cites a `printf` argument, § 6.8.0. The reads are loads; no command is issued to the controller and `SFCR`/`SFCSR`/`SFDR` are never written | `FW-34`'s last row, and nothing before it. It is last for the reason this column asks about: everything Groups H…S measured is in the block when it starts, so a fault — or a bus that never answers — costs this group alone. **The timing legs are gated on Group T** and stay at stage 0's poison when it did not ship |
| 11 | restore both vectors, read back, seal, `rlx_reset` | `0xB0` | `probe2`'s | — |

**Why `c-A0` runs before `c-A`.** It is the negative control; if it fails, `c-A`
was never worth running and the seating learns that in two loads instead of
after a whole group.

**Why Group T is first and Group S is last.** T is four loads from an address the
loader itself reads; S writes a `Status` bit with no documentary support on a
core already measured to mishandle it. Between those two poles the order is
"how many instructions has this silicon already executed?"

**Why `w-imem` is stage 3 and not stage 2.5.** The unqualified `w-size` reading
must be in the block before anything touches the scratchpad state, so that a
fault during `w-imem` costs the discriminator and not the walk.

---

## 8. What is deliberately not in this payload

| | why |
|---|---|
| 🔴 **`CCTL 0x010` (`IMEM0FILL`)** | it stalls the core through a full 16 KiB line-read burst from a BASE/TOP pair this payload did not program and may not have read. **`0x020` alone gets the discriminator; `0x010` only gets the state back**, and the payload ends in `rlx_reset`, so the loader's own reset sequence is the restore |
| **`CCTL 0x400`/`0x800` (`DMEM0ON`/`DMEM0OFF`)** | one source (`rlxregs.h`), absent from the LX4189 map entirely. **A register value does not enter code on one source.** The D-MEM is avoided by placement (`v-dmem`), not by command |
| **`CCTL 0x040`/`0x080`** | the sources **contradict each other** on bits 6–7: the LX4189 doc says `IROMOn`/`IROMOff`, Realtek's `rlxregs.h` says `IMEM0ON` and has nothing at bit 7, and hackpascal's header defines `ILock` as `0xc0`, colliding with its own `IROM0ON`/`IROM0OFF`. Undetermined is the honest state |
| **`cache 0x1b`** | the one op where the Lexra name (`DWB_IInval`) and the MIPS32 encoding (Hit Writeback **Secondary**) contradict, and the one with **zero** occurrences in this unit's kernel — so the binary cannot adjudicate it. A refutation condition for it cannot be written honestly today |
| **`Status.SwC`** | § 6.7 |
| **`rlx_r3k_size` / `GEOM=1`** | 量 dead: the algorithm needs isolation and `CPU-35` measured this core does not isolate, so it can only return `0` — which is also its *"the core does not answer"* value |
| **`rlx_isc_inv`** | 量: its byte stores reached DRAM and corrupted both victims (`probe1` cell 4) |
| **writing `TC1DATA`/`TCCNR`** to get an 18.79 s counter instead of a 10 ms one | it would be strictly better as an instrument, but it is a **register write** where every window in this payload already fits inside 3 ms of a 9.9998 ms wrap. Recorded as the upgrade path for `R5-0`, declined here |
| **flash** | 🆕 **2026-09-01: this payload now READS flash, and the row says so before it says anything else.** Group F issues uncached `lw` from `0xBD000000` and `0xBFC00000` — loads, and nothing else: no command reaches the SPI controller, and `SFCR`/`SFCSR`/`SFDR` are never written. § 6.8. 🔄 **no flash-write command, and the byte count is not this payload's to claim.** `P0` reads `AUTOBURN` before the `put` and the seating stops on anything but `00000000`, and every `--send` this payload's cells issue is a `DW`, a `J` or an `EW` into RAM — that is a **guard**. *(This row read “zero bytes” until 2026-08-30, which is the sentence `RUNSHEET` §B3's `G8b` forbids without a full re-dump hashed against `FLS-14`.)* The **evidence** is an `FLR` bracket, and `probe3`'s seating ran none; `bench/2026-08-30c/PREDICTIONS-B5-block2.md` §8 is where one is |

---

## 9. What makes the whole table void

| if | then |
|---|---|
| `P0` ≠ `00000000` | **nothing is uploaded.** The seating ends before it starts |
| `P1` shows an unchanged `TC0CNT` | Group T does not ship; everything else is unaffected |
| `P2` shows structure in the arena | **the arena moves** and `P2` is re-run. `MEM-14` is the standing proof that *"nothing has read it"* is not *"nothing writes it"*. 🆕 **2026-09-01: `524C5833` AT THE BLOCK BASE IS NOT ON THE LIST ABOVE AND THE OMISSION IS DELIBERATE.** `probe1`'s or `probe2`'s magic in `probe3`'s space means the block overlaps theirs, and both of those hold measurements recovered from DRAM — that is the failure. `probe3`'s **own** magic at `0x80A02000` means the previous `probe3` run's block is still in DRAM, and after `MEM-17` (量 2026-08-31: DRAM keeps written data across a power cycle) that is a **reading**, not a fault: stage 0 poisons the whole block before the first cell, so the run continues. Record the header words and carry on. ⚠️ In the ARENA the same word would still be a failure, because nothing writes `probe3`'s magic there |
| `P3` refuses a 4-digit length | the read-back stays ≤ 999 words; § 4's encoding is the only one that fits and there is no fallback to rows |
| the 1 KiB working set shows any FRESH | 否證 ⓐ. **The size is void, not approximate.** Do not round to the nearest plausible value — that is how a build constant is laundered into a measurement |
| the 64 KiB working set shows no FRESH | the walk cannot evict. The size is void the other way, and the tool could not have failed |
| `w-imem` differs from `w-size` | **the unqualified walk measured the scratchpad.** The `w-imem` run is the I-cache one; the difference is the I-MEM geometry, and both go in the write-up |
| `m-imem` traps and `w-imem` also cannot be run | ⓐ's I-side numbers are recorded **with the I-MEM residual attached to every one of them**, and the 16 KiB coincidence is stated in the same sentence |
| `h-brk` returns `count = 0` | Groups M and X do not run. The handler is not installed and a `cache` trap would reach the loader's permanent hang |
| `c-A0` returns `P0` | Group C is void and so is Group V |
| `c-A` returns `l2 = P1` | Group V is void with its reason in the block; `c-B`/`c-C`/`c-D`/`c-F`/**`c-G`** are recorded `void — no stale line to act on`, **not** as passes |
| `c-A0` disagrees between its two members, or `c-A` does | 🆕 **an eviction artefact, not a coherence reading.** Every Group C cell runs on a PAIR whose separation is deliberately not a power of two, and `c-A` runs at two separations; the payload prints `c PAIR DISAGREES` and both verdicts go in the block |
| `c-F` reports that `CCTL 0x100` does not write back | 🆕 **`c-C` DOES NOT RUN**, and that is a safety interlock rather than a data one: `CCTL 0x001` invalidates the whole D-cache without writing back, including this payload's own spilled `$31`, and the `DWB` in front of it is what makes the reload safe |
| the separated `TC0CNT` pair reads `FFFFFFFF` twice | 🆕 **there is no timer at that address on this machine** — a third state, distinct from *frozen* and from *the load did not write its destination*, and the payload names which one it saw. 量(qemu) 2026-08-26 |
| any arming execution returns FRESH | 🆕 **the `CCTL 0x002` re-arm did not take**, and every walk downstream of it is void. It is summed across every point into one header word, and it is the only W-group check that is assertable under qemu |
| the walk returns a size that is not a power of two | record **未定** rather than the number. A non-power-of-two is the walk measuring something else |
| 🔴 **a `CCTL` command was never decoded** | **no cell in this payload can confirm one was accepted.** CP0 20 is write-only and reads zero (M4), so any cell whose *pass* equals the no-op reading — `w-imem`'s *identical*, `c-F`'s `P0` — reports **未定**, not a verdict |
| a victim's guard word ≠ `03e00008`, or `OLD == NEW` for any victim | that victim can never read STALE or FRESH. The block is void **and names which victims** |
| any two of `P2`'s four windows read byte-identical | a stuck read path. Nothing else in `P2`'s list catches it, because bias garbage is *supposed* to look like structure |
| the D-side arena's relation to `DMEMBASE`/`DMEMTOP` is unknown | every Group V number carries the D-MEM residual — 🔴 **and the 8 KiB D-MEM is exactly the size of the predicted 8 KiB D-cache, the same coincidence as the I side**, stated in the same sentence as the number |
| two seatings and `c-A` still cannot be made to hold | `CPU-45` is **未定** and **`R6` carries the conservative cost**: rings *and* payload buffers in the uncached window, which is what the vendor's own driver does. The throughput number in `R6`'s DoD is then measured against that and compared with nothing |

---

## 10. What `R1h-1` had to build, and where it went wrong

**✅ DONE 2026-08-26.** The list below is kept as written; what each item became
is beside it.

**Build-system work, all of it hard-coded per payload (讀):**
`ISC_probe3 := 0`; `PAYLOADS += probe3`; `SRC_probe3`; `RB_WORDS_probe3`.
`tools/test-rlxprobe.sh` carries two of its own `for p in probe1 probe2` lists.
`RESULT_BASE` defaulted to `0x80A00000` and **`probe3` must be given
`0x80A02000`** — and § H1's standing warning applies: **`make` does not rebuild
when a knob changes, and `make show` prints the knob you asked for beside the
binary you already had.**

🔄 **The `RESULT_BASE` half was done differently and the difference is the
point.** *"probe3 must be given `0x80A02000` explicitly"* is an instruction to a
human, and it fails the first time the human is tired. What shipped is two
mechanisms instead:

1. **a per-payload default** — `RESULT_BASE_probe3 := 0x80A02000`, with a command
   line still winning, so `make P=probe3 payload` alone is correct;
2. **a parse-time refusal** — if `RESULT_BASE` names another payload's block,
   `make` stops with
   `RESULT_BASE=0x80A00000 is probe1's result block and probe1 has a measurement in it. Refusing to build probe3 onto it`.
   量 2026-08-26: it fires for `0x80A00000` and for `0x80A01000`, and the case
   fold is in it, because `0x80a00000` is the same address and a guard that
   caught one spelling is a guard the next person spells around by accident.

**Two more build-system facts that only appeared once it was built:**

- 🔴 **The asm file could not be called `probe3.S`.** The Makefile maps `%.S` and
  `%.c` onto the same `%.o`, so `probe3.S` beside `probe3.c` is one object built
  twice, linked twice, and a page of `multiple definition of` from `ld`. It is
  `cells.S`. Measured on the first build.
- 🔴 **`probe3` is the first payload that MAY contain words outside MIPS-I**, so
  its ISA check cannot be `probe1`/`probe2`'s zero. The image contains exactly
  **5 `cache` ops** (four in Group X, one inside `c-D`'s leaf) and **8 `mfc3`**,
  and the suite names every one of them by encoding and count. 🔄 **The label
  defect this paragraph used to record is fixed (`hazlint` 1.2, 2026-08-27), and
  the sentence it recorded it in was itself wrong.** It said opcode `0x13` is
  COP1X *"from MIPS-II onward"*. It is not: 量 on binutils 2.42, `mfc3`
  assembles under `-march=mips1` **and `-march=mips2`** and is refused at
  `mips3`; `lwxc1` is refused until `mips4`. 讀, MIPS IV Rev 3.2 A 8.3.4 —
  *"Coprocessor 3 is optional and implementation-specific in the MIPS I and
  MIPS II architecture levels. It was removed from MIPS III and later
  architecture levels. Note that in MIPS IV the COP3 primary opcode was reused
  for the COP1X instruction class."* **COP3 is MIPS I and MIPS II; MIPS III
  removed it; MIPS IV reused the opcode.** The conclusion is untouched — this
  core is MIPS-I (`Config.M = 0`, 量), so `0x13` is COP3 — and the gate was
  never affected, because the gate is the load-delay check.
  🔴 **What the fix deliberately did NOT do is take those eight words off the
  ISA watch list.** The same paragraph of the spec is why: at MIPS I the
  architecture makes COP3 *optional and implementation-specific*, so *it is
  MIPS-I* is not evidence that this silicon retires it — and **whether it does
  is § 6's `m-imem`, 否證 M, still open**. The eight are still hits; they are
  hits named `mfc3` at level `MIPS-I COP3`, each printed with its address and
  its rendering. The expected fingerprint is now asserted twice by
  `tools/test-rlxprobe.sh` T1, once through `objdump` and once through
  `hazlint --isa`: **13 hits, 8 `mfc3` + 5 `cache`, in both classifiers.**

### 🔴 One mutation per CHECK MECHANISM, and a coverage table that names the gaps

**Changed 2026-08-26 from *"one mutation per cell"*, and the reason is in this
file's own § 6.2.** There are about forty cells and twelve mutations, because on
the only harness that exists at the desk **most cache readings are identical
mutated and unmutated** — every W cell is FRESH under qemu, every C cell reads
the same value, every `cache` op retires. A mutation whose predicted effect
equals the baseline **cannot fail**, and forty of those would be forty near
duplicates of which half could not fire. Twelve mutations plus a table that says
which cell each one covers **and which cells nothing covers, and why**, is the
honest version. The suite went 106 → 195 cases.

**Six run without an emulator at all** (`tools/test-rlxprobe.sh` `SM1`–`SM6`),
which is the half that keeps working on a machine with no qemu, and the half
that can assert things qemu's own kindness hides:

| | mutation | what must fire | covers |
|:-:|---|---|---|
| `SM1` | `SAFE_A0` emits `nop` | the guardscan reports probe3's routines unguarded | every cell — the guard is what turns a fault from a hang into two prints |
| `SM2` | one extra `cache 0x1b` | the ISA fingerprint stops matching | `x-11`, `x-10`, `x-15`, `x-19`, `c-D`, and the § 8 promise that `0x1b` never ships |
| `SM3` | `RB_HDR` moved by one | **the build fails** — the layout assertion is at compile time | the whole block: `DW <RB> 707` reading the wrong length is a truncated capture that looks complete |
| `SM4` | a `mtc0 $x,$12` added to `rlx_cctl` | the Status-writer count AND its owner list both change | `m-cu3`, `s-isc`, and M5's constraint that nothing else touches `Status` |
| `SM5` | the `s-isc` control bits dropped | the constant leaves the image and the wire | `s-isc` — **and this one has NO qemu leg**, because all three bits read back clear on Malta whether they were set or not |
| `SM6` | the `RB_CLASH` guard removed | probe3 builds onto probe1's block | the seating-day procedure in § 10b |

**Six run under qemu** (`QM1`–`QM6`):

| | mutation | what must fire | covers |
|:-:|---|---|---|
| `QM1` | `x-11`'s `cache 0x11` → the RI encoding | it traps where the baseline retired, **and the `ISSUING` line is still printed first** | 否證 ⓒ's discipline: the row is written to the block **before** the instruction is issued, because a `cache` that neither retires nor traps hangs the payload |
| `QM2` | the arena is armed with NEW instead of OLD | every arming execution reports FRESH | the re-arm detector — the only W-group check assertable on both machines |
| `QM3` | the victim template's guard word corrupted | the payload **refuses to build an arena** and stops before the first walk | every W and V cell: a bad template means the walk jumps into whatever it wrote |
| `QM4` | `c-A`'s gate forced positive | Group V runs and reports FRESH at every size | the self-gate — that reading is indistinguishable from *there is no D-cache*, which is exactly what the gate keeps out of the block |
| `QM5` | 否證 T's all-ones branch removed | the reason disappears while the zeros stay | `t-live`/`t-cal`/`t-ovh`/`t-hit`: *nothing is mapped there* stops being separable from *frozen* |
| `QM6` | Group C's member b dropped | the `mb` field reads 0 | every C cell's pair — the eviction cross-check is a **disagreement** between two members, and nothing else could show it |

**🔴 And the cells NOTHING covers, named rather than left to be discovered:**

| cell / check | why no mutation can fire at the desk |
|---|---|
| `w-line`'s `V0`-only arming | under qemu every probe is FRESH whether or not the probes were fetched before the patch, so exec-all and exec-`V0` give the identical bitmap |
| `w-back` / `w-back2`'s direction discriminator | the same: there is no line to fill backwards from |
| `w-size` / `v-size`'s boundary, and both `assoc` cells | there is no boundary under qemu — every point is all-FRESH — so a mutation to the sweep changes nothing |
| **the `CCTL 0x002` half of the re-arm** | TCG invalidates its translation blocks on the store itself, so dropping the invalidate reads identically. `QM2` mutates the **rewrite** instead and therefore proves the detector can fire, not that the invalidate is needed |
| `c-E`/`c-E0`/`c-E2`'s write-policy branch | TCG models no D-cache, so a write hit and a write miss are one reading |
| `c-G`'s claimed invalidator | same — and it is gated behind `c-A`, which is negative under qemu |
| `m-imem`'s two-prime read | all eight stubs trap on Malta, so the prime states are never reached |
| `x-10`'s functional leg | both victims are FRESH under qemu, treated or not |

**Every one of those is covered on the device by its own must-fire control**,
which is written in the cell above it. That is the division of labour: qemu
checks the emitter, the device checks the claim, and this table is where the two
are kept from being confused for each other.

**Three mutations are worth naming in prose as well:**

1. 🔴 **Substitute `0x0000000E` for `x-11`'s `cache 0x11`.** Under qemu that
   traps (量), which proves the *"write the cell result **before** issuing the
   instruction"* discipline actually holds — without spending a device fault to
   find out. This is 否證 ⓒ made testable at the desk.
2. **Break the arena's `CCTL 0x002` re-arm.** 🔴 **This mutation has no qemu
   leg** — every W cell is FRESH under qemu unmutated (§ 6.2), so the predicted
   effect equals the baseline and the mutation cannot fail on the only harness it
   runs on. It is asserted instead against **the arming execution's own reading**
   (§ 6.2): a victim returning NEW where memory was just rewritten to OLD, which
   the harness checks in the emitted block on both machines.
3. **Emit the bitmap without its index field.** The harness must notice; a
   truncated capture is otherwise unrecoverable and looks complete.

🔴 **Where `R1h-1` will be wrong, written now.**

- **qemu will disagree with the device and that is the expected case.** Every W
  cell is FRESH under qemu, every C cell reads the same value, every `cache` op
  retires. **A qemu run that produces a boundary, a stale line, or a trap on a
  `cache` op means the harness is broken, not that qemu found something.**
- 🔴 **否證 ⓐ's negative control is guaranteed to fail under qemu.** The harness
  must not assert it there. Assert it only against a device capture.
- ✅ **The qemu expectations for `m-cu3`, `s-isc` and the whole of Group T were
  未定 and are now measured** — 2026-08-26, `qemu/2026-08-26/probe3.txt`. `CU3`
  does not stick on Malta's 24Kf, `s-isc`'s three bits all read back clear, and
  `TC0CNT` reads `FFFFFFFF` because Malta has nothing at that address. **Two of
  those turned out to be positive controls rather than blanks**: a core with a
  `Status` write mask is exactly what `s-isc` needs to demonstrate its own
  mechanism on, and *nothing is mapped there* is a third state Group T's
  refutation condition did not have and now does.
- ✅ **No qemu serial capture was committed anywhere in this repository, and
  now one is.** `qemu-run.sh` wrote to a `mktemp -d`; it writes to
  `tools/rlxprobe/build/qemu/` now, which is gitignored but survives the run, and
  `qemu/2026-08-26/probe3.txt` is the first capture this project has kept.
  `qemu/README.md` is a directory of its own beside `bench/` **precisely so that
  a reader sweeping for readings never has to work out which is silicon from a
  filename**.
- ✅ **The victim primitive changed shape** (§ 3: two words, guard first) and
  the verdicts were re-derived rather than copied. What that produced:
  `V_NOTVICTIM` is now **the guard read UNCACHED BEFORE the call**, so a bad
  victim is never called at all — `probe1` could only report a corrupted victim
  after jumping into it; `V_CORRUPT` is the same guard read **again across** the
  call; and `V_VOIDPRIME` was added, because a victim that returns the prime
  means the two instructions never executed and folding that into *weird* would
  lose it. 🔴 **The correction the re-derivation actually caught is in this
  file**: § 6.2's `w-line` row said *"`+4` FRESH → the block is void"*, which is
  `probe1`'s layout — under the new one `+4` is the PATCHED word and `+0` is the
  guard, so the must-fire is `V0` itself.
- 🔄 **The arena is generated at run time — and the gate still covers its
  words, which is better than the disclaimer this bullet asked for.** The
  instruction pair is **assembled in `.text`** (`rlx_vic_template` in `cells.S`),
  gated with everything else, and `rlx_w_arm` COPIES it. What `hazlint` does not
  see is the *replication*, and a replication introduces no instruction; the
  immediate the experiment rewrites is sixteen bits of an `addiu`, which cannot
  introduce a hazard. That is `victims.S`'s own argument preserved rather than
  waived. **The payload also reads the template back through KSEG1 at run time
  and refuses to build an arena if it is not the two words this file assembled**,
  which is the version of the check that can fail.

---

## 10b. 🔴 This payload sits on the shelf across two gates before it is seated

**Added 2026-08-26, after the schedule was settled.** The seating is at the
**tail of `R3`**, so `probe3` is built during `R1h-1` and run after the whole of
`R2` and `R3`. Three things follow, and none of them is optional.

**1. The binary in the tree on seating day is not to be trusted, and this project
has already paid for that lesson.** 量: `make P=probe2 payload
RESULT_BASE=0x80A01000` printed `Nothing to be done for 'payload'` — no compile,
no `show`, no `sha256` — while `build/probe2/probe2.bin` in the tree was a
`0x80A00000` build. The object rules depend on the sources and two headers and
on **nothing that carries a `-D`**.

### 🔴 THE REBUILD-ON-THE-DAY PROCEDURE

**Run this before the board is powered, and read every line of the output.**
It was run for the first time on 2026-08-26 and the numbers below are that run's.

```sh
# 1. empty the build directory.  Not `make clean` -- that removes every
#    payload, and probe1/probe2 in the same tree are what the runsheet's
#    earlier cells were built from.
rm -rf tools/rlxprobe/build/probe3

# 2. build.  RESULT_BASE is the per-payload default now, so it does not have
#    to be typed -- it is typed anyway, because a procedure that relies on a
#    default is a procedure that cannot be checked from its own transcript.
make -C tools/rlxprobe P=probe3 payload RESULT_BASE=0x80A02000

# 3. read the numbers back
make -C tools/rlxprobe P=probe3 show
```

**Five things in that output are checks, not decoration:**

| line | what it must say on 2026-08-26 | what a different value means |
|---|---|---|
| `make` itself | it **compiles**. `Nothing to be done for 'payload'` is a **HARD STOP** | the tree already held an image and nothing rebuilt; `show` will print the knob you asked for beside the binary you already had |
| `sha256` | 🔄 **`fc7b21d479478fcb925723237323176adc7946502a0e71588ae799a626e2824e`, 31,536 bytes, since 2026-09-01** — Group F. *(It was `6f78727507bb0364…` / 29,680 from 2026-08-31)* — the retained bitmap region and the `M(T)` ladder. *(It was `1a0725c0e925b8c3857802d01791768f6b8241dbcf271b1dbd391e287a5ecc0b`, 29,088 bytes, from 2026-08-26 to 2026-08-30, and byte-identical across three rebuilds in that window.)* | the sources moved. That is fine — but the number in `qemu/2026-08-26/probe3.build` no longer describes the image, and the qemu capture beside it was produced by a different payload |
| `result` | `RESULT_BASE=0x80A02000 … DW 80A02000 718` *(707 from 2026-08-31, 641 before that)* | anything else and the read-back is the wrong length or the wrong address |
| `stale check` | `rb=80a02000` | this is the **on-the-wire** check and it is what the operator watches for in the banner |
| `vectors` / `uart` | `general 0x80000080`, `THR 0xB8002000`, `CLEAR_BEV=0`, and **no `*** NOT A DEVICE BUILD ***` line** | a qemu image would install a handler into RAM this device never reads and then fault into the loader's permanent hang |

**And the on-the-wire check once it runs:** the banner must read `rb=80a02000` —
**lower case**, because `report.c`'s digit table is `"0123456789abcdef"` while
the loader's is upper, so `rb=80A02000` is a string a correct run never produces.
`rb=80a00000` or `rb=80a01000` means the binary is a `probe1`/`probe2`-based
build and is about to poison a block that holds a measurement. Since 2026-08-26
that particular mistake cannot reach a `.bin` at all — `make` refuses at parse
time — but the banner check costs nothing and covers the case where the image on
the day came from somewhere other than this Makefile.

**2. ✅ Every qemu column is closed.** The three that were 未定 — `m-cu3`,
`s-isc`, and all of Group T — were measured on 2026-08-26 and are in their cells
above. **And the first qemu serial capture this repository has ever committed is
`qemu/2026-08-26/probe3.txt`**, with `qemu/2026-08-26/probe3.build` recording the
host, the qemu version, the toolchain, both builds and the device image's
`sha256`; `qemu/README.md` says what a capture in there is and what it cannot
show. `tools/audit-bench-log.py` was run over both files — 8/8 patterns fire on
its synthetic control, 0 hits on the capture.

**3. The running order is fixed by physics, not by the schedule.** `probe3` runs
**first** in that seating. `R3`'s DoD is *my kernel boots to a shell and pings*,
and in that state the loader is gone, the DRAM is gone, there is no `<RealTek>`
prompt to type `J` into and no `DW` to recover the result block. **"At the tail
of `R3`" names which seating, not the order inside it** — `PROGRESS.md`'s
stop-loss has said `probe3` goes first since the gate opened, and the schedule
change does not touch it.

⚠️ **And Group P's preflight is cheap enough to re-run rather than trust.** `P0`,
`P1`, `P2` and `P3` cost eight commands and no power cycle of their own; the
readings they check (`TC0CNT` live, the arena free, the `DW` length ceiling) are
properties of a board that will have been power-cycled many times by then.

---

## 11. Where each answer lands

| | question | goes to | and to |
|:-:|---|---|---|
| ⓐ | size / line / associativity, both caches | `SPEC.md` `CPU-25` | `notes/cache-model.md` § *Cache geometry* |
| ⓑ | read-allocate, and what invalidates a clean line | `SPEC.md` `CPU-45` | `docs/rlx-cache-and-cp0.md` § ② — **decision ② names a measurement, or it names the next experiment. It does not name an argument** |
| ⓒ | does the core retire `cache` | `SPEC.md` `CPU-44` | `notes/cache-model.md` |
| ⓓ① | write-through vs write-back | `SPEC.md` `CPU-19` 殘留 | `docs/rlx-cache-and-cp0.md` § ② |
| ⓓ② | `Status.IsC` as a bit | `SPEC.md` `CPU-19` 殘留 | — |
| 🆕 | `CCTL 0x010`/`0x020` named; the I-MEM/D-MEM windows | `SPEC.md` `CPU-24` (closed 2026-08-26 on the desk), `CPU-24` 殘留, and `CPU-46` | `notes/cache-model.md` |
| 🆕 | `CCTL 0x100`'s effect — **only if `c-E` read `P0` and `c-E0` held**; in the write-through branch there is no dirty line and `c-E2` cannot fail | `SPEC.md` `CPU-43`, or **未定** | — |
| 🆕 | **`c-G`: does an uncached READ invalidate a resident clean line** — the core vendor says its family's does, and if this one does too then `R6` has a per-line invalidate primitive that needs no `CCTL` at all | `SPEC.md` `CPU-45` | `docs/rlx-cache-and-cp0.md` § ② — it is a SECOND candidate mechanism for decision ②, and the cheapest one |
| 🆕 | `TC0CNT` as an instrument; the 14.286057 MHz base clock | `SPEC.md` `CLK-17` — **the number the payload divides by must not live only inside a derivation** | `R5-0` |
| 🆕 | `cache 0x10` as a capability, for `CPU-04` | `SPEC.md` `CPU-04` — **as a capability, not as a name.** `CLAUDE.md`'s ban stands | — |

**The trap `R1g-5` walked into, restated so `R1h-4` does not repeat it:** the
walk's number and the kernel's number are **two different claims**, and the
write-up says so **even when they agree**. A build constant that agrees with a
measurement is corroboration; a build constant quoted as a measurement is a
geometry number wearing a measurement's clothes.

---

## 🔴 Ran — 2026-08-29, `bench/2026-08-30/`. Every cell's outcome

`probe3` executed on the silicon on power cycle 1 of seating 5. Report:
`QJ.log`, 5,642 bytes to `rlxprobe: end`, then the payload's own watchdog reset
and a prompt. Block recovered with one `DW` into `Q5-rb.log`, 7,593 bytes / 161
lines. **`cells.run=0000000e` (14), `cells.void=00000008` (8)** — 22 accounted
for, which is the arithmetic that says nothing was silently skipped.

**Two channels, mechanically.** `tools/rbcheck.py` (new, ten controls): the
UART's `sum=`, the seal word `w640`, and `sum(w0…w639) − 0x10` are all
**`C93E60B5`**; the three free margin words are `DEADC0DE`; and the 25
field-to-word pairings of §12 agree **25 of 25** after one pairing in that table
is corrected. See `bench/2026-08-30/CORRECTIONS-block0.md` §3.

### Group P — preflight

| cell | reading | verdict |
|---|---|---|
| `P0` ×2 | `8040D4A0` = `00000000` before and after six commands | gate open, bracket holds |
| `P1` | `001BD530` then `000425D0`; `TC1CNT=0`, `TCCNR=C0000000`, `TCIR=80000000` | live on the first pair; all four pre-registered values matched |
| `P2` | four windows, 16 distinct words each, 46.1–54.1 % ones, **0 of 16 equal between any pair** | no shape fired; bias garbage |
| `P3` | 23,527 B, 500 lines, prompt, no `Unknown command !` | the loader takes a 4-digit length — `LDR-41` |

⚠️ **§5's pointer-shape refutation is not usable as written.** Two of the 64
arena words carry a listed prefix (`81xxxxxx`) and neither is 4-byte aligned.
On uniform random words the loose form — `G0`'s verbatim *"any one
pointer-shaped word and the address is re-picked"* — fires with probability
**63.6 %** on 64 words, and the aligned form at **22.2 %**. It needs a rate, not
a presence test. The shape with real power was *any two windows byte-identical*,
which is a stuck read path and nothing else on the list catches it.

### Group T — the timer. Ships

`g.timer=00000001`. `t.cal.hi=00003af2` (15,090) and `t.cal.lo=00001d78`
(7,544): **hi/lo = 2.0003**, so the bracket scales and does not measure itself.
The predicted values were ≈14,286 and ≈7,143 (算 from `CLK-03` × the tick rate);
the measured pair is **5.6 % high**, which is inside neither of the two
refutation bands (*≈0* → TC0 stopped; *~2× or ~0.5×* → CPI is not 3). So CPI = 3
is corroborated to within 5.6 % and this cell has separated what `CLK-03` could
not.

### Group W — the I-side walk. 16 KiB, 16 B, 2-way

Full working in `notes/cache-model.md`. Both of 否證 ⓐ's controls fired, in both
directions, and the 16 KiB point reproduced (`bmp.rerun.fresh=00000014`).
`w-line0`, the no-fetch negative control, read all-FRESH as required.

`w-imem` is **未定**: `w.imem.differs=00000000`, and §6.1's own warning is the
reason — CP0 20 is write-only (M4), so *identical* is also the no-op reading,
and `m-imem` returned a base without a top.

### Group M — CP3 is reachable, and this is the sharpest qemu disagreement of the seating

`m.traps=00000000`. **All eight `mfc3` stubs executed**; on qemu all eight
trapped (`m.cause=1000042C`). `m.cause` is still `deadc0de` — never written —
which corroborates zero traps from a second direction.

`CU3` sticks: `m.cu3.before=1000fc00` → `m.cu3.set=9000fc00`, the predicted half.
**No reading equals its own prime and `v1 == v2` for all eight** (primes
`0xC0DE0300|i` and `0xD1CE0300|i`, 讀 `probe3.c:1734-1758 (v1 = rlx_call0_primed)`) — so the destination
was written and the value is stable, which is exactly the pair of failures the
two primes exist to separate. r0 and r4 read `20000000`; the rest read `0`.

⚠️ **A base is not a window.** Both tops read `00000000`, so §6.1's condition for
calling `m-imem` answered is not met and the scratchpad's extent is unmeasured.

### Group C — `c-A` negative, and the interlock did its job

`c-A0` (negative control, and it runs first for exactly this reason) returned
`P1`. `c-A` returned `l2 = P1` — no stale line. The payload printed
`Group V VOID -- c-A negative`, and `c-B`/`c-C`/`c-D`/`c-F`/`c-G` are all `VOID`
with `g.ca=00000000`.

🔴 **`c-E` ran and does not count.** §6.5's rule, written before the seating:
with `c-A` negative, residency was never established, so `c-E`/`c-E0`/`c-E2` are
*void — residency not established*. `c E l2=00000000` is **not** a write-policy
verdict. ⓑ is unanswered and the stop-loss allows a second seating.

### Group X — retires, with the control that makes that mean something

`x c11`, `x c10`, `x c15`, `x c19`: all `n=00000000`. `x ri`: **traps**,
`cause=00000028` (ExcCode 10, RI), `epc=80501874`. Same handler, same run — so
*no trap* is a reading and not a broken handler.

⚠️ §6.4's pre-registered caveat is the one that stands: `x.c10.treated=00000001`
**and** `x.c10.twin=00000001`. The untreated twin moved too, so the six
intervening `CCTL` stages explain the treated victim as readily as `cache 0x10`
does. **`CPU-44` closes on *retires*, not on *invalidates*.**

### Group S — none of the three bits sticks, and the refutation did not fire

`s.bits=01010040` (bits 16, 24, 6 — the value the cell actually wrote, not one
reconstructed from the instruction selection). `s.before = s.set = s.restored =
1000fc00`, `restore.mismatch=00000000`, `status_end=1000fc00`.

🔴 The reading carries information **because §6.7's refutation did not fire**:
both control bits also read back clear, so this is not the *"`Status` has no
write mask"* state in which *bit 16 does not stick* would be uninformative.
Consistent with LX4189 §3.4.1's written-as-zero field, and now 量 on this die.

### The header, and the four rows where it was wrong

Predicted and matched: `pc=80502c74`, `flags=50010002`, `rb=80a02000` (lower
case), `status=1000fc00`, `arena=80a10000`, `kseg0=00000001`,
`handler_words=00000016`, `install.bad=00000000`, `break.count=00000001`,
`break.cause=00000024`, and no `CLEAR_BEV` warning.

Wrong, and both are in `CORRECTIONS-block0.md`: `break.epc` came out
**`80500270`**, which the block predicted it would *not* be, and
`install.changed` came out **`0000002b`** — the value withdrawn the day before
for a reason that was itself correct.

### 🔴 The retained bitmap does not survive to the read-back, and the block's header says it does

Found by an adversarial pass on 2026-08-30, 量 on `bench/2026-08-30/Q5-rb.log`.

`probe3.c:1476-1489 (THE RETAINED BITMAP)` states the design: *"THE RETAINED BITMAP. One sweep point
survives to the read-back … the BOUNDARY point, because its PATTERN is what
carries associativity and aliasing."* `probe3.c:85-90 (THE BITMAP HOLDS ONE SWEEP POINT)` builds a self-check on
it — *"so the desk can compare the count the payload thought it wrote against
the length it actually read."*

**It does not survive.** `bmp_clear()` is called at `:1385` inside the `w-assoc`
search loop and again at `:1667` and `:1808`, all **after** the boundary rerun at
`:1336`. The last writer is `x-c10`'s two-victim walk.

量, the block's bitmap region (`w384`, `H_LAYOUT_BMP` → `0x80A02600`):

```
80A02600:  11000000  00000000  00000000  00000000
80A02610 .. 80A029FC: all zero
```

Two `V_STALE` nibbles and 510 `V_NEVER`, against a header that still advertises
`bmp.point=57000010` (the 16 KiB point) and `bmp.count=00000200` (512). A reader
parsing the block by its own header gets 510 never-written victims and a computed
FRESH count of **0**, against `bmp.rerun.fresh=20`.

**Nothing published is falsified.** `bmp.rerun.fresh` and `bmp.firstbad` are
computed at `:1341-1345`, before the clobber, and the sum, the seal and both
channels are unaffected. What is lost is the *pattern* — which is the only
evidence that could have shown the 20 FRESH victims arriving in pairs
`{k, k+256}`, the direct fingerprint of two ways sharing a set, instead of
leaving direct-mapped to be excluded by inference.

`tools/rbcheck.py` now **reports** the discrepancy (advertised victims against
nibbles written) and deliberately does not fail on it: the block is sound
everywhere else, and refusing it over a stale region would be the wrong verdict.
Fixing the payload is a `probe3` change and is carried forward.
✅ **FIXED 2026-08-31 (seventeenth session), and by a second region rather than
by moving the rerun.** `O_BMPK` is 64 words between the scratchpad and the seal,
written once, immediately after `bmp.rerun.fresh` and `bmp.firstbad` are
computed and before anything else can touch `O_BMP`. **The other candidate —
move the boundary rerun below the last `bmp_clear()` — was rejected on a
measurement-shaped argument**: the rerun is only meaningful in the cache state
the `w-size` sweep leaves behind, and `w-assoc`, Group C, Group V and Group X
all run between here and there. Moving it would have produced a region that
survived and a number that meant something else.

**What went with it**, because a region nobody checks is not better than a
region nobody reads: `H_BMP_KEPT` (how much of the point the copy holds) and
`H_BMP_FRESH` — the payload's own FRESH count, which until today existed **only
on the UART**, so a desk holding just the `DW` read-back could recount the
region and had nothing to compare the recount against. `tools/rbcheck.py` C17…C23
are that comparison; C22 and C23 exist because the mutations were written first
and **M25 survived C17…C21** — the truncation limit could be deleted with every
control still green, since every one of those regions has its FRESH nibbles
inside `kept`.

