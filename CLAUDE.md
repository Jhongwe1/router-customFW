# CLAUDE.md

rlxfw — an independent firmware for the TOTOLINK N150RT: Realtek RTL8196E, Lexra
core, big-endian, 4 MiB SPI NOR. **One device, no spare.** Built from three staged
Realtek SDK GPL drops (`notes/vendor-kernel-isa.md` owns the count; `SOURCES.json`
lists every source tree with its role) and one leaked draft datasheet. TOTOLINK
never released source.

**This file holds rules.** Where the project stands is `PROGRESS.md` § Now. Why a
rule exists is in `LOG.md` under the date it was learnt, and in this file's former
text, archived verbatim in `docs/history/claude-md-2026-09-23.md`. Where this file
contradicts the repository, the repository wins and this file is wrong.

## Where things are

| | |
|---|---|
| `PROGRESS.md` | the only owner of *where I am*: active gate, active step, blockers, carried-forward. **Read § Now first, every session** |
| `plan/` | gitignored, always present locally; `plan/README.md` indexes it and `plan/router-rebuild-plan.md` is the whole plan |
| `upstream/` | the reverse-engineering project, a submodule pinned at `4d3ff26`, **read-only**: the pin is the whole credibility of `R9`'s differential proof |
| `$FWRE_WORK` | `/home/key/fwre-work` in WSL, shared with `../router`: every binary; this project's output goes under `$FWRE_WORK/rebuild/`, and `src-vendor/` is a symlink into it |
| `SPEC.md` | every number held about the device, each with a mark for where its value came from, a mark for where its name came from, and a link to the file that owns the finding. An index, not an owner. Written in Chinese |
| `LOG.md` | one dated entry per segment: the history of every decision |
| `docs/history/` | text moved verbatim out of state documents |

A gate is not a session: a gate spans many segments and a session is one step of
one. When told "do `R<n>`", ask which step.

## How to work here

**You build the instruments, I read the dials.** When I state a finding, do not
agree: name the tool that could be lying and the second source that settles it.

- Mark every sentence about the machine **量** (measured on the device), **讀**
  (read out of code or a dump) or **推** (inferred, pending a measurement), and
  never blend them. **未定** marks an open value, which needs a `SPEC.md` § 17 row
  saying what settles it; **殘留** is the question left after a value is settled.
- No register value enters code on one source: two of datasheet, SDK header and
  `devmem` must agree, or it is recorded as undetermined.
- Nothing counts as a result until its refutation condition was written first.
- A tool reporting 0 is making a claim. Every sweep, flag and watcher needs a
  positive control, and a progress check must tell *running* from *never
  started*. A guard is shown permitting as well as refusing.
- A containment rule that holds only if the experiment comes out as expected is
  not a containment rule.
- Uncertain is a valid answer; follow it with the experiment that decides it.
- Propose before writing anything over ~50 lines: the approach and where it will
  fail. Label estimates as guesses.
- **Never predict a Linux-state value from a loader-state constant.** Linux
  reprograms `CDBR` (14 → 1000), `TC0DATA` (142,858 → 2,000), the watchdog's clock
  (~200 kHz, not 14.965 MHz) and `PABCD`'s CNR and DIR.
- Never widen a tolerance to make a result pass; change the experiment instead
  (`IRQ-13`).
- Two counters agreeing is not evidence while they run at the same rate; make the
  rates differ first.
- Never take a constant from a two-point fit. An effect that moves between
  seatings is not a hardware constant. A prefix digest finds the first difference
  and nothing past it.
- Before reasoning from vendor source, confirm the file is in the tree that builds
  (the WLAN driver that builds is `rtl8192cd/`, not `rtl8192e/`). A driver whose
  decision needed vendor code leaves `docs/blind-write-ledger.md` § 4.1 — the
  drivers written blind — for a section of its own, and its diff is never called
  blind.
- Before designing an experiment on a `SPEC.md` row, read its 殘留: it may already
  say the experiment cannot succeed. Enumerate a config change's blast radius
  before making it.
- When a finding is retracted, fix every state and finding file that states it; a
  record keeps what it said, and the retraction is a new `LOG.md` entry.
- Make a recurring rule a tool refusal rather than a habit. Exempt a known defect
  by name — never by date or pattern — with a control that goes red when the
  exemption stops being needed, and sweep the exemption list both ways.
- Before adding a checker rule, measure what it would do to the corpus. Select
  dated entries by date, never by position, and test that the same entries in
  either order give the same verdict (`spec-check` `P21`). Accept a changed
  instrument only if it reproduces the old verdicts on the same population, and
  time a suite only beside the count of what it ran — a refusing suite is fast.
- A green suite is a claim about its controls; a mutation run is what tests them.
  Before trusting a mutation run, confirm the unmutated suite passes.
- Tools refuse with a reason, never a traceback. A pre-flight guard tests the real
  value, not a grep for a literal, and refuses before the port opens.

## Documents: state, record, finding

- **State** — `CLAUDE.md`, `README.md`, and in `PROGRESS.md` § Now, § Gate board,
  § Carried forward and the active gate's step list: what is true now. **Rewrite;
  never append.** A wrong line is fixed where it stands and the fix is recorded in
  `LOG.md`.
- **Record** — `LOG.md`; everything under `bench/` once committed; each
  `docs/GATE-RESULTS.md` entry; `docs/history/`; `CHANGELOG.md`; and, until `R1y`
  moves them out, `PROGRESS.md`'s closed step lists, § Session ladder and
  § Corrections. A record is never edited after the segment that wrote it; a
  correction is a new dated entry. The record of being wrong lives here.
- **Finding** — `SPEC.md` rows and the rest of `notes/` and `docs/`: the current
  value and where it came from. A superseded value keeps one line pointing at the
  file that owns the correction; the story of the correction lives there or in
  `LOG.md`.
- `tools/docsize.py` budgets `CLAUDE.md` and `PROGRESS.md` (whole file and § Now)
  in both directions: over a budget fails, and so does under half of one, so the
  commit that shrinks a document lowers its budget too. A budget changes only in a
  commit that says why.
- **Cite a row by its id** (`NET-102`, `P2-3`, `D5`), not by line number. A line
  number in a record resolves against the file as it was at the record's commit.
  `citecheck` checks line citations in every tracked `.md` except under `bench/`,
  `LOG.md`, `CHANGELOG.md` and `docs/history/`; `docs/GATE-RESULTS.md` is checked.
- Keep the line count above cited lines: new step lists go at the **end** of
  `PROGRESS.md`, new `SPEC.md` rows at the end of § 19, and a rewrite of § Now
  keeps its line count. An insertion or deletion that cannot be avoided — a § 17
  row is the usual one — is compensated in the same commit by joining or splitting
  a wrapped paragraph below it, and every cited line is asserted unchanged
  (`FW-110`).
- Text moved between files moves verbatim; `tools/docmove.py` proves it.
- One piece of state has one owner. Never copy here what another file owns: the
  active gate is `PROGRESS.md`'s; what depends on rlxfw's drivers is
  `docs/KNOWN-ISSUES.md`'s.
- `SPEC.md`: a value mark, a separate name mark and an owner link for every number.
  A finding lands in its owning file first and in `SPEC.md` in the same commit, and
  any number produced, changed or refuted changes `SPEC.md` in that commit. Check
  that a new id is unused before using it anywhere.
- Committed files are written for an engineer, never for a hiring panel: the
  finding, the artefact, stop — no résumé bullets, no "this proves I can X".
  English, except `LOG.md` and `SPEC.md`. Only `plan/` may address me. Commit
  messages say why; the diff says what.
- Every result states what it does not establish.
- Conventions for files that do not exist are not written here; they go in when
  the file appears.

## Never

| | |
|---|---|
| **write flash** | Mainline is zero-write through `R9`; a write needs my explicit yes. *Flash* below lists the commands that count |
| **touch `0x000000–0x005FFF` or `0x006000–0x007FFF`** | The loader — a brick is unrecoverable and there is no spare — and `H601`, this unit's MAC and radio calibration, which no reset restores |
| **let `H601`'s bytes, or their sha256, into this repository's tree** | Tracked or untracked. Naming the addresses is fine |
| **commit the datasheet, a flash dump or a vendor binary** | One is someone else's property; the others identify this device (`$FWRE_WORK/stage2.bin` is one) |
| **open `$FWRE_WORK/disclosure/`** | Unsent vulnerability reports, mode 600 |
| **move `upstream/`'s pin** | `4d3ff26`; `R9` depends on it |
| **build with `-march=mips32`** | The exposed load delay slot miscompiles silently, and `mflxc0`/`mtlxc0` — the LOPI interrupt-mask primitive — do not assemble there (`docs/interrupt-map.md` § 1.1). They are not `mfc3` |
| **write asm under `.set reorder`** | `.set noreorder`, and fill every delay slot yourself |
| **measure the ISA or a CPU hazard under Linux** | The kernel emulates `ll`/`sc`, and `sync` as a no-op; bare metal only (`CPU-47`) |
| **edit vendor source by hand, or inside `src-vendor/`** | Vendor code changes only through a reasoned row of `config/rlxfw-marks.tsv` (`rlxfw_mark("TAG");`, `rlxfw_markx("TAG", expr);`, `obj-y += NAME.o`, the mark include; the anchor must match exactly once) or a patch in `config/host-compat/`, applied by `rlxfw-kbuild.sh` to a **staged** tree. rlxfw's own kernel files live in `config/rlxfw-src/`, mirroring the staged layout. Re-apply with `apply --if-needed`; a partially applied tree is refused. After a build, run `rlxfw-marks verify`, which reads the artefact (`check` reads only the tree), and `kconfig-delta check` |
| **write `RLX5281`** | The core is `RLX4181` rev 1: `PRId 0x0000CD01` 量, the name 讀 from `arch/rlx/include/asm/cpu.h`; `RLX5281` is `0xdc01` and positively excluded. Quote `RLX4181` with its three weaknesses: one header copied three times, no code reads the table, and its encoding breaks for `0xdc01`/`0xdc02` |
| **run a vendor binary outside `tools/vendor-tripwire.sh`** | `--version` included, and from a scratch directory — never the repo root or `src-vendor/`. A census once deleted 2,580 tracked files |
| **keep binaries or vendor trees under `/mnt/c`** | DrvFs reports every file `777`, and NTFS case-folding drops 254 vendor files |

## Flash

- Commands that can write flash, each needing my explicit yes: `FLW`; `EW` and
  `EB`, which write any address with no bound check (`LDR-08`, `LDR-09`), the
  `AUTOBURN` word included; `AUTOBURN` with a non-zero value; and any upload
  before the `AUTOBURN` word at `0x8040D4A0` reads back `00000000` — the loader's
  echo is not evidence (`C-6`). `cardcheck` refuses the four verbs unless the
  card carries my dated `owner-yes` row for that exact payload; it reads only a
  single-quoted `--send`, never an upload (`FW-113`).
- Decide before power whether a seating issues any of them or any `FLR`, and close
  every seating record with that count, the `FLR` status and the bracket's reach.
- Never write *"not one flash byte is written"*: `FLS-26` proved it false for this
  device. Claim what was measured — commands issued, rlxfw's `n_writes`, the
  bracket's reach against the 2026-08-16 dump — and what it cannot see: two writes
  that cancel, and every byte outside the windows read.
- `FLR` only through `tools/flrbracket.py run`, never typed in a `--send`
  (`cardcheck` `A19`); it keeps every pre-read and every `H601` read-back outside
  this repository. Pre-read each destination: DRAM survives a power cycle
  (`MEM-17`), so a pre-read equal to flash voids the round, and the next round
  moves to RAM destinations no `FLR` has used.
- Render a flash window only through `tools/flashwin.py`, which decides what may
  be printed; new tools import `flashwin.overlaps_forbidden` rather than restate
  the rule. `flashwin scan` is the only check that no committed file holds `H601`
  bytes, and it runs only at the desk (*Closeout*).

## At the bench

- The console is a CP2102 at **38400 8N1**, driven through
  `tools/console-capture.py`. Power and physical actions wait for my word;
  everything else runs. List every question before power: one power cycle is the
  most expensive unit here. A timed action (press, then release) starts when I say
  so, in a window of at least 40 s, with the instrument recording the timing.
- Before `J 80500000`, read back the staged head: a reset re-stages that address
  from flash.
- A cell that jumps, or whose payload can reset the board, gets `--esc-after`, so
  the loader prompt is caught instead of the vendor firmware booting; prove the
  prompt was caught before handing the board to `looprun`.
- Reset with `busybox reboot -f`, a watchdog bite (`FW-37`); plain `reboot` signals
  PID 1, which is a shell script. Keep `CONFIG_RTL_WTDOG=n` in any image carrying
  rlxfw's `/dev/watchdog`.
- Name `bench/<date>/` for the day the captures are taken (`tools/capdate.py`), and
  stage every image the card uploads before power.
- Keep every cell inside the card's `cells` fence; before power
  `check-predictions` reads `0 of N` with N the card's own cell count. It checks
  that captures exist and are newer than the card, never their content.
- Predictions are written before power and re-derived from the card's own
  arithmetic — finish every subtraction and factor (one `cat` of a `/proc` file is
  two `read_proc` calls, `FW-64`). Every number sits in a `cardnum` row; every
  address comes from the image's own `System.map` (`cardcheck numbers`); a cell
  that only types `echo` carries no expectation; each cell's preconditions hold in
  its own state. Anything run beside the card is a declared off-card cell, and
  every claim the card makes has a cell. A control boot is kept apart from the
  boots a DoD counts.
- Never repair a frozen card, not even a typo: it destroys the mtime evidence.
  A change to how a frozen card is executed goes into a `CORRECTIONS-*.md`, with
  the alternatives rejected, before it is executed. To freeze: `git add` the card,
  run `spec-check`, then commit.
- Split a block into separate commands at the card's decision points, and
  recompute later windows when an early cell refutes a constant.
- Every capture has a terminator, and a `--send` is at most 127 characters.
  `--idle` must exceed the longest silence the payload can produce, a leading
  `sleep` included. When a duration cannot be predicted or a long silence is
  expected — a pending watchdog bite keeps the console silent until it bites
  (41.9 s at `OVSEL` 8) — use `--until PATTERN` with a `--seconds` cap. It reads
  on 0–50 ms, or ~150 ms after an `--esc-after` match; gate on no byte past it.
- `cardcheck` refuses any command not in the image's measured command table
  (`config/image-commands.tsv`): there is no `dd` and no `md5sum`. This image's
  `ping` ignores `-c`.
- Captures are CRLF: strip `\r` before comparing a parsed field. Gate on a `/proc`
  field, never a console mark — marks interleave with ash's echo (`FW-47`), and a
  refused write is echoed minus its last character (`FW-41`). Route a refused
  write through `cat` to see its errno. A bench gate self-tests on known captures
  and refuses to open the port if its own comparison is broken.
- Timing: a `.timing` row is written before its chunk, so byte `b` arrived at the
  **last** row with `offset <= b` (`FW-35`). Take rates from slopes, not
  intercepts. Never compare hex addresses numerically in `awk` (`8001e714` reads
  as scientific notation).
- The loader answers ARP, not ping; check its link with ARP. Retry a failed
  `looprun` with `--attempt N`, never `--force`. Identify a booted image by the
  tool comparing `RLXFW-ID0` with the build's digest, never by a typed value.
- A `read_proc_t` handler's output stays within one 4,096-byte page. Bump
  `console-capture`'s `tool_version` only when what it writes to the port changes.
- Wrong on purpose — do not "fix": `RTL819X_WDT_HZ` and the watchdog driver's
  `usec` table (76× off; `/proc` prints them and cards predict against them).
- Before a `biteraw`, send `kickms 5000` (`biteraw` does not clear `WDTCLR`). A
  reset-button hold meant to reach the vendor's timer is the boot's first hold over
  ~2 s (`FW-62`). Between LED or button episodes, clear the `REG-37` latch with
  `echo 0 > …/brightness`; pressing again does not clear it. My visual reports are
  data (`FW-63`).

## Environment

**USB and WSL**
- Start a long-lived WSL process before `usbipd attach`
  (`wsl -d Ubuntu-24.04 -- sleep 36000` in the background) and read what `attach`
  prints — it can fail with *there is no WSL 2 distribution running*. Re-read
  `usbipd list` for the busid every time; it moves.
- After every attach and before every seating, run the pre-flight: a 3-second
  capture with the board off. Judge it by its three artefacts and ~3.08 s, never
  its exit code (a healthy 0-byte run exits 1). *Could not open port* means the
  attach did not happen.
- Diagnose a CP2102 drop only while detached (`getportnames()` empty and
  `Get-PnpDevice -FriendlyName '*CP210*'` reading `Unknown`); while attached,
  check `/dev/ttyUSB0` and a command round trip. Right after a detach,
  `usbipd list` looks like a drop for about a second. The drops' cause is
  undetermined.
- An unprivileged ICMP socket is refused in this WSL (`ping_group_range`
  `1 0`, `FW-114`); a host probe drives the system `ping`.
- Session files never go in WSL's `/tmp`, which is emptied at every distro start;
  derived artefacts go under `$FWRE_WORK/rebuild/`.

**Shells, quoting, exit codes**
- The Bash tool is Git Bash: `-lc` strips `$VAR`, and a leading `/` in an argument
  is MSYS-translated. Keep every `wsl` argument slash-free (`bash`, not
  `/usr/bin/python3`), or launch from PowerShell.
- Git Bash's `grep` cannot see a CR: `grep -c $'\r'` matched every line of both
  an LF and a CRLF probe, and a literal CR matched neither (WSL's grep: 2 and 0).
  Count line endings from the bytes, or with `git ls-files --eol`.
- `wsl -d Ubuntu-24.04 -- bash -ls <<'EOF' … EOF` is safe only for bodies without a
  backslash: one quoted heredoc from the Bash tool loses a backslash level. Write
  anything else to a file with the Write tool and run it by path; never nest
  heredocs.
- Read an exit code only inside a script file run by path, with no pipe on that
  command (`${PIPESTATUS[0]}` when a pipe is unavoidable). Nothing goes after a
  backgrounded command whose status matters. A `tail`, a grep for `FAIL`, or a
  tool's own totals line is never its verdict.
- A step whose failure must stop the next is chained on one command line; a heredoc
  terminator ends the command. A step whose output must be read is its own call.
  Never `nohup … &` inside `wsl -- bash -lc`.
- Bench commands run `/usr/bin/python3`, never `python3` (in a login shell that is
  a venv without `pyserial`).
- Windows Python (`C:\Program Files\Python310\python.exe`, 3.10, cp950): call
  `sys.stdout.reconfigure(encoding="utf-8")` first and pass `encoding="utf-8"` to
  every `subprocess` capture. `spec-check.py`, and anything importing it, runs
  under WSL's 3.12; a tool that calls `gh` (`tools/citime.py`) runs under Windows
  Python.
- A `Monitor` command runs in Git Bash: spell paths `/c/Users/…`, and start by
  checking that its input exists.

**Files and git**
- Never `open(path, 'w')` before the content exists: build it, write `path.tmp`,
  then `os.replace`. A script that edits several files checks every anchor before
  its first write.
- Read `git status --porcelain` as its own call, then `git add` by name, then a
  plain `git commit`. Never a path-limited commit: on DrvFs it records `100644`.
- Every tool carries a shebang and is `100755`. Fix drift with
  `git update-index --chmod=+x`, and re-check after any `git restore --staged` of a
  file `HEAD` lacks; `tools/test-file-modes.sh` reads the index.
- `sudo apt-get install` needs `DEBIAN_FRONTEND=noninteractive`; `-y` alone hangs.

**PowerShell, gh, jq**
- `>` and `|` prepend a UTF-8 BOM, so read such output as `utf-8-sig`; `>` also
  turns LF into CRLF. `Get-Date -Format` eats letters inside literal text;
  `Get-Date -UFormat %s` is off by UTC+8 (use
  `[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()`). `Select-Object -Last N` buffers
  the whole pipeline, and `-First N` below the output's line count kills the
  process and fakes its exit code. Never inline `wsl -- bash -c "…$?…"`.
- `gh` exists only on Windows and `jq` only in WSL; `gh --jq` rejects `\(...)`.
  Write `--jq` and `--template` expressions without double quotes. Fetch a gist
  with `curl` in WSL when its bytes matter; `gh gist view --raw` prepends the
  description.

## Closeout

- Before stopping: rewrite `PROGRESS.md` § Now to the current state; append a dated
  `LOG.md` entry, desk-only days included; land every finding and number change in
  its owner file and in `SPEC.md` in the same commit.
- `git add -N` every new `.md` that will be tracked before running `spec-check`,
  which sweeps `git ls-files`.
- Run `spec-check`, `citecheck`, `cfcensus` (`--self-test`, `ratchet`, `check`),
  `ledgerscan check` and `quarantine`, `xcheck sweep`, `capdate`, `docsize`,
  `test-file-modes`, and `flashwin scan --dump` with this unit's dump — no CI job
  runs it. Take `citecheck`'s verdict after the commit (`0 suspended`); before it,
  re-derive every citation you touched. A burst of `C9`/`C10` is usually one
  unclosed backtick.
- Repair a citation by changing its digits only, after confirming the old token is
  on the old line and reading the new line back. A number that quotes a frozen card
  is never renumbered; no tool can see that, so read each line's prose before
  accepting an automatic repair.
- Run `tools/desk-sweep.py` over every declared step before closing, with `--dest`
  on ext4 under `$FWRE_WORK/rebuild/`, never under `/mnt/c` (~31 min). Targeted
  runs are no substitute. It parses `ci.yml` — never rebuild a step's command by
  hand, pass `--only` names exactly as declared, and read the ran count: a `--only`
  that selects nothing prints `0 ran` and exits 0, and a sweep's own count is not
  coverage. `census/merge the captures` and `census/census` are red at the desk by
  design; GitHub decides the census. Read a sweep's first lines before its summary,
  wait for a suite's exit code rather than its `.out`, and never compare the
  sweep's total with CI's wall clock. A 9p wait shows as idle, not `iowait`; count
  voluntary context switches instead.
- While a sweep runs, touch nothing in the source tree — no commit, no tool run
  (an import writes `.pyc`). If it ends with *SOURCE MOVED*, check what moved
  before trusting the green. The record is written after the sweep, so re-run the
  `.md`-subject checks on the final tree, chosen by
  `git diff --name-only <swept commit> HEAD`.
- After a seating, run every suite that can run here rather than
  `ci-census --only`: new captures move population cases (`test-boot-timeline.sh`
  `B2`). With `--only`, name every suite touched and `git grep`
  `tools/ci-expected.tsv` for stale counts. Test lines carry exactly two leading
  spaces; run the census locally before pushing a new tool. A red `text` job hides
  `census`, and a green run certifies only the layers that ran.
