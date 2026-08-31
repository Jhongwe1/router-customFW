# The leak surface: what identifies this unit, and where it already is

**Owner of one thing**: *which byte strings identify this physical device, which
of them are in a published file, and what was decided about each.* `SPEC.md`
§18 is the rule (*nothing that identifies this unit lives here*); `FLS-22` is
the number; this file is the reasoning and the record of being wrong.

Written 2026-08-30/31 (fourteenth session — it ran past midnight), at the desk, no power. Zero flash
bytes, zero power cycles, zero device readings — that sentence held on the day
it was written, because the machine was not plugged in.

🔄 **2026-08-31, seating 7, added §5b's fourth entry — and that one WAS at the
bench, two power cycles.** It is the first near-miss here produced by an
instrument rather than by prose, and the reason it belongs in this file is that
a capture, not a sentence, is what nearly carried this unit's `H601` into the
repository. **The zero-flash-bytes sentence above is about the fourteenth
session and is not a claim about seating 7** — that seating issued no
flash-write command, which is a different and weaker statement, and
`RUNSHEET.md` § Results — seating 7 owns it.

⚠️ **Nothing in this file prints a value.** Offsets, counts, classes and
verdicts only, which is the same line `tools/flashwin.py` draws.

---

## 1. What the thirteenth session reported, and why every clause of it was wrong

`tools/leakscan.py` arrived on 2026-08-30 and reported, over the three
populations nothing had ever scanned:

> exactly one distinct MAC on `FC:19:28` — TOTOLINK's OUI — in seven files,
> four of them in the public `upstream/`. ⚠️ Whether it is this unit's is
> **undetermined**: `FW-17` says the default SSID carries the MAC's last six
> hex digits, and there are **zero** strings of that shape in either
> repository, so the correlation cannot be run.

Four measurements, each with its own route, replace all of it.

| | claim | 量 |
|---|---|---|
| a | `FC:19:28` is TOTOLINK's OUI | 🔴 **false.** It is **Actions Microelectronics**, Shenzhen — IEEE MA-L, registered 2020-08-25, updated 2024-08-13. 讀, the IEEE registry |
| b | the value might be this unit's | 🔴 **it is the WORKSTATION's USB GbE adapter.** It is byte-identical to the `enx<12 hex>` interface name recorded in nine tracked files — systemd's `ID_NET_NAME_MAC` puts the adapter's own MAC in the name — and in both committed host captures it is the source of the ICMP echo **replies** 4/4 and of the requests **0/4**. The board pings the host; the host answers |
| c | it might be in this unit's flash | 🔴 **0 occurrences in the 4 MiB dump** — raw, byte-reversed, and as ASCII in four forms. Its 3-byte OUI occurs **0** times in the dump and **0** times as a literal in the vendor GPL tree |
| d | the attribution is undetermined | 🔴 **it was determinable the whole time.** `FW-17`'s SSID route is genuinely unavailable, and it was never the only one: the arbiter is this unit's own dump and it had been on the same disk for two weeks |

**(d) is the one worth keeping.** The failure was not missing data. It was
stopping at the first check that could not be run, and writing the stop down as
a property of the world.

## 2. The defect underneath it, which is not about this MAC at all

讀 `tools/audit-bench-log.py`, the pattern that exists to catch this unit's
address written as bare hex:

```
("MAC, bare 12 hex", r'\b(?:00[eE]0[4-6][cC]|[fF][cC]1928)[0-9A-Fa-f]{6}\b')
```

🔴 **Neither alternative is this unit's OUI.** 量: the three bytes at
`H601+0x07` in the reference dump match neither. So the one pattern written for
this device **cannot fire on this device**, in any file, ever — this
repository's own *a tool reporting 0 is making a claim*, sitting inside the
leak gate.

⚠️ **And it looked like it was working**, because it fired on something else.
A false positive wearing a true positive's clothes is how a blind spot survives
thirteen days.

**The fix is not to add this unit's OUI to the pattern.** That writes half the
address into a committed file, and it is still a guess — it just moves the
guess. The fix changes the *kind* of evidence:

> stop asking *does this string start with a prefix I believe belongs to the
> router's manufacturer*, and ask **do these six bytes occur inside this
> router's own flash dump**.

That is `leakscan.py --attribute`. The arbiter is
`$FWRE_WORK/dumps/flash-n150rt-console-2.bin` — 4,194,304 bytes read off this
unit on 2026-08-16, sha256 `a800059a…`, `SPEC.md` `FLS-14`. No belief about
vendors enters.

**A second, narrower gap, closed the same way it was found.** `enx<12 hex>` —
the form in which the workstation's adapter appears in nine tracked files and
three `upstream/` ones — is invisible to all eight patterns, because `\b` does
not fall between `enx` and the first hex digit. A ninth pattern,
`MAC, enx interface`, was added. 量 before adding it: **0** files under
`bench/**/*.log` carry that form, so the CI gate turned red on nothing.

⚠️ **`CONTROL` held a real address.** The dash-form control literal was the
workstation adapter's own MAC, in a block whose stated premise is that it is
synthetic. Replaced with an obviously-synthetic value on the colon line's OUI.

## 3. What the classifier says, and the order is the claim

Every identity hit gets exactly one class, tried in this order:

    NOVALUE → TRIVIAL → UNIT → HOST → SYNTH → CONTROL → UNKNOWN

🔴 **`UNIT` is tried before every inference.** *These bytes are in this unit's
flash* is a measurement; *this address is locally administered, so it cannot be
burned in* and *this hit is in one of my own scanner's control literals* are
inferences. A measurement that loses to an inference is a classifier that can
be argued out of a finding. `L11` and `L13` are that ordering as cases, and
`C2`/`C3` are the mutants that invert it.

**量 2026-08-31, whole corpus, taken after the session's last edit** — the population includes this session's own files, and it read 145, then 160, then 161 as this session's own files entered the population:

| class | hits | what it means |
|---|---:|---|
| `HOST` | 81 | equals an `enx<12hex>` name in the corpus — the workstation's adapter |
| `SYNTH` | 35 | locally administered, and not in the dump |
| `NOVALUE` | 15 | the pattern matched a phrase (`S/N:`), not an address |
| `TRIVIAL` | 5 | all-zero or broadcast |
| `CONTROL` | 21 | a scanner literal in this repository's own tools |
| `UNKNOWN` | 3 | globally administered, not in the dump — needs a person |
| 🔴 `UNIT` | **1** | the six bytes exist in this unit's own flash |

🔄 **Re-run 2026-08-31 after seating 7, whose 120-odd new files entered the
population: 161 hits, and the distribution is IDENTICAL in every class.** So the
seating's captures, five prediction blocks and nine owner-file edits contributed
**zero** identity hits. ⚠️ That is a statement about what a text scanner can see:
the two `H601` pre-reads that briefly sat under `bench/` were hex dumps of a `DW`
reply, which **no pattern here matches** — they were caught by the bracket's own
normalise comparison instead (§5b). **An unchanged count is not the same as nothing
having happened.**

**The one `UNIT` is `upstream/BENCH-LOG.md:216`** — in the dump **twice**, both
occurrences inside `H601`, labelled 「（裝置）」 in the file. The line above it,
`:215`, labelled 「（我們）」, is the `FC:19:28` value the thirteenth session
flagged, and it classifies `HOST`.

> The instrument had been pointing one line off, at the operator's own laptop
> adapter instead of at the router, for thirteen days.

⚠️ **What `--attribute` still cannot say.** A value absent from the dump is not
thereby harmless. 量: the on-wire address of `eth4` under my own kernel is
**not** in the dump either, and neither is its OUI — so it is either a driver
default or synthesised, and this tool cannot tell which. The one sentence it is
allowed to make is *do these bytes exist in this unit's flash*.

## 4. How much of `H601` the public repository already carries

Method: harvest every byte string a text line could encode (colon MAC, spaced
hex, contiguous hex words) from all 261 readable files under `upstream/`, look
each up inside the `H601` window of the dump, and take the union of the offsets
covered. `FLS-22` carries the numbers; the reasoning is here.

🔴 **The first version of this measurement reported 98.9 % and was wrong.**
`H601` is 8,046 zero bytes out of 8,192, and an all-zero candidate matches
everywhere. **Its own positive control "passed" by covering 8,042 bytes with an
eight-byte slice**, which is the tell: a control whose reading is absurd is
still a reading. Corrected by dropping constant-byte candidates and scoring
only the **146 non-zero** bytes — the only ones that carry information about
this unit.

**33 of 146 recoverable and placeable; 12 more (the MAC's two copies)
recoverable with an ambiguous position; 45 / 146 = 30.8 %.**

⚠️ **That is a LOWER bound and the write-up must not quote it as a figure.** The
harvester decodes three encodings — colon-separated MAC, space-separated hex
pairs, and contiguous hex runs of eight or more. A byte written in decimal, with
dots, as `0x11, 0x22, …`, or split across a line break is not harvested, and
neither is anything inside the 26 files no text scanner can read. So the true
figure is **at least** 30.8 %, and nothing here bounds it from above.

Not recoverable **by this harvester**:
`0x006004`–`0x006039`, `0x00603E`–`0x006042`, `0x00607B`–`0x0060A7`, and —
worth naming — `0x00648A`–`0x006491` (`HW_WLAN0_WSC_PIN`) and `0x006493` (the
region checksum the device recomputes), which are exactly the bytes `FLS-21`
measured moving under a `formWsc` POST.

## 5. The decision, and it is the owner's

**2026-08-30: `upstream/` is not touched.** Stated as a decision so that a
later reader does not read it as an oversight.

* the device is **end of life** — out of service for years, and reset since.
  ⚠️ A reset does **not** restore `H601` (`RF-06`, `TGT-02`), so the value is
  unchanged; what changed is that nothing is on air.
* 推: the residual is that a wireless-location database may map the BSSID to a
  place this unit **used to be**, years ago. Stale, not current.
* `upstream/` is a separate published repository pinned at `4d3ff26`, and
  `CLAUDE.md` records that this pin *is the whole credibility of R9's
  differential proof*. Rewriting its history would destroy that sha.
* removing it from `HEAD` would not un-publish it either: it has been public
  since 2026-08-17 (`915e675`, `01da319`), and public repositories are mirrored
  and indexed.

**What follows from the decision, mechanically:**

* `leakscan --attribute` is a **desk** command and its verdict is **not** a CI
  gate. Turning it into one needs an allowlist entry per surviving hit, and
  allowlisting a real finding to make a build green is the wrong order — the
  more so when the finding is being left in place deliberately.
* what CI runs is `--self-test` (17 controls, 16 on a runner) and
  `tools/test-leakscan-mutants.py` (23 mutants, 20 on a runner).
* the rule in `SPEC.md` §18 stands for **rlxfw**: this repository is private
  today, and nothing identifying this unit goes into it regardless.

## 5b. 🔴 Four near-misses over two sessions — three by the person writing about them, and one by an instrument doing what it was told

The never-print property was nearly broken three times on 2026-08-31, and none
of the three was broken by the tool:

| | what happened | what caught it |
|---|---|---|
| 1 | a throwaway probe echoed its own **lookup strings** while masking only the file lines it printed, and put a 3-byte OUI into a transcript | nothing. It was noticed by reading the output. `L9` is the control that now exists for it |
| 2 | `audit-bench-log.py`'s `CONTROL` block held a **real address** — the workstation adapter's — in a block whose stated premise is that it is synthetic | the attribution run, which classified a "synthetic" literal as `HOST` |
| 3 | 🔴 **this file** reached for an *example* of an encoding the harvester misses and typed **two octets of this unit's own OUI** as the example | a sweep run because the sentence looked like the shape it was warning about |
| 4 | 🔴 **and then the row above reproduced them again, while explaining them** — third revision, third instance, which is the pattern `spec-check`'s `C8` row already records for ragged tables | 🔴 **not the sweep.** The sweep searched for the **three**-byte OUI and only two had been written, so it reported 0 — *a tool reporting 0 is making a claim*, in the sweep written twenty minutes earlier to enforce exactly this |

### 🔴 2026-08-31, seating 7: a fourth, and it is a different kind from the three above

The three above are **prose** — a sentence that typed part of an address. This
one is a **capture**, written by an instrument doing exactly what it was told.

`bench/2026-08-31/PREDICTIONS-B5-block3.md` sends the `FLR` **pre-reads** to
`--out bench/…`. Two of the four destinations are `H601` windows. The card puts
them in the repository because a pre-read is *expected* to be uninitialised DRAM,
and on cycle 5 it was.

🔴 **On cycle 6 it was not.** DRAM had retained cycle 5's `FLR` results
(`SPEC.md` `MEM-17`), so `X-ph.log` and `X-pc.log` came out byte-identical to
this unit's `H601` — **inside the repository**.

> **The containment was conditional on the experiment coming out the expected
> way. That is not containment; it is a coincidence with a rule written on it.**

| | |
|---|---|
| what caught it | the stop-if comparison the card *already had* — `flashwin normalise` against the expectation — which exists to decide whether the `FLR` is interpretable, **not** to decide where the file may live. It answered a leak question it was not asked |
| what did not catch it | `tools/flashwin.py`'s publication guard (it guards what **it** prints, not where a **capture** lands), `audit-bench-log.py` (its patterns are for text renderings of an address, and a `DW` hex dump is not one), and `leakscan.py` (a desk command, not a gate) |
| exposure | 量 `git status` **before** the move: both `??`. **Nothing entered git history**, and this repository is private. Moved to `$FWRE_WORK/rebuild/bench-only/b5-20260831/` |
| verified after | the whole of `bench/**/*.log` normalised against both `H601` expectations: **0 files**, with a positive control — the same test **does** fire on the out-of-repo copies, so the zero is a measurement |

**What follows, and it is not "be careful".** `PREDICTIONS-B5-block3d.md` writes
every `H601` capture outside the repository, pre-read included. 🔴 **But the
template is still wrong** — the next card will be written by copying block 3 —
and the general fix is a rule nothing currently owns:

> **A capture of a forbidden window may not be addressed to `bench/`, whatever
> the cell expects to find there.**

`flashwin.py` enforces the never-print rule *on its own output*. Nothing enforces
*where a capture of such a window is written*, and the cell that decides is a
`--out` path typed on a card. It is carried forward in `PROGRESS.md` under
*the `H601` pre-read containment is wrong in the template*.

⚠️ **And the count in the heading above is now four, in two sessions.** Three
were prose and one was an instrument; **the instrument one is the one a person
re-reading the file would not have found.**

**So the discipline that works is not care.** Two of the three were caught by a
tool and the third by running a check on a hunch. What follows from it is a
standing sweep, and it is cheap:

> 量 2026-08-31, after the last edit of the session: this repository's own
> tracked files carry **no prefix of two bytes or more** of the address at
> `H601+0x07`, in **any of eight encodings** — colon, bare, `0x`-prefixed and
> space-separated, upper and lower case. **0 hits.**
>
> 🔴 The first version of this sweep searched for the three-byte OUI only, and
> reported 0 while two octets of it were sitting in the paragraph above it.
> **Prefix length is the parameter, and pinning it at three was the defect.**

⚠️ **That is the OUI only, and the OUI is the half an attacker already has.**
The full six bytes are covered by `--attribute`, whose answer is the one `UNIT`
in §3 and it is not in this repository.

## 6. What is still open

| | |
|---|---|
| `upstream/`'s 26 unreadable files | 22 `.jpg`, 2 `.png`, one undecodable `.log`, one `.pyc`. Reported **NOT SCANNED**, never counted clean (`L6`). `upstream/notes/img/README.md` is a per-image inventory with a `Redacted` column and 量 24 rows against 24 files — but a column is a **declaration**, and nothing re-decodes the pixels |
| ~~the `UNKNOWN` class~~ 🔴 **answered, by the repository, before this file was pushed** | The row said *3 hits need a person and nothing schedules that*. 讀 `upstream/tools/fwrecon/tests/test_compcs.py:255,263,307`: all three are fixtures in a unit test whose assertions are `known_mac.hex() not in rendered` and `disclosure == "protect"` — a test of upstream's **own** never-print discipline. They are synthetic by construction and not in the dump because nothing put them there. **This is the second half of the owner audit firing for the third session running**, and the lesson has not changed: a new open question has to be taken back to the repository before it is written down |
| `serial-ish` has no arbiter | 13 `NOVALUE` hits match a phrase, not a value, so `--attribute` cannot classify them. `upstream/BENCH-LOG.md:248` records that this model's `UDN`/`serialNumber` are template constants, identical on every unit — 讀, not 量, and not re-checked here |
| the dump is one source | Two full dumps exist and 量 they are byte-identical over all 4,194,304 bytes, but they were taken on the same day by the same tool. A value absent from *the dump* is not a value absent from *the device* |
| `FORBIDDEN` is copied, not derived | `flashwin.py`'s own docstring says it: its forbidden-region list is a hardcoded copy of `CLAUDE.md`'s, and nothing checks the two against each other. Adding a third region to one and not the other is a silent gap |

---

## 7. 🔴 A third instrument, a third shape, and it found a line the other two are blind to

**2026-08-31, twentieth session, desk.** `tools/flashwin.py scan` — new today,
`SPEC.md` `FLS-22` carries the summary, this section carries the reasoning.

### 7.1 Why a third shape exists at all

Three questions, and until today only two of them had an instrument:

| | question | tool | acts |
|---|---|---|---|
| 1 | may these bytes be **printed**, and where may a rendering be **written**? | `flashwin render` | when a file is produced |
| 2 | where may a **bracket's** read-back and pre-read land? | `flrbracket run` | when a file is produced |
| 3 | **does a file this repository has ALREADY COMMITTED hold forbidden content?** | — | — |

The incident that names the third, 量 2026-08-31 (seating 8): `K-P3` is
`DW 80A00000 2000` — a 32 KiB read of RAM — and it spans `0x80A00600` and
`0x80A00700`, the two destinations the `H601` windows are read into. Its output
lands in `bench/`. It was safe **because the experiment came out the expected
way**: `K-guard600`/`K-guard700` read `0/64` retained words. `CLAUDE.md`
already says a containment rule whose correctness depends on an experiment's
outcome is not a containment rule. This is that sentence with an instrument
behind it.

### 7.2 How it asks, and why the probe set is 113 and not 8,177

It does not look for the SHAPES an address takes — that is §3's classifier and
this one knows nothing about MACs. It asks *are these bytes here*, and the
bytes come from the reference dump:

* the forbidden region is cut into **16-byte windows at every offset**, not
  every sixteenth. That drops the alignment caveat from the guarantee entirely;
* a window with fewer than **4 distinct byte values** is **not searched for** —
  the filter is on the REFERENCE side, so it is not a decision made after
  seeing a match. Finding sixteen identical bytes in a file says nothing about
  this device;
* 量: `H601` is **98.22 %** one repeated byte value and holds **40** distinct
  values in 8,192 bytes, so every-offset costs **113 distinct needles**, which
  is FEWER than the 512 aligned ones would have been. The affordability is a
  property of the region, measured, not an optimisation;
* two channels through one matcher: the file's **raw bytes**, and its
  **hexadecimal decoded** — every maximal hex run, with any token followed by
  `:` dropped, because that is a `DW` reply's or a hexdump's address column and
  leaving it in breaks the byte stream every 16 bytes.

### 7.3 What it found, and it is not what the sweep was expected to find

🟢 **rlxfw's own tree is CLEAN.** `--sweep . --exclude upstream` over **1,381** files: no hit. Without the exclusion — which is the default, and this session is why — `--sweep .` reads **1,683** files and reports **1 HIT**, the one below. 🔴 **量, and the numbers here are the SECOND reading**: the first said *1,378 files, CLEAN* for `--sweep .`, and that was wrong twice — it was counted before this session's own new files existed, and it described a run under the OLD default, which excluded `upstream/`; this same session removed that default. As shipped: **`--sweep . --exclude upstream` = 1,381 files, CLEAN** (rlxfw's own tree) and **`--sweep .` = 1,683 files, 1 HIT** (1,381 + 302 = 1,683, so the partition is exact).
`--sweep bench` over **1,130**: no hit, `K-P3` included — so the check that was
made by hand at the bench on 2026-08-31 is now made by machine, and `S9c` is
that case.

🔴 **`upstream/BENCH-LOG.md` line 2557 is 16 bytes of `H601` at flash
`0x006000`, in a public repository**, as an `xxd`-style hexdump line — eight-hex
offset, then eight four-hex groups, then an ASCII gutter. Located without
printing a byte of it: the hit is at offset 1165 of the hex channel, which maps
to file bytes 163,238–163,275.

⚠️ **Neither existing tool identifies that line as carrying forbidden
CONTENT, and the two of them fail differently.** `leakscan` names twenty-one lines of that file (`:215`, `:216`, `:1848`, `:1931`, `:2042`–`:2044`, `:2057`, `:5186`, `:5196`–`:5197`, `:5329`–`:5330` and six `enx` lines) and **2557 is not among them** — it looks for the text shapes an address takes, and a hexdump of flash bytes has none.

⚠️ **And the two-tool claim was checked for one and ASSUMED for the other.** 量: `leakscan` does not name line 2557 at all (it names twenty-one other lines of that file). **`audit-bench-log.py` DOES name it** — on its *topic* keyword `'H601'`, and the reason is worth the sentence: the flash bytes at `0x006000` **are the ASCII characters `H`,`6`,`0`,`1`** — the region's own name, written into the flash — so the hexdump's ASCII gutter spells it. It is one of **183** hits that tool reports on that file and it **exits 0**, so it is not a gate that fails. **The accurate claim is narrower**: neither existing tool identifies that line as carrying forbidden CONTENT. One does not see it; the other touches it on a word.

### 7.4 What it changes and what it does not

**It does not change §5's decision.** `upstream/` stays as it is. The reason is
unchanged (this unit is EOL, years unused, and reset does not restore `H601` so
the value has not moved) and this line adds no exposure the decision did not
already cover: the same file publishes the MAC in colon form on twenty-one
other lines, which §4 counted and §5 decided about.

**What it does change** is one sentence. *"Nothing checks whether a committed
capture already contains forbidden content"* — the carried-forward row from
seating 8 — is **false for rlxfw's own tree as of today**, with a number:
1,381 files (excluding `upstream/`), CLEAN, and a positive control that a
rendering of the real window HITS.

🔴 **And it changed the tool's own default.** The first version of the walk
excluded `upstream/`. With it excluded the sweep of this repository is CLEAN;
with it included there is one hit. **A default that hides the only finding the
tool has ever made is not a default** — the exclusion is now `--exclude`, on
the command line where a reader can see it.

### 7.5 ⚠️ What it cannot see, and each is a real gap

* **a run shorter than 16 bytes, including a bare six-byte MAC.** That is §3's
  shape. The two instruments are complements and **neither subsumes the
  other** — this one found a line `leakscan` cannot see, and `leakscan` finds
  values that never appear as sixteen contiguous bytes of flash.
* **a byte-swapped or little-endian rendering.** The loader prints big-endian,
  which is the flash's own order, so the channel that matters here is covered;
  a capture from another instrument may not be.
* **anything inside the 98.22 %** of the region that is one repeated byte —
  by construction, and that content identifies nothing.
* **anything compressed or encoded other than plain hex**, `.git`'s objects
  included, which is why `.git` is skipped rather than scanned.

