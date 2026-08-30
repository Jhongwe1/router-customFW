# The leak surface: what identifies this unit, and where it already is

**Owner of one thing**: *which byte strings identify this physical device, which
of them are in a published file, and what was decided about each.* `SPEC.md`
§18 is the rule (*nothing that identifies this unit lives here*); `FLS-22` is
the number; this file is the reasoning and the record of being wrong.

Written 2026-08-30/31 (fourteenth session — it ran past midnight), at the desk, no power. Zero flash
bytes, zero power cycles, zero device readings — today that sentence holds
because the machine was not plugged in.

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
recoverable with an ambiguous position; 45 / 146 = 30.8 %.** Not recoverable:
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

## 6. What is still open

| | |
|---|---|
| `upstream/`'s 26 unreadable files | 22 `.jpg`, 2 `.png`, one undecodable `.log`, one `.pyc`. Reported **NOT SCANNED**, never counted clean (`L6`). `upstream/notes/img/README.md` is a per-image inventory with a `Redacted` column and 量 24 rows against 24 files — but a column is a **declaration**, and nothing re-decodes the pixels |
| ~~the `UNKNOWN` class~~ 🔴 **answered, by the repository, before this file was pushed** | The row said *3 hits need a person and nothing schedules that*. 讀 `upstream/tools/fwrecon/tests/test_compcs.py:255,263,307`: all three are fixtures in a unit test whose assertions are `known_mac.hex() not in rendered` and `disclosure == "protect"` — a test of upstream's **own** never-print discipline. They are synthetic by construction and not in the dump because nothing put them there. **This is the second half of the owner audit firing for the third session running**, and the lesson has not changed: a new open question has to be taken back to the repository before it is written down |
| `serial-ish` has no arbiter | 13 `NOVALUE` hits match a phrase, not a value, so `--attribute` cannot classify them. `upstream/BENCH-LOG.md:248` records that this model's `UDN`/`serialNumber` are template constants, identical on every unit — 讀, not 量, and not re-checked here |
| the dump is one source | Two full dumps exist and 量 they are byte-identical over all 4,194,304 bytes, but they were taken on the same day by the same tool. A value absent from *the dump* is not a value absent from *the device* |
| `FORBIDDEN` is copied, not derived | `flashwin.py`'s own docstring says it: its forbidden-region list is a hardcoded copy of `CLAUDE.md`'s, and nothing checks the two against each other. Adding a third region to one and not the other is a silent gap |
