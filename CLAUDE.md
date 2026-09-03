# CLAUDE.md

rlxfw — an independent firmware for the TOTOLINK N150RT: Realtek RTL8196E, Lexra
core, big-endian, 4 MiB SPI NOR. **One device, no spare.** Built from four
vendors' GPL drops and one leaked draft datasheet, because TOTOLINK never
released source.

> **This file holds only what is true today.** 🔄 **2026-08-29, third update:
> MY KERNEL BOOTED ON THE SILICON.** `loudm` — 1,053,696 bytes, the `rtkload`
> pipeline's own `nfjrom` renamed — went to `0x80500000` over TFTP and was
> entered with `J`. It printed all eleven boot marks, reached a shell that
> **returns output from a typed command**, and pinged the workstation with the
> host's own capture holding both directions. `probe3` ran on the power cycle
> before it and measured this die's I-cache by experiment — **16 KiB, 16-byte
> lines, 2-way** — with both of its refutation controls firing, and found that
> **CP3 is reachable on this part** where the emulator says every `mfc3` traps.
> 🔴 **No flash-write command was issued, and that is NOT the same sentence as
> "not one flash byte is written"** — `RUNSHEET` `G8b` forbids the second without a
> full re-dump, and this seating ran no `FLR` bracket, so the flash-byte count is
> **unmeasured**. 🔄 **2026-08-30, fourth update: that bracket RAN, both
> halves, and it is now a reading.** *(This said “the next seating's card carries
> the bracket”.)* Three 256-byte windows over two power cycles — the loader head,
> the `cr6c` header, and **`H601`, which no bracket in this project had ever
> sampled** — six reads, all byte-identical to the 2026-08-16 dump; the first two windows
> also match the 2026-08-24 captures, and 🔴 **`H601` has none — there is no
> 2026-08-24 capture of it, so its gap is 14 days rather than 6**, with `AUTOBURN` reading `00000001` on the second cycle so
> the second half is an instrument's word and not the operator's. **768 of
> 4,194,304 bytes = 0.0183 %.** It still does not make the forbidden sentence
> sayable — it cannot see two writes that cancel, and it reads 256 of `H601`'s
> 8,192. 🔄 **2026-08-31, fifth update: 1,024 bytes = 0.0244 %, and for the
> first time the bracket has a NEGATIVE CONTROL.** Four windows — the fourth is
> `0x006400`, the canary page `FLS-21` measured moving — read on two power
> cycles, and **every destination was read BEFORE its `FLR`**: all eight
> pre-reads differed from the expectation, so *the `FLR` wrote* is measured
> rather than assumed. `H601` reach **6.3 %**. 🟢 **And one round ran AFTER a
> complete rlxfw boot** — kernel, userspace, 4 MiB through `mtd_read`, an
> `EACCES` write attempt, a ping — which is the first evidence here that a full
> boot of my firmware leaves those windows unchanged. 🔴 **The forbidden
> sentence is no closer**: 0.0244 % cannot see a write outside the windows, and
> no `FLR` full re-dump ran. 🔴 **Cycle 6's carded round was VOID and that is
> the control working** — DRAM retained cycle 5's contents across the power
> cycle (`MEM-17`), so four pre-reads came back equal to the flash and the
> bracket moved to fresh addresses. The same seating booted `quietm` to a shell in **7.260 s** and pinged
> 4/4. 🔴 **It also refuted its own byte prediction**: `quietm` printed 849
> bytes where 401 was predicted, because `CONFIG_PRINTK=n` removes `printk` and
> **not** the vendor driver's 97 `panic_printk` call sites (`SPEC.md` `FW-31`; the same
> evening's adversarial pass corrected that number from 274, which counted seven
> `built-in.o` aggregations alongside the leaves inside them). There is still no driver of mine —
> the ping went out through the vendor's `rtl819x`, which is in the vendor's own
> configuration. *(Until today this said "nothing of mine has executed on the
> silicon", which stopped being true at 23:09; the sentence before that said "no
> loadable image", and that stopped being true at 02:20 the same day.)*
> 🔄 **2026-08-31, SIXTH update — seating 8, four power cycles, and the two
> biggest results of `R3` came out of the last thing it still needed power
> for.** 🟢 **`FW-34`'s last row is CLOSED by measurement**: `probe3`'s Group F
> timed 1,024 uncached loads through `0xBD000000` at stride 4 and at stride
> 1,024 and got **the same number both times** — 30,354 ticks, `R = 1.0000` —
> so the memory-mapped SPI window serves a single-word read as its own
> transaction and the instruction-fetch amplification is the `9×` the model
> bounds it at. The same six words compared `0xBFC00000` against `0xBD000000`
> for the first time in this project. 🟢 **The I-cache is two-way by a SECOND
> route, and it is a shape rather than a count**: at the eviction walk's
> boundary point the victims that miss on re-execution arrive as **ten
> `{k, k+256}` pairs with no singleton**, which two-way predicts and
> direct-mapped does not, *while both predict the same number of them*.
> 🔴 **A bit of DRAM changed while the board was off and the block's own seal
> caught it** — the first thing that seal has ever caught — **and a fourth
> power cycle then refuted this session's own explanation of it**: 35.1 minutes
> off, both ends timed, **598 of 22,976 bits = 2.603 %**, so retention falls off
> steeply with time and one bit after two minutes needs no thermal story. The
> thermal story is retracted in place. 🔴 **The flash sentence has not moved**:
> the bracket ran twice on one seating, `1,024` bytes = **0.0244 %**, all
> byte-identical — **and for the first time with an observed vendor-firmware
> boot bracketed between the two rounds** — but no full re-dump ran and the
> vendor firmware executed on this part for ~2 minutes. ⚠️ **Three defects in
> the seating's own card**, two caught before power: a directory named for a day
> the seating did not happen on, an image the card told the operator to upload
> that was never staged, and a `J` row that had lost the ESC-after-jump that
> hands the loader prompt back — the third cost a power cycle.
> 🔄 **2026-09-02, seventh update: an `edit → result`
> iteration ran as ONE COMMAND against the silicon and reported a
> number.** `looprun --mode bench` drove reset → rescue → burn-flag
> read-back → upload → staged-head read-back → boot → assert with **no
> operator gap between any two stages**, and printed **34.74 s** and seven
> assertions. The one that matters is that **the board printed the id the
> build computed** — `RLXFW-ID0=B1434383`, a sha256 over `config/`,
> compiled in and compared by the tool, **typed by nobody**. 🔴 **And the
> audit run in the hour before power found three defects in that tool, two
> of them safety**: it uploaded with the loader's *echo* as its only
> evidence that the burn flag was off (and `C-6`, 量 2026-08-24, is
> the measurement that says an echo and the word at `0x8040D4A0` are two
> sources); it jumped to `0x80500000` without checking
> what was there, on a board whose reset re-stages that address from flash;
> and 🔴 **`S3` had never been connected to `S2` at all**, so the
> `--skip S2,S3` the card called a convenience was **necessary** rather than
> chosen — an explicit `--cell-top` would have worked too, and nobody knew
> there was anything to pass. **Zero flash-write commands and no `FLR`**, decided
> before power, so the bracket stands at **1,024 of 4,194,304 = 0.0244 %**
> and *not one flash byte is written* is exactly as unsayable as it was.
> **Which gate that is, `PROGRESS.md` says** — this
> file does not restate it, because one piece of state has exactly one owner
> and a gate id copied to a second place goes stale there.
> Conventions for files that do not exist are not written
> here; they go in when the file appears. Where this contradicts the repo, the
> repo wins and this file is wrong.

## Where things are

|                   |                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **`PROGRESS.md`** | sole owner of *where I am* — active gate, active step, blockers, carried-forward. **Read it first, every session**          |
| **`plan/`**       | gitignored, always present locally. Index: `plan/README.md`.  Whole plan: `plan/.md`                                        |
| **`upstream/`**   | the RE project, submodule pinned at `4d3ff26`, **read-only** — that pin is the whole credibility of R9's differential proof |
| **`$FWRE_WORK`**  | `/home/key/fwre-work` — every binary, shared with `../router`. This project's output goes in `$FWRE_WORK/rebuild/`          |
| **`SPEC.md`**     | every number this project holds about the device — part numbers, register readings, addresses, budgets — each with a mark for where the **value** came from and a separate mark for where its **name** came from, and a link to the file that owns the finding. **An index, not an owner**: a finding or a correction lands in the owning file first and in `SPEC.md` in the same commit. Written in Chinese |

**A gate is not a session.** R6 is 35 work-segments, about a month. A session is
one step inside a gate. When I say "do R5", ask which driver.

## How to work here

**You build the instruments, I read the dials.** When I state a finding, do not
agree — name the tool that could be lying and the second source that settles it.
Agreeable understatement is how a claim reaches a hostile reader undefended.

- **Every sentence about this machine is marked**: *measured on the device*, *read
  out of the code or the dump*, or *inferred, pending a measurement*. Mixed
  together they are worth neither.
- **No register value enters code on one source.** datasheet → SDK header →
  `devmem`; two must agree, or it is recorded as undetermined.
- **Nothing counts as a result until its refutation condition is written first** —
  what outcome would have proved it wrong.
- **A tool reporting `0` is making a claim.** Every sweep needs a positive control;
  a tool that cannot fail proves nothing.
- **Uncertain is a valid answer** — follow it with the experiment that decides it.
  Five minutes at the bench beats a paragraph of reasoning.
- **Propose before writing** anything over ~50 lines: the approach, and where it
  will fail. **Label estimates as guesses** — nothing here is calibrated yet.
- **Negative results stay in place.** So does the record of being wrong.

## Never

|                                                        |                                                                                                                             |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| write flash                                            | mainline is zero-write through R9. A write needs my explicit yes                                                            |
| touch `0x000000–0x005FFF` or `0x006000–0x007FFF`       | loader — bricked is unrecoverable, there is no spare. `H601` — this unit's MAC and radio calibration, not restored by reset. 🔄 **2026-08-30, twice in one day — and the morning's sentence was too strong.** *(It read: “nothing has ever CHECKED the second one”.)* True of **rlxfw's own** `G8a`/`G8b` bracket; **false about the device** — `upstream/BENCH-LOG.md` holds seven baselines of `H601`'s first 4 KiB across three days, five power-ups and two flash writes, and it is the check that **caught** the 2026-08-17 write. This file's own rule is that where it contradicts the repo, the repo wins. **Evening: rlxfw's bracket now checks it too.** `bench/2026-08-30c`/`d` read `0x006000`–`0x0060FF` on both power cycles and both were byte-identical to the 2026-08-16 dump — **256 of `H601`'s 8,192 bytes, 3.1 %**, and the other 96.9 % is still unchecked. 🔄 **2026-09-01 (seating 9): a THIRD reading of the same two pages, and this time it answers a different question — whether a *scripted* reset writes them.** `bench/2026-09-01/T-flrh`/`T-flrc`, after one cold boot and twenty `J BFC00000` watchdog resets: both byte-identical to the 2026-08-16 dump, with the read-backs outside the repository and **four RAM destinations no `FLR` here had ever used**, so `MEM-17`'s retention path could not pre-fill them. The reach does not move. 🔄 **2026-08-31: 512 bytes, 6.3 %, and the other 93.7 % is still unchecked** — `bench/2026-08-31*` add `0x006400`, the canary page, on both power cycles; all four readings byte-identical to the 2026-08-16 dump. 🔴 **And a capture of one of these windows nearly entered the repository**: the card writes `FLR` PRE-reads under `bench/` because a pre-read is *expected* to be garbage, and when DRAM retention made that false two files held this unit's MAC. Untracked, moved, nothing in history — but **a containment rule whose correctness depends on the experiment coming out the expected way is not a containment rule**, and the card template still has it. ✅ **2026-09-03: an enforcer now does, and the template was still not edited.** `tools/cardcheck.py` `A19` reports an `FLR` typed inside a `--send`, which is the bypass that reaches `console-capture.py` without `flrbracket run`; `A20` excuses the two frozen cards that do it **by name**, not by date; `A21` is the control that says it is a guard and not a blanket; and `B10` sweeps the corpus **in both directions**, so the allow-list cannot accrete unreported. 量 on its first run: 50 cards, 2 type `FLR`, list exact. The morning's reading, which is what made that bracket exist: 量: `RUNSHEET` §B3's `G8a`/`G8b` flash bracket samples 256 of the loader region's 24,576 bytes, 256 bytes of the `cr6c` header — which no rule forbids writing — and **0 of `H601`'s 8,192**. Six days of write-ups called those *"the two regions that would change"*, and neither of them was the one that cannot change back. `bench/2026-08-30c/PREDICTIONS-B5-block2.md` §8 adds it; its capture may not enter this repository and **not even its sha256 may** (with the window otherwise known, a digest is a 2^24 search for the MAC), which `tools/flashwin.py` enforces rather than remembers. 🆕 **2026-08-31: the OTHER half of that rule now has an enforcer too, and it is the half the template kept getting wrong.** `flashwin` governs what may be *printed*; nothing governed *where a capture of a forbidden window may land*, and on 2026-08-31 two files inside this repository held this unit's MAC because the card wrote `H601` pre-reads under `bench/` on the assumption they would be garbage. `tools/flrbracket.py`'s `run` refuses, **before it opens the port**, to write the read-back of an `H601`-overlapping window anywhere inside this repository, and **the pre-read anywhere inside it at all, whatever the window is** — a pre-read is a `DW` of the RAM destination before the `FLR`, so its content is decided by what was last written there, and `MEM-17` measured DRAM keeping a previous cycle's `FLR` output across a power cycle. *(The first version of this row keyed both on the flash source; an adversarial pass showed that is the 2026-08-31 incident with the roles swapped.)* The line is drawn at **content, not mention**: the `FLR` echo capture holds addresses and no flash bytes, which is why `bench/2026-08-31/W-flrh.log` names `00006000` and is correctly committed. 🆕 **2026-08-31: a THIRD enforcer, and it asks the question the other two cannot.** `flashwin` governs what may be *printed*; `flrbracket` governs where a *bracket's* read-back may land; both act when a file is produced. **`flashwin scan` asks whether a file this repository has ALREADY COMMITTED holds forbidden content** — by the bytes, not by the shapes an address takes, with the probe set filtered on the reference side. 量 on its first sweep: rlxfw's own tree is **CLEAN over 1,381 files** (`--sweep . --exclude upstream`), `K-P3` included; the default `--sweep .` reads **1,683** and reports **1 HIT** — `upstream/BENCH-LOG.md:2557`, sixteen bytes of `H601` as a hexdump line. ⚠️ **`leakscan` does not name that line (it names 22 hit rows over 18 other lines of the same file); `audit-bench-log` does, on its topic keyword `H601` (the flash bytes there ARE the ASCII `H`,`6`,`0`,`1`) among 183 hits, exiting 0** — so neither identifies it as forbidden CONTENT, which is the narrower and correct claim. It does not move `FLS-22`'s decision and it is not meant to; it is the sentence *nothing checks the committed record* that stops being true |
| build with `-march=mips32`                             | the load delay slot is architecturally exposed; mips32 miscompiles **silently** — no fault, no warning, just wrong values   |
| write asm under `.set reorder`                         | you cannot know what the assembler filled in. `noreorder`, fill every delay slot yourself                                   |
| measure the ISA or a CPU hazard under Linux            | the vendor kernel emulates `ll`/`sc` (and `sync`, as a no-op), so you would measure the kernel. Bare metal only. 🔄 **2026-08-27: the reason was half wrong and is narrowed.** This row said "and the FPU" — **there is no FPU emulator in this kernel at all**: `arch/rlx` has no `math-emu`, and `do_cpu` gives `SIGILL` for any coprocessor but 0. `simulate_llsc` alone is enough, so the rule does not move; only its reason does. `CPU-47` |
| edit vendor source by hand, or apply a patch to `src-vendor/`             | 🆕 **2026-08-29: rlxfw patches Realtek's source for the first time.** 🔄 **2026-09-01: there are TWO sanctioned ways, and this row said one.** A row in `config/rlxfw-marks.tsv` is one of them and it is the narrow one — `rlxfw-marks.py` refuses any insert that is not `rlxfw_mark("TAG");`, `rlxfw_markx("TAG", expr);`, `obj-y += NAME.o` or the mark header include, on the stated ground that *an arbitrary statement here would be a patch with no reviewer*. The other is a patch in `config/host-compat/`, applied by `rlxfw-kbuild.sh`, which **stops the build if it does not apply**; `0001` predates this row (2026-08-28) and `0002` (2026-09-01, `P4a`) is what made the omission matter. ⚠️ That directory's name is now narrower than its contents — the driver describes it as *every source change to the vendor tree*, which is the accurate scope — and a rename is carried forward rather than done in the session that widened it. 🔄 **2026-09-02: two more, and they pull the name in OPPOSITE directions.** `0004` is host compatibility in the strictest sense — a 2009 kernel's `\#` escape is a no-op under GNU Make 4.3, so every `.cmd` file is truncated at a bare `#` and every build is a full rebuild — which is the same shape as `0001` and perl 5.22. `0003` is not: it is about when kbuild rewrites a generated header. **So the directory now holds two patches its name fits and two it does not**, and the rename is still carried forward. 量: with all four declared, a fresh stage builds 594 objects and a no-op `make` costs 2; the product moves by 4 bytes of 3,968,240, all of them `RLXFW_SRC_ID`, because `RECIPE_ID` is a digest over `config/` and `config/` gained two files. `notes/incremental-build.md` **The rule below is unchanged: never by hand, never inside `src-vendor/`, always to a staged tree.** Every inserted line is a row in `config/rlxfw-marks.tsv` with a reason, applied by `tools/rlxfw-marks.py` to a **staged** tree — the tool refuses any path under `src-vendor/`, and the anchor must occur **exactly once** or it refuses rather than picking one. Files of mine live in `config/rlxfw-src/`, mirroring the staged layout. ⚠️ **`check` reads the tree and `verify` reads the built artefact, and only the second one can catch a mark that compiled and is not in the image** — measured, on the first run. 🆕 **2026-09-02 (`R5-0`): a staged tree has THREE states and the third is the one that carries the rule.** `apply` used to refuse any second run outright, because applying twice emits the mark twice and a doubled mark reads in a capture as a boot loop — so `--keep --marks` could not run at all, which is what `INC-1` had to measure. `--if-needed` splits that: a **clean** tree is applied to, a **fully applied** one is a no-op, and a 🔴 **partially applied one is REFUSED** — some marks present is a tree that builds and is not what the table describes. The row's rule does not move: `A20` requires plain `apply` to still refuse a marked tree, so `A4` is bypassed only when asked for, never by default |
| commit the datasheet, a flash dump, or a vendor binary | one is someone else's property; the others identify one physical device                                                     |
| open `$FWRE_WORK/disclosure/`                          | unsent vulnerability reports, mode 600                                                                                      |
| ~~write `RLX5281`~~ ✅ **lifted 2026-08-27**                | 🔴 **The `PRId` assignment table this row named arrived, and it was in a GPL drop this project already had.** `arch/rlx/include/asm/cpu.h` maps `PRID_IMP_RLX4181 = 0xcd00`; `PRId = 0x0000CD01` (量) has bits 15:8 = `0xCD`, so the core is **`RLX4181`, revision 1** — and **`RLX5281` is `0xdc01`, now positively excluded rather than merely unproven**. Write `RLX4181`, marked **讀**, with `PRId` itself still 量. Three weaknesses travel with it and must not be dropped when it is quoted: the three drops are **byte-identical** in that header (one source, three copies), **no code in the port reads the table**, and its own encoding breaks for `0xdc01`/`0xdc02`. `notes/vendor-kernel-isa.md` §5. **`RLX5281` stays unwritable, for the opposite reason from before.** *(Original row: `R1-gate` closed 2026-08-26 and did not name it … what lifts it is a `PRId` assignment table, not another seating.)* |

## Environment

- **`usbipd` has nothing to attach to unless a WSL process is already running.**
  Measured 2026-08-24: with the distro idle, `usbipd attach` fails with *there is
  no WSL 2 distribution running*, and 🔄 **an attachment already made can drop
  while the distro is still running** — it died between two tool calls mid-session
  and took `/dev/ttyUSB0` with it. **That drop was not distro idle**, which is
  what this line said until 2026-08-25: `uptime` ran continuously through it, and
  what left was the **CP2102**, off the Windows USB bus after **7 min 24 s of pure
  console idle**, with `usbipd list` moving the busid out of *Connected*. Root
  cause **undetermined**, and none of the three candidates has been ruled out:
  usbip socket transient, USB selective suspend not waking, a loose connector.
  🆕 **2026-08-29: that signature is not specific, 量.** A deliberate
  `usbipd detach` takes the busid out of *Connected* too — for about a second,
  while Windows re-enumerates the device — so a `usbipd list` run immediately
  after a detach reads **exactly** like the drop. **Re-read before concluding
  anything from one listing.** The same day the CP2102 was also absent from
  *Connected* on **first insertion**, with no COM port on the Windows side at
  all, and returned only after a re-seat: consistent with the loose connector
  and separating nothing, so the three candidates stand.
  Start a long-lived process first and leave it running:
  `wsl -d Ubuntu-24.04 -- sleep 36000` in the background — **that is for the attach
  step and is not a fix for the drop above; do not record it as one.** **And the busid is not
  stable** — the USB GbE moved `3-4` → `2-4` across one re-enumeration the same
  day, so re-read `usbipd list` every time rather than reusing the number.
- **The Bash tool is Git Bash, not WSL.** `-lc` mangles the command: `$VAR` is
  stripped and a leading `/` is MSYS-translated (`bash /mnt/c/x.sh` became
  `bash C:/Program Files/Git/mnt/c/x.sh`). 🆕 **2026-08-30: "stripped" is the
  kind half. `$?` is EXPANDED, in the OUTER shell**, so
  `bash -lc 'cmd > f; echo "rc=$?" >> f'` records the outer shell's status and
  not `cmd`'s — 量, it wrote `rc=0` for a suite that had exited 1, and the
  wrong number is worse than an empty one because it reads as a measurement.
  It also swallowed a whole run: a `nohup … &` inside `wsl -- bash -lc` dies
  with its parent, and a progress check written
  `tail -6 f 2>/dev/null || echo "still running"` cannot tell *running* from
  *never started* — that is this project's own "a tool reporting 0 is making a
  claim", in a one-line shell check. **Feed the script over stdin instead** —
  nothing in the body is touched, and shell variables work:

  ```
  wsl -d Ubuntu-24.04 -- bash -ls <<'EOF'
  … ordinary shell, literal paths, $VAR all fine …
  EOF
  ```
  🆕 **But do not nest a second heredoc inside that one.** Measured 2026-08-26,
  three times before it was believed: a `python3 - <<'PY' … PY` inside the outer
  heredoc **loses one level of backslash**, so `\\t` reaches Python as `\t` and
  `"…1 \\\n"` becomes a line continuation that eats the newline. The symptoms are
  a `SyntaxWarning: invalid escape sequence` and an `assert … in s` that fails on
  a string you can see in the file. It also breaks the outer heredoc outright if
  the inner body contains the outer terminator. **Write the script to a file with
  the Write tool and run it by path** — `python3 /mnt/c/…/scratchpad/x.py` — which
  has no quoting layers at all.
  🔄 **2026-08-27: it is not the nesting. ONE quoted heredoc from the Bash tool
  loses a backslash level, and the note above blamed the wrong thing.** 量 with
  `od -c`, which is the instrument to use because everything else in the path
  re-escapes: send `re.compile(r'(?<!\\)\|')` through a single `<<'EOF'` and the
  bytes that reach disk are `re.compile(r'(?<!\)\|')`; `printf 'a\\b'` arrives as
  `printf 'a\b'`. It cost two `re.error: missing ), unterminated subpattern` in
  one session, and once it went further than an error — `cat > f <<'EOF'` wrote
  the corruption into a committed file. ⚠️ **Root cause undetermined**: the tool's
  own command marshalling and the shell are both in the path and this measurement
  does not separate them. **The workaround is unchanged and it is the whole
  point** — Write the file, run it by path. 🔴 **And never `open(path, 'w')` in a
  script that can raise before it writes**: `open()` truncates immediately, so a
  `NameError` one line later leaves the file at zero bytes. It emptied
  `PROGRESS.md` on 2026-08-27; `git checkout --` got it back because it was
  committed. Build the whole string first, write to `path.tmp`, `os.replace`.
- 🆕 **Running a vendor binary is not a read-only act, and `--version` is not a
  safe way to ask one what it is.** Measured 2026-08-28: a census that ran every
  executable in the three rsdk `bin/` directories with `--version` deleted
  **2,580 tracked files** from a pinned vendor clone — mostly regular files
  under `config/uclibc/`, not the symlink farm the first write-up said —
  rewrote four tracked files and left seventeen ignored build products — because `rsdk-linux-config`
  is a statically linked i386 ELF that runs `make` in the tree it lives in. It
  also wrote an `offset.tmp` into **this repository's root**, which is a place no
  vendor-tree check watches. It was recoverable only because the trees are clones
  pinned at known shas. **Wrap anything that executes a vendor binary in
  `tools/vendor-tripwire.sh`, and run it from a scratch directory**, never from
  the repo root and never from inside `src-vendor/`.

- **Binaries and vendor source trees never live under `/mnt/c`.** Measured
  2026-08-23: DrvFs *keeps* symlinks, but reports every file as `777`, so git sets
  `core.fileMode=false` and stops seeing mode changes at all; and NTFS is
  case-insensitive, which silently drops **254 files** from the vendor kernel trees
  (`xt_CONNMARK.h` against `xt_connmark.h`). On this project part of the finding
  *is* filesystem metadata. `src-vendor/` is a symlink into `$FWRE_WORK/rebuild/`.
  - **The same blindness quietly loses the executable bit on new tools.** With
    `core.fileMode=false` a file is recorded with whatever mode `git add` happened
    to capture and nothing ever corrects it: **7 of the first 10 files in `tools/`
    drifted to `100644`** while the three oldest stayed `100755`. Every tool here
    carries a shebang, so every tool is recorded `100755`; the fix for a drifted
    one is `git update-index --chmod=+x <path>`, and `tools/test-file-modes.sh`
    reads the **index** — the thing DrvFs cannot lie about — in both directions.
- **Session working files do not go in WSL's `/tmp`.** Measured 2026-08-23: the
  distro restarts between tool calls (`uptime -s` moved forward mid-session,
  `uptime -p` read "up 0 minutes"), and `/usr/lib/tmpfiles.d/tmp.conf` carries
  `D /tmp` — a capital `D`, so `systemd-tmpfiles-setup` **empties it at every
  start**. It is not a tmpfs; the wipe is deliberate, not a side effect. Derived
  artefacts go in `$FWRE_WORK/rebuild/`, which is where they belong anyway.
- 🆕 **Every bench command runs `/usr/bin/python3`, never `python3`.** Measured
  2026-08-29 (and the tool has said so since 2026-08-24, in a message nothing in
  this file repeated): `python3` on this host resolves to
  `~/.venvs/thermal/bin/python3`, which has **no `pyserial`**, so
  `console-capture.py` refuses. It refuses with the reason rather than a
  traceback, which is the only thing that made it a two-second problem instead of
  a bench-time one. **And a 3-second capture with the board OFF is a free
  pre-flight**: 0 bytes, and the tool splits that into three causes — the
  adapter, the port, or the board — before a power cycle is spent.
  🔄 **2026-09-02: the resolution above is true in a LOGIN shell and not
  otherwise, which makes the trap intermittent rather than constant — and
  an intermittent trap is the worse kind.** 量, with the control run beside
  it: `wsl -- bash -lc 'command -v python3'` gives
  `/home/key/.venvs/thermal/bin/python3`, while `wsl -- bash -c` and
  `wsl -- bash <script>` both give `/usr/bin/python3`, because the venv
  reaches `PATH` through a login profile. **So a script that works when run
  one way breaks when run the other, and neither run tells you which you
  got.** The rule does not move: write `/usr/bin/python3` and the question
  never arises.
- ✅ **`console-capture.py` refuses a capture with neither `--seconds` nor
  `--idle`, and records both in its metadata — fixed 2026-08-30.** *(Until then
  such a capture never returned: both default to `0.0` and the read loop broke on
  neither, so `timeout -s TERM 8` gave `rc=124`. A SIGTERM kill loses
  `.meta.json`; the `.log` and `.timing` survive, flushed per chunk.)*
  **Every capture command still carries a terminator** — the guard makes that a
  refusal rather than a habit, and §B5's card now carries one on all fifteen of
  its capture rows. 🔴 **Where the guard sits was measured, and the obvious
  placement is wrong**: it goes after `_check_send` and before the port is
  opened. Of the four terminator-less invocations in
  `tools/test-console-capture.sh` only **one** changes (`P4`, the 127-character
  line, the only one whose assertion is that the run reaches the port); the other
  three are refused inside `_check_send` first. 🔄 **2026-08-30, later the same
  day: this bullet said *"`N21` pins both sides with one command"* and that is
  false.** `N21` sends **127** characters — a length `_check_send` **accepts** —
  so it gets the terminator refusal whether or not the guard sits above
  `_check_send`; that side was held only by `N4`/`N7`/`N8` happening to carry no
  terminator, which is coverage by accident. **`N29` sends 128 and requires the
  LENGTH refusal**, and `N30` pre-creates the output files and requires the
  TERMINATOR refusal ahead of the overwrite one — those two pin the position,
  one edge each. Found by `tools/test-console-capture-mutants.py`: **25 mutants
  of that guard, TEN alive against the forty cases**, in four classes the cases
  could see only one instance of each. Suite 40 → 46, 25/25 killed.
  🔴 **And a green suite is a claim about the suite**: the mutant runner is now
  the thing that says the cases work, and it runs in CI.
  ⚠️ **`tool_version` deliberately did not move**: it owns *what the
  instrument wrote to the port*, and nothing new goes on the wire — the
  **presence** of the `seconds` key is what dates a capture instead.
- 🆕 **PowerShell has its own three traps, all measured 2026-09-01, and two of
  them make a check silently useless rather than noisy.** ① `Get-Date -Format`
  eats format letters **inside literal text**: `"Windows: yyyy-MM-dd"` printed
  `Win1ow20:` because `d` and `s` are specifiers. ② `<long command> |
  Select-Object -Last N` **buffers the whole pipeline** — a 25-minute suite
  showed nothing until it ended, so there is no progress to watch; run it in the
  background, or let it write files and read those. ③ `wsl -- bash -c "…$?…"`
  dies with *unexpected EOF* on nested quotes. **Same fix as the Bash tool's:
  write the script to a file and run it by path** — `wsl -d Ubuntu-24.04 --
  bash /mnt/c/…/x.sh`.
- 🆕 **A sweep that RECONSTRUCTS the command it runs will eventually run a
  broken one and report it as a broken suite.** 量 2026-09-02: a script that
  pulled each suite out of `ci.yml` with a regex stopped at the `&` of `2>&1`,
  so all 48 invocations ran as `... 2>` and died in the shell — and it printed
  **46 FAIL lines that are indistinguishable from 46 failing suites**. That is
  this project's own rule about `test-flashwin-mutants` (a harness that kills
  everything and a harness that tests nothing print the same thing), inside the
  harness. **Take the whole `run:` value verbatim and hand it to `bash -c`**, so
  what runs on the desk is character-for-character what runs in CI, and read the
  first few lines of the output before believing any summary.
  🔴 **And that is still not enough, measured the same hour.** The corrected
  script grepped `^\s+run: .*tools/` and **silently dropped
  `verify-backup-copy`**, whose step is a YAML literal block: its `run:` line is
  just `|` and the command sits in the body. 46 suites reported ok and the
  47th was never invoked. **`ci-census` is what named it** — `RED … no
  verify-backup-copy.out` — which is the second time that suite has been lost
  this way and the second time the census caught it. **A sweep that selects
  `run:` LINES cannot see a `run:` BLOCK**; either parse the YAML or let the
  census be the arbiter, and never read a sweep's own count as coverage.
  🔴 **2026-09-02: and `ci-census` cannot be that arbiter ON THIS HOST, which is the half the sentence above still got wrong.** 量, running every `run:` step here: 47 of 49 suites green, and the two reds are the census **working**. `test-hazlint` (142 cases) and `test-hazlint-objs` (28) are declared `*bench-only*` in `ci-expected.tsv` because their `K4` population control is `$FWRE_WORK/stage2.bin` — 56 KiB of this unit's vendor bootloader, which may not be committed. `ci-census`'s own `C10` requires *`*bench-only*` plus a real `.out` → red*. **This desk has that file, so they run, so their `.out` exists, so red.** Those two are 170 of the declared `# not-run-total: 478` *(477 when this line was written; 量 2026-09-03 against the tsv and against CI run 33747027566's census, which printed the same 478)*, so the total collapses to **2** here and the mismatch check fires too. ⚠️ **And the total is not recomputable from the table**: `ci-census`'s own docstring says a suite's skip rows are *alternatives, not additive* — which fire depends on configuration — so summing the covers column gives 517, not 478, and that is the table being right rather than wrong. **So: run every suite here and read the per-suite lines; let the census on GitHub decide the census.** A local sweep that ends in two reds every time trains a reader to ignore reds, which is the failure this whole paragraph exists to prevent.
- 🆕 **Reading a suite's output files is a measurement, so it needs a control —
  and freshness is NOT completion.** 量 2026-09-01: `ci-out/` holds the previous
  run's `.out` files, so a summary that just reads them scores stale results as
  new (an mtime cut caught exactly one, and it was the one that would have been
  misread). Then the mtime cut passed a file that was **still being written** —
  3,645 bytes, `RESULT:` absent; 5,968 bytes forty seconds later. **Wait for the
  process's exit code; the output file is not the instrument.**
- Serial console: CP2102, **38400 8N1**. You cannot see it — at the bench you write
  the commands and read what I paste back. One power cycle is the most expensive
  unit here, so list every question before the device is plugged in.

## Committed files

**Written for an engineer, never for a hiring panel.** State the finding, name the
artefact it was measured on, stop. No résumé bullets, no "this proves I can X".
`plan/` is gitignored and may address me directly; committed files may not.

English, except the working log and `SPEC.md`. Commit messages say *why* — the
diff says what.

🔴 **And `ci-census --only <the suites you touched>` is the wrong rule when what you touched is `bench/`.** 量 2026-08-30: a seating that adds two captures moves the population every census-shaped case reads, and `tools/test-boot-timeline.sh`'s `B2` — a hardcoded `N cold, M warm` — went red on GitHub twice while the local `--only` run was green. **A seating changes data, and data is what those cases assert on.** After a seating, run every suite that can run on this host, not only the ones whose code changed.

**Before you stop**: update `PROGRESS.md` § Now, and append a dated entry to
`LOG.md` (create it on the first session) — **including desk-only days**, because
a desk-only day is exactly when the next bench visit's plan changes. **If the
session produced, changed or refuted a number, `SPEC.md` changes in the same
commit** — a spec table that lags the finding is worse than no table, because it
reads as current. Then run `python3 tools/spec-check.py` — it runs its eight
controls first and refuses to report on the file if any of them fails — and
`bash tools/test-file-modes.sh` if a file was added. Two seconds for both.
