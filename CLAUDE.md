# CLAUDE.md

rlxfw — an independent firmware for the TOTOLINK N150RT: Realtek RTL8196E, Lexra
core, big-endian, 4 MiB SPI NOR. **One device, no spare.** Built from four
vendors' GPL drops and one leaked draft datasheet, because TOTOLINK never
released source.

> **This file holds only what is true today.** 🔄 **2026-08-29, second update:
> four LOADABLE IMAGES of mine now exist** — `quiet` and `loud`, each with and
> without the eleven boot marks, wrapped by Realtek's own `rtkload` pipeline into
> `nfjrom` files of 1,027,072 and 1,053,696 bytes, and that pipeline was shown
> the same day to reproduce the vendor's own shipped `nfjrom` byte for byte. Two
> of them have printed eight boot marks under a MIPS32 emulator with the UART
> redirected, halting where this board's own kernel halts. **No driver, nothing
> of mine has executed on the silicon, and not one flash byte is written.**
> *(Until today this said "no loadable image", which stopped being true at
> 02:20.)* **Which gate that is, `PROGRESS.md` says** — this
> file does not restate it, because one piece of state has exactly one owner
> and a gate id copied to a second place goes stale there. Conventions for files that do not exist are not written
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
| touch `0x000000–0x005FFF` or `0x006000–0x007FFF`       | loader — bricked is unrecoverable, there is no spare. `H601` — this unit's MAC and radio calibration, not restored by reset |
| build with `-march=mips32`                             | the load delay slot is architecturally exposed; mips32 miscompiles **silently** — no fault, no warning, just wrong values   |
| write asm under `.set reorder`                         | you cannot know what the assembler filled in. `noreorder`, fill every delay slot yourself                                   |
| measure the ISA or a CPU hazard under Linux            | the vendor kernel emulates `ll`/`sc` (and `sync`, as a no-op), so you would measure the kernel. Bare metal only. 🔄 **2026-08-27: the reason was half wrong and is narrowed.** This row said "and the FPU" — **there is no FPU emulator in this kernel at all**: `arch/rlx` has no `math-emu`, and `do_cpu` gives `SIGILL` for any coprocessor but 0. `simulate_llsc` alone is enough, so the rule does not move; only its reason does. `CPU-47` |
| edit vendor source by hand, or apply a patch to `src-vendor/`             | 🆕 **2026-08-29: rlxfw patches Realtek's source for the first time, and there is exactly one way to do it.** Every inserted line is a row in `config/rlxfw-marks.tsv` with a reason, applied by `tools/rlxfw-marks.py` to a **staged** tree — the tool refuses any path under `src-vendor/`, and the anchor must occur **exactly once** or it refuses rather than picking one. Files of mine live in `config/rlxfw-src/`, mirroring the staged layout. ⚠️ **`check` reads the tree and `verify` reads the built artefact, and only the second one can catch a mark that compiled and is not in the image** — measured, on the first run |
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
  Start a long-lived process first and leave it running:
  `wsl -d Ubuntu-24.04 -- sleep 36000` in the background — **that is for the attach
  step and is not a fix for the drop above; do not record it as one.** **And the busid is not
  stable** — the USB GbE moved `3-4` → `2-4` across one re-enumeration the same
  day, so re-read `usbipd list` every time rather than reusing the number.
- **The Bash tool is Git Bash, not WSL.** `-lc` mangles the command: `$VAR` is
  stripped and a leading `/` is MSYS-translated (`bash /mnt/c/x.sh` became
  `bash C:/Program Files/Git/mnt/c/x.sh`). **Feed the script over stdin instead** —
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
- Serial console: CP2102, **38400 8N1**. You cannot see it — at the bench you write
  the commands and read what I paste back. One power cycle is the most expensive
  unit here, so list every question before the device is plugged in.

## Committed files

**Written for an engineer, never for a hiring panel.** State the finding, name the
artefact it was measured on, stop. No résumé bullets, no "this proves I can X".
`plan/` is gitignored and may address me directly; committed files may not.

English, except the working log and `SPEC.md`. Commit messages say *why* — the
diff says what.

**Before you stop**: update `PROGRESS.md` § Now, and append a dated entry to
`LOG.md` (create it on the first session) — **including desk-only days**, because
a desk-only day is exactly when the next bench visit's plan changes. **If the
session produced, changed or refuted a number, `SPEC.md` changes in the same
commit** — a spec table that lags the finding is worse than no table, because it
reads as current. Then run `python3 tools/spec-check.py` — it runs its eight
controls first and refuses to report on the file if any of them fails — and
`bash tools/test-file-modes.sh` if a file was added. Two seconds for both.
