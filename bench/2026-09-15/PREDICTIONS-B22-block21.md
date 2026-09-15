# Block 21 — column ② on the silicon, and the first binary of mine to run as a Linux process

**`R1-pub-4a` (`D-diff`), the measurement half.** One power cycle. The same 75
`.word` encodings `probe4` ran bare metal, issued from Linux **user mode** by
`/bin/uprobe`, under rlxfw's own kernel. Three riders share the boot because a
Linux shell is the thing they were all waiting for.

Written 2026-09-15, seventy-third segment, desk, **before the board was
powered**. Every number in § 10.1 is re-derived from the artefact it names;
every column-② cell is a prediction registered here or cited by id from a file
frozen before today.

---

## 0. What this block is, in one paragraph

`docs/emulation-surface.md` states 45 census rows in two columns. Column ① is
measured — `bench/2026-09-14/C1-P4j.log`, bare metal, `Status = 0x1000FC00`.
Column ② has **never been measured for any row**. This block measures it. The
instrument is `config/rlxfw-user/isaprobe/uprobe.c`, which links
`tools/rlxprobe/cells4.S` **verbatim**, so the two columns are the same bytes
at two privilege levels rather than two tables that happen to agree.

---

## 1. The image, pinned four ways

| what | value |
|---|---|
| kernel | `up2`, `vmlinux` 4,125,078 B, sha256 `9e2bb2219977692d…` |
| `RECIPE_ID` | **`5abefd82`**, re-derived from `config/` at 19:47 TST today |
| uploadable | `bench-only/up2-work-20260915/up2-20260915/kroot/rtkload/nfjrom`, 1,057,792 B, sha256 `3ff8b3c94029b8ea…` |
| the probe | `/bin/uprobe`, 29,184 B stripped, sha256 `f3bf56ee6d97712e…`, `BUILD_ID` `a87be346bb83e7f9` |

`RECIPE_ID` is a digest over `config/` **only**, so it cannot tell two images
built from one frozen `config/` apart; `--image-sha256` can, and S6 is given
it. `BUILD_ID` is a digest over `uprobe.c`, `cells4.S`, `probe4rows.h` and
`rlxasm.h`, compiled in and printed by the board — **so the board names its
own probe build, and nobody types either value.**

---

## 2. Five things the desk settled today, with zero power

**① The handover's `RECIPE_ID` re-derivation command is broken, and it fails
towards a rebuild.** `find config -type f | xargs -0 sha256sum | …` gives
`aa422fb4`, which is a digest **of a `sha256sum` error message** — `find`
prints newline-separated and `xargs -0` wants NUL, so the whole listing arrives
as one filename. `tools/rlxfw-kbuild.sh` line 262 is the owner and carries
`-print0` and `LC_ALL=C sort -z`; run that way the answer is `5abefd82` and the
image stands. Recorded because an eight-hex-digit wrong answer reads exactly
like a measurement.

**② `up2` is `r59` plus one binary nothing executes, and NOT ONE INSTRUCTION
MOVED.** 量, `r59.System.map` against `up2.System.map` over the 13,172 symbol
names unique in both: **12,271 at the same address, one code symbol moved, and
it is `__initramfs_end`** (`80369e00` → `80371200`, `+0x7400` = 29,696 B =
uprobe plus its cpio header). 900 `b`/`B`/`d` symbols moved by the same
`0x7400`. The mark sets are identical (32 rows each) and the built `.config`
files differ by **one line, which is the timestamp comment**. § 5 turns that
into a prediction no previous seating could make.

⚠️ The naive instrument for this — `join` on the symbol name — reports 3,873
differing addresses, because a `System.map` holds 119 repeated names and the
join pairs the wrong rows. The population above is the names unique **in both
files**, which a pairing cannot get wrong.

**③ 34 of the 75 rows disagree between the device arm and the qemu arm**, so
every column-② cell here is derived from **column ①**, never from
`qemu/2026-09-15/uprobe-user.txt`. Six trap instructions read `SIGTRAP` under
qemu and are predicted `SIGILL` here; four branch-likely, three `SPECIAL2`,
four `SPECIAL3`, five `COP1`, four `cache` and eight Lexra ASE rows all point
the other way. `notes/userspace-probe.md` § 7 said the qemu arm measures the
instrument and nothing else; **34 of 75 is that sentence with a number on it.**

**④ `cells4.S` contains no `jalx`, checked by the bytes rather than by the
table's word.** `docs/emulation-surface.md` § 1 ② forbids running one — MIPS16
is implemented on this part, so it would retire into MIPS16 at an address a
26-bit field picks, which is worse than a panic and spends the power cycle.
量: the two hits for `jalx`/`mtlxc0` in that file are both **comments**, and
`:1226` is the one that says why `mtlxc0` has no payload. **The full-range run
is therefore safe**, and that is a measurement and not a reading of § 3's
`none` cell.

**⑤ There was no uploadable image until 20:18 today.** `up2.manifest` and the
handover both name `up2.vmlinux.elf`, which is not what goes over TFTP. The
`cells/up2/top/**/nfjrom` files are the vendor's own, dated 2026-08-23 and
identical in every cell directory. `S3` — `tools/rtkimage.py build` — had never
been run for this image. It has now; its `vmlinux_img` is **3,609,088 B**,
which independently reproduces the figure `config/rlxfw-initramfs.tsv` records
for `up1` (the two images differ in 4 bytes).

---

## 3. The order, and it is forced rather than chosen

1. **`DW` is a loader verb**, so `FW-70`'s cell can only run at the loader
   prompt, before the boot.
2. **`looprun` owns the middle.** It is used rather than hand-typed cells
   because its `S5b` reads the burn flag out of the word at `0x8040D4A0`
   instead of trusting the rescue's echo (`C-6` measured those two
   disagreeing), and its `S6b` reads back the head of `0x80500000` and compares
   it against **the file it just sent, derived rather than typed** — `S4`'s
   reset re-stages that address from flash, so the alternative to *my image is
   there* is a real vendor image that would boot.
3. **`uprobe` before the six `cat`s.** `uprobe` is the deliverable and the
   `cat`s are free riders; if anything goes wrong the expensive thing is
   already in hand. It reads no `/proc`, so it cannot disturb `FW-64`'s counter
   sequence — which is the only ordering constraint the riders impose.

---

## 4. The guards

**① Nothing on this card can reset the board.** No `RB` cell, no `reboot`, no
`biteraw`, no `/dev/watchdog` open. The only reset in the block is `looprun`'s
own `S4`, which is a `J BFC00000` it aborts on if the watchdog discriminator
does not come back.

**② 🔴 `DW B800200C 1` reads ONE word and the count is part of the safety
argument.** `SPEC.md` `FW-70`: on this UART `+0x00` is RBR and reading it pops
a byte off the receive FIFO; `+0x08` is IIR and reading it clears the pending
interrupt id. Only `+0x0C` (LCR) and `+0x14` (LSR) are free. **A `DW
B8002000 8` would corrupt the console this seating is being captured over.**

**③ Every capture carries a terminator.** `console-capture` refuses one that
does not, and `--idle` is never shorter than a payload's own `sleep` because
no cell on this card sleeps.

**④ The nonce is three characters, and that is load-bearing.** The banner is
`*** rlxuprobe PU <BUILD_ID> <argv[1]> ***`, so a four-character nonce moves
every byte prediction in § 6 by one. `d73` and `r73`.

**⑤ `looprun` aborts** on: no `Reboot Result from Watchdog Timeout!` at `S4`;
burn flag word not `00000000` at `S5b`; no lladdr for `10.1.1.1` at `S5c`;
head mismatch at `S6b`. No later stage runs after an abort.

---

## 5. The boot, and one row of it is an experiment nobody asked for

`up2` differs from `r59` by a 29,184-byte binary in the initramfs that nothing
executes, and by the eight hex characters of `RECIPE_ID`. Every mark is a
fixed-width field.

| field | predicted | why |
|---|---|---|
| boot capture | **1,637 bytes** | all seventeen of `bench/2026-09-10/*-boot.log` are 1,637 and every `=` mark is exactly 8 hex |
| `RLXFW-ID0` | **`5ABEFD82`** | the id the build computed, compared by `S8`, typed by nobody |
| `RLXFW-G3` | `0000003C` **or** `0000007C` | `FW-40`, bit 6 is the LED the vendor's `rtl_gpio_timer` blinks. Seating 20 read 3 and 14 of the two. **Both are a pass; predicting one would manufacture a red** |
| `RLXFW-B10` | present, and **after** `RLXFW-TA8` | the ordering that puts the clockevent before `init_post()` |
| `RLXFW-TA6` | **`0000000B`** | see below |

🔴 **`RLXFW-TA6` is the row worth having.** It is `IRQ-13`'s lost-interrupt
count. Seating 18 read 8 where seating 17 read 11, and the only candidate
offered — that `vmlinux` grew and moved the vendor NIC init's I-cache
alignment — **was refuted by a third image whose size changed and whose `TA6`
did not**. This is the fourth image, and it is the cleanest test the project
has had: the image grew by **29,696 bytes** and **not one instruction moved**
(§ 2 ②), while BSS and data shifted by `0x7400`.

* `TA6 = 0000000B` — agrees with `r59`. Consistent with code alignment being
  the mechanism, and with there being no mechanism at all. **Does not
  discriminate**, and saying so here is the point.
* `TA6 ≠ 0000000B` — 🔴 **the mechanism cannot be the I-cache alignment of
  code**, because no instruction moved. What is left is the `0x7400` shift of
  BSS and data, or something that is not alignment.

Either way this row costs nothing and is registered before power.

---

## 6. Column ②, and the whole prediction is two sentences and a citation

### 6.1 The 44 payload rows the census covers

**Pre-registered in `docs/emulation-surface.md` § 3, and cited by id rather
than restated here.** That file was committed on 2026-09-15 in the
seventy-second segment, before this instrument had run anywhere but an
emulator; copying its 39 cells into this card would replace a dated
pre-registration with a transcription. If a cell here and a cell there ever
disagreed, the older file is the prediction.

The four rows that matter, by that file's own § 4:

| row | predicted ② | why it matters |
|---|---|---|
| `sync` | 🟢 **no signal** — `do_ri` reaches `simulate_sync`, SPECIAL funct `0x0F` | **the only row on which the emulation surface is visible as a trap/no-trap difference.** A `SIGILL` here refutes § 1.4's whole reading, and that is the single most informative outcome this seating can produce |
| `ll` | no signal — `CpU` CE 0, `do_cpu` cpid 0, `simulate_llsc` matches `0x30` | emulated and **invisible**: it already retires on the die, so both columns read *no signal* |
| `sc` | no signal — same path, opcode `0x38` | same, invisible |
| `cache`, `mflxc0` | **SIGILL** | they retire on the die only because column ① was measured at `CU0 = 1`. **A privilege artefact, not emulation** |

### 6.2 The 31 payload rows outside the census, and they are ONE rule

`cells4.S` emits 75 rows; 44 of them are census rows. The other 31 are
`add`, `lw`, `sw`, `mult`, `mult_hi`, `beq`, `jr`, `special0e`, `madd_hi`,
`rotr`, `synci`, `cfc3`, `ltw`, `madh`, `madl`, `mazh`, `mazl`, `msbh`,
`msbl`, `mszh`, `mszl`, `udi0i`, `udi1i`, `udi2i`, `udi3i`, `udi0`, `udi1`,
`udi2`, `udi3`, `udi4`, `udi5`.

**Not one of them requires `CU0`, and not one of them is on the emulation
surface.** So column ② is column ① by three arms:

* **R-a** ① retired (`RIGHT`, `RAN` or `WRONG`) ⇒ ② the same verdict and the
  same value, no signal.
* **R-b** ① `ExcCode 10` (RI) ⇒ ② `SIGILL` / `SI_KERNEL`.
* **R-c** ① `ExcCode 11` (CpU, CE ≠ 0) ⇒ ② `SIGILL` / `SI_KERNEL`.

🟢 **The rule's exceptions are exactly the four rows § 6.1 already handles** —
`cache`, `mflxc0`, `ll`, `sc` are the only encodings in the payload that need
`CU0` or that an emulator answers, and all four are census rows with their own
frozen cells. That is why one rule covers 31 rows without a special case.

**Refutation: any one of the 31 whose ② differs from its ①.** Thirty-one
independent chances, and a rule cannot be repaired row by row after the fact
the way a 31-row table could.

### 6.3 The headline, as one line

Applying § 6.1 and § 6.2 to the device's own column ① — `RAN 16, RIGHT 16,
TRAPS 42, WRONG 1` — `sync` leaves `TRAPS` for no-signal and the five
privileged rows (`cache`×4, `mflxc0`) leave no-signal for `TRAPS`:

```
verdict (user arm): 75 row(s), RAN 12, RIGHT 16, TRAPS 46, WRONG 1
```

**That is the prediction.** `tools/isapay.py verdict --arm user --elf` prints
this line; a different one is a result either way.

### 6.4 The header and the controls, which are the instrument judging itself

| field | predicted | what a miss means |
|---|---|---|
| `rows` | `0000004b` | 75 |
| `first` / `last` | `00000000` / `0000004a` | the full range was run; a mistyped range shows here rather than silently |
| `install_rc` | `00000000` | `sigaction` took; `C1a` |
| `c1a_raise` | `00000001` | a `raise(SIGILL)` reached the handler at all |
| `c1b_special0e_n` | `>= 00000001` | a real reserved encoding reached it |
| `scratch_bad` | `00000000` | the handler did not corrupt the scratch area |
| `scratch_at`, `uc_pc_lo`, `scratch_b`, `max_sig` | `00445d88`, `00000024`, `00000030`, `00000008` | a static binary: these are the same addresses qemu saw |
| terminator | `rlxuprobe: end` | the run completed rather than being killed by `alarm(30)` |
| **C2** | every trapping row's faulting PC equals that row's own `_w` symbol | run with `--elf`; **without it the tool prints `C2 NOT RUN` and exits 1, and an absent check is not a passed check** |

**Byte predictions.** The device's output is CRLF exactly as qemu's is, every
field is fixed width and the nonce is the same length, so:

* `C2-UP` payload — **7,195 bytes, 91 lines, 75 `PU` rows**
* `C2-UPR` payload — **794 bytes, 20 lines, 4 `PU` rows**

`C2-UPR` is the range arm and it is a control, not a reading: it proves on the
die that `first`/`last` do what the header says, with a different nonce so the
two captures cannot be confused for each other.

---

## 7. Rider — `FW-70` ①, and its scope is narrower than the row implies

`SPEC.md` `FW-70` has `LCR` at **讀×2, 量×0**: the vendor Linux chain
(`console=ttyS0,38400`, no `CSTOPB` producer anywhere in the serial tree) and
`rlxdefs.h:195` (loader stage 1 writes `0x03000000` to `0xB800200C`) both say
`0x03`. 量 is zero because no `DW` in all of `bench/` has ever landed in
`0xB8002000`–`0xB80020FF`.

**Cell:** `DW B800200C 1` at the loader prompt.
**Predicted:** top byte `03` — 8N1, 10 bit/char, which is the denominator the
whole `FW-70` throughput analysis rests on.
**Refuted by:** `07` (8N2) or `0B` (parity), either of which moves that
denominator and every percentage derived from it.

⚠️ **What this cell does NOT measure.** It reads the **loader's** LCR, so it
converts source ② to 量. Linux's own LCR stays 讀: this image has no `devmem`
and `FW-46` records that its busybox has no applet that can read a register, so
there is no route to the Linux-era value from a shell. The row moves to
`讀×2, 量×1` and the scope limit goes in with it.

---

## 8. Rider — `FW-64`, and the boot has to be quiet for it

`FW-64` (量 2026-09-15, seventy-first segment): one `cat` is two `read_proc`
calls, and when a printed counter crosses a power of ten the second call
renders one byte more, `proc_file_read` returns `n = 1 > 0`, and `cat` issues a
**third** `read()`. From boot the printed `n_state_chk` sequence is 1, 3, 5, 7,
9 — so the step lands on **the fifth `cat` of a quiet boot**, and after it the
sequence is even and cannot reach a power of ten again.

| cell | `n_state_chk` printed |
|---|---|
| `C2-G1` | 1 |
| `C2-G2` | 3 |
| `C2-G3` | 5 |
| `C2-G4` | 7 |
| `C2-G5` | **9** |
| `C2-G6` | **12** |

and **only `C2-G5`'s dump may carry the extra blank line.**

**Refuted by** a `+3` anywhere `chk+1` is not a power of ten, or by `C2-G6`
reading 11.

⚠️ **Precondition, stated because it is the whole rider:** nothing may read
`/proc/rtl819x-gpio` between the boot and `C2-G1`. `uprobe` does not, and no
other cell on this card touches `/proc`.

---

## 9. What this block does NOT claim

1. **Nothing about the vendor's shipped kernel.** Column ② runs under rlxfw's
   own image; the equivalence that licenses the generalisation is `R1C-1`'s,
   kept true by `tools/emueq.py`, and if that goes red every cell here
   inherits the doubt.
2. **No cost.** Every *how much does the emulation cost* question is `4b`,
   which needs a clock. Nothing here is timed.
3. **No completeness over the emulation surface.** `docs/emulation-surface.md`
   § 6: five of the eight known emulated instructions — the unaligned `lh`,
   `lhu`, `lw`, `sh`, `sw` — have no census row and **cannot** have one under
   `docs/isa-prior-art.md` § 0's admission rule. **This table can show 3 of 8.**
4. **No flash.** Zero flash-write commands, zero `FLR`, zero `map`. The
   bracket stays at 1,024 of 4,194,304 = 0.0244 % and `FLS-26`'s ledger does
   not move.
5. **`mtlxc0` and `jalx` are not measured**, deliberately, and § 2 ④ is the
   evidence that they are not measured by accident either.

---

## 10. The cells

`H` = host, `L` = at the loader prompt, `S` = at the Linux shell.

| # | where | command |
|---|---|---|
| `C1-esc` | H | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-15/C1-esc --esc 45 --esc-period 0.002 --seconds 75` — **the operator powers the board on inside the 45 s ESC window** |
| `C1-LCR` | L | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-15/C1-LCR --send 'DW B800200C 1' --idle 2 --seconds 6` |
| `LOOP` | H | `looprun.py --mode bench --cell up2 --skip S2,S3 --image <nfjrom> --image-sha256 3ff8b3c9… --cell-top <cells/up2/top> --label up2-20260915 --work <bench-only/up2-work-20260915> --recipe-override 5abefd82 --out-dir bench/2026-09-15` |
| `C2-UP` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-15/C2-UP --send '/bin/uprobe d73' --seconds 45` |
| `C2-UPR` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-15/C2-UPR --send '/bin/uprobe r73 0 3' --seconds 20` |
| `C2-G1`…`C2-G6` | S | `console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-15/C2-G<n> --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 15`, six times |

### 10.2 🔴 Three cells carried seating 20's own defect and it was caught here, before power

The first draft gave `C1-esc` `--idle 4` and `C2-UP` `--idle 6`. 讀
`console-capture.py:786` — `--idle N` stops the capture after N seconds **with
no bytes**, counted from the start, which the file's own § at `:92` states as
*"use `--seconds`, not `--idle`"* for exactly this shape.

* **`C1-esc` would have ended four seconds in, with the board still off** and
  the operator still reaching for the switch. 54 bytes, a clean `stop_reason`,
  and `check-predictions` scores existence and mtime rather than content — so
  the block would have reported a pass with no loader prompt caught.
* **`C2-UP` would have cut the capture 24 seconds before `alarm(30)` could
  fire.** A hung row is pure silence, so `--idle 6` ends in it and the one
  thing the alarm exists to tell us — *did a row never return* — is exactly
  what would have been lost. `FW-51` and the 41.931 s bite silence are the
  same trap one instrument earlier.

`C1-LCR` and the six `C2-G*` keep `--idle` because their payload answers
immediately and `--seconds` backs them; `C2-UP` and `C2-UPR` are `--seconds`
only, and the cost of that decision is ~55 s of deliberate waiting.

⚠️ `--until 'rlxuprobe: end'` was considered and **declined**: it would save
40 s and add a failure mode (a pattern that silently does not match) to the one
cell the block cannot lose.

### 10.1 The numbers this card states, and where each is re-derived FROM

```cardnum
up2-vmlinux-bytes	4125078	size /home/key/fwre-work/rebuild/r3-4/out/up2.vmlinux.elf
up2-vmlinux-sha16	9e2bb2219977692d	sha256-16 /home/key/fwre-work/rebuild/r3-4/out/up2.vmlinux.elf
nfjrom-bytes	1057792	size /home/key/fwre-work/rebuild/bench-only/up2-work-20260915/up2-20260915/kroot/rtkload/nfjrom
nfjrom-sha16	3ff8b3c94029b8ea	sha256-16 /home/key/fwre-work/rebuild/bench-only/up2-work-20260915/up2-20260915/kroot/rtkload/nfjrom
uprobe-bytes	29184	size /home/key/fwre-work/rebuild/rlxfw-user/isaprobe/build/uprobe
uprobe-sha16	f3bf56ee6d97712e	sha256-16 /home/key/fwre-work/rebuild/rlxfw-user/isaprobe/build/uprobe
uprobe-installed-sha16	f3bf56ee6d97712e	sha256-16 build/rlxfw-user/isaprobe/uprobe
r59-boot-bytes	1637	size bench/2026-09-10/C1-boot.log
r59-ta6	1	count bench/2026-09-10/C1-boot.log ^RLXFW-TA6=0000000B
r59-id0	1	count bench/2026-09-10/C1-boot.log ^RLXFW-ID0=692A2801
qemu-e2e-bytes	7195	size qemu/2026-09-15/uprobe-user.txt
qemu-e2e-lines	91	lines qemu/2026-09-15/uprobe-user.txt
qemu-e2e-rows	75	count qemu/2026-09-15/uprobe-user.txt ^PU [0-9a-f]
qemu-rng-bytes	794	size qemu/2026-09-15/uprobe-user-range.txt
qemu-rng-lines	20	lines qemu/2026-09-15/uprobe-user-range.txt
```

⚠️ `cardcheck numbers` reads a fenced declaration and cannot see a number
written in prose. The two figures in § 2 ② — 12,271 and `+0x7400` — and the
34-of-75 in § 2 ③ are **prose**, re-derived at the desk today and named here as
unchecked by that tool, which is the shape seating 20's `cnr_as_spec` defect
took when nobody said it out loud.

---

## 11. The fence

```cells
bench/2026-09-15/C1-esc
bench/2026-09-15/C1-LCR
bench/2026-09-15/up2-rz
bench/2026-09-15/up2-ab2
bench/2026-09-15/up2-2a
bench/2026-09-15/up2-boot
bench/2026-09-15/C2-UP
bench/2026-09-15/C2-UPR
bench/2026-09-15/C2-G1
bench/2026-09-15/C2-G2
bench/2026-09-15/C2-G3
bench/2026-09-15/C2-G4
bench/2026-09-15/C2-G5
bench/2026-09-15/C2-G6
```

**14 cells**, in the order they are typed. `bench/2026-09-15/up2-rescue.json`
is the one artefact of this block outside the fence: it is `console-dump.py
rescue`'s report and not a `console-capture` triple, so it has no `.log` /
`.timing` / `.meta.json` for `check-predictions` to score.

## 12. The drop order, if the window closes

`C2-G6` → `C2-G5` … → `C2-G1` (the whole `FW-64` rider, which is free and
repeatable on any future boot) → `C2-UPR` → `C1-LCR`. **`C2-UP` is never
dropped**; it is the block.
