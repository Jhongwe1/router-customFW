# PREDICTIONS — block 7: catching the prompt, and the `H2` test this cycle now makes cleaner

**Written before power is re-applied.** First block of `bench/2026-08-24d/`,
which is the power cycle that recovers the loader after `G6`'s
`J 80500000`.

## The instrument error that cost a cycle, recorded because it changed the plan

`bench/2026-08-24c/A-catch` streamed ESC from **before** power was applied —
that is the only way the loader's ~4.9 s ESC window is caught. The instruction
given for this cycle was *"pull the power, plug it back in, then tell me"*, which
puts the ESC stream **after** the window. The board autobooted into the vendor
kernel (ping `10.1.1.1` 2/2, console silent), so the loader prompt was never
reachable on that cycle.

**Cost**: one power cycle. **What was lost with it**: that cycle's `H2` test,
because a full vendor kernel boot then wrote over DRAM.

## 🔴 And the replacement test is strictly better

`H2` asks whether the structure at `0x81000400` — `00000400 00000001 FFFFFFFF
00000000` / `00000000 00000000 81000418 81000418`, a `list_head` at `+0x18`
pointing to itself — is **left by a previous boot and retained across a short
power-off**, rather than built by the loader.

For that test to mean anything, a vendor kernel has to have run immediately
before the cycle. On the cycle that was just spent, one had — but reading it
required the prompt, which was gone.

**On this cycle a vendor kernel has run twice**: `G6`'s RAM boot, and the
autoboot from flash that followed the mis-sequenced cycle. So the condition is
not merely met, it is met harder than it was in parts one and two — and the
power-off is seconds, against this morning's 16 hours.

| `X1-24d` at `0x81000400` | verdict |
|---|---|
| `00000400 00000001 FFFFFFFF 00000000` / `00000000 00000000 81000418 81000418` | 🔴 **`H2` confirmed.** The structure is **not the loader's** — it is a previous boot's, retained across a short power-off. `C-17` has been asking about the wrong writer since it was opened, and *"the loader's network buffer pool"* is withdrawn. It also means this DRAM retains **content**, not just bias, for seconds — which is a hazard for every canary this project will ever place |
| high-entropy garbage, as `X1` read this morning | **`H2` refuted too.** All three hypotheses are then dead and the structure's origin is unknown — `H1` (link-up) and `H1′` (`IPCONFIG`) still get their own tests later in this block |
| anything else | record it and stop |

## Cells

```cells
bench/2026-08-24d/A-catch
bench/2026-08-24d/A0
bench/2026-08-24d/X1-24d
bench/2026-08-24d/X3-24d
```

| | command | prediction | what it refutes |
|---|---|---|---|
| **A-catch** | `--esc 45 --seconds 65 --cr-settle 3` | boot text byte-identical to `bench/2026-08-24c/A-catch.log[1:182]`; ends on `Unknown command !` + `<RealTek>`, not on ESC; `cr.esc.written: true`, `prompt_seen: true` | 🔴 **and it re-tests the `0xFF`.** This morning's cold boot carried one leading `0xFF`, 340 ms before `Booting...`, which was marked *推* a power-on line-settle artefact. `D1` and `D4`'s warm resets produced none — consistent. **A second cold boot is the test**: `0xFF` present again ⇒ the inference holds on two cold boots and zero warm ones; absent ⇒ it was a one-off and the mark was wrong |
| **A0** | `DW 8040DBC0 1` | **71 bytes**, `8040DBC0:\t8040B070\t00000000\t80409A9C\t8040B074`, byte-identical to `24c/A0.log` | rule 1, and 1.2's terminator for the **fourth** independent time — any `Unknown command !` here refutes it |
| **X1-24d** | `DW 81000400 16` | **213 bytes.** 🔴 **Not predicted — this is the discriminator**, table above | `H2` |
| **X3-24d** | `DW 81000000 1` | **71 bytes**, word 1 = **`00000144`** | 🔴 **the third reproduction** of *something writes `0x00000144` to `0x81000000` on every boot*. Twice already this session, both times after a warm reset; this is the first cold-boot repeat since `X3` itself. Words 2–4 also test bias reproducibility across a **short** power-off against this morning's `7BB04BB7 34361357 AB2563FB` measured across a 16-hour one |

## Sequencing, and it is the whole point of this file

The capture starts **first**. Power is pulled and re-applied **while ESC is
already streaming**. 45 seconds of ESC is ~35 seconds of slack after the pull —
not a race.
