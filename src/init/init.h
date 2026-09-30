/* init.h -- R7: PID 1's compile-time knobs and the SPEC § 4 key ids it reads.
 *
 * The ids WERE the numbers from SPEC-R7 § 4, transcribed here so that init did
 * not depend on another agent's spelling.  `R7-8` collapsed the four
 * transcriptions of that table onto src/lib/schema.h, which now carries the
 * CFGID_* spellings as aliases of its own CFG_ID_*; 量 that init's nine literals
 * had agreed with it on all nine.  init still reaches the store only through
 * SPEC-R7 § 5's pinned functions.
 */

#ifndef RLXFW_INIT_H
#define RLXFW_INIT_H

/* SPEC-R7 § 4 ids, from their one owner. */
#include "schema.h"

/* SPEC-R7 § 3 paths. */
#define PATH_CFG "/var/lib/cfg.bin"
#define PATH_UDHCPD_CONF "/var/udhcpd.conf"
#define PATH_UDHCPD_LEASES "/var/udhcpd.leases"
#define PATH_BUSYBOX "/bin/busybox"
#define PATH_IFUPD "/sbin/ifupd"
#define PATH_SHELL "/bin/sh"
#define PATH_CONSOLE "/dev/console"

/* ------------------------------------------------------------ bench profile */
/*
 * 1 = fork a shell on the console and SAY SO, loudly, on every boot.  0 = do
 * not, and say that too.  Default 1 for R7's first boots (the brief's call).
 * Build the shell out with:
 *
 *   make -C src/init target O=… TC=… TRIP=… BENCH_SHELL=0
 *
 * The kernel command line can turn the shell OFF in a build that has it
 * (`rlxfw.noshell`) but can never turn it ON in a build that does not.  A door
 * that a command line can open is a door.
 */
#ifndef RLXFW_BENCH_SHELL
#define RLXFW_BENCH_SHELL 1
#endif
#define CMDLINE_NOSHELL "rlxfw.noshell"

/* ------------------------------------------------------------- interfaces */
/*
 * 讀 config/rlxfw-init.sh: every seating since B30 brought the LAN up on
 * `rlx0`, which is rlxfw's own `rtl819x-nic` netdev.  未定: no netdev has been
 * shown to carry the WAN on an rlxfw image -- R6-6 (per-port VLAN) was not met,
 * so `RLXFW_WAN_IF` is a placeholder and `wan.mode` defaults to 0, which means
 * udhcpc is not started and the name is never used.  Override both with
 * -DRLXFW_LAN_IF='"eth0"' if a measurement says otherwise.
 */
#ifndef RLXFW_LAN_IF
#define RLXFW_LAN_IF "rlx0"
#endif
#ifndef RLXFW_WAN_IF
#define RLXFW_WAN_IF "eth4"
#endif

/*
 * 1 = write the five /proc verbs that `config/rlxfw-init.sh` writes before its
 * `ifconfig`, in the same order (switch core first: B43's control shows rlx0
 * carries nothing without it).  0 = write nothing to any /proc node and open no
 * interface, which is what `config/rlxfw-init-quiet.sh` is for -- R6b's NET-25
 * needs eth4 to be the first interface opened after power-on.
 */
#ifndef RLXFW_SWITCH_BRINGUP
#define RLXFW_SWITCH_BRINGUP 1
#endif

/* The rung-1 discriminator.  It must stay byte-identical: tools/bootbytes.py
 * compares it across every committed rlxfw boot and RUNSHEET.md B5/P6 checks
 * that this unit's own kernel and rootfs do not contain it. */
#define RLXFW_RUNG1_LINE "rlxfw: init running, RLXFW-R3-RUNG1-OK"

#endif /* RLXFW_INIT_H */
