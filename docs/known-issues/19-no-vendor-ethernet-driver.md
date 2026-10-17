Part of [the known-issues index](../KNOWN-ISSUES.md): entry 19 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 The mainline image has no vendor Ethernet driver, so `R9`'s controlled variable holds only in `quiet-swcore` — 2026-09-28 (`R6b-8` 8g)

Since `R6b-8`'s 8g the mainline kernel configuration — `quiet` and `loud` in
`config/rlxfw-kernel.delta` — is `CONFIG_RTL_819X_SWCORE=n`: the vendor's
`drivers/net/rtl819x/` and `rtk_vlan.o` are out of the link (讀 the drop's
`drivers/net/Makefile`, `obj-$(CONFIG_RTL_819X_SWCORE) += rtl819x/built-in.o`), and the
Ethernet port has one driver, rlxfw's `rtl819x-nic` (`rlx0`). The `SWCORE=y`
configuration goes on building as `quiet-swcore` (`tools/kconfig-delta.py` `VARIANTS`),
the owner's ruling of 2026-09-26 that the `y` config build from every later tree.

**What depends on it**: `R9`'s differential test. The plan's `D16` builds the vendor's
`drivers/net/rtl819x/` into rlxfw's kernel as a controlled variable, so that the network
driver is the same vendor code in both columns of `R9`'s table (`plan/README.md`,
gitignored: its v3 → v4 table, change 3; `RUNSHEET.md`'s `K6` calls it *D16's controlled
variable*). The mainline default no longer has that property: an image built with
`--variant quiet` — `tools/looprun.py`'s default — carries rlxfw's NIC driver and not the
vendor's, and an `R9` column built from it would add the NIC driver to what differs between
the columns. **`R9` must build from `quiet-swcore`**, the variant that still carries the
vendor's `drivers/net/rtl819x/`; there the delta's `CONFIG_RLXFW_VENDOR_ETH_OPEN` row (`y`,
common to every variant) keeps the vendor's `eth*` openable.

The plan's other identical driver, the WLAN driver, is the same source at `SWCORE=n` and
not the same object. 🔄 **量 2026-10-04 this was counted on the artefact, and the count
replaces a 讀 estimate that was wrong**: its `built-in.o` loses **11** symbol-table
entries — four functions — and **6** references at `SWCORE=n`, not the forty this entry
said, and `struct sk_buff` is **192** bytes there against **200** rather than
unquantified. Five of the ten names the seam defines are its references, so it links
against rlxfw's stand-ins for them (`notes/switch-driver.md` §§ 13.3, 13.7, 13.10, and
§ 19.4 for the retraction). In `quiet-swcore` both drivers are the vendor's objects as
built at `SWCORE=y` — and 量 the same day, rlxfw's own `rtl819x-nic.o` differs across the
flip too, so of the two drivers this entry calls identical, neither is the same object.

What this does not establish: that a `quiet-swcore` image's `eth*` carries traffic — 8g
ran nothing on the silicon; that `quiet-swcore` makes the NIC column of `R9` equal to the
vendor firmware's, whose kernel configuration, toolchain and userspace still differ (the
plan's own list of what `R9` does not control); anything measured — this entry is 讀 from
the declaration, the plan and the notes it cites.
