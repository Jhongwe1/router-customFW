Part of [the known-issues index](../KNOWN-ISSUES.md): entry 11 of 19, moved here verbatim from that file on 2026-10-10.

## 🔴 A carriage return is invisible, and so is the tool you would use to see it

Every console capture line ends `\r\n`. `awk`'s `$2` is therefore `"1\r"` and
`[ "1\r" = "1" ]` is false. On 2026-09-08 that produced **three gates
reporting STOP or VOID on cells that had passed, each while printing the
correct value beside the wrong verdict**.

⚠️ 量 2026-09-08, while building the replacement: `cat -A` **under Git Bash
does not show the `^M` either**, because that shell translates the file on the
way in. The tool you would reach for to make a CR visible hides it. `od -c`,
or read the bytes in Python.

`tools/capfield.py` is the shared reader, and it refuses more than it answers:
a name that looks like a **mark** is refused with the reason rather than
returning empty (an empty answer reads to a caller as a failed assertion); a
field that occurs more than once is refused rather than picked (`X14-fast`'s
`dat` occurs 15 times); and `num`/`sub` **require** `--base`, because
`n_writes 0` is decimal and `sfcr FFC00000` is hexadecimal in the same dump
and `FW-35` is in this repository because `awk` read `8001e714` as scientific
notation. Its self-test runs against committed captures whose answers are
known and every other mode refuses to answer if it fails.

🆕 **2026-09-15, and this one says a line number can be undefined.** Building
`CITE-2`'s checker turned up a second consequence of a lone `\r`, on the
instrument side rather than the shell side. Python's
`subprocess(..., text=True)` applies universal-newline translation, so a bare
`\r` **becomes a line break** — `bench/2026-08-23/B.log` is 39 lines of bytes
and **59** read that way, while the same file read with `newline=""` is 39.
The first working version of `citecheck` had one side each way and reported
**76 rotted citations where there are 57**; the nineteen artefacts were all
`bench/` logs and all displaced by a *negative* amount, which is what gave it
away. Both sides now read bytes and split on `\n` only.

🔴 **What survives the fix is a stated limit, not a repair.** 量 2026-09-15:
**7 cited files hold a bare `\r`**, and in those files *line N* is not a
well-defined thing — an editor, `sed -n` and a universal-newline reader do not
agree on which line that is. `citecheck` prints the count on every run rather
than resolving it, because there is nothing to resolve: the ambiguity is in
the file.

🔴🔴 **A FOURTH consumer, 2026-09-17, and this one is not a
gate — it is a published number.** `docs/mfgtest.md` § 9.8,
`bench/2026-09-17/CORRECTIONS-block23.md` and `LOG.md` all quote
**`ae87ac03269985d6`** as the digest over the 32 lines of `MT-FLASH-3`'s flash
map, and it is the number carrying *4,186,112 bytes are unchanged across eight
days*. 量: `sed -n '19,50p' X8-M0.log \| sha256sum` returns
**`70484defc9714ecc…`**. The published value comes back only after
`tr -d '\r'`, **and none of the three files says so.** Negative control: 31 of
the 32 lines give a third value.

⚠️ **The direction matters.** The first three instances failed
loudly — a gate said STOP on a cell that had passed. This one fails
quietly and in the wrong direction: a reader re-deriving the digest from the
committed capture gets a different answer and concludes **the flash moved**.
The normalisation is now written down in `docs/mfgtest.md` § 9.8 and
`SPEC.md` `FW-92`; **nothing enforces it**, and no other published digest in
this repository has been checked the same way.
