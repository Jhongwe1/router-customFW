Part of [the known-issues index](../KNOWN-ISSUES.md): entry 14 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 Two bench directories are named for a day none of their captures happened on

量 2026-09-08 by `tools/capdate.py` on its first sweep. `bench/2026-08-30` and
`bench/2026-08-30b` hold 13 and 24 captures, all taken on **2026-08-29**
(22:59:15-23:13:02 and 23:16:42-23:26:29), and `git log --diff-filter=A` shows
both directories were created before those captures existed. The name was a
prediction that the seating would cross midnight; it did not. This is
`RUNSHEET` lifecycle rule 3's own failure, seven days before that rule was
written.

They are **not renamed**: 40 and 84 references across 23 and 17 files,
including two frozen cards and three tools. They are declared by name in
`capdate.KNOWN_MISNAMED`, and the list is swept in both directions so an entry
that stops applying fails rather than sitting there.
