# PREDICTIONS — Session B5, block 3b: recovering `M-b`/`M-c` after the applet that was on the list was not in the image

**Written at the bench on 2026-08-31, with the board powered and a shell up,
BEFORE either cell below was run.** It exists because `M-b` was refuted by
something the card had not considered, and a recovery cell run without a written
prediction is not a reading.

🔴 **Not to be edited after the first capture lands.**

---

## §0 What `M-b` actually returned

```
wc -lc < /dev/mtd0ro
/bin/sh: wc: not found
#
```

**48 bytes**, reply in **0.037 s**. Not a hang, not `ENODEV`, not `EACCES` —
none of the four outcomes `M-b`'s stop-if column lists.

## §1 The premise that was wrong, and it was wrong at the desk

`PREDICTIONS-B5-block3.md` §7.2 says, correctly and with two routes:

> **`wc` is present** — 量 … the binary's applet table lists 50 names and `wc`
> is one of them, with the negative control … in the same run.

🔴 **That is a claim about `busybox`. The cell needs a claim about the image.**
讀 `config/rlxfw-initramfs.tsv`: the image declares **`/bin/busybox` as a
file** and **thirteen symlinks**, of which eleven point at it —
`sh`, `ash`, `cat`, `echo`, `ls`, `mount`, `ps`, `ifconfig`, `ping`, `mkdir`,
`sleep`. **`wc` is not among them**, so `/bin/sh` searches `PATH`, finds no
`wc`, and says so.

**The applet table and the symlink set are two different populations and the
card compared against the wrong one.** `FW-26` owns the applet census and is not
wrong; what was missing is that nothing checks a card's typed commands against
the declaration of the image that card uploads. That is the same shape as the
carried-forward row *a declaration ahead of every artefact*, one turn further
on: there, a declared node was in no built image; here, a **used** command is in
no declaration.

⚠️ **The failure is benign and the seating continues.** No flash byte was read
or written, the shell is up, and `M-d` needs no applet at all — `echo` is a
shell builtin and `>` is the shell's.

## §2 The recovery, and why it is the same measurement

busybox dispatches an applet given as its first argument, so `busybox wc` runs
the same code the symlink would have reached. **`/bin/busybox` is a declared
`file` in the image**, so this needs nothing that is not already there.

| # | typed | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **M-b2** | `CAP OUT M-b2 --send 'busybox wc -lc < /dev/mtd0ro' --seconds 45` | `␣␣␣␣␣4422␣␣␣1245184` | **53** | `applet not found` → `FW-26`'s census is wrong too, and that is a bigger finding than this cell. A line count ≠ 4422 with the byte count right → the read path truncates, block 3 §7.2a |
| **M-c2** | `CAP OUT M-c2 --send 'busybox wc -lc < /dev/mtd1ro' --seconds 100` | `␣␣␣␣␣7943␣␣␣2949120` | **53** | as above, against 7943 |

**Where 53 comes from.** The same framing model block 3 §7.2 fitted and that
`M-b`'s own refutation has now validated a third time: `len(cmd) + 2` (echo
CR LF) `+ len(reply) + 2 + 2` (the `#␣` prompt).
量 on `M-b`: 20 + 2 + 22 + 2 + 2 = **48**, and 48 is what it wrote.
Here: 28 + 2 + 19 + 2 + 2 = **53**.

**The predictions are unchanged from block 3 §7.2a** — 4,422 and 7,943 newlines,
computed at the desk from the 2026-08-16 dump, with the truncating-`copy_from`
alternative bounded at ≤1,228 and ≤2,007. Nothing about the applet route changes
which bytes `mtd_read` returns.

## §3 What this block cannot claim

⚠️ **`M-b`/`M-c` are refuted as written and stay refuted.** These two cells do
not repair them; they are a different command and they are recorded as their own
cells. The card's rows keep their captures and their outcome.

⚠️ And a pass here still does not move `FLS-20`. A newline count is an
aggregate over 1.2 MB; it separates *this flash* from *a quarter of this flash*
and it places no byte.

## §4 Cells, in order

```cells
bench/2026-08-31/M-b2
bench/2026-08-31/M-c2
```

**Two cells.**
