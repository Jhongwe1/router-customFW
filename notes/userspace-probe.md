# `uprobe` — the first userspace binary this project has compiled, and what it is written against

**`R1-pub-4a`'s instrument.** Opened 2026-09-15, seventy-second segment, at the
desk, board unpowered.

`docs/emulation-surface.md` owns the *table*: 45 rows, column ① measured bare
metal by `probe4`, column ② a pre-registered prediction of what the same
encoding does from Linux user mode. **This file owns the thing that will
measure column ②**, and nothing else: `config/rlxfw-user/isaprobe/uprobe.c`,
its build, the ABI it is written against, its controls and its gates.

Cited **by id, never by `FILE:NNN`**, for `docs/emulation-surface.md`'s reason:
`CITE-2` measured eleven of thirteen pinned line numbers already wrong before
a board was powered.

---

## § 0. What this claims, and the four things it does not

**Claims:** that a statically linked big-endian MIPS-I ELF built by this
project runs the same 75 encodings `probe4` runs, records a signal, a faulting
PC and four result words per row, and refuses rather than reports when its own
controls do not hold.

**Does not claim ①** that anything has run on the silicon. 🔴 As of this
segment **nothing in this file has been executed on the device**. The only
execution is `qemu-mips-static`, whose scope is § 7, and qemu's kernel is the
host's.

**Does not claim ②** a verdict. Exactly like `probe4`, the payload records and
the desk decides — `tools/isapay.py verdict --arm user`. A payload that
compares in place reports a boolean and throws the value away, which is the
row `R1-pub-1`'s DoD calls *the one that matters and the easiest to lose*.

**Does not claim ③** that `R7`'s toolchain question is settled. § 1 applies
`R7`'s own written criterion to three candidates and reports the numbers; the
gate decision is `R7`'s and this file does not take it. What this segment can
say is narrower and is said in § 1: the criterion discriminates, and it
discriminates uniquely.

**Does not claim ④** a cost. Every *how long does the emulation take* question
is `4b`.

---

## § 1. The toolchain, decided by the criterion that was already written

`SPEC.md`'s `TC-05` residual says the userspace toolchain is chosen by the
same criterion as the kernel's: **passes `tools/hazlint` with 0 violations**.
`notes/vendor-toolchains.md` § 5 records that hazlint had **never been run
over any of these `libc.a` files**. 量 2026-09-15, it has now.

Three candidates, each building the same source `-Os -static`, each scanned
twice — once as the linked binary, once as the whole `libc.a` relinked with
`ld -r` so nothing is read across a member seam:

| toolchain | linked binary | whole `libc.a` | load followed by `nop`, in libc |
|---|---|---|---|
| **`rsdk-1.3.6-4181`** | **0 violations** | **0 over 19,096 loads** | **4,051 (21.21 %)** |
| `rsdk-1.3.6-5281` | 140 violations | **4,574** over 19,141 | **1 (0.01 %)** |
| `rsdk-1.5.5-5281` | 128 violations | **3,741** over 14,491 | **0 (0.00 %)** |

**The criterion discriminates, and it selects `rsdk-1.3.6-4181` uniquely.**
Not by a margin — by zero against four and a half thousand.

🔴 **And the 0.01 % is the whole explanation.** `notes/vendor-toolchains.md`
§ 5 predicted that a uClibc built at `-march=5281` is built for a core *with*
a load interlock and would carry no load-delay padding. 量: **one**
nop-after-load in 19,141. Not *less padding* — none. A userspace built with
either 5281 toolchain would put thousands of load-use hazards onto a core
where the load delay slot is architecturally exposed, and `F46` is the
measurement that says this one is.

⚠️ **Two limits on that zero, stated rather than left to be found.**
`hazlint --isa` is rc=1 for all three, so a reading of the criterion as
*"`--isa` zero as well"* selects nothing — and the kernel, already built with
the same toolchain under the same criterion, carries `movz`/`movn` too. What
`--isa` contributes here is content rather than a verdict: 1.3.6-4181 and
-5281 carry only `movz`/`movn`, encodings this project has measured the die
executing; **1.5.5 additionally carries `lwl`/`lwr`/`swl`**, a class the
others do not bring in.

🔴 **The 1.5.5 disqualification is NOT the unaligned group, and an earlier
draft of this section said it was.** That draft reasoned *"RLX4181 does not
implement `lwl`/`lwr`, so 1.5.5's `memcpy` would trap"* — and this project's
own `probe4` reading refutes it: `docs/emulation-surface.md` rows 4, 5, 9 and
10 read **`lwl` retire gpr `A5F00D44`**, **`lwr` retire `1122335A`**, **`swl`
retire m0 `A55A5A0F`**, **`swr` retire m0 `5A0FF20D`**. This die executes the
unaligned group. 1.5.5 is disqualified by 3,741 load-use violations, which is
a different and much larger reason.

---

## § 2. 🔴 The kernel and the C library disagree about `struct sigcontext`, and the harness is written against the kernel

讀, both on 2026-09-15.

`arch/rlx/include/asm/sigcontext.h` — the whole struct, and it is a truncated
one:

```c
struct sigcontext {
	unsigned int		sc_regmask;	/* Unused */
	unsigned int		sc_status;	/* Unused */
	unsigned long long	sc_pc;
	unsigned long long	sc_regs[32];
	unsigned long long	sc_mdhi;
	unsigned long long	sc_mdlo;
};
```

`sizeof` **288**. The toolchain's own `<bits/sigcontext.h>` carries the stock
MIPS struct — the same prefix, then `sc_fpregs[32]`, `sc_ownedfp`,
`sc_fpc_csr`, `sc_fpc_eir`, `sc_used_math`, `sc_dsp`, `sc_mdhi`, `sc_mdlo`,
`sc_hi1`…`sc_lo3` — `sizeof` **592**. The port was done by deleting code, not
by conditionalising it: a grep for `RLX|LEXRA|CONFIG_CPU_HAS_|FPU` across
`signal.c`, `sigcontext.h` and `ucontext.h` returns nothing.

**They agree on every offset this harness reads**, and the arithmetic is
worth writing out because the agreement is not obvious:

| | kernel `arch/rlx` | toolchain header | |
|---|---|---|---|
| `uc_flags` / `uc_link` / `uc_stack` | 0 / 4 / 8..19 | same | `stack_t` is `{ss_sp, ss_size, ss_flags}` in both |
| pad to 8 for `sigcontext` | 20..23 | same | |
| **`uc_mcontext`** | **24** | **24** | ✅ |
| **`sc_pc`** | **32**, 64-bit slot, big-endian ⇒ meaningful word at **36** | **32** | ✅ |
| **`sc_regs[i]`** | **40 + 8i**, word at **44 + 8i** | same | ✅ |
| `sizeof(sigcontext)` | **288** | **592** | 🔴 |
| `uc_sigmask` | **312** | **616** | 🔴 |
| `sizeof(ucontext_t)` | **328** | ~**744** | 🔴 |

🔴 **And the second half of that table is a live hazard, not trivia.** The
kernel allocates the whole `rt_sigframe` — 推 **480 bytes**, from
`signal.c`'s `struct rt_sigframe` — and writes `uc_sigmask` at `uc + 312`.
**Assigning to `uc->uc_sigmask` through the libc header writes 128 bytes
starting 136 bytes past the end of the frame the kernel allocated.** Nothing
in `uprobe.c` touches a ucontext field below `sc_regs`, and the three offsets
it does use are asserted against the libc header at **compile time**, so a
toolchain whose header stops agreeing fails the build rather than producing a
measurement.

⚠️ **Neither arm can validate the disagreeing half**, and that is by design:
qemu builds the stock frame too, so both emulator and device exercise only
the agreeing prefix. The half that differs is the half the harness never
touches.

---

## § 3. The handler advances `sc_pc`, and `+4` is uniform by measurement

讀 `arch/rlx/kernel/traps.c`, 2026-09-15. Three paths deliver a signal for an
encoding the core will not execute, and all three leave `sc_pc` on the
**faulting instruction**:

| path | what it does to EPC |
|---|---|
| `do_ri`, nothing claims the opcode | advances via `compute_return_epc`, then `regs->cp0_epc = old_epc;` — the source's own comment is *"Undo skip-over"* — immediately before `force_sig` |
| `do_cpu`, `cpid == 0`, `simulate_llsc` no match | the same advance and the same undo |
| `do_cpu`, `cpid != 0` | 🔴 **`compute_return_epc` is inside the `if (cpid == 0)` block and never runs**, so the EPC was never advanced and there is nothing to undo |

🔴 **The third row is not the obvious reading.** A plausible model of `do_cpu`
is that its `cpid != 0` arm leaves the EPC advanced, which would make `+4`
skip an extra instruction on every COP1/2/3 row — nine rows of
`docs/emulation-surface.md` § 3. It does not, and the reason is where the
call sits rather than what it does.

**So the handler adds 4 and that is correct on every path.** `sys_rt_sigreturn`
restores it — `err |= __get_user(regs->cp0_epc, &sc->sc_pc);` — with no
alignment check, no `access_ok` on the PC and no `BD` flag anywhere in the
frame.

**Why advance rather than `siglongjmp`.** A `siglongjmp` unwinds, so the cell
never reaches its own epilogue and the four output words are whatever they
were before the fault. Advancing lets the cell finish and write
`out_gpr`/`out_m0`/`out_m1`/`out_aux`, which is what makes the three-way
verdict — *traps / ran-and-right / ran-and-**wrong*** — available on this arm
as well as on `probe4`'s. `tools/isa-payload.tsv`'s `ll` row is the one that
decides it: `ll` and `lwc0` are the same encoding and only the VALUE
separates them.

**`siglongjmp` is kept as an escape hatch, not as the mechanism.** A probed
word that transfers control can land somewhere where `+4` is also bad, and
the process then takes a signal per word forever — a hang, not a reading.
After `UP_MAX_SIG` signals in one row the handler jumps out. `alarm(30)`
bounds the other failure: a probed word that loops with **no** signal at all,
where no counter moves. Both exist because on this project a power cycle is
the most expensive unit there is.

⚠️ **The delay-slot case is avoided rather than handled.** If a probed word
sat in a branch delay slot, `Cause.BD` would be set, `old_epc` would be the
BRANCH's address, and `+4` would land back on the delay slot forever.
`cells4.S` never puts a probed word in one — `tools/rlxprobe/exc.S` says the
same thing for the bare-metal arm — and **control C2 is what makes that an
observation rather than an assumption**: every trapping row's reported PC
must equal that row's own `_w` symbol, and a delay-slot fault would report
the branch instead.

**Two more ABI facts the harness depends on**, both 讀:

- **`si_addr` is useless here.** `do_ri` delivers with `force_sig`, which is
  `force_sig_info(sig, SEND_SIG_PRIV, p)`, and the `SEND_SIG_PRIV` arm fills
  `si_code = SI_KERNEL` with `si_pid = 0` — the same union word `si_addr`
  reads. A design that identifies a row by `si_addr` gets **0** for every row.
  `uc_mcontext.sc_pc` is the only source for the faulting PC, and the qemu run
  confirms it reads a real address where `si_addr` would have read zero.
- **`SA_RESTORER` must not be set.** `install_sigtramp` writes two words —
  `addiu $v0, $zero, 4193` then `syscall` — into the frame on the user stack
  and points `$ra` at them. `SA_RESTORER` is *defined* in
  `arch/rlx/include/asm/signal.h` and **referenced nowhere else in the whole
  of `arch/rlx`**, and `struct k_sigaction` has no restorer member at all.

🔴 **And MIPS numbers its signals differently from every other Linux port,
exactly where this instrument reads.** 讀
`arch/rlx/include/asm/signal.h`: `SIGEMT` takes **7**, so `SIGBUS` is **10**
and `SIGSEGV` is **11**, where the generic ABI has `SIGBUS` 7. A decoder
table copied from `signal(7)` prints a genuine `SIGBUS` as `SIGEMT` and
nothing looks wrong. `tools/isapay.py`'s T21 pins it.

---

## § 4. The controls, and the one that matters most

| | what it asserts | why it exists |
|---|---|---|
| **C1a** | `raise(SIGILL)` reaches the handler | 🔴 A harness whose `sigaction` failed reports *no signal* for all 75 rows — and *no signal* is exactly the reading that means THE SILICON IMPLEMENTS IT. `docs/emulation-surface.md` § 7.3 names that backwards reading for `ll`/`sc`; this is the same trap one level down, at the instrument. `raise` is used rather than an illegal encoding because it borrows nothing from the thing under test |
| **C1b** | the reserved encoding `special0e` traps | C1a proves the signal path; this proves an actual illegal instruction reaches it |
| **C2** | every trapping row's `sc_pc` equals that row's own `rlx_p4_<name>_w` | the delay-slot case, a mis-parse, and a `+4` that went one too far. 🔴 **It lives at the desk**, where the address is resolved out of the artefact's own symbol table — compiling 75 addresses in would be a second copy of something the ELF already carries. **A run with no `--elf` reports `C2 NOT RUN` as a FINDING**: an absent check is not a passing check |
| **C3/C4** | `baseline` rows RIGHT, `reserved` rows not RIGHT | `isapay.py check_controls`, reused unchanged — it is arm-free and holds identically here |
| **end** | the capture carries `rlxuprobe: end` | *it stopped* and *it ended* are different observations |
| `scratch_bad` | no cell altered its own inputs | `probe4.c`'s, carried across |

---

## § 5. The six gates, and the one this artefact does not meet as written

| | gate | 量 |
|---|---|---|
| **G0** | `isapay.py emit --check` | the three generated files match the table |
| **G1** | zero `break` in code this project wrote | `uprobe.o` 0, `cells4.o` 0 |
| **G1b** | the linked ELF: **exactly two `break`, both inside `__GI_abort`** | `linked break=2`, `__GI_abort=[4209680,+412)`, none outside |
| **G2** | `hazlint` over the linked ELF | **0 violations in 938 loads** |
| **G3** | one `_w` symbol per row | 75 / 75 |
| **G4** | the link says exactly one known thing | `known=1  unexpected=0` |

🔴 **G1b is a narrowing of `R1C-1-b` and the gate says so rather than being
quietly relaxed.** `R1C-1-b` requires the linked binary to hold **zero**
`break`. 量: it holds two, both `break 0xff` in `__GI_abort`, and `abort.os`
is pulled into the link by `__uClibc_main.os` — the C runtime's own startup.
The only route to zero is `-nostdlib` with a hand-written `_start`,
`rt_sigaction`, `sigsetjmp` and `siglongjmp`.

**That trade was declined and the reason is written down**: a hand-written
MIPS `sigsetjmp` that saves the wrong callee-saved register is SILENT, and
this whole instrument is a signal handler. The risk of a quiet bug in
hand-marshalled signal plumbing is larger by far than the risk of two `break`s
in a function nothing calls. So the gate becomes **bounded** rather than
waived — the same shape as G4 — and it goes red if a third appears or if one
moves out of `__GI_abort`.

⚠️ For scale: the three-toolchain measurement found **four** `break`s in every
`printf`-using test binary — two in `__GI_fwrite_unlocked`'s divide-by-zero
check and two in abort. This harness writes with `write(2)` and has none of
the fwrite pair. The `write(2)` choice was made for a different reason (§ 6)
and this is a second, measured one.

🔴 **Every count here is taken BY OPCODE**, never from objdump's mnemonic.
量 2026-09-15: the rsdk binutils print `0231280b 	0x231280b` for `movn` —
the raw word. ⚠️ **That is the decoder being right, not wrong**, and
`docs/isa-payload.md` already holds the principle: a decoder told MIPS-I
correctly declines a MIPS-IV encoding, and the rsdk driver's default is
MIPS-I. The trap is one level up — **a census that decodes at one ISA
level cannot see encodings from another**, so grepping a disassembly for
a mnemonic is a lower bound wearing a total's clothes.
`tools/elfops.py` decodes; `nm` supplies only the symbol extent, which is
the one thing it does not lie about here.

---

## § 6. The build stages to ext4, and that is a refusal rather than a preference

🔴 量 2026-09-15, three arms, same compiler, same source bytes, only the
filesystem differing:

| arm | rc |
|---|---|
| source on ext4 | **0** |
| byte-identical source on DrvFs (`/mnt/c`) | **1** — `cc1: <path>: Value too large for defined data type` |
| source on ext4, **only an `-I` pointing at DrvFs** | **1**, the same message |

Cause identified: the rsdk driver and its `cc1` are `ELF 32-bit LSB
executable, Intel 80386`. A 32-bit `stat()` cannot represent a DrvFs inode
number — 量, ext4 `2,276,528` against DrvFs
`12,384,898,976,057,211` — so every path under `/mnt/c` returns `EOVERFLOW`.

**The third arm is the sharp one**: the build may not so much as NAME a path
inside this repository. Four files are staged onto ext4 under `$FWRE_WORK`,
and the staged copies are **hashed against the originals before anything is
compiled** — `tools/desk-sweep.py` verifies its copy for the same reason: the
conclusion is about the repository, so a silent divergence between source and
copy would be a measurement of the wrong tree.

🔴 **Two of those three arms are a RE-DISCOVERY and this section's first
draft claimed all three as new.** `SPEC.md` `TC-56` holds the same result,
量 2026-09-14 -- one segment earlier -- with the same cause, the same
error message, the same inode argument, and the same sentence about it
being the third face of `CLAUDE.md`'s rule. It was found here by
re-measuring rather than by `git grep`, which is the audit method that
actually catches things, and the draft went in before the sweep.

**What is new is the third arm**: `TC-56` varies where the SOURCE lives.
This one holds the source on ext4 and moves only an `-I`, and it fails the
same way -- so the constraint is not *compile from ext4*, it is **the
build may not name a repository path at all**, which is what forces the
staging design rather than a simple `cd`.

It is a **third, independent** reason for `CLAUDE.md`'s *binaries and vendor
source trees never live under `/mnt/c`*, and unlike the mode-bit and
case-folding reasons it is a hard failure rather than a silent one --
`TC-56` says that too.

**Where the product goes, and why it is not under `config/`.** `RECIPE_ID` is
`find config -type f` with **no exclusions and no consultation of
`.gitignore`** — a filesystem walk. An object file left under `config/`
therefore moves the id the board prints, silently. The source lives in
`config/rlxfw-user/isaprobe/` so that `RECIPE_ID` **does** cover it (which is
the property that makes `RLXFW-ID0` mean *this image, including its
userspace*); the product goes to `build/`, which `.gitignore` already covers
and `find config` cannot reach.

⚠️ **`-mno-abicalls -fno-pic` on `cells4.S` is INERT and an earlier draft of
the Makefile claimed it was necessary.** 量, two arms: with and without, the
object is byte-identical, the object flags are `0x1001` both ways, the linked
flags are `0x1005` both ways, and the same link warning appears both ways.
The driver's `-mabicalls` reaches `cc1`, not `as`, and a hand-written `.S`
with no `.abicalls` directive is non-PIC whichever way it is invoked. The
flags stay as a **pin** — if a future gas defaults the other way, this says
which way the artefact was measured — and saying so is the difference between
a pin and a superstition.

---

## § 7. The qemu arm measures the instrument and nothing else

`qemu/2026-09-15/` holds two captures from `qemu-mips-static` (8.2.2),
**user mode** — a different program from the `qemu-system-mips -M malta` runs
the rest of that directory holds, and `qemu/README.md` § *a SECOND EMULATOR*
says what each can and cannot show.

Five statements, all registered before the run and all hit: `install_rc=0`,
`c1a_raise=1`, `c1b_special0e_n=1`, 75 well-formed rows reaching
`rlxuprobe: end`, `scratch_bad=0`. Plus four arms of the row-range argument —
`0..3` gives exactly four rows, an out-of-range `last` clamps, a non-numeric
argument falls back.

🔴 **Nothing in those captures is column ②.** Column ② is about what rlxfw's
kernel on this die does with an encoding — `simulate_llsc`, `simulate_sync`,
`do_cpu`'s `cpid == 0` arm. qemu has none of that code. `sync` reads *no
signal* there because qemu implements `sync`.

🟢 **What the desk half did get is a positive AND a negative control on C2,
before the seating rather than during it.** With `--elf`, all 35 trapping rows
reported a PC equal to their own `_w` symbol; with one PC corrupted in a copy
of the capture, the checker reported *`C2 special0e faulted at DEADBEE0, its
probed word is at 00401330`*. And a user capture handed to `--arm device`
**REFUSES** rather than reporting zero rows.

---

## § 8. What could still be wrong

1. ~~**Nothing here has run on the silicon.**~~ 🔄 **2026-09-15, seating 23:
   it ran, and this row expired at 20:12:38.** `bench/2026-09-15/C2-UP.log` —
   75 payload rows, `install_rc=0`, `c1a_raise=1`, `c1b_special0e_n=1`,
   `scratch_bad=0`, terminator present, `C2` run with `--elf` and silent. § 2
   and § 3 are still 讀 out of source; what changed is that the artefact they
   describe has now answered. ⚠️ **One seating, one boot** — nothing here has
   been repeated.
2. **The `rt_sigframe` size, 480 bytes, is 推** — derived from the struct's
   members rather than from `sizeof` on the target. It matters only to § 2's
   statement of how far past the frame a stock-header write would land; the
   harness does not depend on it.
3. **`sigsetsize` is not checked by this harness.** The kernel requires 16 and
   uClibc is expected to pass it; if it did not, `sigaction` would return
   non-zero and **C1a and `install_rc` are what would say so**. That is a
   control rather than an assumption, but it has never been seen failing.
4. **C2 cannot distinguish a row that faulted at its own word from a row whose
   `_w` symbol the linker placed somewhere surprising.** Both are checked
   against the same artefact. A stronger check would compare the WORD at that
   address against the table, which `isapay.py verify` already does
   separately — running both on the seating's artefact is the pair.
   🔄 **2026-09-15: the pair has been run.** 量 on
   `build/uprobe.elf`, the artefact seating 23 executed:
   **0 `artefact has` mismatches and 0 `NOT FOUND` symbols** over all 75 rows,
   beside a `C2` that ran with `--elf` and was silent.
   ⚠️ **Two things this does not say.** `verify` reports **52** findings of
   the *naming* kind (31 *decodes it as*, 21 *names it*) — by design, because
   a `.word` this core cannot execute still assembles and binutils will not
   name it — and **this segment did not audit whether all 52 are expected**;
   it read only the two counts that pair with `C2`. And 🔴 **`verify` needs
   `--objdump <the rsdk cross objdump>`**: run without it the host's x86
   binutils decodes every row as `00000000` and the tool reports **75 of 75**
   findings, which is a misapplied instrument and not a result. Measured
   today, in that order.
5. ~~**`alarm(30)` is a number, not a measurement.**~~ 🔄 **2026-09-15: it is
   a measurement now, and the estimate was close.** 量
   `bench/2026-09-15/C2-UP.timing`: from the command going out to
   `rlxuprobe: end` arriving is **2.1140 s**, so `alarm(30)` is **14.2×** and
   not the ~16× estimated — the difference being that the console, not the
   compute, is what the run spends its time on.
   🟢 **And that timing independently reproduces `FW-70`.** The capture is
   7,305 bytes in 2.1189 s = **3,447 B/s = 89.8 % of 38400 8N1's nominal
   3,840 B/s**, which lands inside the **88.4–92.7 %** band `FW-70` measured
   for the Linux era over a completely different payload. The device's
   `write(2)` path through the vendor console driver is therefore timed, which
   is the clause this row said was missing.
6. **The `--range` arguments are typed by an operator.** A card that types the
   wrong range gets a short capture, and the `first=`/`last=` header fields
   are what make that visible rather than silent.

---

## § 9. `ucost` — the second compiled binary, and why it does not share the first one's digest

**2026-09-16, the seventy-fifth segment.** `R1-pub-4b`'s instrument.

| | |
|---|---|
| `UCOST_BUILD_ID` | **`8403799745aeb189`** — `cat ucost.c ucost-cells.S \| sha256sum \| cut -c1-16` |
| stripped | **16,692** bytes, static, no `PT_INTERP` |
| sha256 | `76c7e2318021484967ccc0e8c5a2eadd992c5bee372a2a7bcd10d0a1ebe3c6db` |
| flags | `0x1005, noreorder, cpic, o32, mips1` |
| in the image | `uc1`, `RECIPE_ID` **`efa93621`** |

### § 9.1 🔴 It links neither `cells4.S` nor anything else `uprobe` links, and that is the decision

`uprobe`'s `BUILD_ID` is a digest over **four** files — `uprobe.c`,
`cells4.S`, `probe4rows.h`, `rlxasm.h` — and seating 23's capture printed it:
`a87be346bb83e7f9`. Seating 24 **re-runs a `4a` row**, which is the first time
any column-② row will have been repeated, and that repeat is worth most when
the binary is **byte-identical** to the one that produced the original.

So `ucost` is a **separate product in the same directory** with every variable
prefixed, its own digest over its own two files, and no path that reaches those
four. 量 at the end of the segment, after every edit: `a87be346bb83e7f9`,
unchanged.

⚠️ **Consequence, stated rather than left to be found**: this defers
`tools/isa-payload.tsv`'s `special0e` `why` column (`C2` where the
documentation says `C5`) a **fourth** time. The deferral now has an expiry
instead of a wish — **the first rebuild after that repeat lands**.

### § 9.2 Why the probed words are hand written, and what checks them

A cost measurement needs the probed word inside a **counted loop** and nothing
else inside it; `cells4.S`'s cells are shaped for **one** execution under a
fault handler with eight recorded words, and reusing one would measure its
epilogue. And `cells4.S` may not be modified at all this segment (§ 9.1).

So `ucost-cells.S` is hand written — and then nothing structural makes its
encodings agree with the census `4a` ran. `tools/ucostcheck.py` is what does,
and it sweeps **both** directions: six cells are joined to their
`tools/isa-payload.tsv` row, two (`nop_a`, `nop_b`) take a **named** exemption
because `nop` has no census row and cannot have one, and the set that took the
exemption must be **exactly** that list. 量 on its first run: 8 cells, 6
matched, 2 exempt. Its `--self-test` is ten cases of which eight are negative.

### § 9.3 ⚠️ What the gates do NOT say here

* **`hazlint` says nothing about the `ll` cell.** Its load set is MIPS-I and
  `ll` is opcode `0x30`. The gate is green — **0 violations in 642 loads** —
  and that green is not evidence about that one cell.
* **`UG1b` is bounded, not zero**, for the same measured reason as `uprobe`'s:
  the linked ELF holds exactly two `break`s and both are inside `__GI_abort`,
  which is uClibc's own startup. Zeroing them means hand-marshalling signal
  plumbing, and that trade was declined here as it was there.
* **`.align 4` removes I-cache line straddle between a row and its twin. It
  does not remove index conflict** against the exception handler's own lines,
  and no control in this instrument catches that. The experiment that would —
  four forced offsets per cell, slope must be flat — is named and not run.
