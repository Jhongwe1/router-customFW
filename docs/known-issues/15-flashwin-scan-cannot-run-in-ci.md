Part of [the known-issues index](../KNOWN-ISSUES.md): entry 15 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 The check that asks whether a committed file holds forbidden flash bytes cannot run in CI, and has been invoked wrong

`tools/flashwin.py scan` is the only instrument that asks, **by the bytes**,
whether a file this repository has already committed contains content from
`H601` or the loader region. It needs `--dump` — the 4 MiB reference dump —
and that dump may never be committed, because it identifies one physical
device.

**So the check is desk-only by construction.** 量 2026-09-15 on
`.github/workflows/ci.yml`: CI runs `flashwin --self-test` and
`tools/test-flashwin-mutants.py` and **no step runs `scan`**. Those two say
the tool works; neither says anything about what is in the tree.

🔴 **And a desk-only check has nobody to notice that it did not run.** 量
2026-09-15: a `co-flashwin-scan.out` dated **2026-09-10** sits in
`$FWRE_WORK/rebuild/` and its entire content is
`flashwin.py scan: error: the following arguments are required: --dump`. 推:
that closeout's cell did not run and the error was not read. The same
invocation was made again on 2026-09-15 and caught the same way — by reading
the output instead of the exit line.

🟢 Run correctly on 2026-09-15 it reads **CLEAN over 4,441 files with 113
distinct 16-byte probes**. That is the reading; the issue is that nothing
makes it happen.

⚠️ What would close this is not a CI step — it cannot be one. It is a closeout
script that names `--dump` explicitly and fails loudly without it, and the
place that owns the closeout list is `CLAUDE.md`, which is the owner's file.

🔴 **2026-09-15, seating 23's closeout: a THIRD occurrence, and the half that
was missing is now the half that worked.** The closeout ran `scan` without
`--dump` for the third time — 2026-09-10, 2026-09-15 (seventy-second segment),
and again here. **What changed is that the closeout was a script that captured
each gate's output and printed `RED <name> (rc=2)` with the first lines of it**,
so the failure was read in the same minute rather than sitting in a `.out` file
for five days. Re-run correctly it reads **CLEAN over 4,467 files with 113
distinct 16-byte probes**, against `$FWRE_WORK/dumps/flash-n150rt-console-2.bin`
— the dump `notes/flash-digest-scope.md` names.

⚠️ **The remaining half is still open and it is the one this row asked for**:
the script had to be told `--dump` by a human after it went red, so a fourth
occurrence is available to anyone who writes the closeout from memory again.
🔴 **And a second failure mode was found the same way**: the same closeout
invoked `tools/xcheck.py check`, which does not exist — the mode is `sweep` —
and that produced a second `RED` that was also a misuse and not a finding.
**Two of the eight gates went red for reasons that had nothing to do with the
tree**, which is the shape that trains a reader to skim reds. Run correctly,
`xcheck sweep` reads 1,242 artefacts, 3 identities, 0 disagreements.
