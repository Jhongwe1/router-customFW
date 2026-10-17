# kernel/

rlxfw's own kernel sources, laid out as they sit in the staged Linux 2.6.30
tree. None of these files is Realtek's.

The kernel is the vendor's, from the GPL drop pinned in
[`SOURCES.json`](../SOURCES.json). [`tools/rlxfw-kbuild.sh`](../tools/rlxfw-kbuild.sh)
stages that tree, and [`tools/rlxfw-marks.py`](../tools/rlxfw-marks.py), driven by
[`config/rlxfw-marks.tsv`](../config/rlxfw-marks.tsv), copies these files into it
and adds the lines that build them. The vendor's own files change only through
that table and the patches in [`config/host-compat/`](../config/host-compat/);
[`docs/vendor-modifications.md`](../docs/vendor-modifications.md) records every
change. Every byte under `kernel/` and `config/` is an input to `RECIPE_ID`, the
build identity the image prints at boot.

[`LICENSE`](LICENSE): GPL-2.0-only, forced by the kernel these files link into.

## The drivers

| file | what it is | notes |
|---|---|---|
| [`drivers/clocksource/rtl819x-timer.c`](linux-2.6.30/drivers/clocksource/rtl819x-timer.c) | a clocksource on Timer/Counter 1 | [timer-driver](../notes/timer-driver.md) |
| [`drivers/gpio/rtl819x-gpio.c`](linux-2.6.30/drivers/gpio/rtl819x-gpio.c) | a gpiolib `gpio_chip` on the PABCD port | [gpio-driver](../notes/gpio-driver.md) |
| [`drivers/input/keyboard/rtl819x-keys.c`](linux-2.6.30/drivers/input/keyboard/rtl819x-keys.c) | the board's buttons, polled, as an input device | |
| [`drivers/watchdog/rtl819x-wdt.c`](linux-2.6.30/drivers/watchdog/rtl819x-wdt.c) | a `/dev/watchdog` on `WDTCNR` | [watchdog-driver](../notes/watchdog-driver.md) |
| [`drivers/mtd/devices/rtl819x-spi.c`](linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c) | a read-only MTD device on the SPI flash controller, by programmed I/O | [spi-mtd-driver](../notes/spi-mtd-driver.md) |
| [`drivers/mtd/devices/rtl819x-spi-write.c`](linux-2.6.30/drivers/mtd/devices/rtl819x-spi-write.c) | the flash write path: its policy, its counters, two MTD entry points; off in every committed image | [spi-mtd-driver](../notes/spi-mtd-driver.md) |
| [`drivers/mtd/devices/rtl819x-spi-wrpolicy.h`](linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h) | every refusal the write path makes, as pure arithmetic | |
| [`drivers/mtd/devices/rtl819x-spi-install.h`](linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h) | every decision the slot install path makes, as pure functions | |
| [`drivers/net/rtl819x-nic.c`](linux-2.6.30/drivers/net/rtl819x-nic.c) | the CPU-port DMA driver | [nic-driver](../notes/nic-driver.md) |
| [`drivers/net/rtl819x-nic-tx.h`](linux-2.6.30/drivers/net/rtl819x-nic-tx.h) | the TX policy's declarations, and the part of it that touches no hardware | [nic-driver](../notes/nic-driver.md) |
| [`drivers/net/rtl819x-switch.c`](linux-2.6.30/drivers/net/rtl819x-switch.c) | the switch-core driver | [switch-driver](../notes/switch-driver.md) |
| [`drivers/net/rtl819x-view.c`](linux-2.6.30/drivers/net/rtl819x-view.c) | a read-only view of the switch registers, MIB counters and tables, at `/proc/rtl819x-view` | |
| [`drivers/net/rlxfw-seam.c`](linux-2.6.30/drivers/net/rlxfw-seam.c) | what code outside the vendor Ethernet tree still needs from it when that tree is not built | |
| [`drivers/char/rlxfw-entropy.c`](linux-2.6.30/drivers/char/rlxfw-entropy.c) | an entropy source, and its credit policy | [entropy](../notes/entropy.md) |

## The rest

| file | what it is |
|---|---|
| [`arch/rlx/kernel/rlxfw-devices.c`](linux-2.6.30/arch/rlx/kernel/rlxfw-devices.c) | the board's platform devices |
| [`arch/rlx/kernel/rlxfw_mark.c`](linux-2.6.30/arch/rlx/kernel/rlxfw_mark.c) | rlxfw's boot marks, and the reasoning behind them |
| [`include/linux/rlxfw-mark.h`](linux-2.6.30/include/linux/rlxfw-mark.h) | the boot marks' header |
| [`include/linux/rlxfw-entropy.h`](linux-2.6.30/include/linux/rlxfw-entropy.h) | the interface between rlxfw's drivers and its entropy accounting |
