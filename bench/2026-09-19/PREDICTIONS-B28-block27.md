# Block 27 — the switch driver's first execution, and `D2` measured four-cornered

**Frozen before these cells.** Seating 27, `bench/2026-09-19/`.
**declared date 2026-09-19**. Image `r6sw1`, `RECIPE_ID` `f681f8e0`.

🔴 **This card does NOT say "frozen before power", and that is deliberate.** The
board was powered at 00:58 and has been at the `<RealTek>` prompt since. § 0.3
names every capture that predates this card and says what may and may not be
concluded from each.

---

## 0. What this block is

`R6-2`'s DoD is *"the state is proved by a register read-back, not by the
absence of a complaint"*, and its named failure mode is *"that a dumb switch
looks identical to a switch nobody configured"*. The driver that answers it —
`config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c`, 662 lines, commit
`8b4ae4c` — is in the image and **not one of its instructions has ever
executed**. `rlxfw-marks verify` proves a translation unit is in an artefact and
says nothing about reachability.

The proof is four-cornered, not two:

| state | what it is | before today |
|---|---|---|
| `S0` | the loader's state | 量 — block 24, and again today as `X2`–`X7` |
| `S0'` | after early kernel init, **before** the vendor NIC driver | **never measured by anybody**; latched by this driver at `subsys_initcall` |
| `S1` | after `FULL_RST` | never measured |
| `S3` | this driver's dumb configuration | never measured |

`D2` is **`S3 ≠ S1`**, register by register, with a positive control on the
reset, a negative control on the writes, and a round trip.

### 0.1 The instrument

`/proc/rtl819x-switch`, a 37-register census in one array so `dump`, `snap` and
`diff` are generic. Four slots; slot 0 is latched at `subsys_initcall` and
`snap 0` is refused. One write path, guard ordered **before** the store.

**Verbs, 讀 the parser at `:535-609`, in dispatch order**: `unlock i-mean-it` ·
`lock` · `snap <n>` (`n` 1–3; 0 and ≥4 refused) · `diff <a> <b>` ·
`reset full` · `reset vendor` · `start` · `dumb` · `restore <n>` (`n` 0–3).
Anything else `-EINVAL`; `count >= 48` `-EINVAL`.

🔴 **`resetcmp` IS NOT A VERB, and `docs/KNOWN-ISSUES.md:785` says it is.**
量 2026-09-19: the token appears exactly twice in the whole repository — a
comment inside the driver at `:323`, and that `KNOWN-ISSUES` row, which calls it
*"the `resetcmp` verb, which runs both and diffs the dumps."* Typing it returns
`-EINVAL`. **An owner file describes a verb that does not exist**, and this card
composes the comparison out of the verbs that do: `reset full` → `snap` →
`reset vendor` → `snap` → `diff`.

🔴 **And composing it exposed a confound the missing verb hid.**
`rtl819x_sw_do_reset()` asserts `FULL_RST` on **both** paths (`:336-339`); the
vendor recipe only *adds* the 650 ms clock gate after it. So a naive
`reset full` → snap → `reset vendor` → snap → diff measures *the clock gate*
**and** *FULL_RST applied a second time*, and cannot separate them. **§ 2.6 runs
`FULL_RST` twice with a snapshot between, so idempotence is measured first and
the clock-gate delta is read against it.**

### 0.2 The image, re-derived on this desk today

| | |
|---|---|
| `nfjrom` | **1,073,152** bytes, sha256 `c32eb775668e5ba7b7caf11fcb0d2c89c852f768943b6c79b6ed623185b92fe8` |
| built from | `vmlinux` 4,175,548 bytes, sha256 `c792bf601e11221a…`, which is the sha256 the build's own manifest recorded |
| `RECIPE_ID` | **`f681f8e0`** — the manifest's `recipe_id`, **and** `find config -type f -print0 \| LC_ALL=C sort -z \| xargs -0 sha256sum \| sha256sum \| cut -c1-8` re-run today. Two sources, equal. The board must print `RLXFW-ID0=F681F8E0` |
| decompressed | 3,658,240 bytes, 69.8 % of the 5,242,880 ceiling, 1,584,640 free |
| marks | `all 12 mark(s) present once`, 8 witnesses present, 1 confirmed absent, absent from **2** vendor artefacts. `MK9 str:rtl819x-switch mine:2` |

⚠️ **`rtkimage check` exits 1 on this image and the failure is in a file that is
never uploaded.** 量, isolated by measurement today: without `--linuxbin`,
`rc=0`; with it, `rc=1`. `cmd_check` at `:404` counts a `bad` when
`lb['signature'] != b'cr6c'`, and this board's `linux.bin` is **`cr6b`** because
the Makefile selects `linux-ro` for `CONFIG_SQUASHFS=y` and this `cvimg` writes
`cr6b` for that option — which the **same tool's** `--compare-vendor` text
already documents (量 2026-08-29). Two halves of one tool disagree about one
byte. `linux.bin` is the flash image; the RAM boot path uses `nfjrom` and
nothing else.

⚠️ **`MK9` reads `2` here and `3` was reported for this image last segment.**
Not a contradiction: last segment read the **ELF**, this reads the **flat
image**. `RUNSHEET` `P10` exists for exactly that gap, and `config/rlxfw-marks.tsv`'s
own `MK9` row predicts *"contiguous in `.rodata` twice over
(`RTL819X_SW_VERSION`, `RTL819X_SW_PROC_NAME`)"* — so **2 is the predicted flat
count** and the ELF's third occurrence is in a section that does not load.

### 0.3 🔴 What predates this card, and what each capture may be used for

Seven captures in this directory were taken **before** this card existed. They
are `X`-prefixed and therefore structurally outside § 6's fence. Their decision
rules are frozen here:

| capture | when | what it is | what it may be used for |
|---|---|---|---|
| `X0-preflight` | 00:57 | board OFF, 0 bytes, 3.071642 s, three artefacts, `rc=1` | the documented healthy pre-flight signature. **Evidence that the instrument opened the port**, nothing about the board |
| `X1-esc` | 00:58–01:03 | the 300 s ESC window that caught the cold boot; `prompt_seen: true`, 16,193 bytes | **the cold-boot banner**, and the proof that no vendor firmware ran: 4,088 `0x1b`, **0** `^`, **1** `[`, **0** BEL — the exact inverse of `bench/2026-09-17b`'s `X0-esc` (0 `0x1b`, 4,095 `^`, 4,095 `[`, 2,277 BEL), which is the discriminator that seating measured |
| `X2-L4200` | 01:05 | `DW BB804200 4` → `81964000 00000001 04980000 00008003` | **`CVIDR`'s first reading ever on this die**, and `SSIR`'s |
| `X3-L4410` | 01:05 | `DW BB804410 4` → `00000001 00000000 00080000 00000200` | `MSCR`'s first reading ever; `SWTCR0`; `SWTCR1` |
| `X4-L4A00` | 01:05 | `DW BB804A00 4` → `000001FF 00000000 00080008 00080008` | `VCR0`'s first reading ever; `VCR1`; `PVCR0`; `PVCR1` |
| `X5-L4A10` | 01:05 | `DW BB804A10 4` → `00080008 00080008 00000001 00000000` | `PVCR2`–`PVCR4`; `PBVCR0` |
| `X6-L4200b`, `X7-alive` | 01:06, 01:25 | `DW BB804200 4` repeated | **repeatability control on the loader read path** — both byte-identical to `X2`. A chip-version register nobody writes read three times twenty minutes apart |

🔴 **What this costs, stated rather than left to be found.** `X2`–`X5` were read
before this card was written, so the loader-state values in § 2.1 and § 2.3 are
**not blind predictions** — they are measurements this card reasons *from*. What
remains blind, and is the whole point, is **every value the driver reads**: `S0'`,
`S1`, `S1b`, `S2v`, `S3`, and the round trip. No line of this card's § 2.4 → § 2.8
has ever been observed.

🟢 **And one thing improves because of them.** `docs/KNOWN-ISSUES.md:787` records
that `CVIDR` *"is a read-path control that cannot be positive yet … on the first
seating it can only fail."* It can now. `X2`/`X6`/`X7` give it a prior value on
this die by a path — the loader's `DW` — that shares no code with
`__raw_readl()` in my driver. § 2.4 predicts equality.

### 0.4 🔴 Hazards, pre-registered

1. 🔴 **`PSRP` bit 8 is read-to-clear (`NET-11`), and this driver reads all 37
   registers at `subsys_initcall` and 74 times per `cat` (`FW-64`).** So the
   boot latch **consumes any pending link-down event before userspace exists**,
   and every `cat` consumes it again. **`NET-30 殘留`'s decisive experiment —
   *read `PSRP` immediately after a cold boot* — can no longer be run on any
   image containing this driver.** The consumed value survives only in slot 0's
   column of the first `cat`. This is a consequence of a read-only driver and it
   is named here because nothing else in the repository names it.
2. 🔴 **`C3-L4128`/`C4-L4138` consume the same latch at the loader prompt**,
   before the kernel even boots. Declared, not avoided: the reading is worth
   more than the latch, and the latch is already 27 minutes stale.
3. 🔴 **`reset vendor` gates the switch core's clock for 650 ms in a busy wait
   inside a `/proc` write.** The watchdog on this board bites at **1,334.723 ms**
   (`FW-52`/`CLK-28`) and is kicked from the timer tick. `mdelay()` runs with
   interrupts enabled, and the measured precedent is stronger than the argument:
   seating 16's **13.3-second** 4 MiB PIO traversal ran in process context on ten
   boots without a bite — 20× longer. **`C31-RSTV` still carries `--esc-after`**,
   because the cost of being wrong is the vendor firmware running unobserved,
   which has happened twice.
4. 🔴 **`dumb` may kill networking.** It writes `VCR0 = 0x80000000`
   (802.1Q-unaware) and every PVID to 1 while the vendor's NIC driver is running
   with its own VLAN configuration. `C36-PING1` is the measurement, not a smoke
   test, and a failure there is a result.
5. ⚠️ **Every runtime mark is emitted inside the `/proc` write via
   `rlxfw_puts` (direct UART) while ash's echo drains through the tty**, so
   `FW-47` interleaving applies. **Every verdict on this card is a FIELD in a
   following `cat`, never the text of a mark.** Every verb cell carries
   `sleep 1 ; ` for the same reason (`bench/2026-09-17b/CORRECTIONS-block26.md`
   § 1: six for six, zero interleaving).
6. ⚠️ **Every capture line is CRLF.** Any comparison quoted below is against the
   field after `tr -d '\r'`.
7. ⚠️ **This image's `ping` ignores `-c` (`NET-26`)**, so `ping 10.1.1.2` sends
   the default. The measured default on this build is **4**.
8. ⚠️ **`echo read <a> 4` prints ONE word** — the `4` is a byte count
   (`NET-33`). `C14-IMR` asks for `8` because it wants two.
9. 🔴🔴 **`memDump` issues FIVE `READ_MEM32` per row — at `+0/+4/+8/+12/+16` —
   BEFORE it tests `max == 0`** (讀 `rtl865x_proc_debug.c:141-145`, and an
   identical copy at `common/rtl_utils.c:160-164`). So `read <a> 4` **touches
   twenty bytes and displays four**, and `read 0xB8010028 8` physically reads
   `…28`, `…2C`, `…30`, `…34`, `…38`. **If any register in that span is
   read-to-clear, a read destroys it and the output cannot show that it did.**
   This is why `C16-IMR2` uses a command **character-identical** to `C14-IMR`
   rather than a narrower one: both sides of the comparison then have the same
   side effects, which is what makes the difference attributable to the write
   between them. Block 26's card knew the over-read; that it happens *before*
   the `max` test is 讀 today.

---

## 1. The boot

`looprun --mode bench --skip S2,S3` drives reset → rescue → burn-flag read-back
→ host link → upload → staged-head read-back → boot → assert with no operator
gap. `S2` and `S3` are skipped because the image is already built and verified
at the desk; `--cell-top` is therefore not needed and `--image` is passed
explicitly.

⚠️ **`looprun`'s four captures are outside § 6's fence**, as block 26 did it.
It asserts on its own: the burn flag reads `00000000` **from the word at
`0x8040D4A0`** and not from the loader's echo (`C-6` measured those two
disagreeing), the staged head equals the image it sent, and the board prints the
id the build computed.

🔴 **Host-side precondition, performed at the desk at 01:32 and recorded here
because `RUNSHEET` `P3` has fired four times**: `enxfc19286184c9` was **DOWN with
no address** — the fifth occurrence. Fixed before power was spent:
`10.1.1.2/24`, `Link detected: yes`, `ip -4 route get 10.1.1.1` resolving through
that interface and not through WSL's NAT'd `eth0`. ⚠️ `ethtool` also reads
**`Duplex: Half`** at 100 Mb/s, which is recorded as a suspect and is not
expected to affect a TFTP put.

**Boot-capture prediction: `bench/2026-09-19/r6sw1-boot.log` is 1,759 bytes.**

Derived, not copied, by `scratchpad/s87-bootpred.py`:

```
  710  const          (bootbytes K2: ONE value over 98 captures, 7 images)
+ 927  baseline marks (57 marks, bench/2026-09-10/C1-boot.log, 1,637 bytes)
+ 122  switch marks   (SW0 11 + SW1..SW5 20 each + SW6 11)
------
= 1759
```

🔴 **Its precondition is checked rather than assumed**: `bootbytes predict`
prints the baseline's own length and says *add for each NEW boot mark* — which is
wrong if this image DROPPED a driver. So the script asks the flat image whether
each of the 57 baseline tags is present. 量 today: **0 absent**, and all seven
switch marks present **exactly once**. The baseline capture has the same shape as
`looprun`'s `S7` (`sent: "J 80500000"`, `--idle 8 --seconds 45`), so the two
numbers are comparable.

**Refutation.** 1,766 means `SW6-NOPROC` fired instead of `SW6` — `create_proc_entry`
failed and every Linux-phase cell below is void. Any other length is unexplained
and § 2.4 onward is void.

---

## 2. The predictions

### 2.1 The loader phase — `C1`–`C8`

These die the moment `looprun` boots the kernel, so they are first.

| cell | address | register | prediction | where from |
|---|---|---|---|---|
| `C1-L4104` | `BB804104` | `PCRP0`–`PCRP3` | `007F0039 047F0039 087F0039 0C7F0039` | `upstream/BENCH-LOG.md:4770-4795`, **2026-08**, same die, loader state. A match is a cross-seating repeatability result three weeks apart |
| `C2-L4114` | `BB804114` | `PCRP4`, `PCRP5`, `PCRP6`, `PCRP7` | `107F0039`, **`00000000`**, `187F00xx`, `1C7F00xx` | same source. `PCRP5 = 0` is `NET-10`'s measured hole and is the **negative control on the whole window**: if it reads `147F00xx` the pattern is an address echo and nothing in this row means anything |
| `C3-L4128` | `BB804128` | `PSRP0`–`PSRP3` | `000010E0` on the unlinked ports; **exactly one** of `PSRP0`–`PSRP4` carries `LinkUp` (bit 4) with `Speed` = 100M, because the cable is in and the host reads `Link detected: yes` | block 24 decode + the host-side reading taken at 01:32 |
| `C4-L4138` | `BB804138` | `PSRP4`–`PSRP7` | `PSRP5 = 000000E2`, `PSRP6 = 0000007A`, `PSRP7 = 0000007A` | block 24's `C10-PS0` decode |
| `C5-L4148` | `BB804148` | **`PSRP8`**, `P0GMIICR`, +2 | `PSRP8` **未定 — never read by anybody**. `P0GMIICR = 00037D00` | the sweep has always stopped one word short of `PSRP8` |
| `C6-L4600` | `BB804600` | `PSRP6_RW` | `0000007A` | header comment `/*CPU Port Status : R/W */`. `00000000` withdraws the corroboration and is also a result |
| `C7-L4400` | `BB804400` | **`TEACR`**, +2, **`ALECR`** | 未定 — **two of the seven registers never read in any state** | — |
| `C8-MDIOR` | — | — | see § 2.2 | — |

🟢 **`PSRP` bits 13:12 are `PortEEEStatus`, and that closes a 未定 already in the
repo.** `docs/loader-phy-and-switch.md`'s last section records `PSRP0`
`000010E0`→`000000E0` and `PSRP3` `000010F9`→`000000F9` across loader/Linux with
*"the whole difference is bit 12 … 未定"*. It is `PortEEEStatus[0]`
(`PortEEEStatus_MASK (3<<12)`), whose only user in the entire vendor driver is
the line that prints it. **The loader-state values carry their own control**:
the field is set on exactly the five ports with an embedded PHY and clear on the
three without, with the unpopulated port 5 sitting between the classes.

### 2.2 `C8-MDIOR` — a discovery cell, and why it is armed

量 `upstream/RUNBOOK.md:988`, `:2513`: the loader's command table contains
**`MDIOR`, `MDIOW`, `PHYR`, `PHYW`, `PORT1`**, cross-checked against the
binary's own string table by a tool that refuses to report unless it finds all
17 names — so the list is complete. **Not one of them has ever been executed**,
in either project. ⚠️ Their argument syntax is unknown, and
`RUNBOOK.md:2568-2572` measured that the `?` help text is *not* the syntax
(`IPCONFIG:10.1.1.1` is rejected; `IPCONFIG 10.1.1.1` works).

Three outcomes, all results: a usage line names the syntax; `Unknown command !`
refutes the command list; a value means the bare form works.

🔴 **The hazard and the recovery.** A malformed command could fault the loader.
The loader runs its own watchdog at roughly one second (`CLK-08b`), so a fault
resets the board — and `--esc-after 15` catches the prompt that comes back.
**`MDIOW` and `PHYW` write and are not typed on this card**; a `cardnum` row
asserts their absence.

### 2.3 What `dumb` will and will not move, per register

🔴 **The naive form of `D2` is "nine registers move", and this card does not say
it, because `scratchpad/s87-decode.py` shows it would be refuted with the
hardware innocent.** Against **loader state**, three of the nine writes are
no-ops:

| register | loader (量, `X3`/`X4`/`X5`) | `dumb` writes | moves? |
|---|---|---|---|
| `MSCR` | `00000001` | `00000001` | **NO — already equal** |
| `VCR0` | `000001FF` | `80000000` | yes |
| `PVCR0`–`PVCR3` | `00080008` ×4 | `00010001` ×4 | yes |
| `PVCR4` | `00000001` | `00000001` | **NO — already equal** |
| `SWTCR0` | `00080000` | `00080000` (`v & ~0xC01F`) | **NO — already equal** |
| `SWTCR1` | `00000200` | `00000000` | yes |

⚠️ **Loader state is not `S1`.** `S1` is after `FULL_RST` and nobody has read it.
What this licenses is a **per-register** prediction instead of a blanket one, and
it names in advance the three whose contribution to `D2` is at risk.

🔴 **A second, independent way `D2` could be refuted by arithmetic**: if
`FULL_RST` zeroes everything — which is what `rtl8651_clearRegister()` thinks
blank looks like, though **that function has no caller anywhere in the tree** —
then `SWTCR0` (`0 & ~0xC01F = 0`) and `SWTCR1` (`0` over `0`) do not move
`S1 → S3` either. **`D2` holds if `S3 ≠ S1` on at least one register**, and the
registers most likely to carry it are `VCR0` and `PVCR0`–`PVCR3`.

🟢 **The documentary cross-check, on the one register that has one.** The draft
datasheet's Table 64 gives per-bit defaults for `PCRP0`–`PCRP4` assembling to
`0x007F....`, and this unit reads `PCRP0 = 0x007F0039`. **After `FULL_RST`,
`PCRP0`'s top half is predicted `0x007F`.** `PCRP0` is in the census, so `C27-RST1`'s
`cat` carries it with no extra cell. If it is not `0x007F`, *"full reset as a
reset baseline"* is refuted — which is also a result, and is why it is written here.

### 2.4 `C9-SW0` — the at-rest dump, and `S0'`

51 lines: 10 header, 4 slot, 37 register. Each register line is
`r %-9s %04X %08X %08X %d%d\n` = **38 bytes** (39 on the wire with ONLCR);
`P0GMIICR` at 8 characters is the longest name, so the `%-9s` never overflows and
the 3,600-byte page budget is never approached.

| field | prediction |
|---|---|
| `version` | `rtl819x-switch 1.0` |
| `nreg` | `37` |
| `unlocked` | `0` |
| `n_writes` | **`0`** — the sentence the whole driver is shaped around |
| `n_refused` | `0` |
| `n_reads` | **`38`** = 1 (`boot_cvidr`) + 37 (the slot-0 snapshot) |
| `n_reset` / `n_dumb` / `n_restore` | `0` / `0` / `0` |
| `boot_cvidr` | **`81964000`** |
| `slot0_full` … `slot3_full` | `1` / `0` / `0` / `0` |
| `r CVIDR 4200` live | **`81964000`**, equal to `X2`/`X6`/`X7` |
| `both` digit set | on exactly **11** rows |
| `dumb` digit set | on exactly **9** rows |

🟢 **The positive control**: `boot_cvidr`, the live `CVIDR` column and the slot-0
`CVIDR` column must all read `81964000`, the value the loader's `DW` read three
times. **Two code paths that share nothing, on a register nobody writes.**
If they disagree, the read path is broken and every reading below is void.

🔴 **The boot marks are the same values by a third path.** `SW1` = `boot_cvidr`;
`SW2`/`SW3`/`SW4`/`SW5` = slot 0's `MSCR`/`SWTCR1`/`VCR0`/`PVCR0`. They are
looked up **by name** and a miss returns `DEADBEEF`, so a `DEADBEEF` in the boot
capture is a table bug and not a reading.

⚠️ **`both` is predicted from the ARRAY, not from the driver's own comment**,
which says *"the twelve"* while the array flags **11** (it omits `PITCR`). The
comment is wrong; the array is what compiles.

### 2.5 `C10`–`C12` — the two controls that must come before any write

**`C10-SAME` / `C11-CAT1` — same-state sampling.** `snap 1`, `snap 2`, `diff 1 2`
with nothing between them. **Predict `SW-DIFF=00000000`.**
🔴 **The card's own correction**: the obvious form is `snap 1` then `diff 0 1`,
and that is **not** a same-state test — slot 0 is latched at `subsys_initcall`,
before the vendor NIC driver's `device_initcall`, so `diff 0 1` measures
everything the vendor driver did. Two back-to-back snapshots is the test.
A non-zero count names a register that moves on its own; `PSRP`'s read-to-clear
bit 8 and `MDCIOSR` are the candidates, and the desk can identify it by diffing
`C9`'s and `C11`'s register columns.

**`C12-LOCK` — the guard seen refusing, with a number.** `echo dumb` while
locked. Predict `-EPERM` at the shell, and in the same cell's `cat`:
`n_refused 1`, `n_writes 0`, `unlocked 0`, `n_dumb 0`.
🔴 **One refusal, not nine**: the guard is ordered before the store and the verb
`return`s on the first `-EPERM`, so a locked `dumb` costs **one** read (`MSCR`,
which happens before the first write) and **one** refusal.
⚠️ **`FW-41`**: ash puts a refused write's payload on the console **minus its
last character**, so `dum` may appear. That is a known instrument behaviour and
not a defect.

### 2.6 `C24`–`C33` — the reset ladder, `D2`, and the counter table

Every value below is generated by `scratchpad/s87-counters3.py`, which is the
driver's own arithmetic re-implemented from `file:line`. The card quotes the
generator rather than restating multiplications.

```
cell                                                  unlkd n_writes n_ref n_reads n_reset n_dumb n_restr slots
C9-SW0    at rest, and S0' in the right-hand column       0        0     0      38       0      0       0  1000
C11-CAT1  after snap 1 / snap 2 / diff 1 2                0        0     0     186       0      0       0  1110
C12-LOCK  the cat inside the LOCKED-dumb cell             0        0     1     261       0      0       0  1110
C26-UNLK  the cat inside the unlock cell                  1        0     1     335       0      0       0  1110
C27-RST1  [S1]  first FULL_RST                            1        1     1     410       1      0       0  1110
C28-SNP1  slot 1 <- S1                                    1        1     1     521       1      0       0  1110
C29-RST2  [S1b] second FULL_RST                           1        2     1     596       2      0       0  1110
C30-SNP2D slot 2 <- S1b, diff 1 2 = IDEMPOTENCE control   1        2     1     707       2      0       0  1110
C32-CATV  [S2v] after reset vendor                        1        7     1     782       3      0       0  1110
C33-SNP3D slot 3 <- S2v, diff 2 3 = the clock gate        1        7     1     893       3      0       0  1111
C34-DUMB  [S3]  the dumb configuration                    1       16     1     976       3      1       0  1111
C35-D2    slot 1 <- S3, diff 3 1 = D2                     1       16     1    1087       3      1       0  1111
C39-REST  round trip back to S0'                          1       25     1    1161       3      1       1  1111
C41-CATF  final                                           1       25     1    1235       3      1       1  1111
```

**`n_writes` 25, every one named**: 1 `C27-RST1` · 1 `C29-RST2` ·
**5** `C31-RSTV` (1 `SSIR` + 4 `SYS_CLK_MAG`) · 9 `C34-DUMB` · 9 `C39-REST`.
**`n_refused` 1**, and it is `C12`.

🔴 **`reset vendor` is FIVE writes, not one.** Its four `SYS_CLK_MAG` stores
bypass `rtl819x_sw_wr()` and add to `n_writes` by hand (`:341-357`), and its four
`__raw_readl(clk)` are **not** counted in `n_reads`. A card predicting `n_writes`
+1 there would be refuted by a driver that is behaving exactly as written.

🔴 **The refutation on the whole table, written first.** If the first `cat`
reports `n_reads` differing from **38** by a multiple of 37, then `FW-64` — *one
`cat` is two `read_proc` invocations* — does not hold for this driver and one
`cat` is one invocation. **That is a result about this kernel**, obtained on a
second driver, and the rest of the column is then re-derived with
`invocations=1`. Any other difference is unexplained and every counter
prediction on this card is void.

**The three comparisons this ladder exists for:**

| | cells | predicts | refuted by |
|---|---|---|---|
| **The reset's positive control** | `C9` vs `C27` | **at least one** census register satisfies `S1 ≠ S0'` | **zero**. Then `FULL_RST` did nothing, and `C29`–`C35` are recorded **VOID, not passed**. This is `R6-2`'s stop condition and it is written before the verb ran once |
| **Idempotence** | `C30`'s `SW-DIFF`, cross-checked against the `cat` columns of `C28` and `C29` | **0** — `FULL_RST` applied twice reaches the same state | non-zero. Then `FULL_RST` is not idempotent, and the clock-gate delta below **cannot be attributed** and is recorded as such |
| **What the 650 ms clock gate adds** | `C33`'s `SW-DIFF`, and `C32` vs `C29` at the desk | **未定 — no source in this repository has an opinion.** `rtl865x_asicCom.c:2002-2016` shows the vendor does not trust `FULL_RST` alone on the 8196E; whether the extra 650 ms moves a register has never been measured by anybody | nothing. Both answers are results, and `0` is the more interesting one |

**`D2` itself**: `C35`'s `SW-DIFF` is `|S3 − S2v|`, and the desk diffs `C34`'s
register columns against `C32`'s. **`D2` holds if that count is ≥ 1.** § 2.3
predicts which registers carry it.

⚠️ **The slots are reused and every state survives only in a capture.** Slot 1
holds the same-state snapshot at `C10`, then `S1` at `C28`, then `S3` at `C35`;
slot 2 holds `C10`'s second snapshot, then `S1b` at `C30`; slot 3 holds `S2v`.
Each overwrite loses the previous value **inside the driver** — which is why
every one of those states is also in a `cat` capture, and why the desk's diff of
the register columns is the primary evidence and `SW-DIFF` is the cross-check.
Slot 0 is never overwritten: `snap 0` is refused.

🟢 **The negative control on the writes** is free and is read off the same
captures: the 28 registers whose `dumb` digit is `0` must satisfy `S3 == S2v`.
If a register this driver never writes moves, something other than this driver
is moving it.

### 2.7 `C39-REST` — the round trip, and the hazard that makes it necessary

`restore 0` writes slot 0 back — **only the nine `dumb` registers**, because
writing a status register back is not a restore. Predict: the nine return to
their `S0'` values, `n_restore 1`, `n_writes 25`.

🔴 **This is not a formality.** This part has a measured counter-example:
`WDTCLR` was written `00A40000` and read back `00240000` (`FW-52`). And the
vendor's own `_rtl8651_readAsicEntry` reads a switch **table** entry twice into
two buffers and retries up to ten times if they disagree. ⚠️ That is the indirect
table path, not the direct register path this driver uses, and **nothing has
established that the direct path is free of the same problem.** If a register
does not come back, a read-back is not the proof `D2` assumes it is, and that is
the most consequential thing this card could find.

### 2.8 `C13`–`C18` — `R6-3`'s rung zero, with the engine off and the mask closed

`NET-38` gives the CPU-interface block at `CPU_IFACE_BASE = 0xB8010000`:
`CPUICR` `+0x000`, `CPUIIMR` `+0x028`, `CPUIISR` `+0x02C`, and
**`SWINTSET` = bit 20**, *"Set software interrupt"*. Writing it raises the NIC's
interrupt **with no ring, no descriptor, no PHY and no cable** — a rung below the
plan's `loopback → TX → RX → NAPI` ladder, which separates *loopback does not
work* from *my interrupt never arrives*. Those two are the same observation from
outside.

🔴 **There is no software-interrupt STATUS bit in any source.** 量: `SWINT|SW_INT|SOFT_INT`
over the whole header returns **one** line, `SWINTSET` itself; `CPUIISR`'s bit
list occupies 1, 2, 3–8, 9, 10, 16, 17–22, 23, 24, 25–30, 31 — **bit 0 is the
only unassigned bit.** 推 that it is the one. **So this is a discovery cell, and
whichever bit changes names something no source in this project documents.**

**Why it is safe here and would not be sixty seconds later.** With no interface
up, the vendor's probe has left `CPUICR = 00000000` (engine off, 量 `NET-33`) and
`CPUIIMR = 0`. With the mask closed no interrupt is delivered, the vendor's
handler never runs, and its `REG32(CPUIISR) = REG32(CPUIISR)` ack cannot clear my
bit — the same masked-observation strategy that has succeeded twice already
(`IRQ-08`, `IRQ-09`). **`C23-IFUP` calls `ndo_open`, which writes
`CPUICR = C4000000` and opens the vendor's mask.** That is why this block is
ordered before it and not after.

**The `write` syntax, 讀 from source today and not guessed.** 量
`rtl865x_proc_debug.c:4152-4161`: the token is `write`, matched as a **5-byte
prefix** by `memcmp(cmd_addr, "write", 5)` with the terminator never checked;
it takes **exactly two** arguments and no length; both go through
`simple_strtol(tokptr, NULL, 0)`; the store is `WRITE_MEM32(mem_addr,
mem_data)` = one 32-bit volatile store, with `big_endian32(x)` an identity on
this build. **There is no bounds check of any kind** — no `virt_addr_valid`, no
range test, no KSEG test. Those two lines are the whole validation.

🔴 **Five ways a typo writes to the wrong place instead of failing**, each 讀,
each checked against the two literal strings below before this card was frozen:

| | what it does | is it possible here |
|---|---|---|
| a **doubled space** | `strsep` returns an empty token, `""` is not NULL so no guard fires, `simple_strtol("")` is 0 → a store to **virtual address 0** | no: single spaces, asserted by a `cardnum` row |
| **hex without `0x`** | `simple_strtol(…, 0)` picks base 10, `'B'` breaks the loop at the first character → 0 → a store to **address 0** | no: both arguments carry `0x` |
| a **bare leading `0`** | base 0 reads it as **octal** — `00100000` would store 32768, not 1048576 | no: both arguments are `0x`-prefixed |
| a typo at the **end of the verb** | the prefix match means `writes` and `write1` still write; `WRITE` and `wirte` are safe. The inverse of intuition | no: the literal is `write` |
| **`len == 64`** | `if (len > 64)` admits 64 and then writes `tmpbuf[64]` on a `char tmpbuf[64]` — a one-byte stack overflow | no: the payload is **27** bytes |

**The two literal payloads**: `write 0xB8010000 0x00100000` and
`write 0xB8010000 0x00000000`.

**The predicted console output, and its formatting is itself a trap.** Two
lines per write (`:4134`, `:4162`), through `rtlglue_printf` → `panic_printk`,
so they survive `CONFIG_PRINTK=n` and carry no prefix and no timestamp:

```
cmd write
Write memory 0xb8010000 dat 0x100000: 0x<readback>
```

🔴 `%p` is **lowercase, zero-padded to 8** (`lib/vsprintf.c:738-743`), while
`%x` is **not padded** — so `0x00100000` prints as `dat 0x100000` and
`0x00000000` prints as `dat 0x0`. **A card predicting `dat 0x00100000` would
read as a refutation with the hardware innocent.** The `<readback>` is
deliberately **not** pre-registered: the handler reads the register back after
the store, `SWINTSET` may be self-clearing, and no source has an opinion — so
only the prefix up to `0x` is predicted, and the readback is the measurement.

| cell | predicts | refuted by |
|---|---|---|
| `C13-DMA0` | `CPUICR` = `00000000` | `C4000000` — an interface is up, and `C15`/`C17` are **abandoned**, not run |
| `C14-IMR` | `CPUIIMR` = `00000000`; `CPUIISR` **未定, never read by anybody** | `CPUIIMR ≠ 0` — the mask is open, and `C15`/`C17` are **abandoned** |
| `C15-SWSET` | `cmd write` then `Write memory 0xb8010000 dat 0x100000: 0x…` | any other address in that line — the parse went somewhere else and the block is void |
| `C16-IMR2` | exactly one `CPUIISR` bit differs from `C14`'s reading; 推 bit 0 | zero bits: `SWINTSET` raises no pending flag at all, which is also a result. More than one: unexplained |
| `C17-SWOFF` | `Write memory 0xb8010000 dat 0x0: 0x…` | as `C15` |
| `C18-DMA1` | `CPUICR` back to `00000000` | anything else: `SWINTSET` does not self-clear **and** the restore did not take |

⚠️ **`CPUIIMR` is never written by any cell on this card**, and the only address
any cell writes is `0xB8010000`. Three `cardnum` rows assert it: the count of
`echo write` is **2**, the count of `echo write 0xB8010000` is **2**, and the
count of `write 0xB8010028` is **0**.

🔴 **One source in three copies, re-derived here with the boundary stated.**
量 2026-09-19, taking the function as *from the line carrying its definition to
the first line that is exactly `}` in column 0*: **1,434 bytes, md5
`5e6d253247ffb4ff3f8a3edf04d43f4f`, identical in all three drops** —
`rtl819x-toolchain` `:4115-4178`, `saturn49-wecb` `:4118-4181`, `wecb-vz-gpl`
`:4115-4178`, at `<drop>/rtl819x/linux-2.6.30/…` in the latter two. The same
weakness `CLAUDE.md` records for the `PRId` table; **it must not be quoted as
three-way corroboration.**
⚠️ **The boundary is part of the number.** A first pass at this measurement
reported 1,435 bytes and a different md5 from a different closing-brace rule,
and a length and a digest that depend on an unstated convention are two numbers
nobody can reproduce. ⚠️ **Reachability is 推**: no `.config` in the vendor tree
was checked for `CONFIG_RTL_DEBUG_TOOL`; the argument is that `read`
demonstrably works on this device and both handlers are registered in the same
`if` block (`:5817-5824`).

### 2.9 `C19`–`C25` — the vendor `/proc` files, and the two this card lost

🔴🔴 **The pre-power audit killed two cells and `FW-46` is why they existed.**
`FW-46` says nothing in this repository can ask *can this image run this
command* before a card is frozen. **It can now, on the artefact**: a `/proc`
entry's name is a NUL-delimited `.rodata` literal, so
`b"\x00name\x00"` in the flat image answers it. 量 2026-09-19, with four
controls — `port_status` **1**, `memory` **2**, `rtl819x-switch` **1**, and a
synthetic name **0**:

**The vendor registers 42 distinct `/proc/rtl865x/` entries. Thirteen survive
into this image**: `stats`, `arp`, `ip`, `pppoe`, `igmp`, `memory`,
`diagnostic`, `port_status`, `phyReg`, `asicCounter`, `mmd`, `mac`,
`fc_threshold`. **Twenty-nine do not**, and two of them —
**`vlan` and `pvid`** — were cells on the first draft of this card. They would
have produced *"No such file or directory"* and scored as passes, because
`check-predictions` scores existence and mtime and not content.

**What replaced them is better**, and only because the audit ran:

| cell | predicts | where from |
|---|---|---|
| `C19-PHYID` | two lines of the form `read phyId(0), regId(2),regData:0x….` and `regId(3)` — **this project has never identified the PHY silicon**, and these two registers are the OUI, model and revision | 讀 `rtl865x_proc_debug.c`, `proc_phyReg_write`: the token is `read`, the arguments are `<phyId> <regId>`, both `simple_strtol(…, 0)`, and the printf is `"read phyId(%d), regId(%d),regData:0x%x\n"` through `rtlglue_printf` → `panic_printk`. 🔴 **`proc_phyReg_read`'s whole body is `return PROC_READ_RETURN_VALUE;`** — `cat /proc/rtl865x/phyReg` prints **nothing**, so the read is on the WRITE side, the same shape as `/proc/rtl865x/memory` |
| `C20-PHYST` | `regId(0)` = BMCR and `regId(1)` = BMSR for PHY 0 — link, autoneg and speed **from the PHY's own registers**, which is a second source for `PSRP0` sharing no code with it | same handler. 🟢 And a third source is already on this card: `C8-MDIOR` asks the **loader** for the same layer |
| `C21-PORT` | seven rows, `Port0`…`Port5` then one `CPUPort`; `CPUPort` shows `1G`, `NWay Mode Disabled`, `EEE Status 0`; `Port5 LinkDown` | 讀 `rtl865x_proc_debug.c:4192-4198`. 🔴 **`CPUPort` is a real register read of `PSRP6` = `0xBB804140`, not a hardcoded string** — the `port==CPU` test selects six characters of label and nothing else. `PSRP7` is never printed: the loop stops at `CPU = 6`, so `NET-10 殘留`'s *"`/proc` lists exactly one `CPUPort`"* is **predicted by the loop bound and is not evidence about `PSRP7`** |
| `C22-ACNT0` / `C25-ACNT1` | per-port ASIC MIB counters, **never read on this device**, bracketing `C23-IFUP` and `C24-PING0`. **Predict: at least one port's TX and RX counters advance by ≥ 4 across the bracket** | 讀 `rtl865x_proc_mibCounter_read` returns `len = 0` and calls `rtl865xC_dumpAsicDiagCounter()`, whose output goes to the **console** — so the file reads empty and the capture still holds the dump. 🟢 **This is `D3`'s shape**: a hardware counter that shares no code with `ifconfig`'s software counters or with `ping`'s own arithmetic |

🟢 **`NET-37 殘留` is resolved at the desk, and losing the `vlan` cell does not cost
it anything.** The residual reads *"`eth5`'s member mask is `0x0` while `PVCR4`
says P8 = 9"*. 量: that `0x0` is a literal `0` in a C struct initialiser
(`rtl_nic.c:455`) printed back by a boot `printf` that never touches the ASIC
(`:6479`), and it is the row `rtl865x_config()` **skips** (`:7358`,
`if(vlanconfig[i].memPort == 0) continue;`). The real LAN VLAN is built by
`re865x_packVlanConfig()`, which ORs in `0x100` — the CPU port — at
`rtl_nic.c:1266-1270`, the only such site in the driver, giving vid 9 the mask
`0x10F`. **The three numbers were never in contradiction; the residual paired
each with the wrong one.** And *"the interface `eth5`"* names something that does
not exist — `:6479` prints the array index; the device is `eth7` (量
`bench/2026-08-30c/V-6a.log`). The nine PVID fields it predicts were **already
confirmed by block 26's register readings, 9 of 9 with zero residual**, so this
card does not need the `/proc` file to close it.

---

## 3. The guards

1. **Zero flash writes.** No cell types `FLR`, `EW`, `EB`, `FLW` or any burn
   command, and four `cardnum` rows assert it. `looprun`'s `S5b` reads the burn
   flag from the word at `0x8040D4A0` and aborts unless it is `00000000`.
2. **No `echo write` to `/proc/rtl865x/memory` except the two named cells**,
   which write `CPUICR` and restore it. A `cardnum` row bounds the count at
   exactly two and names the address.
3. **`MDIOW` and `PHYW` are never typed.** A `cardnum` row asserts zero.
4. **`CPUIIMR` is never written.** A `cardnum` row asserts zero.
5. **No `--send` reaches 128 characters** (the measured cliff). A `cardnum` row
   asserts zero over 127.
6. **Every value criterion names an ADDRESS, never a word ordinal** —
   `DW <a> 1` returns four words and `echo read <a> 4` returns one.
7. **`--esc-after` on the one cell whose payload could reset the board**
   (`C31-RSTV`), and on `C8-MDIOR`, whose payload is an unverified loader command.

---

## 4. What this block does NOT claim

1. **It does not close `R6-3` or `R6-4`.** `R6-3` is a different driver and none
   of it exists; `C13`–`C18` are its rung zero and nothing more. `R6-4`'s DoD
   requires the vendor driver **not** loaded, and it is loaded throughout.
2. **`FULL_RST` is not proven to be a power-on reset.** It is a soft reset of
   *"tables & queues"*. What `D2` can support is *differs from the state this
   part's own documented full reset leaves it in* — strictly stronger than
   *differs from loader state*, strictly weaker than *differs from the power-on
   default*. The gap is named, not hidden.
3. **It says nothing about the VLAN table.** The table is reached indirectly
   through the TACI block (`SWTACR`/`SWTAA`/`TCR7`), which is a protocol and not
   a register write, and no cell here writes it. 🔴 And 量: on the 8196E that
   table is a **16-slot CAM with its own `vid` field**, so `rtl8651_getAsicVlan(9,…)`
   reads **slot 9**, not *"vid 9"* — worth knowing before anyone writes a card
   against it.
4. **It does not move `FLS-26`'s ledger** (99.61 % proven identical, 0.195 %
   proven different, 0.195 % undetermined). No `map` cell, no `FLR`.
5. **Which ASIC port the CPU physically attaches to is NOT settled.** The vendor
   source contradicts itself three ways: `enum PORTID` has `CPU = 6`; the
   VLAN/PVID path hardcodes bit **8** with `cpu port(port 8)` in the header; and
   `rtl865xc_swNic.h:155` has `RTL8651_CPU_PORT 0x07` in the packet-descriptor
   space. What is settled is narrower: for VLAN and PVID purposes the driver uses
   **8**, and for `PSRP`/`PCRP` indexing it uses **6**.
6. **The three GPL drops are one source in three copies** for
   `port_status_read` — 67 lines, sha256 prefix `a6eaa4b2d2f434a2`, `diff`
   IDENTICAL both pairs. The same weakness `CLAUDE.md` records for the `PRId`
   table. What makes § 2.9 more than that is the device's own printed output.

---

## 5. The cells

```
#-- L. PCRP0..PCRP3 at the loader prompt.  upstream 2026-08 read 007F0039 047F0039 087F0039 0C7F0039 on this die.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C1-L4104 --send 'DW BB804104 4' --until 'RealTek>' --seconds 15
#-- L. PCRP4..PCRP7.  PCRP5 must read 00000000 -- that is the negative control on the whole window.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C2-L4114 --send 'DW BB804114 4' --until 'RealTek>' --seconds 15
#-- L. PSRP0..PSRP3.  Consumes the read-to-clear LinkDownEventFlag; declared in 0.4.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C3-L4128 --send 'DW BB804128 4' --until 'RealTek>' --seconds 15
#-- L. PSRP4..PSRP7.  PSRP6 is the CPU port.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C4-L4138 --send 'DW BB804138 4' --until 'RealTek>' --seconds 15
#-- L. PSRP8 -- never read by anybody; every previous sweep stopped one word short.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C5-L4148 --send 'DW BB804148 4' --until 'RealTek>' --seconds 15
#-- L. PSRP6_RW, the header's /*CPU Port Status : R/W */.  Predict 0000007A.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C6-L4600 --send 'DW BB804600 4' --until 'RealTek>' --seconds 15
#-- L. TEACR and ALECR -- two of the seven registers never read in any state.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C7-L4400 --send 'DW BB804400 4' --until 'RealTek>' --seconds 15
#-- L. DISCOVERY.  A loader command that exists and has never been executed.  esc-after is the recovery.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C8-MDIOR --send 'MDIOR' --esc-after 15 --esc-period 0.02 --until 'RealTek>' --seconds 30
```

```
#-- H+L. reset -> rescue -> burnflag -> hostlink -> upload -> staged head -> boot -> assert, no operator gap.
/usr/bin/python3 tools/looprun.py --mode bench --cell r6sw1 --out-dir bench/2026-09-19 --port /dev/ttyUSB0 --host 10.1.1.1 --skip S2,S3 --recipe-override f681f8e0 --image /home/key/fwre-work/rebuild/imgwork/r6sw1/kroot/rtkload/nfjrom --image-sha256 c32eb775668e5ba7b7caf11fcb0d2c89c852f768943b6c79b6ed623185b92fe8
```

```
#-- S. THE FIRST EXECUTION OF THIS DRIVER.  37 registers live beside S0', and n_writes 0.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C9-SW0 --send 'sleep 1 ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. same-state sampling.  NOT diff 0 1 -- slot 0 predates the vendor NIC driver.  Predict SW-DIFF=00000000.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C10-SAME --send 'sleep 1 ; echo snap 1 > /proc/rtl819x-switch ; echo snap 2 > /proc/rtl819x-switch ; echo diff 1 2 > /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. the fields that carry C10's verdict.  n_reads 186, slots 1110.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C11-CAT1 --send 'sleep 1 ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. the guard seen REFUSING, with a number.  n_refused 1, not 9.  FW-41 may eat the last character.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C12-LOCK --send 'sleep 1 ; echo dumb > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. CPUICR baseline.  Must be 00000000 -- engine off -- or C15 and C17 are abandoned.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C13-DMA0 --send 'sleep 1 ; echo read 0xB8010000 4 > /proc/rtl865x/memory' --idle 5 --seconds 30
#-- S. CPUIIMR and CPUIISR.  8 is a BYTE count, so this prints two words.  CPUIISR has never been read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C14-IMR --send 'sleep 1 ; echo read 0xB8010028 8 > /proc/rtl865x/memory' --idle 5 --seconds 30
#-- S. R6-3 RUNG ZERO.  SWINTSET, engine off and mask closed.  27-byte payload, single spaces, both args 0x-prefixed.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C15-SWSET --send 'sleep 1 ; echo write 0xB8010000 0x00100000 > /proc/rtl865x/memory' --idle 5 --seconds 30
#-- S. CHARACTER-IDENTICAL to C14 so the five-word over-read is the same on both sides of the write.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C16-IMR2 --send 'sleep 1 ; echo read 0xB8010028 8 > /proc/rtl865x/memory' --idle 5 --seconds 30
#-- S. put CPUICR back.  Predict `dat 0x0`, not `dat 0x00000000` -- %x is not padded.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C17-SWOFF --send 'sleep 1 ; echo write 0xB8010000 0x00000000 > /proc/rtl865x/memory' --idle 5 --seconds 30
#-- S. CHARACTER-IDENTICAL to C13.  CPUICR must be 00000000 again.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C18-DMA1 --send 'sleep 1 ; echo read 0xB8010000 4 > /proc/rtl865x/memory' --idle 5 --seconds 30
#-- S. PHY 0 identifier registers 2 and 3.  This project has never identified the PHY silicon.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C19-PHYID --send 'sleep 1 ; echo read 0 2 > /proc/rtl865x/phyReg ; echo read 0 3 > /proc/rtl865x/phyReg' --idle 5 --seconds 30
#-- S. PHY 0 BMCR and BMSR.  Link and autoneg from the PHY's own registers -- a second source for PSRP0.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C20-PHYST --send 'sleep 1 ; echo read 0 0 > /proc/rtl865x/phyReg ; echo read 0 1 > /proc/rtl865x/phyReg' --idle 5 --seconds 30
#-- S. port_status BEFORE dumb.  After dumb, "what the vendor set" and "what I set" stop being separable.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C21-PORT --send 'sleep 1 ; cat /proc/rtl865x/port_status' --idle 5 --seconds 30
#-- S. ASIC MIB counters, never read on this device.  The baseline half of the bracket around four pings.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C22-ACNT0 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --idle 5 --seconds 40
#-- S. ndo_open.  Writes CPUICR C4000000 and opens the vendor's mask, which is why it is here and not earlier.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C23-IFUP --send 'ifconfig eth4 10.1.1.1 netmask 255.255.255.0 up' --idle 5 --seconds 30
#-- S. the network is alive with the VENDOR's switch configuration.  C36 is read against this.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C24-PING0 --send 'ping 10.1.1.2' --idle 6 --seconds 40
#-- S. the other half.  At least one port's TX and RX must advance by >= 4 -- a hardware counter, sharing no code with ping.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C25-ACNT1 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --idle 5 --seconds 40
#-- S. unlocked 1, n_writes still 0.  The guard comes down and nothing has been written yet.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C26-UNLK --send 'sleep 1 ; echo unlock i-mean-it > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. S1.  THE RESET'S POSITIVE CONTROL: at least one register must differ from S0' or C29..C35 are VOID.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C27-RST1 --send 'sleep 1 ; echo reset full > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. slot 1 <- S1.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C28-SNP1 --send 'sleep 1 ; echo snap 1 > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. S1b.  A SECOND FULL_RST, so idempotence is measured before the clock gate is attributed.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C29-RST2 --send 'sleep 1 ; echo reset full > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. diff 1 2 is the IDEMPOTENCE control.  Predict SW-DIFF=00000000.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C30-SNP2D --send 'sleep 1 ; echo snap 2 > /proc/rtl819x-switch ; echo diff 1 2 > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. reset vendor.  650 ms of mdelay; esc-after is armed because the cost of a bite is vendor firmware.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C31-RSTV --send 'sleep 1 ; echo reset vendor > /proc/rtl819x-switch' --esc-after 12 --esc-period 0.02 --until 'RealTek>' --seconds 35
#-- S. S2v.  The verdict on C31 is n_reset 3 and n_writes 7 HERE, never the mark text.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C32-CATV --send 'sleep 1 ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. diff 2 3 is what the 650 ms clock gate adds.  No source in this repository has an opinion.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C33-SNP3D --send 'sleep 1 ; echo snap 3 > /proc/rtl819x-switch ; echo diff 2 3 > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. S3.  THE DUMB CONFIGURATION.  Nine writes, each preceded by a read of the same register.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C34-DUMB --send 'sleep 1 ; echo dumb > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. D2.  diff 3 1 is |S3 - S2v|.  D2 holds if it is at least 1.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C35-D2 --send 'sleep 1 ; echo snap 1 > /proc/rtl819x-switch ; echo diff 3 1 > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. does the network survive a dumb switch.  A failure here is a result, not a fault.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C36-PING1 --send 'ping 10.1.1.2' --idle 6 --seconds 40
#-- S. ASIC counters after dumb.  Did frames still move through the switch with every PVID at 1.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C37-ACNT2 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --idle 5 --seconds 40
#-- S. port_status after dumb, against C21.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C38-PORT2 --send 'sleep 1 ; cat /proc/rtl865x/port_status' --idle 5 --seconds 30
#-- S. the ROUND TRIP.  WDTCLR is this part's measured counter-example; a register that does not come back is the headline.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C39-REST --send 'sleep 1 ; echo restore 0 > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
#-- S. does the network come back with the vendor's configuration restored.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C40-PING2 --send 'ping 10.1.1.2' --idle 6 --seconds 40
#-- S. n_writes 25, and section 2.6 names every one of them.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-19/C41-CATF --send 'sleep 1 ; cat /proc/rtl819x-switch' --idle 5 --seconds 40
```

### 5.1 The numbers this card states, and where each is re-derived FROM

```cardnum
cells-fence	41	count bench/2026-09-19/PREDICTIONS-B28-block27.md ^bench/2026-09-19/C[0-9]+-[A-Za-z0-9_]+$
image-bytes	1073152	size /home/key/fwre-work/rebuild/imgwork/r6sw1/kroot/rtkload/nfjrom
image-sha16	c32eb775668e5ba7	sha256-16 /home/key/fwre-work/rebuild/imgwork/r6sw1/kroot/rtkload/nfjrom
declared-date	1	count bench/2026-09-19/PREDICTIONS-B28-block27.md [*][*]declared date 2026-09-19[*][*]
send-over-127	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*(EW |EB |FLW )
no-phy-write	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*(MDIOW|PHYW)
no-cpuiimr-write	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*write 0xB8010028
mem-writes	2	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*echo write
mem-writes-cpuicr	2	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*echo write 0xB8010000 0x[0-9A-F]{8} >
no-doubled-space	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md -{2}send '[^']*echo write[ ]{2}
no-autoexec	0	count bench/2026-09-19/PREDICTIONS-B28-block27.md ^/usr/bin/python3 .*(allow-autoexec|boot[.]img)
```

---

## 6. The fence

```cells
bench/2026-09-19/C1-L4104
bench/2026-09-19/C2-L4114
bench/2026-09-19/C3-L4128
bench/2026-09-19/C4-L4138
bench/2026-09-19/C5-L4148
bench/2026-09-19/C6-L4600
bench/2026-09-19/C7-L4400
bench/2026-09-19/C8-MDIOR
bench/2026-09-19/C9-SW0
bench/2026-09-19/C10-SAME
bench/2026-09-19/C11-CAT1
bench/2026-09-19/C12-LOCK
bench/2026-09-19/C13-DMA0
bench/2026-09-19/C14-IMR
bench/2026-09-19/C15-SWSET
bench/2026-09-19/C16-IMR2
bench/2026-09-19/C17-SWOFF
bench/2026-09-19/C18-DMA1
bench/2026-09-19/C19-PHYID
bench/2026-09-19/C20-PHYST
bench/2026-09-19/C21-PORT
bench/2026-09-19/C22-ACNT0
bench/2026-09-19/C23-IFUP
bench/2026-09-19/C24-PING0
bench/2026-09-19/C25-ACNT1
bench/2026-09-19/C26-UNLK
bench/2026-09-19/C27-RST1
bench/2026-09-19/C28-SNP1
bench/2026-09-19/C29-RST2
bench/2026-09-19/C30-SNP2D
bench/2026-09-19/C31-RSTV
bench/2026-09-19/C32-CATV
bench/2026-09-19/C33-SNP3D
bench/2026-09-19/C34-DUMB
bench/2026-09-19/C35-D2
bench/2026-09-19/C36-PING1
bench/2026-09-19/C37-ACNT2
bench/2026-09-19/C38-PORT2
bench/2026-09-19/C39-REST
bench/2026-09-19/C40-PING2
bench/2026-09-19/C41-CATF
```

⚠️ **The fence holds 41 entries and the cell ids run to 41, with no gaps.**
Two things moved it during the pre-power audit, and both are recorded rather
than smoothed over. `C15`–`C18` were held out of the first draft because the
`write` syntax of `/proc/rtl865x/memory` was unverified; they are in because it
was verified from source before the freeze (§ 2.8). And `C19`/`C20` were
`cat /proc/rtl865x/vlan` and `cat /proc/rtl865x/pvid` until the audit measured
that **neither file exists in this image** (§ 2.9) — they became the two
`phyReg` cells, and `asicCounter` gained a bracket of its own, which is why the
count rose by three rather than falling by two.

⚠️ **`N of N` means the cells this card types at the shell and at the loader
prompt.** `looprun`'s four captures — `r6sw1-rz`, `r6sw1-rescue.json`,
`r6sw1-ab2`, `r6sw1-2a`, `r6sw1-boot` — are outside it on purpose, and so is its
verdict. The seven `X` captures of § 0.3 are structurally outside it: the fence
regex anchors on `C[0-9]+-`.
