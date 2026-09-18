# Block 27 — the pre-power audit

**§ 0 was written BEFORE power was spent on any cell of this card, before any
cell ran, and is committed in a commit that predates every `C`-prefixed capture
in this directory.** The board was already at the loader prompt when it was
written — `bench/2026-09-19/X1-esc`, 00:58 — and the seven `X` captures listed
in the card's § 0.3 predate it too. Nothing else does.

Base rate to beat, 讀 `bench/2026-09-14b/CORRECTIONS-block19.md:50-56`:
**18 cards, 144 defects ≈ 8 per card, 12.5 % caught before power** — except the
one card with an explicit pre-audit policy, which caught **50 %**. ⚠️ That file
says of its own five figures *"these are 讀, not 量"*: the counting rule was
chosen per file and nothing in the repository can re-derive 144. The durable
half is the ratio.

---

## § 0 — sixteen findings before power

### 0.1 Two owner files describe things that are not there

**F1 🔴 `resetcmp` is not a verb.** 量: the token occurs exactly twice in the
whole repository — `rtl819x-switch.c:323`, a comment saying *"`resetcmp` in the
card is what asks"*, and `docs/KNOWN-ISSUES.md:785`, which calls it *"the
`resetcmp` **verb**, which runs both and diffs the dumps."* The parser at
`:535-609` has no such token; typing it returns `-EINVAL`. **The seating brief
for this segment listed it as cell 8.** Composed instead out of
`reset full` → `snap` → `reset vendor` → `snap` → `diff`.

**F2 🔴 And composing it exposed a confound the missing verb hid.**
`rtl819x_sw_do_reset()` asserts `FULL_RST` on **both** paths (`:336-339`); the
vendor recipe only adds the clock gate afterwards. A naive
`reset full` → snap → `reset vendor` → snap → diff therefore measures *the
650 ms clock gate* **and** *`FULL_RST` applied a second time* and cannot
separate them. The card runs `FULL_RST` twice with a snapshot between, so
**idempotence is measured before the clock-gate delta is attributed**. Without
that, a non-zero diff would have been written up as *the clock gate does
something* with no way to know.

**F3 🔴 `docs/KNOWN-ISSUES.md:777` is wrong by a factor of four.** It says
*"Eight of the nine registers the `dumb` verb writes have no reading on this die
in ANY state … `MSCR`, `VCR0`, `SWTCR1` and `PVCR1`–`PVCR4` have never been
read."* 量: `SWTCR1` = `00000200` and `PVCR1`/`2`/`3` = `00080008` are in
`bench/2026-09-17b` and in `SPEC.md:234`. It is **two of nine** — `MSCR` and
`VCR0` — and after this seating's `X3`/`X4` it is **zero of nine**. 推 the
mechanism: `hdrcensus` searches committed files for an 8-hex token, and a
`DW <base> 4` window labels only its base, so the other three words are
invisible to it. `notes/switch-driver.md:35` inherits the same error.

### 0.2 The cell that would have produced nothing, and the census that replaced it

**F4 🔴🔴 `/proc/rtl865x/vlan` and `/proc/rtl865x/pvid` DO NOT EXIST in this
image, and both were cells on the first draft.** They would have printed
*"No such file or directory"* — and **`check-predictions` scores existence and
mtime, not content**, so the seating would have reported `41 of 41` with two
cells empty. This is `FW-46`'s class: *nothing in this repository can ask "can
this image run this command" before a card is frozen.*

🟢 **It can now, and the method is three lines.** A `/proc` entry's name is a
NUL-delimited `.rodata` literal, so `b"\x00name\x00"` in the flat image answers
it. 量 2026-09-19 with four controls — `port_status` **1**, `memory` **2**,
`rtl819x-switch` **1**, a synthetic name **0**:

**The vendor registers 42 distinct `/proc/rtl865x/` entries. THIRTEEN survive
into this image**: `stats`, `arp`, `ip`, `pppoe`, `igmp`, `memory`,
`diagnostic`, `port_status`, `phyReg`, `asicCounter`, `mmd`, `mac`,
`fc_threshold`.
**Twenty-nine do not**: `vlan`, `netif`, `acl`, `advRt`, `storm_control`,
`soft_aclChains`, `soft_qosRules`, `hs`, `nic_mbuf`, `rxRing`, `txRing`,
`mbufRing`, `pvid`, `mirrorPort`, `l2`, `hwMCast`, `swMCast`, `nexthop`, `l3`,
`napt`, `sw_napt`, `sw_l2`, `perf_dump`, `port_bandwidth`, `queue_bandwidth`,
`priority_decision`, `rateLimit`, `eventMgr`, `priveSkbDebug`.

⚠️ **This is a fact about THIS image's config, not about the device.** The
vendor firmware has more of them; `rxRing`, `txRing`, `mbufRing` and `nic_mbuf`
in particular are exactly what `R6-3` would want, and they are absent from
rlxfw's board template. That is a configuration decision nobody has made
deliberately, and it is carried forward rather than changed tonight.

**F5 🟢 What replaced the two dead cells is better, and only the audit produced
it.** `phyReg` gives the PHY's own registers — **this project has never
identified the PHY silicon** — and `asicCounter` gives per-port hardware MIB
counters, which is `D3`'s *"two sources"* shape: a counter that shares no code
with `ifconfig`'s software counters or with `ping`'s arithmetic. Bracketing four
pings between two `asicCounter` reads was not on any brief.

**F6 🔴 `proc_phyReg_read`'s entire body is `return PROC_READ_RETURN_VALUE;`** —
`cat /proc/rtl865x/phyReg` prints **nothing**. The read is on the **write** side:
`echo read <phyId> <regId> > /proc/rtl865x/phyReg`, output
`"read phyId(%d), regId(%d),regData:0x%x\n"` to the console through
`rtlglue_printf` → `panic_printk`. A card that had written `cat` there would
have produced an empty capture that scores as a pass. `asicCounter` is the same
shape: `rtl865x_proc_mibCounter_read` returns `len = 0` and calls
`rtl865xC_dumpAsicDiagCounter()`, whose output goes to the console — so the
file reads empty and the **capture** still holds the dump.

### 0.3 The instrument's own side effects

**F7 🔴🔴 `memDump` issues FIVE `READ_MEM32` per row — `+0/+4/+8/+12/+16` —
BEFORE it tests `max == 0`** (讀 `rtl865x_proc_debug.c:141-145`, identical copy
at `common/rtl_utils.c:160-164`). So `read <a> 4` **touches twenty bytes and
displays four**. The first draft read `CPUIIMR` and `CPUIISR` in two separate
cells; each already touched the other plus three registers past it, so if
anything in that span is read-to-clear **the first read destroys what the second
measures, and the output cannot show that it did.** Fixed by making `C16-IMR2`
character-identical to `C14-IMR` and `C18-DMA1` identical to `C13-DMA0`, so the
over-read is the same on both sides of the write and the difference is
attributable.

**F8 🔴 `PSRP` bit 8 is read-to-clear (`NET-11`) and this driver reads all 37
registers at `subsys_initcall` and 74 times per `cat` (`FW-64`).** So the boot
latch consumes any pending link-down event **before userspace exists**, and
every `cat` consumes it again. **`NET-30 殘留`'s decisive experiment — *read
`PSRP` immediately after a cold boot* — can no longer be run on any image
containing this driver.** Nothing in the repository named this; a read-only
driver still has a destructive read.

### 0.4 Two tools disagreeing with themselves

**F9 🔴 `rtkimage check` exits 1 on every image built for this board, and the
same tool documents why.** 量, isolated: without `--linuxbin` `rc=0`, with it
`rc=1`. `cmd_check:404` counts a `bad` when `signature != b'cr6c'`; this board's
`linux.bin` is **`cr6b`** because the Makefile selects `linux-ro` for
`CONFIG_SQUASHFS=y` — which `--compare-vendor`'s own text records (量
2026-08-29). `linux.bin` is the flash image and plays no part in the RAM boot
path. **Two halves of one tool disagree about one byte**, and its exit code is
therefore unusable as a gate for any RAM-boot image unless `--linuxbin` is
withheld.

**F10 ⚠️ `MK9` reads 2 on the flat image and 3 was reported for the same image
last segment.** Not a contradiction: last segment read the ELF. `RUNSHEET` `P10`
exists for that gap, and `config/rlxfw-marks.tsv`'s own `MK9` row predicts
*"contiguous in `.rodata` twice over"* — so **2 is the predicted flat count**.
Recorded because a reader comparing the two numbers would otherwise be right to
worry.

**F11 ⚠️ `cardcheck commands` does not classify the `looprun` cell.** 量: the
card holds 42 commands and `cardcheck` reports **41 (8 LOADER, 33 SHELL)** —
the cells with a `--send`. The `looprun` invocation has none, so **its arguments
are checked by no gate in this repository.** Checked by hand instead: the image
path, its sha256 and the `--recipe-override` are all `cardnum` rows, and
`--skip S2,S3` is what makes `--cell-top` unnecessary.

### 0.5 Three things the card itself got wrong, caught by its own gates

**F12 🔴 A line wrap broke a `cardnum` regex.** `**declared date` and
`2026-09-19**` landed on different lines, so `cardcheck numbers` read **0**
where the card said 1 — `12 of 13 re-derived`. Fixed by putting the phrase on
one line. **The gate caught it; reading the card did not.**

**F13 🔴 Six stale cell references survived a renumber**, and a script found
them where reading did not: `C22-IFUP`→`C23`, `C25-RST1`→`C27`,
`C29-RSTV`→`C31`, `C34-PING1`→`C36`, `C36-REST`→`C39`, and one reference to a
cell that no longer exists. Every `C<n>` mentioned in prose is now checked
against the fence by a three-line script, which is how this class should be
caught from now on.

**F14 🔴 A number from a subagent was not reproducible and it was already in the
card.** The `proc_mem_write` length and md5 were quoted as **1,435 /
`cd16eb64…`**; re-derived here with the boundary **stated** — *from the
definition line to the first line that is exactly `}` in column 0* — it is
**1,434 / `5e6d253247ffb4ff3f8a3edf04d43f4f`**, identical in all three drops.
**A length and a digest that depend on an unstated convention are two numbers
nobody can reproduce.** The three-drop identity claim survives; the numbers did
not. *(The first attempt to check it also looked for the file at the wrong path
in two of the three drops and concluded it was absent — which would have been a
second wrong finding in the other direction.)*

### 0.6 The host, and a preflight that paid for itself

**F15 🔴 `RUNSHEET` `P3` fired for the fifth time.** The USB GbE was **DOWN with
no address** and `ip -4 route get 10.1.1.1` resolved through WSL's NAT'd `eth0`.
Fixed at the desk **before the upload**, which is what that row's own
carried-forward repair asks for: `10.1.1.2/24`, `Link detected: yes`, route
through `enxfc19286184c9`. ⚠️ `ethtool` also reads **`Duplex: Half`** at
100 Mb/s; recorded as a suspect, not expected to affect a TFTP put.

**F16 🟢 `RECIPE_ID` was checked rather than assumed, and it could have gone the
other way.** The image was built at 19:17 on 2026-09-17 and **a commit at 19:50
touched `config/`**, which is the digest's input. 量: the manifest's
`recipe_id` is `f681f8e0` and recomputing from `config/` at `HEAD` today gives
`f681f8e0` — the commit carried content that already existed at build time. Had
they differed, the card would have predicted a string the board never prints.

---

## § 0.7 What this audit did NOT check

1. **`looprun --mode plan` was not run** with the card's exact arguments.
   Checklist item 3, skipped; the arguments were walked by hand instead (F11).
2. **`rlxfw-kbuild.sh --dry-run`** was not run. `RECIPE_ID` was established two
   other ways (F16), which is the thing that check exists to establish.
3. **`eth4` is 推.** The previous seating's image brought up `eth4` successfully
   and this image has the same vendor NIC driver, but the interface名 has not
   been observed on **this** image.
4. **The `C15`/`C17` gate is manual.** The card says `C13`/`C14` must be read
   before `C15` is typed, and nothing enforces that — `bench/2026-09-14c`'s
   lesson was that *an abort condition the runner cannot read gets acted on
   late*. The cells are run one at a time and read as they come, which is the
   mitigation, and it is a procedure rather than a guard.
5. **Nothing here is 量 on the silicon.** Every finding above is 讀 or a desk
   measurement on an artefact. The card's predictions are untested.

---

## § 1 — the loader phase, and the probe that cost a power press

**Everything below is 量, after power, on 2026-09-19 between 01:42 and 01:45.**
§ 0 above was committed at 01:41:31 (`8e51c4d`) and predates every capture in
this section.

### 1.1 `C1`–`C7`: seven cells, and one refutation

| cell | read | against the card |
|---|---|---|
| `C1-L4104` | `007F0039 047F0039 087F0039 0C7F0039` | 🟢 **four of four**, byte-identical to `upstream/BENCH-LOG.md:4770-4795` from 2026-08 — a cross-seating repeatability result three weeks and several power cycles apart |
| `C2-L4114` | `107F0039` **`00000000`** `187F0038 1C7F0038` | 🟢 `PCRP4` as predicted; **`PCRP5 = 0` — the negative control fires**; `PCRP6` bit 25 clear as `A2` predicted |
| `C3-L4128` | `000010E0 000010E0 000010E0` **`000011F9`** | 🟢 **exactly one of `PSRP0`–`PSRP4` carries `LinkUp` with speed 100M, and it is port 3** — so the cable is in socket 3, measured rather than looked at |
| `C4-L4138` | `000010E0` `000000E2` `0000007A` `0000007A` | 🟢 **three of three** — `PSRP5`, `PSRP6`, `PSRP7` all as predicted from block 24's decode |
| `C5-L4148` | **`PSRP8 = 0000007A`**, `P0GMIICR = 00037D00` | `PSRP8`'s first reading ever; `P0GMIICR` as predicted. See § 1.2 |
| `C6-L4600` | **`0000007E`** | 🔴 **REFUTED.** The card predicted `0000007A` from the header comment `/*CPU Port Status : R/W */`. `PSRP6 XOR PSRP6_RW = 0x00000004` — **one bit, bit 2** — so `0xBB804600` is not a second view of `PSRP6`. The corroboration the card hoped for is withdrawn, and a new 未定 replaces it: what bit 2 is |
| `C7-L4400` | `00000000` ×4 | `TEACR` and `ALECR`, two of the seven never-read registers, both read **zero**. ⚠️ **未定, not a result**: all four words in the window are zero and the window has no non-zero neighbour to act as a control, unlike `C2` where `PCRP5`'s zero sits between non-zero values |

### 1.2 🔴 `NET-10 殘留` closes, and it closes by REMOVING a piece of evidence

`A2`'s report proposed the test in advance: *"If `PSRP8` is also `0000007A`,
then `7A` is the non-PHY default and **`PSRP7`'s equality with `PSRP6` carries
no information**."* 量: `PSRP8` **is** `0000007A`. `PSRP6`, `PSRP7` and `PSRP8`
are the same word, and that word is what a port with no PHY reads.

So `SPEC.md` `NET-10 殘留`'s *"`/proc` lists exactly one `CPUPort`"* was already
known to be predicted by the printer's loop bound rather than by the hardware,
and now the register-side half is gone too. **What settles which port is the CPU
port is the vendor printer's own loop variable (`CPU = 6`, and the device
printed `Port0`…`Port5` then one `CPUPort` row), not any property of `PSRP7`.**

### 1.3 🟢🟢 `C8-MDIOR` was a discovery cell and it discovered more than a syntax

`MDIOR` bare returns **`Parameters not enough!`** — not `Unknown command !`. So
the command in `upstream/RUNBOOK.md:988`'s table is real, reachable from the
prompt, and takes arguments. **It had never been executed in either project.**

Three off-card probes (`X8`, `X9`, `X10`, declared here) then found that
`MDIOR <a> <b>` **sweeps all 32 MDIO addresses and reads register 0 regardless
of its arguments** — `Reg=0` in all three, with three different argument pairs.
⚠️ **What the two arguments mean is 未定.**

But the sweep is the result:

> **MDIO addresses 0x00–0x04 read `0x1100`. Addresses 0x05–0x1F read
> `0x0000`.**

`0x1100` decoded: `aneg_enable` (bit 12) and `duplex` (bit 8) — an
autonegotiating, full-duplex-preferring PHY. `0x0000` at an MDIO address is the
classic *nothing answers here*.

🟢 **So there are exactly five PHYs on this die, at MDIO addresses 0–4 — and
tonight three other register families say the same thing, sharing no code with
MDIO and no code with each other:**

| family | what it says |
|---|---|
| MDIO (`X8`) | PHYs answer at 0–4, silence at 5–31 |
| `PCRP` bit 0 `EnablePHYIf` (`C1`/`C2`) | set on 0–4, **clear** on 6 and 7; `PCRP5` not populated at all |
| `PSRP` bits 13:12 `PortEEEStatus` (`C3`/`C4`/`C5`) | set on 0–4, clear on 5, 6, 7, 8 — and EEE is a PHY feature |
| `PSRP` value (`C4`/`C5`) | `0x7A` on 6, 7 and 8 — one non-PHY default |

⚠️ **And `PCRP`'s top byte is `4n`** — `00 04 08 0C 10 · — · 18 1C` — which is
exactly the address-echo pattern `upstream/BENCH-LOG.md:4790-4791` worried
about. **`PCRP5` reading `00000000` instead of `147F00xx` is what closes it**,
for the second time and on a second seating.

### 1.4 🔴🔴 `PHYR` with no arguments HANGS THE LOADER, and the card's recovery for that hazard does not work

量 `X11-phyr`, 82 bytes:

```
PHYR
cp0_cause=00000028, cp0_epc=80000000, ra=00000000Undefined Exception happen.
```

`cp0_cause = 0x28` → `ExcCode = (cause >> 2) & 0x1F` = **10 = RI, Reserved
Instruction**. `epc = 0x80000000` — the base of KSEG0 — and `ra = 0`, so it was
not reached by a `jal`. The loader jumped to the bottom of RAM and executed what
was there.

**Then nothing.** `X12` and `X13` are **0 bytes**; `X14-probe` streamed ESC for
8 s over a 12 s window and got **0 bytes** with `prompt_seen: false`, while
`/dev/ttyUSB0` was present and the tool opened the port and ran the whole
window. **The board is hung in the exception handler and no watchdog resets
it.**

⚠️ **The alternative explanation was eliminated by measurement, not assumed.**
`usbipd list` still reads `Attached`, `/dev/ttyUSB0` is present with its mtime
advancing on every open, and `dmesg` shows only `vhci_hcd: urb->status -104`
(`-ECONNRESET`, a URB unlink on a read timeout) and no disconnect. The link is
healthy and the board is silent.

### 🔴 THE CORRECTION THIS SECTION NEEDS, AND IT IS ABOUT HOW IT WAS WRITTEN

The paragraph above was drafted as a discovery. **It is not one.**
`docs/loader-command-semantics.md` § 10, written **2026-08-25**, already says all
of it, marked 讀, with the cheap cell that would make it 量 named and never run:

> `do_reserved` at **`0x80400BE8`** … `80400c18: j 0x80400c18  <- BRANCH TO
> ITSELF` … The exception entry has already pushed the KU/IE stack so `IEc` is
> 0, **and the watchdog is not armed** … **Nothing recovers it. One fault costs
> one power cycle.** … **Neither string ends in `\n`** (NUL at `0xA52B` and
> `0xA547`), so what reaches the wire is **one unterminated line followed by
> permanent silence.**

**I wrote up a finding without reading the file that owns it.** That is the
process failure, and it is recorded because the repository's own audit method
says the valuable pass is the one that asks *who owns this claim* before writing
it down.

🟢 **What tonight actually is, and it is worth more than a discovery: FIVE of
§ 10's claims went 讀 → 量 in one accidental capture.**

| § 10 claim, written 2026-08-25 | tonight |
|---|---|
| a fault reaches `do_reserved` for an ordinary ExcCode | ✅ ExcCode **10 (RI)** is one of the thirty slots § 10 says point at `0x80400BE8` |
| the two strings are printed by two `prom_printf` calls | ✅ both appeared, and the format matches `"cp0_cause=%X, cp0_epc=%X, ra=%X"` |
| **neither string ends in `\n`**, so the wire sees ONE unterminated line | ✅ **byte-exactly**: `…ra=00000000Undefined Exception happen.` with no separator at all |
| the watchdog is not armed, so nothing bites | ✅ no reset over 12 s with ESC streaming |
| **one fault costs one power cycle** | ✅ |

⚠️ § 10 also says *"Nothing here is measured on the device; the cell that would
make it a measurement is `DW 80000080 32` at the prompt, which is read-only and
costs nothing."* **That cell has never been run, and tonight measured the same
thing the expensive way.** The accidental measurement is in one respect stronger
— it observes the *behaviour* rather than the vector table — but it is not a
substitute for the free cell, and that cell is carried forward.

🟢 **And one thing tonight adds that § 10 does not have**: `epc = 0x80000000`
with `ra = 0`. Nothing had been uploaded, so `0x80000000` held whatever a
cold-booted board leaves there, and executing it raised RI rather than, say, an
address error. **What `PHYR` transfers control to is `0x80000000` itself** — not
a wild pointer, but that exact address, which § 10 notes is also where a
`boot.img` upload would begin writing.

🔴 **The card's § 2.2 says, of exactly this hazard:** *"The loader runs its own
watchdog at roughly one second (`CLK-08b`), so a fault resets the board — and
`--esc-after 15` catches the prompt that comes back."* **That is refuted.**
`--esc-after` was armed on `X11` for 10 s and there was nothing to catch.
`CLK-08b`'s ~1 s is the watchdog's **configured** period in loader state; it is
not evidence that the loader **arms** it at the prompt, and this measurement
says it does not. **The sentence is left in the frozen card and corrected here,
because repairing a frozen card destroys its own mtime evidence.**

⚠️ **What this cost, counted rather than estimated**: one power press. All eight
loader cells were already captured; the remaining phases need a fresh loader
prompt anyway, which the power cycle provides. **Zero flash writes, zero `FLR`**
— a Reserved Instruction exception is a CPU event and touches no flash.

🔴 **The rule that comes out of it**, and it is narrower than *do not type
unknown commands*: **a loader command that reports `Parameters not enough!` for
zero arguments is safe to explore; one that faults is not, and the two are
indistinguishable before the fact.** `MDIOR` did the first, `PHYR` did the
second, and they are adjacent entries in the same command table. Any future
probe of `PHYW`, `MDIOW` or `PORT1` must assume the `PHYR` outcome, not the
`MDIOR` one.

---

## § 2 — the Linux phase, and `R6-2`'s DoD

**量, 2026-09-19 between 02:01 and 02:40, on the power cycle the `PHYR` fault
made necessary.** `check-predictions`: **`41 of 41` captures came after the
prediction, 0 did not.**

### 2.1 The boot

`looprun --mode bench --skip S2,S3` closed the loop in **39.24 s** with **nine
assertions**, the one that matters being `A3 the id the build computed -- board
printed f681f8e0, build computed f681f8e0`. `A0b` read `AUTOBURN` back as
`00000000` **from the word at `0x8040D4A0`**, not from the loader's echo.

🟢 **The boot capture is 1,759 bytes against a prediction of 1,759**, derived at
the desk as `710 const + 927 baseline marks + 122 switch marks` with the
precondition checked (all 57 baseline tags present in the flat image, all seven
switch marks present exactly once).

```
RLXFW-SW0 · SW1=81964000 · SW2=00000001 · SW3=00000200 · SW4=000001FF
SW5=00080008 · SW6 · RLXFW-ID0=F681F8E0
```

`SW6`, not `SW6-NOPROC`.

### 2.2 🟢 The read path is proved, by paths that share no code

`SW1` is `boot_cvidr`, latched by `__raw_readl()` at `subsys_initcall`. It reads
**`81964000`** — **identical to the loader's `DW BB804200`**, which was read
four times across a power cycle (`X2`, `X6`, `X7`, `X18`, all byte-identical).
The live `CVIDR` column and the slot-0 column in every `cat` read it too. **Two
code paths sharing nothing, on a register nobody writes.** Every reading below
is licensed by this.

### 2.3 🟢🟢 `S0'`, a state nobody had ever measured

The four marked registers are **byte-identical to loader state**: `MSCR`
`00000001`, `SWTCR1` `00000200`, `VCR0` `000001FF`, `PVCR0` `00080008`.

🔴 **But that is not "early init does not touch the switch", and the first draft
of this section said so.** 量 from `C9-SW0`'s two columns: `PCRP0`–`PCRP4` are
`nn7F0038` at `S0'` and `nn7F0039` at the loader — **`EnablePHYIf` is CLEARED
between the prompt and `subsys_initcall`**. 🟢 And that transition is **exactly
what `upstream/BENCH-LOG.md:4770-4795` recorded in August**: *"At rest under the
loader: `007F0039`… **After `J`: all `...0038`**."* Two projects, three weeks
apart, the same state transition.

**The full `S0'` → Linux table: 25 of 37 registers move** once the vendor NIC
driver's `device_initcall` has run. `C9-SW0` carries both columns.

🟢 **And it settles `C7`'s undetermined.** `TEACR` and `ALECR` read `00000000`
at the loader **and** at `S0'`, which alone cannot distinguish *the register is
zero* from *the window is not decoded*. Live they read **`00000002`** and
**`000505F2`**. Same addresses, non-zero values: **the window is decoded and the
zeros were real.**

### 2.4 🟢 Every counter in the derived table hit

`scratchpad/s87-counters4.py` re-implements the driver's arithmetic from
`file:line`. Measured, in order: `n_reads` **38 · 186 · 261 · 335 · 410 · 521 ·
596 · 707 · 782 · 893 · 976** and `n_writes` **0 · 0 · 0 · 0 · 1 · 1 · 2 · 2 ·
7 · 7 · 16**, ending at **`n_writes 25`, `n_refused 1`, `n_reset 3`, `n_dumb 1`,
`n_restore 1`**, all four slots full.

🟢 **`n_reads 186` on the first `cat` after two snapshots confirms `FW-64` on a
SECOND driver**: `38 + 74 + 37 + 37`. One `cat` is two `read_proc` invocations.

🟢 **`n_writes` 2 → 7 across `reset vendor` confirms it is FIVE writes**, one
`SSIR` plus four `SYS_CLK_MAG` that bypass the guarded path and increment the
counter by hand. A card predicting +1 would have been refuted by a driver
behaving exactly as written.

🟢 **`n_refused 1`, not 9** — a locked `dumb` costs one read and one refusal
because the verb returns on its first `-EPERM`. The guard was seen refusing,
with a number.

### 2.5 🟢🟢 The three controls the block rests on

| control | predicted | measured |
|---|---|---|
| **same-state sampling** | `SW-DIFF=00000000` | **`00000000`** — two back-to-back 37-register snapshots identical |
| **the reset's POSITIVE control** | at least one register differs `S0'` → `S1` | **24 of 37 differ.** The block is licensed, not void |
| **idempotence** | `SW-DIFF=00000000` | **`00000000`** by the verb **and 0 of 37 by the captures** — two instruments |

### 2.6 🟢 What the vendor's 650 ms clock gate adds: nothing, and the one thing that moved proves it worked

`diff 2 3` = **`00000000`**. The capture diff of the `cat` immediately before
against the one immediately after reads **1 of 37**, and it is `PSRP0`
`000010E0` → `000011E0` — **bit 8, `LinkDownEventFlag`, which `NET-11` says is
read-to-clear.** So the clock gate **did** drop and restore the link, and the
only register that records it is a latch the next read consumes.

🟢 **That latch is then seen being consumed, in three consecutive captures**:
`C30` `000010E0`, `C32` `000011E0`, `C33` `000010E0`. `NET-11`'s read-to-clear,
demonstrated in the wild rather than read out of a header.

🔴 **And the two instruments disagreeing is itself the finding.** `SW-DIFF`
compares two SNAPSHOTS taken at two instants; `C32`'s `cat` sat between `snap 2`
and `snap 3` and consumed the latch, so the verb could not see it. **A `diff`
count is a statement about two moments, not about an interval**, and any
register that changes for a reason other than the verb is invisible to it.

⚠️ **So the honest claim is narrower than *the clock gate changes nothing***:
over the nine `dumb` registers it changes nothing, over 36 of 37 it changes
nothing, and the one that moves is a link-status latch moving because the gate
worked.

### 2.7 🟢🟢 `D2` HOLDS — on two registers, exactly as the desk predicted

`diff 3 1` = **`SW-DIFF=00000002`**. By the captures, `S2v` → `S3`:

```
SWTCR1  441C  00000200 -> 00000000
VCR0    4A00  000001FF -> 80000000
of the 9 registers `dumb` writes, 2 moved
of the 28 it never writes,        0 moved   <- the NEGATIVE control
```

🔴🔴 **Seven of the nine writes are no-ops against `S1`, and the card said which
seven before the verb ran.** 量 the `S1` column: `MSCR` `00000001`, `SWTCR0`
`00080000` (and `v & ~0xC01F` leaves it), `PVCR0`–`PVCR3` `00010001`, `PVCR4`
`00000001` — **each already exactly the value `dumb` writes.**

**So Realtek's own `FULL_RST` is already most of a dumb switch.** That is
`R6-2`'s named failure mode — *"that a dumb switch looks identical to a switch
nobody configured"* — arriving as a measurement rather than as a worry. The DoD
survives it because two registers do move, and because the card predicted which
two from the loader-state readings taken twenty minutes earlier.

### 2.8 🟢🟢 The round trip: 9 of 9 came back

After `restore 0`, every one of the nine registers `dumb` disturbed reads its
`S0'` value again. **The direct register path on this die reads back.**
`FW-52`'s `WDTCLR` counter-example — written `00A40000`, read `00240000` — does
**not** generalise to this block, and the vendor's own ten-retry double-read on
the indirect TABLE path is not evidence about this path. That was the most
consequential thing this card could have found and it is the reassuring answer,
measured.

### 2.9 🔴 `dumb` kills the network, and `restore 0` does not bring it back

`C24-PING0` before: **4 transmitted, 4 received, 0 % loss.**
After `dumb`: **4 transmitted, 0 received, 100 % loss.**
After `restore 0` (`X24-ping3`, off-card, window sized for a failing ping):
**still no reply.**

⚠️ **The second half is correct behaviour, not a failure.** `restore 0` writes
back `S0'`, and `S0'` is the state **before** the vendor NIC driver configured
the switch — `VCR0 = 000001FF` with all nine ingress filters on and every PVID
at 8. It was never a working configuration. The card's round-trip prediction is
about **register values**, and those came back 9 of 9.

### 2.10 🔴 `SWINTSET` is refuted, and an off-card control says it is the die and not the instrument

`C15` wrote `CPUICR = 0x00100000` and the handler's own read-back printed
`0x0`; `C16`, character-identical to `C14`, read `CPUIIMR 00000000` and
`CPUIISR 80000000` — **byte-identical to `C14`. Zero bits moved.**

🟢 The output format hit exactly: `%p` lowercase zero-padded (`0xb8010000`),
`%x` **not** padded (`dat 0x100000`). A card predicting `dat 0x00100000` would
have read a correct result as a refutation.

🔴 **The card had no control for *the write never reached the register*.** Four
off-card cells added one: `X19`–`X22` wrote `0x04000000` — the mbuf-size field,
configuration rather than a trigger, with `TXCMD`/`RXCMD` clear — through the
**same** `echo write` path. It **stuck**, confirmed by the handler's read-back
**and** by an independent `echo read`, and the restore to `0` also took.

**So `C16`'s zero is a fact about bit 20.** With the engine off (`CPUICR` `0`)
and the mask closed (`CPUIIMR` `0`), writing `SWINTSET` leaves no trace and
raises no `CPUIISR` bit. `NET-38 殘留` ① — *which `CPUIISR` bit is the software
interrupt* — is **not** answered; 推 it needs `TXCMD`/`RXCMD` set, or the mask
open, or bit 20 is not `SWINTSET` on this part. **`R6-3`'s rung zero as designed
does not work**, and that is worth more before the driver exists than after.

🟢 `CPUIISR`'s first reading ever is **`80000000`**.

### 2.11 🟢🟢 The PHY is identified, and the ASIC's own counters agree with the netdev

```
phyId(0) regId(2) = 0x001c      phyId(0) regId(3) = 0xc880
phyId(0) regId(0) = 0x1100      phyId(0) regId(1) = 0x78c9
```

🟢 **`BMCR = 0x1100` is byte-identical to what the loader's `MDIOR` read for
PHY 0** — the vendor's `/proc/rtl865x/phyReg` under Linux and the loader's own
MDIO primitive, two paths, one value. `BMSR = 0x78c9` has Link Status and
Autoneg Complete **clear**, and PHY 0 is port 0, which `PSRP0` and
`/proc/rtl865x/port_status` both report LinkDown. Three sources agree.

🟢 **`asicCounter` bracketing four pings went from all-zero to `Rcv 536 bytes,
6 unicast` and `Snd 536 bytes, 5 unicast + 1 broadcast`** — and `SPEC.md`
`NET-34` records `ifconfig eth4` reading `RX packets:6 TX packets:6`,
`RX bytes:536 TX bytes:536` for the same operation. **The switch silicon's MIB
and the Linux netdev's software accounting agree exactly, sharing no code.**
That is `D3`'s *two sources* shape, demonstrated.

🔴 **And an unplanned reading with a tension in it.** The traffic appears on
`<Port: 3>` in both directions — the port `PSRP3` says is the only one linked —
**and on `<Port: 5>` as TX only, 6 unicast, RX zero.** 推 (weak) that port 5's
TX counter counts frames forwarded toward the CPU. ⚠️ **It contradicts the desk
reading that port 5 is the unpopulated MII port**, which `PCRP5 = 00000000` in
all three states supports. This project already knows the CPU port carries three
disagreeing numberings (`enum PORTID` 6, `swNic.h` 7, the VLAN path's bit 8);
the MIB dump is a fourth data point and it is **recorded, not adjudicated**.

### 2.12 🔴 The card's own defect: a window sized for the success case

`--idle 6` on the two `ping` cells is shorter than a **failing** ping takes to
give up. `C36-PING1` ended at ~6 s with the ping still running, so the next
command sat in the tty buffer and **`C36`, `C37`, `C40` and `C41`'s output is
each displaced one cell later** — `C38-PORT2`'s capture holds `C37`'s command
and the `100 % packet loss` line belonging to `C36`.

**Nothing is lost and nothing is void**; the data is in the following capture
and `check-predictions` scores `41 of 41` because every cell ran. But
**`check-predictions` scores existence and mtime, so a displaced capture looks
exactly like a correct one** — the same family as the `--idle`/`sleep` trap that
nearly emptied a whole press ladder on seating 20.

**The rule this adds**: a cell whose payload can FAIL must have its window sized
for the failure, not for the success. A succeeding `ping` prints for ~4 s; a
failing one prints **nothing** for ~4 s and then prints its statistics, so an
`--idle` shorter than that ends the capture with the shell still busy.

---

## § 3 — where this seating's instruments went, and the audit pass that asked

The eighth audit method — *enumerate what this segment produced, then ask who
owns each thing* — found one gap that the other seven do not reach: **the card
cites two scripts by a `scratchpad/` path, and a scratchpad is session-local.**
A card citing a script nobody can run cites nothing, and this repository's own
lesson is that *recording a conclusion without the re-runnable command that
produced it is not recording it* — which is why `tools/bootbytes.py` exists.

| built as | landed as | why it is worth keeping |
|---|---|---|
| `scratchpad/s87-procs.py` | **`tools/imgprocs.py`** | `FW-46`'s answer. It is what killed two cells of this card before power, and every future card needs it. Four controls print on every run and a broken search REFUSES rather than reporting absences |
| `scratchpad/s87-diff.py` | **`tools/swdiff.py`** | the instrument behind every register conclusion in § 2. It refuses unless both captures carry exactly 37 rows, and it splits the report by the `dumb` flag so the negative control is read off the same output |
| `scratchpad/s87-counters4.py` | ⚠️ **not promoted** | the driver's counter arithmetic, re-implemented from `file:line`. It is cited by the card's § 2.6 and by § 2.4 above, and it is **carried forward** rather than committed tonight: it hardcodes one cell ordering, so promoting it means parameterising the cell list, and a tool committed without controls is the thing this repo refuses |
| `scratchpad/s87-bootpred.py` | ⚠️ **not promoted** | it wraps `bootbytes` and adds the precondition `bootbytes predict` does not check — *is every baseline tag still in this image*. It belongs **inside** `bootbytes`, not beside it, and that is a small edit to an existing tool with an existing suite |
| `scratchpad/s87-run.sh` | ⚠️ **not promoted** | runs a card's cells taken verbatim out of the frozen card rather than retyped. Genuinely reusable and genuinely untested |

🔴 **So three of five are carried forward, and saying so is the point.** The
card's § 2.6 quotes `scratchpad/s87-counters4.py` and that citation will not
resolve for a future reader; this row is where they find out what it was and
that it was not lost, only not promoted.

🟢 **And one tool was changed rather than added.** `tools/xcheck.py` 1.0 → 1.1:
the sweep now excludes a capture whose `.log` is 0 bytes, **counted and
printed**. 量 2026-09-19: this seating committed the **first five 0-byte
captures in the repository's history** — four of them the evidence that a hung
board sent nothing, one the documented healthy board-off pre-flight — and
`tools/ci-expected.tsv:338` already listed *"an empty file refuses in one and
returns `[]` in the other"* among the *"REAL divergence(s) the corpus cannot
reach"*. **The corpus reached it.** The divergence stays where it is tested, in
control `C3`; what changed is the sweep's population, by a predicate that
belongs to neither parser. Two new controls, `C3d` and `C3e`, say the exclusion
happens and that it is a guard rather than a blanket: self-test 18 → **20**,
`ci-expected.tsv` updated in the same edit.
