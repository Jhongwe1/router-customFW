# `PROGRESS.md` § `R9`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `R9`'s closing commit on 2026-10-04, once its
rows were closed. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R9`'s step list — ✅ CLOSED 2026-10-04, in three segments (120th, 121st, 122nd)

**Gate:** the differential security proof, with **zero flash writes** (§ Gate
board, row `R9`). **Opened** 2026-10-04 by the owner, continuing the relaxation
of 2026-09-27 and 2026-09-30. `R8b` stays behind it and only `R9-6` holds it:
`R8b`'s first slot write destroys the vendor firmware's ability to boot from
flash, which is this gate's control column.

### Why the definition was re-specified before anything could count

The plan's two clauses fail in **different** ways, so they take different
repairs, and neither repair is a widened tolerance.

**通過 could not fail.** Its distinctive clause — 「修不掉」那欄不是空的 — is
satisfied by seven rows committed in `plan/` § 8.2 *before* `R9` exists, so no
`R9` outcome leaves the column empty. That is the `R7` defect verbatim, which
the board's own `R7` row records: a gate whose instrument cannot fail. Replaced
by a per-row requirement, below, whose fourth clause is a reading that may not
exist.

**否證 could not be executed.** 「一條『我修好了』的測試在原廠韌體上也沒有觸發
→ 重寫」 is a sound refutation and it is inexecutable for every case needing a
shell: **the vendor firmware has no shell** (`docs/GATE-RESULTS.md`, `P2`'s
*⊘ Structural, not deferred*), and every evidenced path into vendor userspace
opens with a flash write (`VDR-1`; `formSysCmd` writes `0x00C000`, 量 `P10-10`)
inside a gate titled 零 flash 寫入. So the vendor column is re-grounded on four
evidence tiers, and **a row whose tier carries no executable refutation may not
claim absence** — it may claim only that the surface is absent, or publish 未定.

| tier | vendor-side evidence | costs a vendor boot |
|---|---|:---:|
| **`V-A`** | live, network-facing: the vendor's `boa` on 80/tcp, and 52869 and 52881 open (量, `V1-NMAP`), plus DNS as an extension — a host-side probe sends a request and reads the reply. **DHCP is out**: a DHCPDISCOVER needs a broadcast from port 68 while the host holds a static address, which is a host reconfiguration and not a probe. The vendor answers on **10.1.1.1/24, the same address as rlxfw** (量 `V1-ICMP`), so no second host address is needed — and that identity is why `R9-7` can be comparable at all | **yes**, once (`R9-6`) |
| **`V-B`** | static: the dump-derived tree and vendor source — imports, config defaults, service set | no |
| **`V-C`** | the vendor boot console — `bench/2026-09-23/V1`–`V7-BOOT`, `bench/2026-09-25/M1-BOOT`, `M2-BOOT`, already captured | no |
| **`V-D`** | needs a shell ⇒ **⊘ Structural**, cited from `P2` and never re-derived | no |

**The re-specified 通過.** The table publishes N rows, and every row carries ①
a mechanism class from the closed set ⟨架構性／有界化／服務不存在／平台限制／
不適用⟩, the primary key — **`平台限制` added 2026-10-04**, because the plan's
seven platform limits fit none of the other four and filing them `不適用`
asserts the case does not apply, which is false: it applies and rlxfw does not
fix it, which is the plan's own third column. Such a row still owes ④, and ④
there is a check that would fire if the platform *did* support the mitigation; ② a vendor cell that is a reading from `V-A`/`V-B`/`V-C` **naming
its capture or artefact**, or `⊘ Structural` naming the committed finding; ③ an
rlxfw cell **from the same instrument as ②**; ④ **a check that would have
detected the opposite of what the row claims, together with that check's
reading.** A row missing ④'s reading publishes **未定**, never as a win. The
gate **fails** if any published row lacks ④, or if the renderer accepts a
planted row saying 「我的設計修好了這條」, a mechanism outside the closed set,
or an evidence link that does not resolve — and all four refusals are shown
firing on planted rows before any real row renders.

**What this re-specification does not establish.** It does not make the gate
easier or harder to pass; it makes the outcome decidable. It says nothing about
whether rlxfw is more secure than the vendor firmware, and three of the plan's
seven sampled rows are held disclosure items at the pin — and **thirteen of
the nineteen are held**, not four (`D-3`, `D-4`, `D-9`…`D-19`; 量 from the
status column, 2026-10-04, correcting this list's own first wording, which took
the four that intersect the plan's samples for the whole set), so the published
table carries class-level rows only. This list is 12 steps; the three live figures for the gate's size are
reconciled in `LOG.md` 2026-10-04 rather than here.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R9-0`** ✅ **2026-10-04** | desk | This list, the board row, and one name for the artefact: **`docs/differential.md`**, retiring `fix-ledger.md` as a second name for the same table (plan § 6 and § 12.2 #8 against § 14.3) | The re-specified 通過 above is failable: ④ is a reading that may be absent, and the renderer's four refusals fire on planted rows before any real row renders | Re-specifying to something merely harder rather than something that can come out either way — the failure this step exists to repair |
| **`R9-1`** ✅ **2026-10-04** | desk | `config/fix-cases.toml`: one row per upstream case carrying mechanism class, evidence tier, ④'s check and reading, and the refutation written **before** the result | A row with a result and an empty refutation is REFUSED, shown on a planted row; editing a prediction changes the digest in the same commit; the unmutated suite passes before any mutation run | Assigning a tier from what is cheap to measure instead of from what the case needs — which silently converts a `V-D` into a fake `V-A` |
| **`R9-2`** ✅ **2026-10-04** | desk | The partition of upstream's 141 cases (量: 141 `[[case]]`, freeze sha256 `7ade245…85c7`) into `V-A`/`V-B`/`V-C`/`V-D`, each row's tier derivable from a cited field | Every class non-empty **or** the step states which is empty and why, rather than reporting a convenient 0; `V-D` derived from `P2`'s settled finding with no new measurement | Reading upstream's 82 device-closed results as this gate's vendor column: they came from **upstream's** instruments, and a changed instrument counts only if it reproduces the old verdicts on the same population |
| **`R9-3`** ✅ **2026-10-04** | desk | `tools/diffprobe.py` — the request/reply recorder, because **no committed tool produces both columns**: `tools/hostprobe.py` records host events with timestamps and never a packet's contents | Refuses rather than answers when undecidable; its self-test distinguishes *empty body* from *no reply*; a planted mismatch goes red; it refuses if the two columns would use a different host, cable or port | An instrument that reports 0 findings against the vendor because it never connected — a tool reporting 0 is making a claim, so this one needs a positive control that is known to trigger |
| **`R9-4`** ✅ **2026-10-04** | desk | The `V-B` static column from instruments that already exist, including `uspacescan --vendor-census` (量 on artefact 2026-09-30: 28 of 55 vendor ELFs import `system`/`popen` against rlxfw's 0) | A row claiming *the vendor triggers* that cannot be separated from *shape present, effect absent* publishes undetermined, never green (the `CVE-2014-8361` precedent, plan § 8.1) | Reading an import census as exploitability: `system` being linked is not `system` being reachable from a request |
| **`R9-5`** ✅ **2026-10-04** | desk | `quiet-swcore` built and verified on the artefact — the controlled variable the mainline lost at 8g, where `SWCORE=n` became the default and **has never booted** | Any difference beyond the `SWCORE` set withdraws 「相同的只有 NIC 與 WiFi 驅動」; the WLAN driver is listed as a difference **regardless**, because at `SWCORE=n` it is the same source and not the same object (🔄 量 2026-10-04: **11** symbol-table entries gone, not forty — 推 the forty was the kconfig count, 840 − 800 — and `sk_buff` 192 B against 200; `FW-203`, `FW-204`) | Treating same source as same object, which is the whole content of the controlled-variable claim |
| **`R9-6`** ✅ **2026-10-04** | bench + owner | **The one vendor seating, and the only step that holds `R8b`**: rlxfw → `map` → vendor autoboot by a measured path (`M1-BOOT`, `M2-BOOT` or `J 80500000`, all 量) → host runs every `V-A` probe → rlxfw → `map` | Every `V-A` probe **fails on the vendor**, and a probe that does not trigger is **rewritten, not re-graded**; the bracket is void unless both maps agree **and group 0's difference is explained rather than matched to `P2`'s 31-same/1-DIFFER pattern**; zero flash verbs and zero `FLR`, counted and stated; `n_writes` stated as carrying no information (`FW-142`) **and as blind to the vendor's own write path**. 🔴 **Two independent containments, both owed, because the vendor writes flash on an *unauthenticated* request past an uptime threshold (`FW-196`)**: ① the probe list uses only names that branch skips, and ② the whole vendor HTTP episode finishes inside the threshold, which makes the branch unreachable whatever the path. ① depends on the list being right and ② does not, and `CLAUDE.md` refuses a containment that holds only if the experiment comes out as expected; the board never left at the prompt (`NET-165`). 🔴 **`GET /config.dat` is unauthenticated on the vendor and answers a COMPCS blob** (讀): that probe records status and length **only** — no body and no digest — because this unit's own configuration, or a hash of it, may not enter the repository | Accepting the second map as clean because it looks like the first. `H601` is not hashed (`FLS-31`), so a DIFFER in group 0 is a claim about something else and has to be named |
| **`R9-7`** ✅ **2026-10-04** | bench | The rlxfw column, from the **same** instrument, host, cable and port as `R9-6` | A different tool, host or port publishes *not comparable*; a probe passing on rlxfw whose vendor cell is undetermined publishes undetermined, not as a win | Reusing `R7`'s host readings (`bench/2026-09-30/R78-host.txt`) as this column — they came from a differently declared off-card cell |
| **`R9-8`** ✅ **2026-10-04** | desk | `docs/differential.md`: four columns with 機制類別 as primary key, the **five** uncontrolled-variable classes in the header (kernel config, libc, toolchain, userspace, service set), and the held items absent | The renderer refuses a mechanism outside the closed set, an unresolving evidence link, and 「我的設計修好了這條」, each shown firing on a planted row; **no content from any of the thirteen held ids** appears, at class level or below | A class-level row that is in substance a named reproduction of a held item — plan § 15 forbids it while held, and the report has not been sent |
| **`R9-9`** ✅ **2026-10-04** | desk | `docs/threat-model.md` and `docs/hardening-matrix.md` (plan § 8.4, `REVIEW-2026-08-22.md` item 14) | No all-❌ matrix, and no ❌ without a platform reason; every evidence cell names an existing reading **or** is 未定 with a § 17 row saying what settles it — NX/RIXI and `checksec` have no reading anywhere outside `plan/`, so those cells are 未定 | Filling a cell from the plan's intention rather than a reading, which is how a matrix becomes a claim about documents instead of about the device |
| **`R9-10`** ✅ **2026-10-04** | desk | The SBOM, over the **`R7`** image manifest and not `R3`'s `config/rlxfw-initramfs.tsv` | Every component resolves to `SOURCES.json` or a nameable file; `IMG-1` ② is re-derived and not quoted, because `R7` replaced the vendor busybox and uClibc | An SBOM of the image the plan intended rather than the image that was built |
| **`R9-11`** ✅ **2026-10-04** | desk + owner | The deliverables that **cannot** complete, each ⊘ with a reason, a category and a reopening condition: `cvewatch`; `docs/disclosure.md`'s findings half; the demo recording (script committed, recording the owner's); `study/QA.md`; and `VDR-1`/`FW-67`'s silicon halves | Every ⊘ names its category and what would reopen it, by name and never by date or pattern. `cvewatch` blocks none of bricking, an `H601` leak or a misjudged result (the owner's rule of 2026-09-26). `disclosure.md` is ≥ 90 days downstream of a send that has not happened. `study/QA.md` is gitignored, and `CLAUDE.md` forbids a committed file written for a hiring panel | ⊘ used to retire a row that is merely inconvenient. `VDR-1` and `FW-67` are the one place this gate's title and its own carried-forward rows conflict: both need vendor userspace, which needs a flash write — so they are ⊘ here with the conflict named, not quietly dropped |
