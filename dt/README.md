# `dt/` — the second binding model

`R5`'s Definition of Done asks every driver for **two** binding models, and
this directory is the second one. The first is the `platform_device` binding
under `config/rlxfw-src/linux-2.6.30/`, and that one **has run on the
silicon**.

> 🔴 **NOTHING IN THIS DIRECTORY HAS BEEN PROBED ON HARDWARE, AND NOTHING IN
> IT CAN BE.** Linux 2.6.30 — the kernel this project builds and boots on the
> TOTOLINK N150RT — has no device tree at all. `of_match_table`, `ioremap` of
> a `reg` cell, and `devm_*` do not exist there in the form these bindings
> assume. What is claimed here is exactly what `R5`'s DoD asks for and no
> more: **the `.dts` compiles, the bindings are well-formed, and the tree
> validates against them.** Whether a driver would bind to these nodes on a
> modern kernel is `R10a`'s question, and this directory is what makes `R10a`
> cheap rather than what answers it.

Every number in the source files carries the `SPEC.md` id it came from and the
mark that id holds — 量 measured on this device, 讀 read out of the datasheet
or the vendor's code, 推 inferred. A `.dts` is a description of hardware, so a
number in it that nobody measured is a claim in a file that reads like a fact.

## What is here

| | |
|---|---|
| `rtl8196e.dtsi` | the SoC: interrupt controller, timer, watchdog, GPIO, SPI flash controller |
| `rtl8196e-totolink-n150rt.dts` | the board: memory, the console, the reset button, the LED, the flash layout |
| `bindings/**/*.yaml` | one binding per block, in the mainline layout — the directory path must match the `$id` path or `dt-doc-validate` cannot resolve the file |
| `unmatched-allow.tsv` | every `compatible` in the tree that no schema in the corpus describes, with the reason. Stage C of `tools/dtcheck.py` turns an undeclared one into a finding |

## How it is checked

`python3 tools/dtcheck.py` — three stages, and the whole reason that file is a
program rather than three lines of shell is that **all three underlying tools
print a real failure and then exit 0** (量 2026-09-09, dtc 1.7.0 /
dtschema 2026.6). Read its module docstring before trusting a green.

```
python3 tools/dtcheck.py --self-test     # 23 controls; every stage's twin
python3 tools/dtcheck.py                 # the tree in this directory
```

## Three scope limits, stated rather than left to be found

1. **No C preprocessor.** Mainline runs `cpp` over a `.dts` so that
   `GPIO_ACTIVE_LOW` and friends resolve. This directory uses dtc's own
   `/include/` and writes the literal with the macro named in a comment, so
   the pipeline is exactly `dtc` → `dt-validate` and has no third moving part.
2. **`dtschema` ships the core schemas, not the kernel's.** `gpio-leds`,
   `gpio-keys` and `fixed-partitions` are kernel-subsystem bindings and are
   not in the corpus here; they are in `unmatched-allow.tsv` by name.
   `tools/dtcheck.py --extra-schema <linux>/Documentation/devicetree/bindings`
   validates against them when a kernel tree is at hand, and the report says
   which corpus ran.
3. **No third-party port has been read.** `docs/blind-write-ledger.md` § 4.6
   records the only contact this project has had with `shibajee`'s
   `rtl8196e.dtsi` — one `cpu@0` node, fetched 2026-08-25 for `CPU-25` — and
   § 6 makes the derivation check the first operation on those trees at
   `R5-9`. The nodes here were written from this repository's own
   measurements; where one of them agrees with that file, the agreement is the
   cross-check § 4.6 already names, not a copy.
