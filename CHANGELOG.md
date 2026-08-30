# Changelog

🔴 **2026-08-29, later the same day: a kernel of mine boots on the device, to a
shell that answers, and pings.** `loudm` — 1,053,696 bytes, built by Realtek's
own wrapper pipeline, which the same day was shown to reproduce the vendor's own
shipped `nfjrom` byte for byte — was delivered to RAM over TFTP and entered from
the loader prompt. It printed all eleven of its boot marks, reached a shell that
returns output from a typed command, and exchanged four ICMP echoes with the
workstation, with the host's own packet capture holding both directions. On the
power cycle before it, a bare-metal payload of mine measured this die's
instruction cache by experiment — **16 KiB, 16-byte lines, two-way** — with the
controls that would have voided the number firing in both directions.

🔴 **No flash-write command of mine has ever been issued** — and as of
2026-08-30 this paragraph no longer says the other thing, because the other thing
was never measured. *(It read: "**Not one byte of mine has been written to this
device's flash**", in the most-read paragraph in the repository, while
`RUNSHEET` §B3's `G8b` row has said since 2026-08-24 that such a sentence needs a
full re-dump hashed against `FLS-14`.)* What IS measured is 512 bytes of a
4,194,304-byte part, unchanged across three kernel executions and two uploads on
2026-08-24 — and the seating that booted my own kernel ran no such bracket at
all, so it holds **less** flash evidence than that one did. 🟢 **2026-08-30: that bracket ran, both halves, and it is now a reading.** Three 256-byte windows over two power cycles — the loader head, the `cr6c` header, and **`H601`, this unit's MAC and radio calibration, which no bracket in this project had ever sampled** — all six reads byte-identical to the 2026-08-16 dump, and the first two windows also to the 2026-08-24 captures — 🔴 **`H601` has no 2026-08-24 comparand and never will, so its unobserved interval is 14 days, not 6** — with `AUTOBURN` read back as `00000001` on the second cycle so that the second half is a second observation rather than the operator's word for having cycled the power. **768 bytes of 4,194,304: 0.0183 %.** It is still not *"no byte was written"* — it cannot see two writes that cancel, and it reads 256 of `H601`'s 8,192. `H601`'s two captures are not in this repository and **not even their sha256 is published**, because a digest over a window whose only unknown is 24 bits of MAC is a 2^24 search; what is published is the verdict and the control that the same renderer reproduces two committed captures byte for byte.

And there is still no driver of mine: the ping went out through the vendor's own
network driver, in the vendor's own configuration.

> *Until 2026-08-29 23:09 this paragraph read: "**Nothing of mine has executed on
> the silicon**, and not one byte of mine has been written to this device's
> flash." Earlier the same day it read "**There is still no loadable image**",
> and until 2026-08-28 "**Nothing has been built.**" The flash clause has
> survived all four rewrites and is the one that matters.* 🔴 **And on
> 2026-08-30 it turned out to be the one sentence in it that had never been
> measured** — surviving four rewrites is not the same as being checked once.

Tags mark where the outside world can check the work, not where a feature landed.
`PROGRESS.md` is the only file that says where the work actually is.

---

## Unreleased

🔴 **2026-08-31 — desk, no power: the instrument that drove the flash bracket
had only ever been shown to refuse a CORRECT echo.**

The `FLR` command's first typed argument is the RAM destination and the loader
echoes `from <source> to <destination>` — the other order — so a card that swaps
them reads plausibly both ways. `RUNSHEET` §B3 makes *read the echo before typing
`Y`* a rule, and seating 7 turned it into a shell script. 量: that script
compared the flash source as typed, six hex digits, against the loader's echo,
zero-padded to eight; it rejected a correct echo, sent `N`, and got `Abort!`.
The failure was safe. **Nothing had ever shown it would refuse a WRONG echo,
which is the only reason it exists.**

`tools/flrbracket.py` is that rule as an instrument: a pure
`classify(reply, src, dst, nbytes, sent)` returning `PROCEED` / `ABORT` /
`REFUSE` — three outcomes and not two, because *the loader did not ask* must
send nothing and *the loader asked about something else* must send `N`. Its
corpus is hardware: the nine `FLR` echoes, eight replies to `Y` and one to `N`
that seating 7 recorded.

Three things it does that the script did not, each measured off that corpus
rather than reasoned: it compares the **length** field, which is the third typed
argument and went unchecked; it parses all three fields as **exactly eight hex
digits** and compares integers, which kills zero-padding, hex case and the
extra-digit boundary in one move; and it requires the echo to occur **exactly
once** after the operator's own typed line is stripped, because the first line of
a capture is the operator's bytes coming back and a classifier that searches it
reads its own input as the loader's confirmation — the defect class of
`d008372`, one tool over.

🔴 **The containment rule that a card template kept getting wrong is now
enforced by the tool, and the line is drawn at content rather than at mention.**
An `FLR` echo holds addresses and no flash bytes; the pre-read and the read-back
hold 256 each, and on 2026-08-31 the pre-read held this unit's MAC while the
card's own hypothesis said it would hold garbage. `run` refuses, before it opens
the port, to write either inside this repository for an `H601`-overlapping
window. Without `--go` it is a dry run that prints every `console-capture.py`
command it would issue, so the bracket can be rehearsed at the desk for no power
cycle — and 量, that rehearsal reproduces seating 7's own commands verbatim.

**50 controls, then 41 mutants.** `B0` is the first
case and is not a mutant — the unmutated tool must be green through the same
temp root or the run refuses to report kills — and every row names the case it
must turn red, counting as a kill only if that case failed. Both controls exist
because a pass over `flashwin` reported 8 of 8 killed with every kill invalid.
Of the three survivors, one was a real gap (`classify_abort` tests two strings
and only one had a case), one was **a control of the tool's own that could not
fail** (it searched stderr for `pre-read`, which the refusal's own explanatory
paragraph contains), and one was a defect in the mutant itself, reported as
`WRONG-CASE` rather than counted. 🔴 **Then an adversarial pass ran against it and found THIRTEEN live mutants and four controls that could not fail**, which is why the final numbers are 50 and 41 rather than 30 and 24. Two were safety defects in the tool: **the containment guard reasoned about `--src` while the pre-read's content is decided by `--dst`** -- so a non-forbidden window read into a RAM address an earlier cycle used for `H601` had a pre-read full of this unit's MAC and the guard never looked, which is the 2026-08-31 incident with the roles swapped -- and **`--bytes 0` walked straight past the containment test**, because `overlaps_forbidden` is half-open and `end > lo` is false for a zero-length window on the `H601` base. Both reproduced on the tool with `rc=0`. Four more were the four WIRE CONSTANTS: every negative fixture built its string out of the constant it was testing, so `CONFIRM = "(Y)es"`, `PROMPT = "<Real"`, `SUCCESS = "Successed"` and `ABORTED_MSG = "Abort"` all survived -- the `d008372` defect class inside the file written to prevent it. And **`P2` was a strict duplicate of `P1`'s first row**, unable to fail unless `P1` also did, while its comment claimed to test something `classify` cannot express.

🔴 **And `FW-34`'s open half is settled at the desk — the candidate `SPEC.md`
§17 named is the one that is wrong.** §17 said the byte-versus-word question was
worth a factor of 4 and was settleable from two disassemblies. It was, and it is
worth a factor of **1**: stage 1's copy loop at `0xBFC001BC` reads a 32-bit word
at a time, and so does the kernel's `memcpy`, eight of them per 32 bytes. What
replaces it was not on the list. **≤9×**: stage 1's loop executes at
`0xBFC001D0` — KSEG1, uncached by architecture — so its eight instruction
fetches per iteration are themselves reads of the SPI device it is copying from,
9 uncached word reads per 4 bytes against the kernel's 1. **4×**: stage 1 writes
`SFCR` zero times in 4,848 bytes while stage 2 writes it twice, so stage 1 runs
at the reset default `SPI_CLK_DIV = 111B` (DIV 16) and everything after runs at
the `001B` (DIV 4) that `REG-13` measured. 🟢 The same disassembly re-derives
**20,924** from two immediates, which is the first time this repository can show
where that number comes from rather than quote it. The product over-predicts the
measurement by 2.1–2.3×, and that gap is a term the model does not have: the
measured figure is `busybox wc`'s end-to-end rate and the model is of the bus
alone. One unknown is left — whether the window prefetches a sequential fetch
stream — and it has a cell that costs no power cycle.

🔴 **2026-08-31 — seating 7, two power cycles: the flash bracket got its
first negative control, and the card was refuted three times by being run.**

The bracket's claim has always been *these flash bytes are unchanged*, evidenced
by a `DW` of the destination after an `FLR` matching a rendering of the
2026-08-16 dump. **Nothing in that chain ever showed the `FLR` wrote anything** —
an `FLR` that silently did nothing, over RAM that happened to hold the right
bytes, produces an identical capture. Block 3 added a pre-read of every
destination.

* **Both rounds: 4 of 4 pre-reads differed, 4 of 4 read-backs matched the dump.**
  Four windows now, the fourth being `0x006400` — the canary page `FLS-21`
  measured moving under a `formWsc` POST. **1,024 of 4,194,304 bytes = 0.0244 %**;
  `H601` reach 3.1 % → **6.3 %**.
* 🟢 **One round ran after a complete rlxfw boot** — kernel, userspace,
  4,194,304 bytes through `mtd_read`, an `EACCES` write attempt, a ping. First
  evidence here that a full boot of this firmware leaves those windows unchanged.
* 🔴 **And on the second round the control FIRED.** All four of cycle 6's carded
  pre-reads came back *equal* to the flash expectations: **DRAM had retained
  cycle 5's contents across the power cycle** (`MEM-17`). Addresses nobody had
  written were still garbage, so it is retention, not a reset that did not
  happen. The bracket moved to fresh addresses; `X-ab` lost its claim to prove a
  cold boot (`REG-23`: every reset restores `AUTOBURN`, which says nothing about
  DRAM decay); and seating 6's second half, which reused its first half's
  destinations, now carries a **doubt — not a refutation**.

**Three things the card got wrong, all found by running it.**

* `M-b`/`M-c` returned `/bin/sh: wc: not found`. `wc` is one of busybox's fifty
  applets and **not one of the image's eleven declared symlinks**. *The applet
  table and the symlink set are different populations, and nothing compares a
  card's typed commands against the declaration of the image it uploads.*
  Recovered with `busybox wc` under a prediction block written first.
* `M-d` measured **78 bytes, not 73**: the device's shell prints argv[0] as
  `/bin/sh` where the qemu harness printed `sh`. Five characters, on every
  shell-error cell this project will write.
* The read rate was **~16×** the `CLK-15`-derived estimate — 0.92–1.01 MB/s
  against 59.8 KB/s — so the terminators were an order of magnitude too generous.

**What the changed cell bought.** `wc -c` was changed to `wc -lc` before the
first capture landed, because the card's *"not a content check"* was true about
digests and false about `wc`. It excluded a live alternative:
`rtl8196_map_copy_from` caps a copy at 1024 bytes and returns `void`, so a short
read reports success — **and a byte count cannot see it**. Which function is live
is `CONFIG_MTD_COMPLEX_MAPPINGS`, unset in all 31 built configs. H1 would have
given ≤1228 and ≤2007; **H0 came back four times** (`FW-34`).

**The safety property is now measured at two points**: `Permission denied` on
both `/dev/mtd0ro` and `/dev/mtd1ro` at zero flash bytes, and the even, writable
minor confirmed **absent** (`FW-30`).

🔴 **A containment rule was found to be conditional on its own experiment.** The
card writes `H601` **pre-reads** under `bench/` because a pre-read is *expected*
to be garbage; when retention made that false, two files in the repository held
this unit's MAC. Untracked, moved, nothing in history — and the template is still
wrong. Every `H601` capture now lands outside the repository, pre-read included.

**Wire census, three tools rather than one**: 75 `console-capture` sends, 12
rescue sends, 2 TFTP uploads — **89 operations, 0 flash-write commands**, with a
positive control showing the matcher fires on a synthetic `FLW`. ⚠️ That is *no
write command was issued*, which is still not *not one flash byte is written*.

🔴 **2026-08-30/31 — desk, no power: the instrument made a judgement, and
the adversarial pass showed its author had the value, the vendor and two
published counts all wrong.**

Yesterday `tools/leakscan.py` reported one distinct MAC on `FC:19:28` — described
as *TOTOLINK's OUI* — in seven files, four of them in a public repository, and
recorded the attribution as **undetermined** because `FW-17`'s SSID correlation
could not be run. Four measurements replace all of it:

* `FC:19:28` is **Actions Microelectronics**, IEEE MA-L, registered 2020-08-25 —
  not TOTOLINK.
* the value is **the workstation's own USB Ethernet adapter**: byte-identical to
  the `enx<12 hex>` interface name in nine tracked files, the source of the ICMP
  echo **replies** 4/4 in both committed host captures and of the requests 0/4.
* it occurs **0 times** in this unit's own 4 MiB flash dump — raw, byte-reversed
  and as ASCII in four forms — and its three-byte OUI occurs 0 times there and 0
  times in the vendor source.
* 🔴 the attribution was **never undetermined**. `FW-17`'s route was
  genuinely unavailable and it was never the only one: the arbiter is this unit's
  own dump, and it had been on the same disk for two weeks. The failure was
  stopping at the first check that could not be run.

**The defect underneath it is not about this MAC.** The pattern written to catch
this unit's address in bare hex is restricted to two OUIs and **neither is this
device's**, so it cannot fire on this device in any file — and it looked like it
was working because it fired on something else. The fix is not to add the right
OUI, which would write half the address into a committed file and would still be
a guess: `leakscan --attribute` asks the dump instead of the prefix.

**What the dump then said.** One `UNIT` classification in the whole corpus:
`upstream/BENCH-LOG.md:216`, six bytes that occur twice inside `H601`, labelled
as the device's, with the workstation adapter on the line above. **45 of
`H601`'s 146 non-zero bytes are recoverable from that public repository**; the
WPS PIN field and the region checksum are not. 🔴 The first version of
that coverage figure said **98.9 %** and was an artefact — `H601` is 8,046 zero
bytes out of 8,192, and the measurement's own positive control "passed" by
covering 8,042 bytes with an eight-byte slice.

**It is left in place, as a recorded decision**: the device is end of life, out
of service for years and reset since, and `upstream/` is a separate published
repository whose pin is load-bearing evidence here. `SPEC.md` `FLS-22` carries
the numbers and the reasoning is in `notes/leak-surface.md`.

**Instruments.** `leakscan` 6 → 17 controls and a mutation suite of 24 in three
phases — its first run had **eight survivors**, three of them defects in the
mutants and five real, including a `render` that printed the whole finding tuple
past a control that checked two string forms of the value and not its `repr`.
`flashwin` 19 → 24: a `normalise` subcommand, because a `DW` reply carries the
RAM destination in two places and so two reads of one flash window into different
addresses never compared equal — which is why the bracket's second half had to
reuse the first half's destination, and reusing it costs the control that would
show the read wrote anything at all.

**And the next seating's card is written**: 54 cells over two power cycles, with
a pre-read of every `FLR` destination, a fourth window over the only page of
`H601` this device has ever been seen to change, and the first device-side read
of that region through a path the kernel refuses to open for writing.


🔴 **2026-08-30 — desk, no power: the image that booted cannot be rebuilt from
its own recorded configuration, and the whole difference is a compiler flag no
committed file carries.**

The session set out to land three queued items on one kernel rebuild. It landed
them, and on the way it found that `quietm` — the image that ran on this silicon
on 2026-08-29, and that three `SPEC.md` rows are measured on — comes out
**16,780 bytes of `.text` smaller** when rebuilt today from its own
`.config-installed`, byte for byte, on the same host.

Everything that could have explained it was measured and did not: the pinned
drop is at `HEAD 5c9be5d9` with a clean worktree, **zero** ignored files and one
reflog entry from the clone; the two `.config-built` files differ on **zero**
lines; the compiled-file lists differ on **zero** lines (599 each); the marks log
differs on **zero** lines; and the symbol sets are identical in both directions.
A build at `-j4` and one at `-j8` produce the same `.text` to the byte, so the
`-j` race that this tree's header-rewriting Makefile invites is excluded rather
than assumed.

The difference is `-fno-if-conversion`, found by diffing the `.cmd` files kbuild
writes per object — all **746** of them, of which **588** differ and every one
differs in exactly that one way and in no other. That is `SPEC.md` `TC-25`: the flag that takes `hazlint` from
**seven load-use violations to zero** by removing 98.8 % of this gcc's
conditional moves — the codegen safety net Decision A's refutation condition
names. It reached the 2026-08-28 build as a flag typed at a shell. Three
committed files declare 36 kconfig symbols, 31 image entries and 15 source
insertions, each with a reason; this one was in none of them, and the build
driver recorded the `.config` it configured with and nothing about what it
compiled with.

**So a rebuild that followed every committed file in this repository produced a
kernel with seven load-use violations in it, and every gate here stayed green.**
Measured: `hazlint` on that build reports 7, every one a `movz` reading the
register a `lw` two instructions earlier writes.

`config/rlxfw-cflags` declares it now, `tools/rlxfw-kbuild.sh` reads it **before
the tree is staged** and refuses when no flag set is in force, `--no-cflags` is
the only way to ask for an empty one, and the effective value is written beside
`<cell>.config-built`. Where the guard sits is part of the claim: four of
`tools/test-kbuild-cflags.sh`'s five cases need no vendor material because a
refusal that costs a 480 MB copy first is a refusal nobody exercises. 🔴 The
first version of the guard could not tell `--cflags-kernel ""` from the flag
being absent, so the one request the file exists to refuse fell through to the
declaration — caught by the guard's own `C2` on its first run, and it is the same
distinction `console-capture`'s `N20` pins one tool over.

**What the rebuild was for, and it all landed.** `CONFIG_MTD_CHAR=y`, with
`(NEW)` predicted at 0 and measured at 0, one differing symbol line, and the
artefact control firing: five mtdchar symbols where there were none, against six
mtdblock symbols that did not move. The image now declares **only odd MTD
minors** — `/dev/mtd0ro` and `/dev/mtd1ro` — so there is no node in it through
which the kernel would let anything write flash, and `/dev/mtdblock1` is
withdrawn. That was an argument in a comment until today; it is a check now
(`mkinitramfs` `A24`/`A25`/`A26`, with two mutations in `test-config-gates`), and
its control is complete rather than partial: `mknod` is not among this
`busybox`'s fifty applets, so the declared set is the only set of device nodes
this image can ever hold.

`mkinitramfs verify` reads the **artefact**: the `.init.ramfs` section out of the
built `vmlinux`, the newc cpio parsed, every entry compared to the declaration by
path, kind, mode and dev numbers. 🔴 The obvious implementation is wrong and it
was measured rather than feared — the first `070701` in `quietm.vmlinux.elf` is
363,784 bytes *before* `.init.ramfs`, inside the kernel's own string data, right
next to `no cpio magic`. 🔴 And its negative control refuted the prediction
written for it: the 2026-08-28 image fails with **two** missing nodes, not the
three predicted, because removing a node from a declaration produces no
difference in an artefact that never had it. A change to the document counted as
a difference in the image — which is the confusion the tool exists to stop.

The `.text` of the corrected build was predicted at **2,449,180** by adding three
separately measured deltas and came out **2,449,212** — 32 bytes, 0.001 %. The
prediction beside it was refuted in its second half: a bound on bytes was carried
into a bound on a percentage whose denominator it never named.

🔴 **And the leak gate scans 240 of the 898 files this repository tracks** — which
`bench/README.md` had already said, earlier the same day, along with the fact
that `upstream/BENCH-LOG.md` prints actual `H601` byte values and a digest over the
4 KiB at flash `0x6000`. What is new is the scan run over the gap, not the gap. The
CI step globs `bench/**/*.log`. The 658 tracked files it never reads — plus `upstream/`'s 302, which `git ls-files`
cannot see at all, for 960 unread in total — hold **100**
identity-pattern hits — 92 once the scanner's own eight control literals come out,
🔄 **Corrected the same day (fourteenth session): both numbers are wrong.** 量 on a clean
HEAD it is **99**, not 100, and the scanner's own literals are **10**, not 8 — `leakscan.py`'s
own two were missed because it was written that day — so the prose figure is **89**. And
`FC:19:28` is **Actions Microelectronics**, not TOTOLINK; the value is the workstation's USB
adapter. `notes/leak-surface.md`, `SPEC.md` `FLS-22`.
and 28 of them inside `bench/` itself: two in the prediction cards and 26 in the
two host-side packet captures, which are `.txt` and so are outside a gate named
for that directory. `upstream/` is invisible by
construction: it is a submodule, `git ls-files` returns one line for it, and
every sweep built on that has read **zero** of its 302 files. 量, counts only,
with no value printed anywhere: exactly one MAC on this model's vendor OUI exists
in the corpus, in seven files, four of them in a repository that is public — while
`SPEC.md` §18's first sentence is that nothing identifying this unit is here.
Whether that address is this unit's is **undetermined**: the check that would
settle it needs a default-SSID string, and there are zero of them in either
repository. `tools/leakscan.py` is new, imports the existing patterns rather than
copying them, and never prints what matched. Only its self-test is in CI: turning
the verdict into a gate needs an allowlist entry per surviving hit, and
allowlisting a possible real leak to get a green build is the wrong order.

🔴 **And CI went red on the suite this session added, on a class the machine
the push happens from cannot see.** `ci-census` counts a printed `skip` only
when its label appears in `tools/ci-expected.tsv`'s allowed-skip column; the
column said `C1 the GPL drop` while the suite prints `C1 the declared flags
reach the build`, so the case vanished with neither a FAIL nor a skip line and
the build died on arithmetic that never named the label. On this machine
`$FWRE_WORK` holds the GPL drop, so that case **runs**, prints no skip line,
and its label is never compared — the suite was **9/9 green here while CI was
red**. That is the **second consecutive day** CI has caught something the local
pre-push procedure could not, and the third distinct blindness recorded in that
procedure this week. The fix is a case rather than care: `C7` reads the table,
which is the only check that works in both configurations, and the label is now
one shell variable used three times. Verified in the configuration that failed —
the step the first pass skipped.

🔴 **2026-08-30 — desk, no power: forty green cases, and ten mutants of the
guard they had just been written for were alive.**
`tools/console-capture.py` — the one instrument every capture at the bench runs
through — gained a refusal for a capture with no terminator, and its suite went
29 → 40, all green. A mutation pass over **25** edits of that guard killed
fifteen of them. The ten survivors fall into four classes, and not one of the
forty cases could see a *class* — only an instance of one:

* a **waiver**: an early `return` on any flag the cases leave at default.
  `if args.esc > 0: return` in front of the guard passes all forty — and
  `--esc 25` is the shape of the capture this project takes at the start of every
  seating. Measured on a pty, that mutant with no terminator does not return:
  killed after 8 s, log written, metadata lost. Which is the failure the guard
  was added for, back.
* the **contract**: not one of the forty asserted an exit code, so a refusal that
  exits *successfully* was green — and a card written `cmd || abort` would read
  it as a success. None of them looked at stdout either, so a refusal printed
  there instead of on stderr was green too, and a card written `cmd > log` would
  have swallowed it into the log.
* the **message**: checked by one substring, so a refusal naming a flag that does
  not exist passed.
* the **position**: the guard moved below the overwrite refusal passed, which
  also inverts which error an operator sees first — told the file exists, they
  pass `--force` and hit the loop that does not return.

Six new cases close all four, 40 → **46**. One of them corrected a claim this
repository had been making about itself: the case that supposedly pinned the
guard's position *"from one command"* sends a 127-character line, a length the
validator **accepts**, so it passed whether or not the guard sat in the right
place. That side had been held by three other cases happening to carry no
terminator — coverage by accident. And *"ten survived"* is no longer a sentence
in a log that nothing re-runs: the 25 mutants are a committed suite that runs the
whole file per mutant, refuses if the unmutated baseline is not green, and
reports a mutation whose anchor has moved as a **survivor** rather than skipping
it. 25 of 25 killed.

### A checker that was about one file, pointed at all seventy-one

`spec-check`'s cell-count check had been about `SPEC.md`. Pointed at every
tracked `.md` — 71 files, 620 tables, ~43,000 code spans — its first run found
**eight** broken rows where the census behind it had said six; that census had
looked at three files. Generalising it exposed three shapes it could not see at
all, each found by turning the previous one on:

* a row split over more than one physical line. Markdown has no continuation
  syntax, so a literal newline inside a code span ends the row there — and every
  checker here walked lines beginning with a pipe, so the continuation was
  invisible **and every row below it in the same table vanished from the count**.
* a pipe-line belonging to no table, which the cell-count check cannot see by
  construction, since it walks tables and a stranded row is in none. **Nine rows
  of the findings page** — the page a reader is pointed at, including its three
  newest entries — were stranded by a single blank line and rendering as
  paragraphs full of pipes. The same defect was recorded against `SPEC.md` three
  days earlier and found then by a human review; this time a checker found it.
* a code span whose whole content is whitespace, which is what `\r` and `\n`
  become when typed as real characters.

**One of those three had made a reading wrong, not a rendering.**
`docs/loader-command-semantics.md` annotated **both** exits of the loader's
line-reader with the same empty character, so its own sentence *"only one writes
a terminator"* named neither. Settled by disassembling this unit's loader: the
NUL sits in the delay slot of the carriage-return path's jump, and the line-feed
path returns without one. All ten defects fixed; the checker caught the entry
written about it, on the way in.

### The device node this project was about to declare cannot exist

`R3-9` planned a second path to the flash — a device node, and a size read
through this project's own MTD stack. Measured before the line was written, by
two routes with a positive control on each: the character-device driver is not
compiled into either built image, so the node would open `No such device`. **And
the obvious substitution is the one node this project must not create**: it
addresses the flash partition that contains the bootloader and the per-unit
region a factory reset does not restore, the block driver has a write path, and
a read-only mode bit is not a control because root ignores it. The node declared
instead addresses the other partition, runs the identical read path, buys the
identical reading, and leaves **no writable node over either region that cannot
be undone**. The control is the absence of a node, not the mode bits.

The size it predicts was wrong in its first draft by a subtraction error, and the
second source is what caught it — which is what the two-source rule is for.

### And a card's pre-flight had gone stale under it

The next seating's card asks the operator to run one tool before power and
expects `13 passed`. That tool was rewritten to print `19` **in the same session
that wrote the card**, and nothing re-read the pre-flight. A stale expectation on
the first line of a pre-flight is the one place a mismatch reads as *wrong
version, stop* — with the board in the operator's hand. Corrected, with both
numbers measured. `bench/README.md` also gained sections for the four
directories the index had skipped, which is where the only flash evidence this
project has lives; writing them found that the paragraph deferring the work had
guessed two numbers wrong, and that of the *"three kernel executions"* the flash
bracket spans, **only two are captures** — the third is an inference, and the
capture that would have held it expires at the bootloader banner.

🔴 **2026-08-30 — desk, no power: the next seating's two cards, and the flash
question stops being one this project can only argue about.**
`bench/2026-08-30c/PREDICTIONS-B5-block2.md` is 31 cells across **two** power
cycles — `quietm` plus the first round of an `FLR` bracket, then a ninety-second
cycle that is nothing but the second round. `0 of 31` at the desk, which is the
correct answer before a seating.

### The sentence this repository forbids was in the card's own header, and in this file's first paragraph

`RUNSHEET` §B3's `G8b` row has said since 2026-08-24 that two 256-byte flash
reads entitle a write-up to *"the loader head and the `cr6c` header are
unchanged"* and **not** to *"zero flash bytes written"*. §B5's card header said
`Flash bytes written: 0.` `bench/README.md` said it in **five** per-seating
headings, and 量 — **not one of those five seatings ran an `FLR` bracket.** This
file's opening paragraph said *"not one byte of mine has been written to this
device's flash"*, in the most-read place in the repository. All of them are
corrected in place with the originals kept.

🔴 **And `H601` — the one region a wrong write cannot be undone in — has never
been in the bracket at all.** 量: `G8a`/`G8b` sample 256 of the loader region's
24,576 bytes, 256 bytes of the `cr6c` header (which no rule forbids writing), and
**0 of `H601`'s 8,192**. Six days of write-ups said *"the two regions that would
change"* and neither of them was the one that cannot change back.

### `tools/flashwin.py` — an instrument for a reading that can never be published

`H601`'s bytes are this unit's MAC and radio calibration, so its capture cannot
be committed and **not even its sha256 can**: with the rest of a 256-byte window
known, a digest is a 2^24 search for the address. So the expectation is computed
at the desk from this unit's own 4 MiB dump, and **the control is what is
public**: the same renderer must reproduce `bench/2026-08-24d/G8a-rd0.log` and
`G8a-rd6.log` byte for byte. 量 — both do, 777 bytes each, and the two committed
dumps are byte-identical over all 4,194,304 bytes. Thirteen controls; ten of
them, including the publication guard driven as a subprocess in all three
directions, run on a stock runner.

### `console-capture.py` refuses a capture that cannot end, and records what ended it

Both halves of the defect found before power on 2026-08-29 are closed. 🔴 **Where
the guard sits was measured and the obvious answer is wrong**: of the four
terminator-less invocations in the suite, only **one** reaches it — the other
three are refused by `_check_send` first — so `P4` gains `--seconds 1` and `N21`
was described as pinning the guard's position from both sides with one command.
🔴 **It does not, and the entry above this one says so**: `N21` sends 127
characters, a length the validator accepts, so it passes whether or not the guard
sits in the right place. Left here as written, with the correction beside it.
`test-console-capture` 29 → **40**, nine of the eleven new cases controls.
`TOOL_VERSION` deliberately did not move: it owns what went out on the wire, and
the presence of the `seconds` key is what dates a capture instead.

### Three counts that were wrong, and a directory nothing ignored

- **The `A-catch` census's population is a filename.** 量: eleven files match,
  one of them is not a `console-capture.py` output at all (no `.meta.json`; an
  interactive transcript), and two more predate `tool_version`. The last two
  write-ups said nine and eight.
- **`bench/README.md` has nine sections for fourteen directories**, and the five
  with none include the whole of `R0` — where the only flash evidence lives.
- **`PROGRESS.md`'s § Now recorded the eighth segment twice**, and the copy that
  was dropped still pointed at *"the Active step row"* for its details.
- **`ci-out/` had never been in `.gitignore`**, and the pre-push census
  `CLAUDE.md` mandates is what creates it. `test-gitignore` 18 → **21**, because
  one ignore line is not one claim.

🔴 **And that pre-push census immediately earned its keep**: `flashwin`'s skip
label did not match the table, `ci-census` read `UNEXPECTED-SKIP` and
`10+0+0 != 13`, and the build would have gone red for the third time in three
sessions. Fixed before the push; the census closes at **455**.

`SPEC.md` `FLS-14` gains its reproducibility and its cross-path agreement;
`FW-26` (this unit's busybox has no applet that can digest a stream, so the flash
cannot be cross-read from its own userspace) and `FW-27` (**my kernel reaches a
shell in 8.98 s, 2.9× faster than this unit's own**) are new.
`notes/kernel-build.md` §17 owns what `quietm` can and cannot print — including
that a **panic is still visible with `CONFIG_PRINTK=n`**, 量 in the built
`vmlinux`'s symbol table, so silence there is a hang rather than a suppressed
panic.

### The adversarial pass, and the instrument half of it is the expensive one

Three hostile readers. The card gave up sixteen items, two of which would have
cost bench time: **`$FWRE_WORK` is empty in every shell on this host**, so the
card's `--out $FWRE_WORK/…` expanded to `/rebuild/…` and produced an uncaught
`PermissionError` *after* the `H601` read had been spent (every path on the card
is literal now); and **§7.3 printed the sentence `SPEC.md` `LDR-39` explicitly
rejects** — *"exactly 1,027,072 bytes and not one more"* — where the pair
actually brackets `[n, n+16)`. A third put `MAP-17` and the mark 量 on a value
this repository has twice written up as being neither.

🔴 **And the mutation pass is the one that changed the most.** It ran **45
mutants against the two instruments and 24 survived**; three of them printed this
unit's MAC — the rendering written to stdout on the refusal path, the withheld
digest printed beside the word *withheld*, and the dump never opened at all. The
common cause was one sentence: every case that could leak used **one argument
triple against an all-zero dump**, and `R1`/`R2` called the renderer in process,
so nothing between *open the file* and *format the words* had a control over it.
`flashwin`'s self-test is rebuilt — 13 → **19**, every leak-capable case drives
the real command line and asserts stdout is **empty**, `R1`/`R2` go through
`--out` and `cmp` — and **22 of 22 of the surviving mutants are now killed**.
`console-capture`'s equivalent nine are carried forward rather than half-fixed:
the sharpest is that the guard can be waived by any flag its four cases leave at
default, and `--esc 25` is `A-catch`'s own shape.

**Zero flash bytes, zero power cycles, zero device readings — and today that
sentence is legitimate, because the board was never plugged in.** That is the
distinction the rest of this entry is about.

---

**`R1h-3` + `R3-8a`, 2026-08-29 — the first seating of `R3`. `probe3` measured the
I-cache, then a kernel of mine booted to a shell and pinged.** Two power cycles, 26
captured cells, and **no flash-write command issued** — 🔴 **which is not the same
as "zero flash bytes", a sentence `RUNSHEET`'s own `G8b` row forbids without a full
re-dump, and this seating ran no `FLR` bracket at all.** The flash-byte count is
**unmeasured**. Both prediction blocks pass their own gate — `13 of 13`
and `12 of 12` — and `--sweep bench` reads 39 files, 181 cells, 161 ordered, 0 out of order.
`SPEC.md` `CPU-25`/`CPU-44`/`CPU-45`/`CPU-19`/`CPU-46`/`LDR-40`/`NET-13`/`REG-07`/`TC-36`
move and `LDR-41` is new; `tools/rbcheck.py` is new.

### All five of `R3`'s DoD rows are met, and the anti-DoD fired positively

- 🔴 **D1–D5.** `loudm` entered at `0x80500000`, printed all eleven boot marks and M4,
  reached a shell that returns output from a typed command, and got 4/4 ICMP replies with
  the host's own capture holding request **and** reply.
- 🔴 **The anti-DoD is satisfied by three independent discriminators, not by absence.**
  `PROGRESS.md` has said since the gate opened that a banner proves nothing, because the
  loader re-stages `0x80500000` on a watchdog reset. What fired: the entry address out of
  the image's own header (`start address: 0x80003600`; the vendor's staged image is
  `0x80003440`), a string that exists only in my tree (`RLXFW-B00`), and my build stamp
  (`Linux version 2.6.30.9 (key@K) … #1 Fri Aug 28 23:37:47 CST 2026`).
- **`PRId` was read three times through three paths in one seating** — `RLXFW-B02=0000CD01`
  upper case, `CPU revision is: 0000cd01` lower case, and `/proc/cpuinfo`'s
  `cpu model : 52481` in decimal. Three formatters, one register.

### The cache geometry is a measurement now, and the kernel's own number is not

- 🔴 **16 KiB, 16-byte lines, 2-way, 512 sets**, and **both** of 否證 ⓐ's controls fired:
  every victim STALE at 1/2/4/8 KiB (the walk cannot evict below the cache) and every victim
  FRESH at 32/64 KiB (it can evict at all). The 16 KiB point reproduced inside the seating.
  The three numbers are one structure — `T = 8192` is exactly a two-way 16 KiB cache's way
  size — rather than three quotable readings.
- 🔴 **The kernel's `icache: 16kB/16B, dcache: 8kB/16B` line is a printed build constant.**
  Every value is a `#define` in `arch/rlx/bsp/bspcpu.h:12-22`, used in `#if` preprocessor
  conditionals elsewhere in the same file. **This is the trap `R1h-4`'s DoD names by name.**
  They agree, and that is corroboration rather than one number — and the same line carries
  `dcache: 8kB`, for which no measurement exists at all, because Group V never ran.

### Two answers the emulator would have given backwards

- 🔴 **CP3 is reachable on this die**: all eight `mfc3` stubs executed, `m.traps=00000000`,
  `m.cause` still poison. On qemu all eight trap. No reading equals its own prime and
  `v1 == v2` for all eight, which is the pair of failures the two primes exist to separate.
- 🔴 **This core retires the `cache` instruction** — four ops, no traps — **while `x ri`
  traps in the same run under the same handler**. Without that control, *no trap* and *the
  handler is broken* would be one observation. ⚠️ Retires is not invalidates:
  `x.c10.treated` and `x.c10.twin` are both 1.

### What the seating found wrong with its own instructions

- 🔴 **`console-capture.py` with neither `--seconds` nor `--idle` never returns** — both
  default to `0.0` and the read loop breaks on neither (`rc=124` under `timeout -s TERM 8`).
  **Twelve of `RUNSHEET` §B5's thirteen card rows omit it**, and block 0 omits it on `Q-A`,
  while all eight committed `A-catch` captures passed it. Found at the desk, before power.
- 🔴 **Block 0's cross-check table pairs `tmpl` with the wrong word.** The UART prints the
  guard word and the block's word 19 holds the template address; the guard word is at word
  20. With that corrected the two channels agree **25 of 25**. The mechanical check that was
  run — *every header word is written somewhere* — cannot catch a UART line and a block word
  sharing a name while carrying different quantities.
- 🔴 **`G0`'s pointer-shape refutation fires on noise**: 63.6 % on 64 words of random data as
  quoted verbatim, 22.2 % under the *aligned* reading. First run was this seating.
- 🔴 **Decision B's stated premise is false, and it is a safety statement.** *"An initramfs
  boot never instantiates an MTD partition map"* — this boot created two, and the first spans
  `0x000000–0x130000`, which **contains both regions `CLAUDE.md` forbids**. Nothing was
  written; the decision stands on its other three legs; the margin it claimed was not there.
- **`A-catch`'s `^[` prefix rule watches for the wrong bytes.** The loader echoes raw `0x1B`
  (量 twice, 81,457 and 117 bytes); `^[` is a Linux tty. The rule would not have fired on the
  case it names, and corrected it says *which* of the two was answering.

### What did not close, said plainly

- **ⓑ / `CPU-45`.** `c-A` came back negative and the payload's own interlock voided Group V.
  That is a pre-written branch behaving correctly, not a failure; the stop-loss allows a
  second seating and this was the first.
- **`w-imem`.** `m-imem` returned a base and **no top**, so a base is not a window and the
  16 KiB still cannot be separated from the 16 KiB scratchpad **by size**. Associativity is
  not exposed to that confound, because a scratchpad has no sets.
- **`quietm`.** Power cycle 3 was not spent. `L-3` reaching D4 selects it, and its prediction
  block is deliberately unwritten — writing predictions for an experiment whose contents a
  result decides is writing a prediction that cannot be refuted.


**`R3-7`, 2026-08-29 — the seating sheet becomes a card, and computing every value on it
rather than transcribing it refuted eleven things the sheet asserted.** `RUNSHEET` §B5 gains
the card and §B5-c1…c12; `notes/kernel-build.md` §12 is new and fills a section number that
never existed; `SPEC.md` `LDR-38`/`LDR-39`/`TC-36`/`FW-25` are new and `LDR-26`/`TC-30` are
corrected. **Zero flash bytes, zero power cycles, zero device readings.**

### The cell that checked whether the upload landed could not fail

- 🔴 **`K2`'s head read is byte-identical between my image and the staged vendor one.** 量, three
  device captures across two power cycles — `bench/2026-08-23/B.log:16`, `2026-08-24c/G1a.log`,
  `2026-08-24d/G5-rb1.log` — against all five `nfjrom` files this project can build: the same four
  words, because every image in the family is linked from the same `rtkload` `start.o`. The row
  rested on its own sentence *"my image and the staged one differ in their first 16 bytes (量 at
  the desk)"*; that 量 was finally taken and it says the opposite.
- **What discriminates is the `lui`/`addiu` pair at `0x80500018`**, which the linker fills with
  `__vmlinux_end`: `26101400` = `loudm`, `2610AC00` = the `quiet` pair, `26101000` = **either**
  `loud` **or** the staged vendor image — only the `lui` separates those two, so both words are
  read. `0x80500000 + size` reproduces the four `nfjrom` rows exactly; the staged one is
  `base + size − 2`, and the 2 is `LDR-18`'s checksum (`FW-12` already carried the decomposition).
- 🔴 **The tail is the only part of the upload that admits a before/after pair.** It is 39,918
  bytes (`quietm`) / 66,542 (`loudm`) above the staged image's end, so it can be read before the
  transfer with nothing written and no fallback destroyed. One `DW … 8` gets a positive control
  (the last line must **become** zero) and a negative one (the first line past `image_end` must
  **not move**) — and the coherence control for the pair was already in the tree, unquoted:
  `bench/2026-08-24d`'s `G5-pv1` → `put` → `G5-rb1`.

### `nfjrom` does not force `0x80000000`. `boot.img` does

- 🔴 **`SPEC.md` held two rows for one mechanism and they disagreed.** `LDR-26` said both names
  force the load address; `LDR-37`, eleven rows below, and `docs/FINDINGS.md` both say `boot.img`
  writes it. 讀 this unit's own `stage2.bin` at `0x80401208`: a `nfjrom` match sets
  `0x8040D390 = 1` and **branches past the `boot.img` test entirely**.
- **The correction runs toward the danger.** With `nfjrom` as the TFTP filename the loader jumps to
  the address already set — `0x80500000`, the right one — so the accident resembles a successful
  boot and silently costs the `J` line, the `AUTOBURN` timing and all of `K2`. ⚠️ It is
  **distinguishable**: 量, `Jump to 0x%x` is referenced only from the auto-execute branch and
  `---Jump to address=%X` only from the `J` handler. Disjoint.
- ⚠️ **Two routines, opposite polarity**: `nfjrom` goes through `strstr` (match = `v0 ≠ 0`),
  `boot.img` through `strcmp` (match = `v0 = 0`), so `boot.img` is exact-match and *containing*
  is over-broad. And the guard is on `loader-tftp.py`'s `--filename`, not on the local path.
- 🔴 **Provenance cuts against this project**: upstream never made the error — its own comment says
  *"and `boot.img` **additionally** forces the load address"*. rlxfw introduced it while
  summarising, so there is **one** independent reading, not two.

### `uname` is not an applet, and the fix written for it earlier would not have worked

- 量, this unit's own `busybox` under `qemu-mips-static`: `busybox uname -a` → **`uname: applet not
  found`**. The binary lists **50** applets and `uname` is the only one of the fourteen this seating
  needs that is absent. Both controls are in the same run.
- 🔴 `notes/kernel-build.md` §9 records a `/bin/uname` symlink added for `K5` and then removed —
  **three passes and none asked whether the applet exists.** `K5` reads `/proc/version`, which
  prints `linux_banner` verbatim and carries `(user@host)` and the gcc version that `uname -a`
  drops. `notes/rootfs-census.md` gains the applet list; `SPEC.md` `FW-25`.

### Four more that only the adversarial pass found

- 🔴 **The card numbered words 1-based in one row and 0-based in a stop-if three rows later**, so a
  correctly landed `loudm` would have been aborted. Every stop-if names an **address** now. This is
  the only item of the eleven that could have cost a power cycle.
- 🔴 **`check-predictions.py --sweep` cannot be a CI gate: git does not store mtimes.** A step was
  written and removed the same hour — on a fresh `git clone --depth 1` the sweep reads **128 of 156
  cells as out of order**, 量 twice. The ordering claim is a pre-push gate on the machine that took
  the captures and proves nothing to anyone who clones this repository, which is a harder limit than
  the docstring's *"not a cryptographic timestamp"*.
- 🔴 **The tool's `--self-test` printed six `ok` lines without counting what ran**, and a mutation
  pass killed only **7 of 15** mutants — including one that made the sweep return 0 on a real
  regression. Controls 4 → **15**, four of them driving the file as a subprocess to assert its exit
  code, `run_controls` counting what ran. **11 of 11 killed.**
- 🔴 **The netdev plan was made from the *vendor's* kernel.** 量 on the artefact this seating
  uploads: **six** netdevs, not five, and the registration line calls one of them `eth5` while
  `ifconfig -a` calls it `eth7`. Four of the five candidates are LAN, so trying two and calling D5
  refuted would have been a false refutation on a cable in any of three jacks.

### Also

- `K6`/`K7` gave the board **the workstation's own address** (`10.1.1.2`, 讀 §G3) and pinged the
  loader's. Board `10.1.1.10` → host `10.1.1.2`, and `arp` in the `tcpdump` filter, which is the
  one word that separates *ARP never resolved* from *the driver does not transmit*.
- `P6`/`P10`'s two vendor artefacts are **one kernel in two forms** (量: `vmlinux-rederived.bin` is
  `r0-vendor-kernel.bin` decompressed, byte-identical), and the compressed leg cannot fail —
  **my own uploaded `nfjrom` reads `RLXFW` 0 times too**.
- `/proc/cpuinfo` under my kernel prints **six** fields where this unit's shipped kernel prints
  seven: the format string `hardware watchpoint\t: %s` is in its image and occurs **zero** times in
  either of mine. A free discriminator and a second data point of `TC-17`'s shape (`TC-36`).
- `bench/2026-08-30b/PREDICTIONS-B5-block1.md` is written and frozen — twelve cells, `0 of 12` at
  the desk, which is control `N2` firing on every capture that is still in the future.

---

**`R3-2` stages 3–6, `P2` and `P3`, 2026-08-29 — the pipeline reproduces Realtek's own `nfjrom`
byte for byte, and the boot ladder prints at the desk.** `notes/kernel-build.md` §13, §14 and §15
are new; §2.1, §3.3, §3.4, §5, §11.1 and §11.7 are corrected.

### The image: the control is the vendor's own artefact, and it holds

- 🔴 **`nfjrom` rebuilt from the drop's own `vmlinux.elf` is byte-identical to the one the drop
  ships** — 854,016 bytes, sha256 `5cc8d61d4b4e8914`. So is `vmlinux-stripped` and so is
  `vmlinux_img`. That turns four assumptions into readings at once: which of the two shipped LZMA
  binaries the wrapper selects, the 8-byte `cvimg vmlinuxhdr` prefix, and that the loader stub built
  with `rsdk-1.3.6-4181` produces the same **loaded** bytes as the vendor's.
- **`memload-full` differs by 492 bytes and every one is DWARF.** Ten `.debug_info` sections at +43
  each — the length difference between the two `DW_AT_comp_dir` strings, 101 characters against 58 —
  two `.debug_line` tables at +32, and 2 bytes of section alignment. No allocated section differs in
  address or size.
- 🔴 **`linux.bin` differs by one byte, the signature — `cr6b` against `cr6c` — and supplying the
  right one closes it.** 量: `cvimg signature nfjrom out 0x80500000 0x30000 cr6c` produces a file
  **byte-identical to the shipped `linux.bin`**, so the pipeline reproduces **five of five**
  artefacts and only `memload-full`'s DWARF differs. *(The first write-up of this said the tool
  **cannot** emit `cr6c`; the adversarial pass refuted it with one command, and the refutation is
  the better result.)* What survives: the Makefile's own `CV_OPTION` picks `linux-ro` for this
  board and `linux-ro` writes `cr6b`, **so the shipped `linux.bin` was not built by this Makefile
  path with this configuration**. For `R9` that is one argument, not a blocker — the rule is not
  to take the signature from the option logic without reading what came out.
- **Four images end to end**: `nfjrom` 1,027,072 (`quiet`, `quietm`), 1,052,672 (`loud`), 1,053,696
  (`loudm`), each round-tripping byte-identically, each `kernelStartAddr` `0x80003600`, 66.2 % and
  67.6 % of the 5,242,880-byte ceiling. Realtek's own `cvimg size_chk` prints the same two margins —
  an independent second source for the ceiling correction made on 2026-08-28.
- 🔴 **`RUNSHEET` `P3` was conflating three sizes.** 3,968,113–4,042,388 are `vmlinux` ELF sizes; the
  desk channel ingests the decompressed image; **what is uploaded is `nfjrom`**, about a quarter of
  the number that was written down. And it is literally named `nfjrom`, one of the two filenames the
  loader force-loads at `0x80000000` and auto-executes.

### `P2`: `hazlint` over the objects, and `TC-21` asserted instead of assumed

- **0 violations in 1,607 / 1,675 / 1,617 / 1,685 loads** across 59–60 leaf objects on the four
  trees, with **0 unresolved successors** — the `.o` false-negative channel is empty on this material.
- 🔴 **The control is what makes it a measurement**: the same six sources re-assembled from the
  build's **own recorded command line** with `-Wa,-march=5281` appended carry **11**, split
  5/1/2/2/1/0. Same sources, one token, 0 against 11.
- 🔴 **The enumeration nearly was blind.** `find arch/rlx -name '*.o'` returns 57/58 and `find -L`
  returns 63/64; the six it cannot see are the BSP, including the object that calls
  `bsp_swcore_init`. The tool refuses unless `bsp/setup.o` is in the swept list.
- **`TC-m` measured rather than argued**: 26 objects claim an excision and not one scanned fewer
  bytes than it holds, so the error is conservative — it can manufacture a violation and cannot hide
  one. `TC-m` is still carried, and `P2` no longer waits on it.

### `P3`: the desk channel prints the boot ladder

- 🔴 **`RLXFW-B00` … `RLXFW-B07=FFFFFFFF`**, eight marks in order, then `bsp_machine_halt`. So
  `bsp_swcore_init()` returns −1 with no switch core, and the seating carries both values of `B07`
  instead of one and a silence.
- 🔴 **`B02` prints `00018000`** — the emulator's `PRId`, where this die must print `0000CD01`. The
  mark is demonstrated to be a run-time read *before* the power cycle that depends on it.
- **The control holds**: an unmarked image prints **0 bytes** through the same channel. An unmarked
  `loud` prints 42 — the early console `CONFIG_PRINTK=y` registers — which is a finding about what
  that capture will look like, not a mark.
- 🔴 **§5's four instruction counts are corrected.** They are listed program counters, not
  instructions; the distinct counts are 828 / 843 / 908 / 938, and the control's 880 is in no log.
  Neither could be checked, because the qemu invocation had not been recorded — which is now printed
  on every run.

### New instruments

- `tools/rtkimage.py` (3 controls) + `tools/test-rtkimage.sh` (32 cases)
- `tools/hazlint-objs.py` (12 controls) + `tools/test-hazlint-objs.sh` (28 cases)
- `tools/deskchan.py` (5 controls) + `tools/test-deskchan.sh` (18 cases)
- Each of the three refused at least once before it reported anything: on an enumeration that could
  not see the board, on a UART window that was not there, and on a truncated payload that decodes
  partially without raising and would have been printed as a smaller image.

---

**`R3-6`, 2026-08-28/29 — the step opened by clearing three carried-forward debts, and the two that
came with an instruction attached both had the instruction wrong.** `notes/kernel-build.md` §10 and
§11 are new; §2, §9.1 and §9.2 are corrected.

### The `grep -r` sweep: the blind spot is real, the prescribed fix is not

- 🔴 **`grep -r arch/rlx` has never seen the BSP.** 量: 321 files against `-R`'s 333 — the
  difference is **13 files, 91,549 bytes**, which is the whole board: `setup.c`, `prom.c`,
  `serial.c`, `irq.c`, `pci.c`, `timer.c`, `kgdb.c`, three headers, the `Makefile` and
  `vmlinux.lds.S`.
- **The sweep has a positive control, because a sweep reporting "nothing moved" is a claim.**
  `bsp_swcore_init` `-r`=0 `-R`=1; `BSP_UART0_BASE` `-r`=0 `-R`=2. Both fire.
- **Fifteen zero-claims re-run and NOT ONE is refuted** — `simulate_llsc`, `math-emu`,
  `PRID_IMP_RLX4181`, `r3k/r4k_cache_init`, `CCTL`, `IMEM0FILL`, `movz`/`movn` and the rest.
  The BSP contains none of those tokens, which is itself readable: it is board glue, not CPU code.
- **One enumeration moves.** `TC-g`'s *"seventeen `.S` files under `arch/rlx`"* is **eighteen**;
  the eighteenth is `arch/rlx/bsp/vmlinux.lds.S`, a linker script. **No count in `TC-g`'s table
  changes** — what changes is that it is now excluded for a reason rather than unseen.
- 🔴 **The instruction "re-run everything with `-R`" is refuted, and in the dangerous
  direction.** The primary drop has **28 symlinked directories**, not one. At the drop root `-R`
  reports **79,857 paths for 66,977 distinct real files — a 19.2 % inflation** — and it follows
  three `romfs/tmp -> /var/tmp` links **out of the tree**. A canary planted in `/var/tmp` came back
  from `grep -R` at three paths inside the drop; four of this project's own `boa` analysis logs are
  reachable that way today and would be reported as vendor content.
- 🔴 **`arch/rlx/bsp` DANGLES in two of the three drops.** `target` is a tracked symlink
  (mode 120000) only in `rtl819x-toolchain`. So the prescribed `-R` re-run across three drops
  returns 13/0/0 and reads as *"only one drop has it"*, which is false: the BSP is in all three at
  `boards/rtl8196e/bsp/`, 12 source files, byte-identical except one `#if` in `setup.c`'s reboot
  path. **Every BSP reading in the new sections is taken through that path, never through
  `arch/rlx/bsp/`.**

### `TC-j`: the controls now execute `main()`, and `_scan_elf` is deleted

- 🔴 **`hazlint` 1.4's `K11`–`K16` called a private copy of `main()`'s pipeline** while their
  names claimed properties of the command line. Three mutations recreating `TC-f` verbatim passed
  all twenty controls.
- **The fix is a subprocess, not an in-process `main()`.** `main()` runs the controls, so a control
  calling it would recurse — and the anti-recursion guard would itself be a path no user invocation
  takes, which is the same defect one level down. `HAZLINT_CHILD=1` suppresses only the control
  block; `K17` is the control on that claim and `M20` is its mutation.
- **`_scan_elf` is deleted rather than left unused**: a private copy of the pipeline still in the
  file is one somebody will call again.
- **All three named mutations now fail**, plus the guard one: m17 → K11, m18 → K12,
  m19 → K13/K14/K16, m20 → K13. `test-hazlint.sh` **121 → 142**.
- 🔴 **Moving the controls to the CLI immediately found three states `_scan_elf` accepted that
  the real program refuses**: a window intersecting nothing (`scan([])` returned a green 0 where the
  program dies), a fixture whose every word is excised, and a `--vma-range` that missed its own site.
- **The control report now prints `unit` and `cli` as separate blocks** and says
  **NO cli CONTROL RAN** if none did.
- ⚠️ **It costs, and the number is measured rather than waved at.** `hazlint` is a BUILD GATE
  (`tools/rlxprobe/Makefile`), and a full scan of the `R3` kernel goes **1.51 s → 3.41 s** — the
  self-test alone 0.75 s → 2.72 s, about 0.28 s for each of the seven children. **The cheaper
  option was to run the `cli` controls only under `--self-test`, and it is rejected**: that would
  put a different control set on the gate path from the one on the self-test path, which is the
  exact class of defect `TC-j` is about.
- ⚠️ **`TC-j`'s "CI runs zero hazlint cases" is true and is not an oversight.** `K4`'s population
  control is 56 KiB of this unit's bootloader and can never be committed, so the suite exits 1 on a
  runner by design. 量: all seven `cli` controls pass with `$FWRE_WORK` empty.

### `R3-6`: this board has no output path between kernel entry and userspace

- 🔴 **`early_printk` is a WEAK EMPTY STUB and `CONFIG_EARLY_PRINTK=y` is set.** 量 on the
  built `vmlinux`: 16 bytes at `0x80013bec`, `sw a1,4(sp) / sw a2,8(sp) / jr ra / sw a3,12(sp)` —
  the unoverridden `__attribute__((weak))` body from `kernel/printk_log.c:42`. `printk` is three
  20-byte `move v0,zero / jr ra` stubs. `panic_printk` is real but needs a registered console.
  **A reader who trusted the config symbol would have got a silent boot and a correct-looking
  `.config`.**
- **`prom_putchar` is the instrument** — GLOBAL, 100 bytes at `0x8000b080`, polling `0xB8002014`
  and writing `0xB8002000` uncached, with a busy loop Realtek bounds at 30,000 spins so it cannot
  hang. It works from the first C instruction of the kernel.
- 🔴 **And the most likely early failure is silent by construction**: `bsp_setup()` ends
  `ret = bsp_swcore_init(version); if (ret) bsp_machine_halt();` and `bsp_machine_halt()` is a bare
  `while(1)` with no message anywhere.
- **Eleven boot marks**, `config/rlxfw-marks.tsv`, one row each with the suspect it brackets — B00
  before any console exists, through B05 (the UART divisor) and B06 (the CP3 scratchpad), to B10 at
  the `ramdisk_execute_command` branch. **B02 prints `PRId`** — a second independent reading of
  `CPU-04`, whose 量 `0x0000CD01` came from `probe2`'s bare-metal CP0 census — and **B07 prints
  `bsp_swcore_init`'s return value**, which is otherwise consumed by that `while(1)`.
- 🔴 **The new tool refused twice and both refusals were real defects.** (a) With the tag passed
  as a runtime argument the marks printed correctly and were **not contiguous in the image**;
  `verify` read `RLXFW-B0` **zero times** while `check` on the staged tree was green — because
  `check` reads the tree and `verify` reads the artefact. (b) `RLXFW-B1` matched `RLXFW-B10`; fixed
  by carrying the terminator in the search string **and** by zero-padding the tags, because the same
  ambiguity bites a human grepping a capture.
- **Cost, 量: +127 bytes on the ELF and ZERO on the decompressed image.** `hazlint` 0 violations
  on both variants (109,922 and 111,801 loads).
- **`src-vendor/` is never written.** The marks are applied to the staged tree and
  `rlxfw-marks.py` refuses any path under `src-vendor/`.

### `CONFIG_PRINTK`: two declared variants from one delta file

- **`quiet` is the vendor's configuration; `loud` adds `CONFIG_PRINTK=y` and
  `CONFIG_PRINTK_TIME=y`.** One file with an `@loud` variant column — a second delta file would be
  a copy of all 35 rules, and a copy is a second owner.
- 🔴 **§6.6's trap fired on the first attempt**: `CONFIG_PRINTK=y` alone takes `(NEW)` from 0 to 1.
  `PRINTK_TIME` is pinned and `(NEW)` is back to 0.
- **`PRINTK_TIME=y` is a measurement, not a default.** `arch/rlx` defines no `sched_clock`, so
  `printk_time` uses the jiffies generic at `kernel/sched_clock.c:39` — **not** the CP0 `Count`
  this die does not implement, which would have printed `0.000000` on every line.
- **Cost 量**: decompressed image **3,472,384 → 3,546,112 (+73,728, +2.1 %)**, 66.2 % → 67.6 % of
  the ceiling. ⚠️ **The estimate written before the build was "150–300 KB" and was wrong by 2–4×.**

### The ceiling was being measured on the wrong file

- 🔴 **`mkinitramfs.py --kernel-image` used `os.path.getsize(vmlinux)`** — the ELF file size,
  495,729 bytes larger than the image on this kernel. It read **75.7 % used where the truth is
  66.2 %**. The error was conservative, so nothing over-ceiling ever passed; what it would have
  caused is a **false alarm**, whose documented response is to move `LOAD_START_ADDR`.
- 🔴 **And `RUNSHEET` `P9` attributed 3,472,384 to a tool that could not compute it.**
- **Fixed to read the `PT_LOAD` program headers** (`p_filesz`, not `p_memsz` — `.bss` is not in what
  the decompressor writes), reproducing the `objcopy -O binary` route by a path with no cross
  toolchain in it. `A20`–`A23` are the controls; `A20`'s fixture is built so file size and load
  extent cannot coincide.

### Tools

- **New**: `tools/rlxfw-marks.py` (18 controls), `config/rlxfw-marks.tsv`,
  `config/rlxfw-src/linux-2.6.30/{arch/rlx/kernel/rlxfw_mark.c,include/linux/rlxfw-mark.h}`.
- `tools/hazlint` 1.4 → **1.5**; self-test 20 → 21 controls, seven of them `cli`.
- `tools/kconfig-delta.py` 22 → **24** controls (the `@variant` mechanism, and `C24` caught that the
  CLI validated a variant name while the library function silently fell through).
- `tools/mkinitramfs.py` 19 → **23** controls.
- `tools/test-hazlint.sh` 121 → **142**; `tools/test-config-gates.sh` 34 → **45**.
- `tools/rlxfw-kbuild.sh` gains `--marks`, off by default so every pre-`R3-6` measurement stays
  reproducible by the same driver.

**Zero flash bytes, zero power cycles, zero device readings.** Four kernel builds, `-j4`,
`vendor-tripwire` CLEAN on all four.


**`R3-4` and `R3-5`, 2026-08-28 — both of the things this step was told to fix turned out to be
described wrongly, and the corrections came from building the instrument rather than re-reading the
claim.** `notes/kernel-build.md` §1.4 and §6 are rewritten with the originals quoted in place.

- 🔴 **`CONFIG_ARCH_CPU_SLEEP` was never a settable line, and the vendor ships it on.**
  `boards/rtl8196e/config.in:30` declares it `bool` with **no prompt** and `default y`, so no
  `.config` line reaches it and the vendor's own `# ... is not set` is a dead line. `oldconfig` is
  asked **nothing at all** on that template — `(NEW)` is 0 — and `< /dev/null` and
  `yes '' |` produce identical output, because `conf_askvalue()` presets its buffer and ignores
  `fgets`'s return value. And the `sleep` instruction `0x42000038` is at `0x80007EA8` in **this
  unit's own shipped kernel**, the one measured booting on the silicon on 2026-08-24.
- 🔴 **The four-way stdin sweep only means something because a positive control was built
  for it.** Six promptable symbols were deleted so `oldconfig` had to ask; `yes n` then moved all
  six while `ARCH_CPU_SLEEP` moved under none of them. All 21 derived differences were argued with
  at once and none moved — `CONFIG_SWAP`, flipped in the same file, did.
- 🔴 **The ban on `yes '' | make oldconfig` was inert on the vendor's template and became
  real the moment rlxfw touched the config.** `CONFIG_BLK_DEV_INITRD=y` opens a menu and
  produces four `(NEW)` prompts. 🔴 **And the failure it produces is not a wrong default — it
  is a build that never ends.** `CONFIG_INITRAMFS_ROOT_UID` is an integer symbol; fed `n` it
  fails validation and kconfig re-asks forever. 量: one such run wrote a **58 GiB** log
  before it was killed, and it is what filled this machine's disk. That is a sharper
  reason for the pinning than "the answer decides symbol values", and it was found by
  the adversarial pass reading the artefact the killed run left behind. The fix is not a forbidden string: every symbol that menu offers is written
  into the input, `(NEW)` returns to 0, and a build with no prompts cannot be changed by an answer.
- 🔴 **`hazlint`'s coverage gap was a span, not its contents.** The 975,944-byte MIPS16 band holds
  **15,050 bytes** of MIPS16, and 38 of those 39 functions are in `.iram`, not `.text` — **`.text`'s
  own MIPS16 content is one function, 714 bytes, 0.029 %** — and that one function was
  dragging the bound down 947,878 bytes. 1.4 excises MIPS16 **by name** from the symbol table.
  Coverage 61.5 % → **99.29 %**, and two more violations of the same shape came out of the part
  the bound had been hiding.
- ⚠️ **And the excision buys that coverage at a price**: cutting a span in two creates a
  seam, and 8 loads now sit at a span head with nothing before them this scan can see.
  `hazlint` reports them as *notes — a stated limit, not a finding*. **"0 violations"
  means 0 among the successors it can resolve, and 8 it declines to rule on.**
- 🔴 **Removing the bound exposed two things it had been covering.** `.rodata` was inside
  the scan (a linked kernel's one executable `PT_LOAD` covers it, and two of its words decode as
  `jalx`), and `sys_call_table` is 2,656 bytes of function pointers declared `STT_OBJECT` and linked
  into `.text` — the only two unresolved successors in every build measured today.
- 🔴 **All seven violations have one cause, read out of the vendor's own tools.** gcc emits
  `lw $2` / `j $31` / `movz $2,$6,$5` with Realtek's own marker `#RLX4181/RLX4281:conditional move`
  — a conditional move in the branch delay slot, under `.set noreorder`. And gas could not have
  fixed it anyway: its `.set reorder` load-delay model covers `movz`'s `rs` and `rt` and **not**
  `rd`.
- 🔴 **The narrowest fix is a measurement.** `CFLAGS_KERNEL=-fno-if-conversion` reaches
  **0 violations** with no source change — 109,594 loads on the sweep build, 109,912 on the `R3` kernel, and quoting one for the other is what the first version of this line did, costing 2,597 → 31 conditional moves
  (−98.8 %) and +16,788 bytes of `.text` (+0.69 %). `-fno-if-conversion2` removes **none**
  further and costs 4,808 more, so it is out.
- 🔴 **Three build inputs were undeclared and two were invisible**: a `timeconst.pl` perl
  patch the build on disk already carried, the top-level SDK `.config` (normally written by a curses
  program — a build input nobody else could reproduce), and the fact that **the build rewrites
  `data_MAC_REG_88E.c` inside its own source tree**, which makes re-staging required rather than
  tidy. Built from the pinned drop plus the declared inputs, `.text` comes out **byte-identical** to
  the `vmlinux` already on disk; the whole difference is the build stamp.
- **`R3-5`**: an initramfs of **29** entries, 24 of them this device's own binaries unmodified and 5
  named as mine — 31/26/5 until the adversarial pass turned the `unit` tag check on
  for `slink` and `dir` entries and it refused two of them, every source checked against its tag rather than trusted. Decompressed image
  **3,472,384** bytes against the **5,242,880** ceiling, margin 1,770,496.
- **The seating's discriminator became a four-mark ladder**, two of whose marks are computed at run
  time and none of which costs a line of vendor source: `start address:` printed by the decompressor
  out of my image's own header **before the kernel is entered**, and a string my `/init` prints.
- New: `config/` (5 files), `tools/kconfig-delta.py` (22 controls), `tools/mkinitramfs.py` (19),
  `tools/test-config-gates.sh` (34, of which 11 are mutations that each name the control that must go
  red). `hazlint` 1.3 → 1.4, self-test 14 → 20, `test-hazlint` 109 → 121.
- **Zero flash bytes, zero power cycles, zero device readings.**


**`R3` opens, 2026-08-28 — and the three findings it opens with all came out of material this repository already had.** Desk only, no power, zero flash bytes.
`notes/kernel-build.md` is the new owner.

- 🔴 **A control that had been built and never read.** `notes/vendor-toolchains.md`
  §4 called the `rsdk-1.3.6-5281` kernel column *not run — cheap, and not done*;
  the `vmlinux` had been linked at 05:57 that morning and the note was committed at
  06:45. Read, with the `.config` measured identical across both builds: changing
  **`-march` alone** moves the whole-image violation count **4 → 20,201**, changing
  **the toolchain generation alone** moves it **20,201 → 21,185**, +4.9 %. The
  confound that table carried is gone.
- 🔴 **`TC-g` closes, and eleven load-use hazards in hand-written kernel assembly
  turn out to be prevented by the assembler rather than by the author** — five in
  the exception return path, five in the user-copy routines, and one that is
  `lw k0,0(k0)` followed by `jr k0` in the general exception dispatcher. **No
  compiler flag would fix them; there is no compiler in that path.** The detector's
  own positive control caught its first version, which counted instructions where
  the two `-march` values emit the same number of them.
- 🔴 **The four "unexplained" violations are one shape**: a conditional move whose
  destination is the register the load just wrote. Two are on `R3`'s boot path.
  Across everything measured to run on this die — the whole shipped kernel, its
  `boa`, its `busybox`, its loader — the pattern occurs **zero** times.
- 🆕 **A desk execution channel, with its ceiling measured rather than assumed.**
  `qemu-system-mips` runs ~1,000 instructions of this board's kernel and stops in
  the switch-core probe — and this unit's own kernel stops in the same place, so
  the ceiling belongs to the emulator. On the way out, qemu decodes opcode `0x13`
  as `lwxc1`: the same MIPS-IV mislabel this project fixed in its own tool on
  2026-08-27.
- 🆕 **The `cr6c` image format is read end to end**, and `check_image()`'s 16-bit
  sum rule is evaluated for the first time — zero on two independent images, and
  `0xFFFF` when one bit is flipped.
- 🆕 **Two decisions with refutation conditions**: the kernel is built with
  `rsdk-1.3.6-4181` through its own wrapper, and the first boot mounts an
  initramfs of this unit's own userspace rather than the flash rootfs.

---

**`R2a/b/d-4`, 2026-08-28 — the rebuilds got built, and the instrument they were
to be judged by turned out to be measuring the other axis.** Desk only, no power,
zero flash bytes. `notes/rebuild-vs-shipped.md` is the new owner.

- 🔴 **One compiler flag costs more of the score than changing the program does.**
  Single-variable by construction: `-march` alone (4181 vs 5281, one source, one
  `.config`, one gcc) is **0.3360**; the toolchain generation alone is **0.2132**;
  swapping Realtek's 8196E `boa` for Actiontec's fork of it, toolchain held, is
  **0.9359**. Jaccard agrees. **So `R2b` was asking a source question of a
  toolchain instrument**, and `TC-02` stays 推 for a harder reason than before.
- ✅ **The `lwl` puzzle from 2019 closes.** Byte-identical source, no `.config`
  change, only the rsdk: **0 / 0 / 26**, and 32 when the 1.5.5 code generator is
  driven at `-march=4181`. It was the wrapper generation and nothing else.
- 🆕 **`TC-19`, a third channel out of the same material**: twelve shipped
  userspace binaries across six trees report **0 load-delay violations**, and the
  positive control for that zero is in the same table — the `-march=5281`
  rebuilds return 5,224–10,494. This unit's userspace, like its kernel, was built
  for a core that exposes the load delay slot.
- 🆕 **`TC-20`**: all three drops' `users/Makefile` name
  `rsdk-1.5.5-4181-…-110225` and none of them ships it. ⚠️ The `Kconfig` that
  looks like corroboration is **generated** by `find toolchain -type d`, so it
  corroborates nothing.
- ✅ **`TC-c`**: the kernel's MIPS16 comes from `__attribute__((mips16))` in
  `8192cd_cfg.h`, which is the **default** branch on Linux with the driver built
  in. The measurement the note had proposed — `make V=1` and grep for `-mips16` —
  would have returned a false zero.
- **`tools/rebuild-census.py`** (8 controls) and **`tools/test-rebuild-census.sh`**
  (27 cases, 6 of them mutations). The tool's job is to make `binsim`, `opcount`
  and `hazlint` read the *same* window, and to apply the decision rule
  mechanically — including the branch where a **perfect** score with a changed
  container is still `VOID`.
- 🔴 **The adversarial pass changed five sentences that were already written**,
  four of them a measured number sitting beside an unmeasured adjective. Among
  them: "the entire program replaced" is a superset fork with 29 of 56 files
  byte-identical; "389 objects, 0 non-MIPS" had walked one subdirectory; and the
  crt attribution had been checked with an instrument relocations defeat, then
  re-established with a 5-KB hello-world that reproduces the same three
  violations with no `boa` in it.

**`R2a/b/d-3`, 2026-08-28 — the step asked for a container, the container was
never needed, and what it actually produced was a reason not to build this board
with the toolchain that is on the disk.** Desk only, no power, zero flash bytes.
`notes/vendor-toolchains.md` is the new owner.

- 🔴 **A census of mine wrote into the vendor source trees.** `rsdk-linux-config`
  answers `--version` by running `make` in the tree it lives in: **2,580 tracked
  files** deleted (mostly regular files under `config/uclibc/`; the first
  write-up said "symlinks under `include/bits/`" and that directory holds 93),
  4 files rewritten, 17 ignored build products, plus an `offset.tmp` in this
  repository's root. Restored byte-for-byte against the
  pinned sha. **`tools/vendor-tripwire.sh`** (24 controls, one of which runs the
  actual culprit) now wraps anything that executes a vendor binary, with two
  independent detectors because git alone cannot see a write that produced
  identical bytes.

- **It was never one missing library for `as`.** Seventeen of rsdk-1.5.5's
  binutils were unrunnable for one i386 `libz.so.1`; `gcc`, `cpp` and `xgcc` are
  statically linked, which is exactly why the old DoD looked satisfied. Two
  recipes proved, hermetic first so the second could not mask it, with a
  negative control between them and pinned sha256s.

- **The DoD is now a build.** `tools/tc-smoke.sh` (31 controls) runs a four-rung
  ladder per toolchain and reports a rung not reached as not reached. Above it:
  the vendor's own `users/dhrystone` built and **run** under `qemu-mips` with
  every internal self-check matching, and a **complete `vmlinux` — 724 objects,
  linked twice with two different toolchains**. The only thing in the way was
  `kernel/timeconst.pl`'s `defined(@val)`, removed from Perl in 5.22. A host
  idiom, not a compiler.

- 🔴 **`TC-15`: the vendor's own compiler and assembler agree on which Lexra
  cores expose the load delay slot.** `{4180, 4181, 5181, mips1}` pad loads with
  `nop`; `{5280, 5281, 4281, mips2}` do not — measured two ways, across two
  toolchain generations, one of which has no such checker at all. Building this
  4181 board's kernel with the only rsdk-1.5.5 on hand (`-march=5281`, enforced
  by its wrapper) puts **49 load-delay violations into three objects**, two of
  them the exception handler and the cache management code. At whole-image scale,
  from one source: the `-march=4181` `vmlinux` is 28.77 % padded with **256**
  violations, the `-march=5281` one is 2.06 % padded with **36,264**, and this
  unit's own kernel is **29.91 % padded with 168** — on the 4181 side by both
  measures at once.

- 🔴 **`TC-17`, and a discriminator retired to make room for it.** Each drop's
  own top-level `.config` names the rsdk it is configured for, and all three name
  a 1.3.6 while this unit's banner is `4.4.5-1.5.5p2`. The MIPS16 discriminator
  it replaces was **refuted by the build**: a `vmlinux` from one of the five
  shipped configs carries 39 symbols marked `[MIPS16]`.

- **`-fuse-uls` is in no drop's build system.** It is injected by the rsdk-1.5.5
  wrapper and by neither 1.3.6 wrapper, which is the whole explanation for the
  2019 drop to zero that `notes/lwl-mystery.md` was carrying.

- **`opcount --mips16` and `hazlint`'s MIPS16 refusal got their first ground
  truth.** They have only ever run on a stripped image; the `vmlinux` built here
  has a symbol table. The counter finds **25 distinct `jalx` targets** where the
  symbol table marks **39 symbols `[MIPS16]`** — **consistent, not equal**, and
  the gap is the tools' own documented blind spot: a MIPS16 routine entered
  through `jr`/`jalr` on an odd address is never counted. The instrument is
  confirmed as a detector and measured as an undercount, which is more than it
  had before and less than agreement.

**`R2a/b/d-2`, 2026-08-27 — the two greps landed on something, and one of the
things they landed on was a rule this repository had written for itself.** Desk
only, no power, zero flash bytes. `notes/vendor-kernel-isa.md` owns all of it.

- 🔴 **The plan's grep path was wrong and would have returned two false zeros.**
  It greps `arch/mips/`; this SoC's port is **`arch/rlx/`**, a sibling tree in
  the same drops. `arch/mips/` became the scanner's liveness control: the same
  needles hit there, so a zero in `arch/rlx/` is an answer rather than a blind
  spot. Which port was *built* is read out of the binary, from three literals
  that exist only in `arch/rlx`-only files.

- **What this kernel emulates**: `ll`/`sc` and `sync` (as a no-op), because
  `ARCH_CPU_LLSC=n` and `ARCH_CPU_SYNC=n` for this board; **not** `rdhwr`, whose
  two call sites the vendor `#if 0`'d out where mainline calls them
  unconditionally; and 🔴 **not the FPU — there is no `math-emu` under
  `arch/rlx` at all**, and `do_cpu` returns `SIGILL` for any coprocessor but 0.
  Binary side agrees: zero `ll`, `sc`, `sync`, `lwc1`, `swc1` and `sdc1` in
  2.85 MB of text — ⚠️ not *zero FPU opcodes*; that span holds one `COP1` and
  two `ldc1`, all inside a 1 KiB non-code island, excluded by adjudication. **`CLAUDE.md`'s bench rule said the kernel emulates "`ll`/`sc` and the
  FPU"** — half of that is wrong, the conclusion is not, and only the reason
  moved.

- 🔴 **`F49` is a third answer, not one of the plan's two.** `cpu_cache_init()`
  calls `rlx_cache_init()` unconditionally — no `r3k`, no `r4k`, no probe. And
  the `#ifdef` structure of `cache-rlx.c` is what *produces* the reading
  `CPU-44` took off this unit's binary on 2026-08-26: `DCACHE_OP` is defined for
  RLX4181 and `ICACHE_OP` only for 4281/5281, so the D side uses the `cache`
  instruction and the I side uses CCTL. An observation became a consequence.

- **`CPU-25`'s blank is filled** from `boards/rtl8196e/bsp/bspcpu.h`: I-cache
  16 KiB, D-cache 8 KiB, both 16-byte line, no L2, 32 TLB entries. The line size
  has a second source in this unit's own binary, and the TLB count agrees with a
  device measurement that contains no TLB probe.

- 🔴 **`CLAUDE.md`'s core-naming ban is lifted, on the condition `CLAUDE.md`
  itself named.** `arch/rlx/include/asm/cpu.h` is a `PRId` assignment table:
  `PRID_IMP_RLX4181 = 0xcd00` against a measured `PRId` of `0x0000CD01`. So the
  core is **RLX4181 rev 1**, and **RLX5281 (`0xdc01`) is excluded rather than
  unproven**. Three weaknesses travel with it and are written into the rule
  itself: one source in three byte-identical copies, no code in the port reads
  the table, and its own encoding breaks for two entries.

- 🔴 **This unit's kernel contains MIPS16**, entered with `jalx` into and around
  the `.iram` section that `_imem_dmem_init` loads into a 16 KiB on-chip
  scratchpad — verified by disassembling a target with the vendor's own
  `rsdk-1.3.6-4181` objdump and finding a complete function whose literal pool
  holds a KSEG1 register address, against a random-bytes control that does not
  cohere. **That breaks a superset claim two instruments here were standing
  on**, so `opcount.py` gained a `--mips16` precondition test and `hazlint` 1.3
  now *refuses* a range containing MIPS16. All twelve vendor userland ELF binaries
  were re-checked by two independent tests, and `stage2.bin` — a raw image with
  no ELF header — by the `jalx` test alone with its control fired. All clean, so
  no number already in this repository moves.

- 🔴 **`hazlint` 1.2's own note records a number the shipped tool does not
  produce.** Running both versions out of git against the same sha256: violations
  on the kernel go **172 → 168**, not 172 → 171, and **four** sites leave rather
  than one. Three of the four are the `lwcz`/`swcz` half that 1.2 called
  *latent, "because nothing in this tree emits one"* — this tree's own kernel
  emits three.

- **New instrument, `tools/isa-probe.sh`**: the vendor binutils' opcode table
  read one instruction at a time against each of six Lexra `-march` values. It
  measures `movz`/`movn` for `rlx4181` on a toolchain in hand — where the repo
  previously had only the *description* of an undownloaded gcc patch saying the
  same thing, so this is a second source and not a first — agrees
  with the board configs on `sync`, **disagrees with them on `ll`/`sc`** — which
  is recorded as a disagreement — and 🔴 **says nothing about ULS**, because
  every column including `mips1` accepts `lwl`.

- 🔴 **The 2018→2019 change in `boa` is a build flag, and the first answer here
  was a false zero.** The lever is `-fuse-uls`, which **both** rsdk generations
  carry; only the default differs, and Realtek pass it explicitly in
  `rsdk-1.5.5`'s own uClibc configuration. The sentence this entry first
  carried — *it is the toolchain version, not a flag, and `-march` does not move
  it* — came from a sweep in which four of five points **did not compile**: the
  rsdk driver answers `FATAL: -march mismatch` and exits 1 without writing the
  output, and the exit status was never checked, so the `grep` read the previous
  iteration's file. Retracted: *the presence of compiler-generated `lwl` dates a
  binary's toolchain*. It dates a build flag. It does, however, remove the open
  puzzle this entry left about `boa` going 144 → 0 in 2019.

- ⚠️ **`R2a/b/d-3`'s premise is refuted and the step is not ticked.** Both 32-bit
  rsdk toolchains run natively in this WSL distro, which is the step's own DoD
  signal, reached by none of its three container routes. What is left is one
  missing i386 library for `rsdk-1.5.5`'s assembler. A step whose premise was
  refuted has not been performed.

- Suites: `test-opcount` 15 → 24, `test-hazlint` 96 → 109, `test-isa-probe` new
  at 40, and CI's `NOT RUN IN THIS JOB` 320 → 353. Three defects in this
  session's own work were caught by this repository's own checkers: `spec-check`
  C8 fired on an unescaped `|` inside a code span, C5 on a literal that had not
  reached its owner file, and `ci-census` on a skip label that did not match its
  row.

**`R2a/b/d-1`, 2026-08-27 — the floor moved, and reading the matrix refuted a
sentence this gate had been carrying since it opened.** Desk only, no power,
zero flash bytes. `notes/which-drop.md` owns all of it.

- 🔴 **`@floor` is now `boa unit-2018` against `busybox unit-2018` = 0.1581 —
  the `CROSS` cell itself**, in a five-field cross-program form the manifest
  grew for it. The route there matters more than the number. The step's first
  answer was `busybox unit-2018 v3.4.0` = 0.1646, on the argument that `boa`
  crosses a source rewrite on that step (讀: −16.5 % of its bytes,
  `+libcjson`, `+libmtdapi`, strings 0.6629) while `busybox` does not. **The
  adversarial review killed it on the denominator.** Containment divides by the
  smaller feature set; busybox's is 42,297 grams against boa's 28,887, a factor
  of 1.46, so the two numbers were read at different denominators. 讀 at a
  matched one, the ordering reverses: a pair sharing its whole upstream source
  across the model change scores **0.1212**, *below* the **0.1551–0.1581** a
  pair sharing no source reaches. At this scale the corpus holds no cell above
  the no-shared-source level and below `BASE`, so the tightest correct floor
  **is** that level.
- **`E7` and `E8` are what make it a reading rather than a choice.** `E7`: the
  named cell must be the highest of every program in the reference's tree at
  least as large as the reference — 0.1581 against `pppd` 0.1578 and `wscd`
  0.1551. Smaller programs are excluded, and 讀 says why: inside `unit-2018`,
  **422 of 630 cross-program cells sit above 0.1646**, topped by
  `sysconf`/`timelycheck` at 0.9967 — two vendor tools that share their source.
  "Two different programs" is not "two programs that share no source". `E8`
  measures what a model change alone costs, which turns the rule's precondition
  into a reading: **a comparison across a compilation-model change is VOID, not
  a fail.**
- 🔴 **`--corpus` exits 0, so the `REFUTED` branch stopped firing** — and a
  verdict that has stopped firing is not one that has been satisfied, it is one
  nobody is watching. The verdict became a function; `D5` drives it in both
  directions, at the boundary, **and with its second argument moved** — a
  reviewer built a mutant that ignored that argument and passed all 24 controls
  and all 74 runner cases, and it is `M12` now. `M11` inverts it, and the suite
  builds a second synthetic corpus on the refuted side. `binsim` 23 → 24
  synthetic controls and 9 → 11 that need the trees, `test-binsim` 71 → 96
  cases, census 306 → 320 not run in CI.
- 🔴 **Product line is crossed with the clustering, not confounded with it**, and
  the corpus refutes the claim on its own. The similarity partition separates
  perfectly — lowest within-cluster cell **0.9740**, highest between-cluster
  cell **0.8951**, no overlap over all fifteen — and 讀 `/etc/version` shows
  product does not line up with it: N150RT appears in all three clusters, two
  *different products* inside one cluster score 0.9863 and 0.9818, and two
  builds of *one product* across clusters score 0.8860 and 0.0650. The high one
  is quoted too: 0.8860 is the best case product line has anywhere here, and it
  is still below every within-cluster cell. The vendor's version number is
  refuted the same way — this unit and `n300rt-2.1.6` are both stamped V2.1.6
  and land in different clusters — their cell is 0.8951, the highest
  between-cluster cell there is and still below the lowest within-cluster one.
  What is still collinear is date and SDK generation,
  which is a tautology.
- 🔴 **`busybox` is a toolchain tracer, and on one edge it separates the two
  halves this metric is supposed to be unable to separate.** One upstream source
  across all six trees, so its cells move only when the toolchain does: across
  the 2016→2018 edge `busybox` is 0.9995–1.0000 while `boa` drops to
  0.877–0.895, so **that step is `boa`'s source and not the toolchain**. The
  sharpest cell is the deliberately different one — `n200re-3.2.0`'s `busybox`
  has 1,869 fewer code words than this unit's and all 40,915 of its 7-grams are
  a strict subset of this unit's 42,297. A third instrument,
  `G(boa_t) ∩ G(busybox_t)` compared between trees, gives the same 4+2 with a
  ninefold gap **without putting two builds of one program side by side**.
- **This unit's nearest neighbour is `n200re-3.2.0` at 0.9818**, second 0.8951,
  a gap of 8.67 pp — 108× the estimated reproducibility error — and the ranking
  holds at every `k` from 2 to 16.
- 🔴 **`TC-02` stays 推, and that is the answer rather than a deferral.** The
  corpus is six *shipped images*; a GPL drop is a source and toolchain release,
  and no similarity between images can name one. The gate's own refutation
  condition did not fire (span 92.8 pp against a 5 pp bar) and the answer is
  still undetermined, which means that condition was never the binding one. The
  binding one is now written down. `SPEC.md` `TC-02a`, `TC-11`, `TC-12`.

**`R2a/b/d-0`, 2026-08-27 — the ruler, and the corpus refuting the plan's own
floor.** `R2b` needs a similarity metric whose thresholds come out of the data.
`tools/binsim.py` is that metric, with **32 controls that run before any number
is reported**. Desk only, no power, zero flash bytes.

- **`binsim(A,B)` is the containment of code 7-grams** over `[DT_INIT, DT_FINI)`,
  with Jaccard printed beside it and never instead of it. The window is not
  `.text` because **four of the six `boa` have no section header table** and
  `objdump -d` emits nothing for them; the two that kept theirs are the
  window's positive control, and the other eight files are covered by a decoding
  invariant — every `j`/`jal` in the window must target the executable segment.
  Measured 1.000 inside, 0.000–0.043 in the 4 KiB after, and 0.000–0.098 over
  the same bytes read two bytes misaligned, which is the negative control on
  that control.
- 🔴 **`k` is 7 and not 4, and the rule that picked it was written first.** A
  word-permutation of `unit-2018/bin/boa` — the identical instruction multiset
  in a destroyed order — still scores **0.4398** at k=4. The token alphabet is
  52 and 96,490 windows yield only 7,333 distinct 4-grams, so 4-grams are mostly
  shared compiler idioms. `E6`/`E6b` re-derive the choice on every corpus run
  rather than trusting the constant.
- 🔴 **The corpus refuted `plan/router-rebuild-plan.md:1128`.** `BASE` 0.9818,
  `FLOOR` 0.0650, and `binsim(unit-2018/boa, unit-2018/busybox)` — same tree,
  same toolchain, **different program** — **0.1581**. `FLOOR` sits *below* the
  cross-program floor, so the plan's warn band swallows the whole no-evidence
  region. Mechanism named: `boa` loses `pic` in 2019 (`TC-04`), and dropping PIC
  rewrites every prologue and every call. The tool prints `REFUTED` and exits 1
  rather than substituting a better number.
- **Three anchors came free with the material.** `bin/acltd` is **one sha256 in
  all six trees** — the identity anchor *and* the positive control on the void
  verdict, whose fifteen cells span exactly zero. The eight-byte busybox pair
  has **byte-identical code windows**, so the code channel says 1.0000 and the
  strings channel says 0.9972 — two channels that never disagreed would be one
  channel counted twice. And the container format partitions the six **2+2+2**
  with no similarity metric at all, which is the same partition
  `notes/lwl-mystery.md` gets from unaligned instruction counts.
- **The matrix discriminates**: `boa` spans 92.8 pp, `busybox` 83.5 pp, against
  the plan's 5 pp void threshold. Noise floor **0.0000** — all sixteen pairs
  with byte-identical code windows score exactly 1.000 on both measures.
  **Reading the matrix is `R2a/b/d-1`**, and date, product line and SDK
  generation are collinear in this corpus.
  🔄 **Two of those three sentences were refuted the same day and are left here
  as written.** The noise floor is not 0.0000 — those sixteen pairs are selected
  *by* byte-equality of the window that is then scored, so 1.000 is arithmetic;
  the estimate is **8.0e-4, 推**, and the adversarial review at the foot of this
  entry is what caught it. And **product line is not collinear** with the
  clustering, which `R2a/b/d-1` measured out of `/etc/version`. See the
  `R2a/b/d-1` entry above.
- 🔴 **And it caught a latent defect in the census.** `ci-census.py`'s case
  regexes were anchored `^\s*`, so a tool a suite *invokes* had its control
  lines counted as the outer suite's cases — with the cross compiler present
  that read `test-rlxprobe` as 116/107 against 202 and reported cases as
  missing, which was false. It never fired in CI, so the 101/101 configuration
  `ci-expected.tsv` documents was a number the census could not reproduce.
  Anchored at exactly two spaces; `ci-census` 12 → 14 controls.

**`R1h-1`, 2026-08-26 to 2026-08-27 — `probe3` is built and runs, and finishing
it corrected the tool that gates it.** The desk half of `R1h` closes here; the
bench half is spent at the tail of `R3`, in the same seating, with `probe3`
first. Desk only, no power, zero flash bytes.

- **`cells.S` and `probe3.c` are new**, through the `hazlint` gate at **804
  loads, 0 violations**, running from banner to `rlxprobe: end` under
  `qemu-system-mips`. **The first qemu capture this repository has committed**
  is beside it — `qemu/2026-08-26/probe3.txt`, in a directory parallel to
  `bench/` rather than under it, because someone sweeping `bench/` for readings
  in six months should not have to infer from a filename which ones came from an
  emulator.
- 🔴 **The core vendor's datasheet arrived the same day and refuted four cells.**
  `c-E0`/`c-E2` would have refuted `CCTL 0x100` by an artefact of their own
  running order (§5.2: an uncached read invalidates a resident line, and `c-E`
  ends with one); cell `c-G` is new, because that same sentence is a per-line
  invalidate primitive that costs one load and no `CCTL`; `w-line`'s void
  threshold sat at `+192` where 128 bytes is a legal line for this family; and
  associativity stopped being sourceless. ⚠️ **The LX4189 is provably not this
  part** — its Table 2 lists no TLB and this die has 32 entries — so every
  citation carries that caveat.
- **The suite went 106 → 195 cases**, twelve mutations and a coverage table that
  **names the cells nothing covers, and why**: on this harness most cache
  readings are identical mutated and unmutated, and a mutation whose predicted
  effect equals the baseline cannot fail.
- 🔴 **Then the gate itself turned out to be reading an opcode under the wrong
  ISA.** `tools/hazlint` called primary opcode `0x13` `COP1X (MIPS-IV)`. On a
  MIPS-I core it is COP3 — and the note that caught it got the history wrong by
  two levels, which is the kind of error that survives by sounding specific.
  **Measured** on binutils 2.42: `mfc3` assembles at `-march=mips1` *and*
  `mips2`, is refused at `mips3`; `lwxc1` waits for `mips4`. **Read**, MIPS IV
  Instruction Set Rev 3.2 § A 8.3.4: *"Coprocessor 3 is optional and
  implementation-specific in the MIPS I and MIPS II architecture levels. It was
  removed from MIPS III and later architecture levels. Note that in MIPS IV the
  COP3 primary opcode was reused for the COP1X instruction class."*
- 🔴 **And that same sentence stopped the fix from going where it was aimed.**
  The plan was to take the MIPS-I COP3 forms off the ISA watch list. *Optional
  and implementation-specific* means ISA membership is not evidence that this
  silicon executes them — and whether it does is the open cell `m-imem`, which
  `probe3` carries eight `mfc3` to answer. **Nothing came off the list.** The
  eight are still reported; they are reported as `mfc3` at level `MIPS-I COP3`,
  each printed with its address and its decode instead of as `.word`.
- **One misreading, three consequences.** The label; `reads()` returning
  `{rs, rt}`, which is COP1X's operand model and made the COPz *function
  selector* a general register — `mtc3`'s selector is `4`, and the tool read
  that `4` as `$a0`; and `control_flow()` not knowing `bc3` is a branch, so a
  load in its delay slot had its successor resolved to the fall-through alone.
  🔴 **That third one had survived the 2026-08-24 decoder sweep precisely
  because the first one was there**: COP1X is not a branch, so there was nothing
  to look for.
- 🔴 **The gate's verdict is unchanged on everything it gates** — measured
  before and after, on `stage2.bin` (1,474 / 646 / 0) and on all four payloads.
  **One number does move, and finding it took an adversarial reader**: the
  decompressed device kernel goes 172 violations to 171, and the one that
  leaves is `0x802BC490` — a `lhu t7` followed by a data word whose `rs` field
  is 15, which the old operand model read as register `$t7`. A false positive,
  in data decoded as code, and the only place in the tree where this fix is
  observable at all. A fix that moves almost no number is a fix the suite
  almost cannot see, so the deliverable is the controls: `hazlint` 10 → **12** (`K6d`; `K9`, eleven fixture words plus
  6,656 swept for the invariant that a strict hit is always a loose hit, and
  which **runs without `stage2.bin`**; and `K6c`'s two counts pinned rather
  than merely asserted unequal), `test-hazlint.sh` 56 → **96**,
  `test-rlxprobe.sh` 195 → **202**. The `--isa` count that moves is `K6c`'s
  strict total, 236 → **261**: a COP3 `CO` word has no fields fixed at zero, so
  the old MIPS-IV funct table was rejecting 69 of the 97 where this rule
  rejects 44 — 40 CO words gained, 15 undefined-`rs` words lost, net +25.
- **Three more defects fell out of the same thread.** `tools/opcount.py` carried
  the identical bad row. A case in `test-hazlint.sh` read `[ -n "$STAGE2" ]`'s
  exit status instead of the tool's, so **it could not fail on the bench machine
  and could not pass anywhere else** — and it was the case checking the gate's
  own exit-code contract. And `cells.S` justified emitting raw words by claiming
  `-march=mips1` refuses both `mfc3` and `cache`; measured, it refuses only
  `cache`. The comment was corrected and the payload was not touched: rebuilt,
  the image is byte-identical.
- **Two files disagreed about the same measurement and the wrong one was the one
  nothing checks.** `ci-expected.tsv` said the suite fails 14 cases on a runner;
  `ci.yml` said 26; measured on HEAD, 26. Both re-measured and dated — three
  times in one afternoon, because each control the review added made the row
  stale again.
- 🔴 **The whole change was then put to five adversarial readers, each finding
  sent to a separate agent whose job was to refute it: 11 of 25 survived.** Two
  of the four substantive ones are above. The others: `notes/cache-model.md`
  claimed no word of the 97 has its low 11 bits zero, and nine do — one of them
  a well-formed `bc3f` that is `hazlint`'s own fixture, so the loader does
  contain a valid COP3 word and the separating property is a valid COP3
  *move*. And the identical mislabel was still alive one opcode along: `0x33`
  is `LWC3` on MIPS-I and was `(pref', 'MIPS-IV')` in two tools, while `reads()` treated `swc3`'s
  coprocessor register as a general one — measured, that made the shipped tool
  refuse `lw t0` / `swc3 t0,0(a0)`, a build stopped for a hazard that is not
  there. Three of the new controls were themselves too weak to catch a mutant
  and were strengthened.

**`R1h-0`, 2026-08-26 — `probe3`'s cell table, and writing it refuted two things
the table was going to stand on.** `docs/probe3-cells.md`: eleven sections, every
expected value and refutation condition written before its cell, every expected
value naming its capture or artefact, and *expected under qemu* kept in a
separate column from *expected on the device* — because `probe1` cell 1 came back
FRESH on qemu and STALE on silicon, and that opposition is the whole experiment.
Desk only, no power, zero flash bytes.

- 🔴 **The prediction and the mechanism were about different caches.** The walk's
  mechanism — a store into the instruction stream is not seen — is measured, and
  it measures the **I-cache**; the prediction written for it (D 8 KiB, line 16 B,
  cut from this unit's own kernel) is about the **D-cache**. The walk as
  described could not have refuted the prediction written for it. `probe3` now
  carries two walks, and the D-side one is armed at run time by its own cell A.
- 🔴 **This part has a 16 KiB local instruction scratchpad, and it is exactly the
  size of the predicted I-cache.** Nothing in this repository had ever recorded
  it. It was found by asking what `CCTL 0x010`/`0x020` are: they are
  `IMEM0FILL`/`IMEM0OFF`, named by four sources of which two are independent —
  the Lexra LX4189 datasheet, **`arch/rlx/include/asm/rlxregs.h` in the GPL drops
  this project already held**, the RTL8196E datasheet's *"16Kbyte I-MEM, 8Kbyte
  D-MEM"* (already quoted verbatim at `SOURCES.json:195`), and this unit's own
  kernel programming a 16 KiB window into `CP3 $0`/`$1` and then issuing `0x010`.
  **`CPU-24` closes; `CPU-46` is new.** The same search failure as `arch/rlx/`
  one release earlier: the fact was in the tree and the search went elsewhere.
- 🔴 **`CPU-25`'s source count was wrong in the direction of too few.** The
  datasheet in `refs/` states both cache sizes on its own first page. What has no
  source of any kind is **the associativity**, not the I-cache size. ⚠️ And the
  datasheet documents a variant `SOURCES.json` records this unit as *not being* —
  so the geometry is two vendor documents about two variants of a family this die
  is measured to belong to, and still not a reading of this die.
- **`CCTL` is edge-triggered on 0→1**, so a probe that writes it once and expects
  an effect is a tool that cannot fail. `CLK-17` is new — the 14.286057 MHz rate
  a timing payload actually divides by, which until now existed only inside a
  derivation. `CLK-02`'s name is corrected against the datasheet it cites.
- 🔴 **The table was then put to four adversarial readers and they found eight
  blockers**, two of which would have cost the power cycle: a whole-cache
  `DInval` that discards the return address off a KSEG0 stack, and a CP3 read
  that would have trapped because the preceding cell restored `Status`. Also a
  write-buffer confound that made one cell unable to fail, three line-size cells
  with no must-fire reading, and a timer field read 16× wrong. All fixed; the
  list is in `LOG.md`, because the record of being wrong stays in place.

**`R1-gate` closes, 2026-08-26 — and the write-up refuted two things the gate had
been standing on.** `docs/rlx-cache-and-cp0.md` is the closing statement: the four
downstream decisions, each with the reading that decided it, and what the gate did
not prove. Desk only, no power, zero flash bytes.

- **Three of the four decisions name a measurement. The fourth names none, and
  that is written down rather than smoothed over.** Where the MTD driver flushes
  (`CCTL 0x002`, **instruction side only**), where the exception handler can live
  (`0x80000080`, `BEV = 0`, `break` trapped and returned), and whether the SoC
  timer driver is a prerequisite (it is, `Count` is not implemented) are settled.
  **Whether the Ethernet driver's descriptor rings need an uncached window is
  not**, and it moves to a new gate with a payload, a DoD and a stop-loss rather
  than staying an open row on a closed gate.
- 🔴 **"The D-cache is write-through" was a reading the measurement does not
  carry.** Both cells that established it stored to a line the D-cache did not
  hold — a write **miss** — and under a miss, write-through and write-back
  without write-allocate are indistinguishable. The vendor's own board config for
  this SoC says write-back. **A descriptor ring is a write *hit***, so the CPU→
  memory direction is not covered for the pattern the driver will actually use.
- 🔴 **A refutation condition this project wrote for itself is met.** *"Refuted by
  finding a `cache` instruction anywhere in vendor code that executes"* — the scan
  that returned zero had only ever been run on the 56 KB loader. This unit's own
  kernel carries **37 of them**, D side only, in one span, separated from 15 data
  false positives by three independent properties. It does not make this a MIPS32
  core (`Config.M = 0` is measured); it means there may be a working D-cache
  invalidate here, which is exactly what the open decision needs.
- **Four CCTL commands have names from a source that states them, and one command
  had no row at all.** Found in `arch/rlx/mm/cache-rlx.c` — a directory the
  earlier conclusion never listed, in a tree this repository already cited
  elsewhere. `0x010` and `0x020` remain unnamed in every source, and the only
  instrument that could name them is one this project declines to run on a
  single-device budget.
- 🔴 **`SPEC.md`'s cache row had been outside two of its checker's checks since
  the day it was written.** One unescaped `|` gave it eight cells in a
  seven-column table; every check reads cells by index, so they read the wrong
  cell and passed, and the summary reported the row as *skipped*. `spec-check.py`
  gains **C8** — cell count must equal the header's — and a ninth mutation that
  re-creates that exact defect. Pointing the same scan at the rest of the
  repository found two more, both of which had been mis-rendering tables since
  they were written.

**`R1g-4b`, at the bench, 2026-08-25 — `R1e` closes and `R1-gate` has only its
write-up left.** One power cycle, 23 captures, 🔄 **no flash-write command issued** *(was “zero flash bytes”; no `FLR` bracket ran)*, and 16 of 16
captures written after the block that predicted them.

- **The CP0 census ran on this silicon**, under an exception handler installed at
  `0x80000080` and read back word for word before anything was allowed to fault.
  `Status.BEV = 0` — and `break` trapping into that handler and returning is the
  direct evidence that the core *fetches* there, rather than an inference from
  the copy having landed. `PRId = 0x0000CD01`, predicted in writing beforehand.
  `Count` is not implemented, so this SoC's timer driver is a prerequisite.
  The CP0 ignores the select field. `Config.M = 0`, so it is not a MIPS32 core.
- **`nowrite = 0` on all 256 rows is the row that makes the rest mean anything.**
  Reading every register twice with two different primes is what separates *this
  register reads zero* from *the instruction never wrote its destination*, and
  without it `Count = 0` would have been ambiguous exactly where it is
  load-bearing.
- **`Random` (rd 1) came back moving**, sixteen distinct values inside 0…31 —
  the positive control the census could not otherwise have had, and an
  independent corroboration of the 32 TLB entries.
- **Three tool defects, found by pointing the tools at the new captures.**
  `reply-size.py check` crashed on the one input it exists to report; its
  `UNREADABLE` branch existed, was counted, and could never print. Its suite
  goes 12 → 21. `boot-timeline.py`'s artifact anchor assumed a one-byte prefix
  and mis-measured a two-byte one by two orders of magnitude; 12 → 15.
- 🔴 **A power cycle was spent on a wrong assumption and it is recorded as one.**
  A second `J 80500000` booted the vendor kernel, because the loader re-stages
  that address on a watchdog reset too — so a payload cannot be re-run on one
  power cycle without re-uploading. Nothing already measured was lost.

**`R1g-4b`'s desk half, 2026-08-25.** `probe2` is fixed against measured values
rather than read ones, and the suite that would have to tell a fixed payload from
a shipped one went from 66 cases to **106**.

- **`tools/rlxprobe/probe2`** — the five must-fix items from
  `docs/rlxprobe-audit-2026-08-25.md`. `SAFE_A0` before the one instruction in
  the tree guaranteed by design to fault; a 44-word read-back of the installed
  handler, so *the stores did not land* and *the core does not fetch there* stop
  being one hang; one binary instead of two indistinguishable ones; a primed
  destination on every CP0 read; and **no `mtc0` to CP0 register 12 anywhere in a
  device image**, which is what "it does not touch `Status.IsC`" looks like when
  it is a claim about the emitted words instead of about a comment.
- **The census reads every register twice, with two different prime families.**
  *Not written* becomes certain rather than likely, and **a register that changes
  between the two reads reports itself** — a second, independent route to `F50b`.
- **Four mutations, one per must-fix, run under qemu.** One of them exists
  because qemu cannot reach the state it tests: its `mfc0` always writes `rt`, so
  a payload with one census stub emitting `nop` is the only way to show that
  `S_NOWRITE` can be produced at all. The first qemu run of the fixed payload
  found a defect in the fix.
- **`tools/reply-size.py`** — `LDR-07`'s reply-length formula as an instrument.
  Twelve controls; the per-family constants fitted from the captures rather than
  counted by hand; **121 modelled, 0 unexplained** over `bench/`. The two
  captures that never fitted have names now instead of being misses.
- **`tools/boot-timeline.py`** — the named intervals of a boot, with the anchor
  bytes stated. It refutes `CLK-15`'s *"cold and warm are the same"*: the two
  populations do not overlap, and the difference survives **inside a single power
  cycle, twice**.
- `PROGRESS.md`'s `Est.` column is answered: 198 is not the plan's total, not its
  desk+bench, and not any consistent subset of it. No rule reproduces it.

## v0.0 — 2026-08-25

**The instruments and the record.** Fifteen tools, each with the controls that
show it can fail; three loader documents read to instruction level; one gate
closed on silicon; and, from today, something that runs them all on every push.

### What is established

| | |
|---|---|
| **`S0` closed 2026-08-23** | 3-2-1 encrypted backup plus a restore drill. Copy ③ downloaded and read back: 19/19 byte-identical, none missing, none extra, with a positive control that fired |
| **`R0` closed 2026-08-24** | **The vendor's kernel, delivered over TFTP and executed from RAM, reached userspace and answered ping 2/2 at 3.6 ms.** `G7.log` is byte-identical to `G6.log` as a whole file, 1789 bytes, same sha256; `G6` reproduces the pre-existing boot log byte-exactly from `decompressing kernel:` onward, 1687 of 1687 bytes |
| **No flash-write command was issued** | in any of the 81 captures across five power cycles. The flash evidence is **bounded and the wording matters**: the loader head and the `cr6c` image header are byte-identical across three kernel executions and two uploads, and that reaches **512 bytes of a 4,194,304-byte part**. It is not *"zero flash bytes written"*, and no instrument here can establish that |
| **`AUTOBURN` measured off at the burn path's own instruction** | `00000000` at `0x80401B9C` *during* the transfers, and `00000001` after the power cycle — which is the positive control on that ordering |

### What is not

Everything about the core itself. The instruction set, the pipeline hazards and
the CP0 registers are read out of binaries and vendor source; **nothing of mine
has executed a single instruction on this silicon.** That is `R1`, it is the
active gate, and it runs bare metal because Linux emulates the two rows the
toolchain decision rests on.

### In this tag

- **`docs/FINDINGS.md`** — one line per finding, ordered by the decision it
  changed. The map this repository's 400 KB of prose did not have.
- **`.github/workflows/ci.yml`** and **`tools/ci-census.py`** — the suites run on
  every push, and the census refuses a green build whose arithmetic does not
  close. It earned its keep on its first real input: 20 + 23 = 43 against a bench
  total of 45, so two cases had been vanishing out of `tools/test-rlxprobe.sh`
  with neither a `FAIL` nor a `skip` line. **88 cases run on a runner; 101 do
  not, and every one of the 101 is named on the build page** — they need a 56 KiB
  vendor bootloader that may not be redistributed.
- **`tools/rlxprobe/probe1`** — the `R1d` payload: six cells that decide, on
  silicon, which cache-management sequence makes this core see an instruction
  just written into RAM. Not yet run.
- **`tools/console-capture.py` 1.3** — `--esc-period`, and the period each
  capture *achieved* is now measured and recorded rather than assumed.
- `README.md` rewritten: the previous first screen said *"no claim in this
  repository has been observed on silicon"*, which stopped being true on
  2026-08-23.

### Corrections that landed with it

- 🔴 **The general exception vector on this core is `0x80000080`, not
  `0x80000180`.** The MIPS32 address had reached **seven committed sites** and
  five more in the planning material. A handler written there would have landed
  in RAM nothing reads, and the fault would still have hung the board.
- 🔴 **A fault the loader does not handle hangs forever** — `do_reserved` ends in
  a branch to itself with interrupts already off and the watchdog not armed. One
  fault costs one power cycle, and there is no spare unit.
- 🔴 **`do_reserved` dereferences the faulting code's own `$a0`**, and
  `rlx_cctl(0x002)` would have handed it the integer 2 — a kuseg address, a TLB
  refill to a vector nothing populated, and from there **undetermined**. Guarded
  before the payload was ever built, in two instructions. The sharper claim that
  went with it — *"it could branch into the loader's flash-write path"* — was
  refuted by the same day's adversarial pass and withdrawn: `0x5A5AA5A5` decodes
  as `BLEZL`, not a jump.
- 🔴 **A TFTP upload named `boot.img` makes the loader write from `0x80000000`
  upward**, over both exception vectors. On the do-not-type list from today.
- **`SPEC.md` `CPU-26` named the wrong table.** `0x8040A5C0` is the TFTP/ARP boot
  state machine, 24 entries; the exception table is `exception_handlers[32]` at
  `0x8040EB40`, in BSS.
- **`C-16` closes, and the refutation that had been recorded against it was
  itself wrong.** `check_image()` *is* the copier; it reads `gCHKKEY_HIT` at its
  17th instruction, not its first two. The block counter is where the document
  said, and it reads zero because a later rootfs scan sets it to exactly zero.
- **`CLK-15`**: the 350 ms of silence after `Booting...` is stage 1 copying
  20,924 bytes out of memory-mapped SPI NOR, uncached, a word at a time — and
  `Booting...` is printed by **stage 1**, so the experiment this project had
  written down for it pointed at the wrong binary.

Every one of these is in `PROGRESS.md`'s Corrections table with the date and
what caught it.
