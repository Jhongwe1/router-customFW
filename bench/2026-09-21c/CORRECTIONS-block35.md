# CORRECTIONS — block 35, seating 33

The card (`PREDICTIONS-B37-block35.md`) is frozen and is never edited. Every
departure from it is recorded here, and **§ 0 is written before the corrected
cell is executed**.

---

## § 0 `A0` ran once and stopped at `S5c`, because `--host` does not mean what I read it to mean

**Written at 2026-09-21T12:5x, before the corrected `A0` runs.**

### What happened

`A0` was invoked with `--host 10.1.1.2`. I read `--host` as *the host machine's
address*. It is not: it is **`IPCONFIG`'s argument, which is the loader's own
IP**. Three sources say so and all three were available before the run:

* `tools/looprun.py:117` — `DEFAULT_HOST = "10.1.1.1"`
* `upstream/tools/loader-tftp.py:616-617` — `--host` … *"the address `IPCONFIG`
  was given, e.g. 10.1.1.1"*
* `bench/2026-09-21b/F1-rescue.json` — the previous seating's own record:
  `IPCONFIG 10.1.1.1` → `Now your Target IP is 10.1.1.1`

So `S5` set the **loader's** IP to `10.1.1.2`, which is this host's own address
on `enxfc19286184c9`. `S5c` then asked whether `10.1.1.2` answers ARP, the
kernel routed that question to `lo` because it is a local address, and the
check failed with `dev=lo src=10.1.1.2 … no lladdr no state`.

### 🟢 The guard worked, and it is worth saying which one

`S5c` exists because a host-side fault used to be reported in the board's
vocabulary after `S6` had already spent a 12 s TFTP timeout. It stopped this
run **before `S6`**, and its two readings separate correctly: `P-a` passed (the
host does have an address on that route) and `P-b` failed (nothing answers ARP
there). Neither reading blamed the board, and neither was wrong.

### What attempt 1 produced, and what survives

| artefact | verdict |
|---|---|
| `A0-rescue.json` | 🔴 **wrong** — records `"ip": "10.1.1.2"`. Superseded by the corrected run. |
| `A0-ab2` / `.meta.json` / `.timing` | 🟢 **valid and kept.** It reads `8040D4A0: 00000000`, and the burn flag is not a function of the loader's IP. This is the card's `A0-ab2` cell and it resolves. |

### The corrected run, and why it is shaped this way

`console-capture.py` refuses to overwrite a capture, correctly, and this project
does not pass `--force` — `RESULTS-block34.md` § 1 records a stale file being
read as a measurement after exactly that. So the corrected run is:

1. **An explicitly declared off-card cell `X1-AB3`**, a second
   `DW 8040D4A0 1` taken immediately before the upload, gated on `00000000`.
   This exists so that skipping `S5b` does not cost the burn-flag reading.
   🔴 `C-6` is the measurement that says the rescue's **echo** and the word at
   `0x8040D4A0` are two different sources and have been seen disagreeing, so
   the echo alone is not evidence and this cell is not optional.
2. `looprun --skip S2,S3,S4,S5b --attempt 1 --host 10.1.1.1`.

`S5b` is skipped **only** because `X1-AB3` is its reading under another name,
taken later than `A0-ab2` and immediately before `S6`. The alternative —
`--attempt 2` — would rename `A0-2a` and `A0-boot` to `A0-att2-*` and leave two
frozen fence cells permanently unresolved, to buy a reading this cell already
provides.

---

## § 0b 🟢 `looprun` REFUSED that plan, and the refusal is the best thing in this section

**量 2026-09-21T13:0x.** The corrected run above was invoked and `looprun`
exited **2** without opening the port:

> `looprun: --skip S5b removes the read-back of the loader's burn flag, which
> RUNSHEET G2/H1a make mandatory before an upload. A guard that a flag can
> switch off is not a guard, and this one stands between an upload that lands
> in RAM and one written to the only unit there is`

`X1-AB3` had already read `00000000` and my own gate had already passed, so the
reasoning behind the skip was sound and the tool refused it anyway — **because
a precondition that the caller can argue their way past is not a
precondition.** That is the same principle as `flashwin` enforcing the `H601`
rule rather than remembering it, and it is recorded here as a property of
`looprun` measured today, not as an obstacle.

### The route actually taken

`S5b` runs. Attempt 1's two partial artefacts are moved aside under declared
names so that the completed run owns the card's cell names:

| from | to | why |
|---|---|---|
| `A0-ab2.{log,meta.json,timing}` | `X1-AB2-attempt1.{log,meta.json,timing}` | attempt 1 stopped at `S5c`; the cell `A0` never completed, so its partial artefacts are not that cell's result. Content preserved, nothing deleted, no `--force`. |
| `A0-rescue.json` | `X1-rescue-attempt1.json` | records the wrong `"ip": "10.1.1.2"`. Kept because it is the evidence for § 0. |

Both were **untracked** at the time of the move — the freezing commit
`b0e54b6` predates them — so nothing in git history is rewritten by it.

`X1-AB3`, `X1-AB2-attempt1` and `X1-rescue-attempt1` are **explicitly declared
off-card cells** and appear in no `cells` fence.

### What this does NOT excuse

The error was mine and it was available at the desk: the card's own § 6 copies
the previous seating's `A0` comment block, which does not carry `--host` at
all, and I supplied a value rather than taking the default. **A flag whose
default is correct is a flag not to pass.**
