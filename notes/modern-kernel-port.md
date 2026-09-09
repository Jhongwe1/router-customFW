# Porting a driver written for 2.6.30 to a current kernel

`R5-12` ②.  `PROGRESS.md`'s `D2` has two clauses: each driver has a
compile-tested DT binding (done, forty-ninth segment) **and** the driver
itself compiles in a modern kernel tree.  The second was neither confirmed nor
refuted: the forty-ninth segment measured it by counting identifiers and
recorded that the method could not see a symbol whose *signature* changed, so
its figure was a lower bound.  This file is the experiment that settles it for
one driver.

`rtl819x-wdt` is the driver, chosen by the forty-ninth segment because it had
the smallest missing set.

---

## 1.  Which kernel, and why it is not the one the census used

量 2026-09-09, `https://www.kernel.org/releases.json`:

| moniker | version | eol |
|---|---|---|
| mainline | 7.3-rc2 | no |
| stable | 7.2.4 | no |
| longterm | **6.18.50** | no |
| longterm | 6.12.109 / 6.6.156 / 6.1.187 / 5.15.220 / 5.10.269 | no |

🔴 **6.8 is not on that list at all.**  The census was run against
`linux-headers-6.8.0-139`, which is Ubuntu 24.04's GA kernel and is what this
host has installed.  🔴 **Two sentences that stood here are withdrawn as
unmeasured**, and the second contradicted the one above it: *"upstream stopped
maintaining 6.8 long before this segment"* — the listing says it is absent
today and nothing here dates its removal — and *"a claim about a kernel nobody
ships"* — Ubuntu 24.04 ships it, which is the whole reason the headers are on
this host.

What is measured is narrower and enough: **6.8 is absent from the maintained
list, and 6.18.50 is the newest entry marked `longterm` with `iseol: false`.**
A distribution kernel and an upstream-maintained one are different claims, and
only the second is what *"compiles in a modern kernel tree"* is asking about.
The target here is **6.18.50**.

That choice is not free: it means the census's numbers and this compile are
against **different trees**, and § 4 separates the two effects rather than
pooling them.

Tree: `linux-6.18.50.tar.xz`, 154,612,024 bytes, sha256
`d2fc041dab4e11d9645e3ba53be058faa52b8ce28a8a97c889bb2cacee170461`, unpacked to
1.7 GiB.  Configuration `malta_defconfig` + `CONFIG_WATCHDOG=y` +
`CONFIG_PROC_FS=y`, `ARCH=mips`, `CROSS_COMPILE=mips-linux-gnu-`
(GCC 12.4.0).  Nothing here claims mainline supports the Lexra RLX4181 — it
does not — and nothing needs it to: the question is whether the C compiles
against modern kernel APIs, and `malta` is the mainline configuration whose
word size and endianness match this part.

---

## 2.  The instrument's controls, which is where the first defect came from

🔴 **`make drivers/watchdog/X.o` on a file kbuild declines to build exits 0 and
prints nothing, which reads exactly like "compiles clean".**  Every number
below is void unless the build system can be shown to fail and to succeed.

| control | what it asserts | 量 |
|---|---|---|
| `C0a` | a file containing `#error` must FAIL | rc **2**, the `#error` text present, **no object produced** |
| `C0b` | a trivially valid file must build, and the object must carry its symbol | rc **0**, 1,204-byte object, `rlxfw_ctl_ok_marker` present |

🔴 **And `C0b` caught something nobody was looking for.**  It runs
`objdump -f` on the object it produced, and the first run printed
**`elf32-tradlittlemips`**.  `malta_defconfig` is little-endian; the RTL8196E
is big-endian, and `CLAUDE.md`'s whole `-march=mips32` rule exists because this
part's details are not negotiable.  The tree was switched
(`CONFIG_CPU_BIG_ENDIAN=y`, re-`prepare`) and now produces
**`elf32-tradbigmips`, `mips:isa32r2`**.

🟢 **The endianness change is also a control on the result**: the round-0
diagnostics are **identical, line for line, in both endiannesses**.  So the
port measured below is an API question and not an endianness question — which
is worth having in writing, because it is exactly the sort of thing a reader
would otherwise assume.

---

## 3.  The ladder

**Prediction, written before the first rung ran: 6 → 5 → 4 → 3 → 0
diagnostics, and each rung removes only its own.**

| rung | change | rc | errors | warnings | object |
|---|---|---:|---:|---:|---|
| `R0` | none — verbatim, 1,547 lines | 2 | **6** | 1 | — |
| `R1` | `del_timer_sync` → `timer_delete_sync` | 2 | 5 | 1 | — |
| `R2` | drop `.llseek = no_llseek` | 2 | 4 | 1 | — |
| `R3` | `setup_timer` → `timer_setup`, callback takes `struct timer_list *` | 2 | 3 | 1 | — |
| `R4` | `create_proc_entry` + `->read_proc`/`->write_proc` → `proc_create` + `proc_ops` | 2 | 🔴 **4** | 2 | — |
| `R5` | move the shim block below the two handler definitions | **0** | **0** | **0** | **22,696 B** |

🟢 **`R1`, `R2` and `R3` hit the prediction exactly.**  Each removed its own
diagnostic and introduced none.

🔴 **`R4` refuted it — 3 → 4, not 3 → 0 — and the cause is mine, not the
kernel's.**  The four are `implicit declaration of ‘rtl819x_wdt_read_proc’`,
the same for `..._write_proc`, and two `static declaration follows non-static
declaration`.  The shim block was inserted before `struct miscdevice` at line
1085 and the two handlers are defined at 1157 and 1387: C wants the
declaration first.  It is recorded as its own rung rather than folded into
`R4` because *the fix is a move* — no API is involved — and a ladder that
quietly renumbered would have hidden a wrong prediction.

**`R0` had zero *fatal* errors**, which is the reason a ladder was possible at
all.  A missing `#include` is fatal and stops the compiler, so one masking
header would have made this a serial hunt with one error visible at a time.
`<asm/uaccess.h>` was the expected candidate and it still resolves on
`arch/mips`.

### The object is real

```
elf32-tradbigmips   mips:isa32r2   22,696 bytes   178 symbols
rtl819x_wdt_init  rtl819x_wdt_proc_ops  rtl819x_wdt_fops
rtl819x_wdt_tick  rtl819x_wdt_miscdev          all present
```

### The size of the port

**`+46 / −10` lines against 1,547 = 3.62 % of the file, in 8 hunks, over 4
distinct APIs.**  ⚠️ **That counts blank added and removed lines, which is
`diff -u`'s own convention**; this port adds five blank lines and removes
one, so a re-derivation with `grep '^+[^+]'` — a pattern that cannot match
a line consisting of just `+` — gives **`+41 / −9` = 3.232 %** instead.
量 both, stated here because the first re-derivation of this number used
that pattern and disagreed with the published figure until the convention
was the thing examined rather than the figure.  🔴 **The first draft of this sentence said *34 are the `/proc` shim … the
other three APIs are one line each*, and both halves are wrong.**  量, by
assigning every added line so the classes sum to 46: the shim block is
**39** lines (6 of them its comment), and the `/proc` change costs **42**
once its `<linux/seq_file.h>` include and its two-line `proc_create` call
are counted with it.  That leaves **4**: `timer_setup` costs two — the call
and the callback's signature — `timer_delete_sync` one, one blank line, and
dropping `no_llseek` adds nothing at all.  **So one API is 91 % of the
port**, which is a more useful thing to know than a per-API average.

---

## 4.  Scoring the forty-ninth segment's census

That census predicted **3** identifiers for this driver, and the union's
commentary named them: `create_proc_entry`, `read_proc`, `write_proc`.

The instrument is the census's own method — is the identifier present under a
tree's `include/` — run over three trees, with `kmalloc` and `request_irq` as
controls that must read *present* everywhere.

🔴 **The controls fired on the first run and voided the whole table.**  The
2.6.30 path was written as `src-vendor/linux-2.6.30/include`; the drop is one
level deeper (`src-vendor/rtl819x-toolchain/linux-2.6.30`), the directory did
not exist, `find` reported **0 header files**, and every identifier including
`kmalloc` came back *not 2.6.30 kernel API*.  **This is the same failure the
census's own positive control caught one segment earlier** — an index pointed
at a directory with no headers — and it is caught the same way, by two
identifiers with known answers rather than by the table looking reasonable.

With the path corrected (2,073 / 6,078 / 6,508 header files):

| identifier the compiler named | 2.6.30 | 6.8 | 6.18.50 | verdict |
|---|---|---|---|---|
| `create_proc_entry` | yes | no | no | ✅ census flagged it |
| `read_proc` | yes | no | no | ✅ census flagged it |
| `write_proc` | yes | no | no | ✅ census flagged it |
| **`setup_timer`** | yes | **yes** | **yes** | 🔴 **census MISSED it** |
| `del_timer_sync` | yes | yes | no | outside the census's reach |
| `no_llseek` | yes | yes | no | outside the census's reach |
| `kmalloc` *(control)* | yes | yes | yes | — |
| `request_irq` *(control)* | yes | yes | yes | — |

### 🔴 Why `setup_timer` was missed, and it is a mechanism the census did not declare

量 — the **only** occurrence of `setup_timer` under 6.8's and 6.18's `include/`:

```
include/linux/serial_8250.h:97:  void  (*setup_timer)(struct uart_8250_port *);
```

It is a **member of an unrelated struct in an unrelated subsystem**.  The
census asks *does this identifier appear anywhere under `include/`*, sees that
line, and concludes the symbol survives.  The compiler says
`implicit declaration of function ‘setup_timer’`.

The forty-ninth segment declared one blind spot — *a symbol that still exists
with a changed signature* — and this is a different one: **a symbol that does
not exist as an API at all, whose name collides with a member of some other
structure.**  Both under-count, so the direction of the stated conclusion is
unchanged, but the declared limit does not name this mechanism and now does.

### The 6.8 → 6.18 term, separated

`del_timer_sync` is in 6.8's `include/linux/timer.h` and absent from 6.18's.
`no_llseek` is in 6.8's `fs.h` and `debugfs.h` and absent from 6.18's.  Both
are honest consequences of targeting the current longterm instead of the EOL
kernel the census used — **not** census defects.

**So: against 6.8 the true figure for this driver is 4, where the census said
3 — under by one in four.  Against 6.18.50 it is 6.**

---

## 5.  All four drivers, round 0 — and this refutes § 4's own conclusion

The paragraph that used to open § 6 read *"the plan's ~0.3-segment estimate
survives the experiment built to test it"*.  That was written after compiling
**one** driver, and the forty-ninth segment had chosen that driver **because it
had the smallest missing set**.  Compiling the other three takes minutes, so
there is no excuse for generalising from one.

🔴 **First, the instrument had a defect and one file compiled twice is what
caught it.**  The copies were first named `<driver>.verb.c`; kbuild derives
`KBUILD_MODNAME` from the filename, a dot is not a valid C identifier, and
every driver picked up an extra
`<command-line>: error: expected ‘=’ … before ‘.’ token`.
量: `rtl819x-wdt` read **7** errors under that name and **6** under its own.
Renamed without dots, and the wdt column returns to 6 — which is the control.

| driver | lines | census said (vs 6.8) | gcc diagnostics (vs 6.18.50) | root causes 🔄 | |
|---|---:|---:|---:|---:|---|
| `rtl819x-timer` | 2,813 | 8 | **1, and it is FATAL** | **9** | `asm/rlxregs.h` not found |
| `rtl819x-gpio` | 673 | 3 | **24** | **4** | **20** cascade from one incomplete type |
| `rtl819x-spi` | 1,738 | 5 | **18** | **5** | five or six distinct API changes |
| `rtl819x-wdt` | 1,547 | 3 | **6** | **4** | 4 root causes, measured by § 3's ladder |

⚠️ **A diagnostic count is not a root-cause count and must not be quoted as
one.**  ~~Only `rtl819x-wdt` has a *measured* root-cause count — 4 — because only
it was put through a ladder in which each rung removed exactly its own
diagnostics.  For the others the count below is a count of lines gcc printed.~~
🔄 **2026-09-10: all four have ladders now and the column above is measured —
see § 9.**  The warning does not move; what moves is which rows it applies to.
🔴 **And § 9 adds a SECOND thing a diagnostic count is not: a count of EDIT
SITES.**  Two mechanisms were measured that make a round-0 figure a **floor**,
and one of them raised `gpio` from 24 to 25.

### 🔴 `gpio` and `spi`: the census's DECLARED blind spot dominates

`rtl819x-gpio`: 🔴 **the first draft of this line said *21 of the 24*, and
量 — classifying every diagnostic so the classes have to sum to 24 — it is
**20**, plus one `gpiochip_add` and three `/proc`.  The 21st is a different
diagnostic arising from the same header move, which is not the same
sentence.**  So: **20 of the 24** are `struct gpio_chip` used as an
**incomplete type** — `has no member named ‘label’`, `‘owner’`, `‘request’`, `‘free’`,
`‘direction_input’`, `‘get’`, `‘direction_output’`, `‘set’`, `‘to_irq’`,
`‘base’`, `‘ngpio’`, `‘can_sleep’`, then `invalid use of undefined type` six
times.  **The name `gpio_chip` still exists**; mainline moved its definition out
of `<linux/gpio.h>` and into `<linux/gpio/driver.h>`.  An identifier census sees
the name in both trees and scores it as surviving.

`rtl819x-spi`: `struct mtd_info` **has no member named ‘read’; did you mean
‘_read’?** — and the same for `write` and `erase`; `struct erase_info` has no
`state` and no `mtd`; `MTD_ERASE_FAILED` is gone; `struct shash_desc` has no
`flags`; `add_mtd_device` is an implicit declaration.  Again: `mtd_info` and
`erase_info` both still exist, under their own names, with different members.

**This is exactly the limit the forty-ninth segment wrote down** — *a symbol
that still exists with a changed signature* — and it was declared without being
measured.  It is measured now, and on two of the four drivers it is the
majority of the work.

### 🔴 `timer`: a third category the census could not have a name for

`rtl819x-timer` does not reach a single API diagnostic.  It stops at

```
<copy of rtl819x-timer.c>:409:10: fatal error: asm/rlxregs.h: No such file or directory
```

*(The compiler names the throwaway filename the copy was given inside the 6.18
tree.  It is elided here on purpose: `ledgerscan check` reads a path shaped
like a driver tree as a CITATION that the blind-write ledger has to cover, and
it is right to — it cannot tell a scratch copy from a path this project has
read.  The line is `rtl819x-timer.c:409`,
`config/rlxfw-src/linux-2.6.30/drivers/clocksource/`.)*

量: that header exists only at
`arch/rlx/include/asm/rlxregs.h` (with a copy under `arch/mips/include/asm/` in
the same drop) — it is the **vendor's** architecture header, and **mainline has
no `arch/rlx` at all**.  So this is neither a removed identifier nor a changed
signature: it is an `#include` of a platform that upstream does not have.  An
identifier census cannot see an `#include`, and no kernel version will ever
provide this one.

⚠️ **`rtl819x-timer`'s cost is therefore UNMEASURED, not small.**  The fatal
masks everything behind it, and the work needed before it can even be counted
is to decouple the driver from `arch/rlx`'s register header.

---

## 6.  The answer to `D2` ②

🟢 🔄 **2026-09-10: ALL FOUR compile in a current-longterm kernel tree**, each
through its own ladder, each object produced and checked.  ② is answered.

| driver | ladder | code churn | all churn | object | symbols |
|---|---|---:|---:|---:|---:|
| `rtl819x-timer` | 25 → 20 → 19 → 18 → 7 → 6 → 4 → 3 → **0** | **4.19 %** | 6.65 % | 37,300 B | 268 |
| `rtl819x-gpio`  | 24 → 5 → 4 → 1 → **0** | **6.98 %** | 10.55 % | 11,512 B | 109 |
| `rtl819x-spi`   | 18 → 11 → 6 → 5 → 4 → **0** | **4.66 %** | 7.59 % | 27,572 B | 210 |
| `rtl819x-wdt`   | 6 → 5 → 4 → 3 → 4 → **0** | **2.84 %** | 3.62 % | 22,696 B | 178 |

*Code churn* excludes added comment lines; *all churn* is the raw
`diff -u` figure and is what § 3's published 3.62 % is.  Both are given
because these ports are heavily commented on purpose and a churn number that
counts the explanation of a change as part of its cost is not a port cost.
The wdt row was **re-derived by this segment's own counter** and reproduces
`+46 / −10 = 3.62 %` exactly, which is the control on the counter — the
forty-ninth segment's defect ⑪ was a re-derivation tool that was itself wrong.

🔴 **The previous version of this section said ② was NOT answered for the other
three and that the plan's ~0.3-segment estimate "survives for this driver",
warning that generalising from `rtl819x-wdt` would be generalising from the
driver chosen for being easiest.  That warning was right and now has a
magnitude**: code churn across the four is **2.84 %–6.98 %**, a spread of
**2.46×**, and `wdt` is indeed the cheapest of the four.  The suspicion was
correct; the factor is 2.46, not an order of magnitude.

⚠️ **Churn does not scale with file size, on n = 4.**  The largest file
(`timer`, 2,813 lines) is the second *cheapest* at 4.19 % and the smallest
(`gpio`, 673) is the dearest at 6.98 % — the opposite order to what "a bigger
driver is a bigger port" would predict.  What the cost tracks is **which
subsystems the driver touches and whether any of them was reworked**: `gpio`
touches one subsystem that had a wholesale rework, `timer` touches five that
each drifted cheaply.  n = 4 and this is written as an observation, not a rule.

🔴 **`timer` was the one with no measured cost and it is not the expensive
one.**  The forty-ninth segment recorded its cost as *unmeasured, not small*,
because one fatal `#include` masked everything behind it.  Measured: the arch
coupling is **one line**, the replacement header supplies all three symbols it
was included for, and the eight API rungs behind it are ordinary drift.  The
honest sentence is the one that segment already wrote — the fatal made it
unmeasured — and this segment must not upgrade that into "it was hard".

⚠️ **What this does NOT establish, stated rather than left to be assumed:**

* **It compiles; it has never run.**  There is no 6.18 kernel on this part and
  there will not be one inside `R5`.  Nothing here is a claim about behaviour.
* **Compiling is not upstream acceptance**, and `D1`'s bar is *accepted
  upstream-style*.  Two things in this driver would not survive review and
  neither is a compile error: it is a hand-rolled `miscdevice` on
  `WATCHDOG_MINOR` where a modern driver registers a `struct watchdog_device`,
  and its `/proc` file is instrumentation that upstream would want in debugfs
  or nowhere.  **The port measured here is the floor, not the ceiling.**
* **The `/proc` shim preserves a 2.6.30 contract on purpose.**  It hands
  `rtl819x_wdt_read_proc` one `__get_free_page()` page, which is exactly the
  buffer that function was written against — no bounds check, one page — so
  the port changes the interface and not the behaviour.  A rewrite into
  `seq_file` proper would change what the bench reads, and the bench is what
  frozen cards predict against.
* **The three other drivers have a round 0 and nothing else.**  § 5 has their
  diagnostic counts; none has a ladder, so none has a *root-cause* count, and
  none has a port.  `rtl819x-timer`'s is not even a lower bound — its one
  diagnostic is fatal and masks whatever is behind it.
* **`config/rlxfw-src/` is untouched.**  Editing it would move `RECIPE_ID`,
  which is a digest over `config/`, and invalidate the image that has run on
  the silicon.  The port lives here as a diff and nowhere else.

---

## 7.  The port (`rtl819x-wdt` only)

```diff
--- rtl819x-wdt.c	(2.6.30, config/rlxfw-src/linux-2.6.30/drivers/watchdog/)
+++ rtl819x-wdt.c	(6.18.50)
@@ -416,6 +416,7 @@
 #include <linux/proc_fs.h>
+#include <linux/seq_file.h>
 #include <linux/spinlock.h>
@@ -839,7 +840,7 @@
-static void rtl819x_wdt_tick(unsigned long unused)
+static void rtl819x_wdt_tick(struct timer_list *unused)
@@ -905,7 +906,7 @@
-		del_timer_sync(&rtl819x_wdt_timer);
+		timer_delete_sync(&rtl819x_wdt_timer);
@@ -1084,7 +1085,6 @@
 static const struct file_operations rtl819x_wdt_fops = {
 	.owner		= THIS_MODULE,
-	.llseek		= no_llseek,
@@ -1443,6 +1443,46 @@   (immediately after rtl819x_wdt_write_proc, see R5)
+/* 3.10 removed read_proc/write_proc.  The two handler BODIES are
+ * untouched: these shims give them the modern entry points, so the port is a
+ * change of interface and not of behaviour.  __get_free_page is deliberate --
+ * 2.6.30's read_proc contract is one PAGE_SIZE buffer with no bounds check,
+ * which is what rtl819x_wdt_read_proc was written against. */
+static int rtl819x_wdt_proc_show(struct seq_file *m, void *v)
+{
+	char *page = (char *)__get_free_page(GFP_KERNEL);
+	int eof = 0, len;
+
+	if (!page)
+		return -ENOMEM;
+	len = rtl819x_wdt_read_proc(page, NULL, 0, PAGE_SIZE, &eof, NULL);
+	if (len > 0)
+		seq_write(m, page, len);
+	free_page((unsigned long)page);
+	return 0;
+}
+
+static int rtl819x_wdt_proc_open(struct inode *inode, struct file *file)
+{
+	return single_open(file, rtl819x_wdt_proc_show, NULL);
+}
+
+static ssize_t rtl819x_wdt_proc_write(struct file *file,
+				      const char __user *buffer,
+				      size_t count, loff_t *ppos)
+{
+	return rtl819x_wdt_write_proc(file, buffer, (unsigned long)count, NULL);
+}
+
+static const struct proc_ops rtl819x_wdt_proc_ops = {
+	.proc_open	= rtl819x_wdt_proc_open,
+	.proc_read	= seq_read,
+	.proc_lseek	= seq_lseek,
+	.proc_release	= single_release,
+	.proc_write	= rtl819x_wdt_proc_write,
+};
@@ -1479,8 +1519,6 @@
 static int __init rtl819x_wdt_init(void)
 {
-	struct proc_dir_entry *pde;
-
 	rlxfw_mark("W0");
@@ -1502,7 +1540,7 @@
-	setup_timer(&rtl819x_wdt_timer, rtl819x_wdt_tick, 0);
+	timer_setup(&rtl819x_wdt_timer, rtl819x_wdt_tick, 0);
@@ -1524,16 +1562,14 @@
-	pde = create_proc_entry(RTL819X_WDT_PROC_NAME, 0644, NULL);
-	if (!pde) {
+	if (!proc_create(RTL819X_WDT_PROC_NAME, 0644, NULL,
+			 &rtl819x_wdt_proc_ops)) {
 		rlxfw_mark("W5-NOPROC");
 		return 0;
 	}
-	pde->read_proc  = rtl819x_wdt_read_proc;
-	pde->write_proc = rtl819x_wdt_write_proc;
 	rlxfw_mark("W5");
```

The working tree, the four rung logs and the full `diff -u` are under
`$FWRE_WORK/modern/` and are not committed: a 1.7 GiB kernel tree is not this
repository's to carry, and the diff above is the whole of what was changed.

---

## 8.  Reproducing it

```sh
W=$FWRE_WORK/modern
curl -fLO https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.50.tar.xz
tar xf linux-6.18.50.tar.xz && cd linux-6.18.50
export ARCH=mips CROSS_COMPILE=mips-linux-gnu-
make malta_defconfig
./scripts/config --enable CONFIG_WATCHDOG --enable CONFIG_PROC_FS \
                 --enable CONFIG_CPU_BIG_ENDIAN --disable CONFIG_CPU_LITTLE_ENDIAN
make olddefconfig && make -j4 prepare scripts
cp .../config/rlxfw-src/linux-2.6.30/include/linux/rlxfw-mark.h include/linux/
cp .../config/rlxfw-src/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c drivers/watchdog/
#  ... apply § 6 ...
make drivers/watchdog/rtl819x-wdt.o
```

Host packages this needed and did not have: `flex`, `bison`, `libelf-dev`.

---

## 9.  The other three ports — 2026-09-10, fifty-first segment

Same tree, same big-endian `.config`, same instrument.  Every prediction below
was written to `PREDICTIONS-seg51.md` **before the first rung ran**.

### 9.1  The instrument's controls, and one is stronger than § 2's

🔴 **§ 2 ran `C0a`/`C0b` once, in `drivers/watchdog/`.**  "kbuild declines to
build this file, exits 0 and prints nothing" is a **per-directory** property —
a directory kbuild does not descend into behaves differently from one it does —
so a control taken in one directory says nothing about three others.  量: the
pair now runs in **all four** directories the numbers are measured in
(`watchdog`, `gpio`, `clocksource`, `mtd/devices`), **8 of 8 PASS**, every
`C0b` object 1,204 B and `elf32-tradbigmips`.

🟢 **A per-MEASUREMENT control was added as well**: every rung asserts that the
log contains kbuild's own `CC <target>` line for the object it is about.  A
directory-level control proves the directory can fail; this proves *this file*
reached the compiler.

🔴 **The counter was calibrated against the previous segment's saved logs
before it took a new number** — 6 / 24 / 18 errors and 1 fatal, all reproduced.
⚠️ **Two of its four assertions failed and the failure was MINE**: the script
asserted 0 warnings for `gpio` and `spi`, which the published table never
claimed — it published a diagnostic count only.  量: `gpio` round 0 carries
**19 warnings** and `spi` **4**, neither of them previously written down.
*A number re-derived differently does not mean the original was wrong;* the
first question is whether what is being checked is the number or a convention.

### 9.2  A configuration confounder, raised and then refuted by measurement

🔴 The tree had `# CONFIG_GPIOLIB is not set`, and § 5's `gpio` numbers were
taken in it.  A gpio driver measured against a kernel whose gpio subsystem is
switched off is not obviously the same experiment as one measured against a
kernel that has it — the same shape as § 2's endianness control, and nobody
had run it.

量: enabling `CONFIG_GPIOLIB` moves **79 lines** of `.config`, and all three
round-0 results are **identical, diagnostic for diagnostic** — `timer` 1 fatal,
`gpio` 24, `spi` 18.  `timer` and `spi` are the negative control: had they
moved, the change would not have been specific and no `gpio` delta could have
been attributed to it.

**Why it does not matter, which is the part worth keeping**: the driver
includes `<linux/gpio.h>`, which no longer defines `struct gpio_chip` under
either setting, and `gpiochip_add` is gone from mainline entirely rather than
being config-gated.  ⚠️ **The scope of that finding is round 0 only.**  It is
false for the *ladder*: once `<linux/gpio/driver.h>` is included,
`gpiochip_add_data` is declared only under `CONFIG_GPIOLIB`.  The ladders were
run with it **on**, which is also the honest configuration for a gpio driver.

### 9.3  The three ladders

**`rtl819x-timer` — 1 fatal → 25 → 20 → 19 → 18 → 7 → 6 → 4 → 3 → 0**

| rung | change | predicted | measured |
|---|---|---:|---:|
| `T-R1` | `<asm/rlxregs.h>` → `<asm/mipsregs.h>` | fatal cleared, +1 new error | fatal cleared, **25**, and no new error |
| `T-R2` | `cycle_t` → `u64` (`clocksource.read` since 4.10) | 20 | **20** |
| `T-R3` | `clocksource_register()` → `__clocksource_register()` | 19 | **19** |
| `T-R4` | `del_timer_sync` → `timer_delete_sync` | 18 | **18** *(19 on the first attempt — see § 9.4)* |
| `T-R5` | `.set_mode` + `enum clock_event_mode` → four `set_state_*` | 7 | **7** |
| `T-R6` | drop `IRQF_DISABLED` | 6 | **6** |
| `T-R7` | `timespec`/`getnstimeofday` → `timespec64`/`ktime_get_real_ts64` | 4 | **4** |
| `T-R8` | `setup_timer` → `timer_setup`, callback signature with it | 3 | **3** |
| `T-R9` | `create_proc_entry` + `read_proc`/`write_proc` → `proc_create` + `proc_ops` | 0 | **0** |

🔴 **`T-R1`'s prediction was REFUTED and the premise was right.**  It said
mainline would not have `ST0_IEC`, because a MIPS32 core has one `ST0_IE` at
bit 0 where this Lexra core has the MIPS-I three-deep `IEc/IEp/IEo` stack.
The ISA reasoning is correct; the conclusion about *mainline's header* is not.
量 `arch/mips/include/asm/mipsregs.h`: `ST0_IE` at :420 and **`ST0_IEC` at
:449, same value** — mainline still supports R3000-class parts and carries both
names.  So the entire `arch/rlx` coupling costs **one changed line and zero
diagnostics**, and the prediction failed on the header's contents rather than
on the architecture.

🟢 **`T-R9` did not repeat § 3's `R4`.**  That rung refuted its own prediction
because the shim block was placed above the handlers it names.  Here the
forward declarations and the shim were both placed correctly *in advance*,
with the reason written into the patch — which is what a recorded refutation
is for.

**`rtl819x-gpio` — 24 → 5 → 4 → 1 → 0.**  Predicted `24 → 4 → 3 → 0`;
**every rung missed by exactly one**, and the constant offset is one
diagnostic that round 0 could not show (§ 9.4).  `G-R4` closed it: 0 errors,
0 warnings, 11,512 B.

**`rtl819x-spi` — 18 → 11 → 6 → 5 → 4 → 0, five rungs, five hits.**  The
prediction written before round 0 was `18 → ~10 → ~6 → ~3 → 0`, labelled 猜
with four rungs; it was **sharpened to the five-rung form from round 0's
classification, still before any rung ran**, and both are recorded.

### 9.4  🔴 TWO MECHANISMS THAT MAKE A ROUND-0 COUNT A FLOOR

Neither is "a diagnostic count is not a root-cause count", which § 5 already
says.  Both are about a different thing: **the count does not see everything
that has to change.**

**① One diagnostic can stand for N edit sites.**  `T-R4` was predicted to take
19 → 18 and measured **19**.  量: `del_timer_sync` has **two** call sites
(1237 and 1928) and round 0 printed **one**.  gcc reports an implicitly
declared function once per *translation unit* — the implicit declaration
enters file scope, so later calls are silent — and fixing the first merely
promotes the second to being the first.  **Found by the rung missing its
prediction**, which is what a ladder is for.  ⚠️ This class is present in every
driver's count: `gpio`'s 24 and `spi`'s 18 each contain implicit-declaration
diagnostics whose call-site count was never checked.

**② An incomplete type masks whole diagnostics about its members.**  `G-R1`
was predicted to take 24 → 4 and measured **5**.  量: while `struct gpio_chip`
is an incomplete type the compiler cannot type-check anything assigned to its
members, so mainline's change of `.set` from
`void (*)(struct gpio_chip *, unsigned, int)` to `int (*)(...)` — the 6.15
`set_rv` conversion — was **invisible in all 24 round-0 diagnostics** and
appeared only once the header was added.  The offset is constant through
`G-R2` and `G-R3` because those rungs do not touch it.

**So `24 / 18 / 6` are floors on the work, not measurements of it**, and the
`8 / 3 / 5 / 3` identifier census is a floor on a floor.

### 9.5  Four porting decisions that are judgments, not compile fixes

Each of these compiles either way.  Each is recorded because the alternative
would have been a behaviour change wearing a compile fix's clothes.

1. **`__clocksource_register()` and not `clocksource_register_hz()`.**  This
   driver runs its own `rtl819x_pick_shift()` search with a documented
   argument about `clocksource_hz2mult`'s silent u32 truncation and the
   `mask * mult` s63 bound.  讀 `kernel/time/clocksource.c`:
   `__clocksource_update_freq_scale()` calls `clocks_calc_mult_shift()` **only
   when `freq` is non-zero**, and `__clocksource_register()` passes 0.
   `clocksource_register_hz()` would have silently discarded the search.
2. **`.event_handler = clockevents_handle_noop` is dropped, and so is the
   derived `/proc` field `ce_handler_is_noop`.**  讀: the symbol is a global
   function declared only in `kernel/time/tick-internal.h`, so no driver may
   name it.  **What the ten boots rested on survives** — the driver's own
   comment says the ADDRESS is printed "so it can be resolved against this
   build's own System.map", and that is what `cardcheck numbers` resolved
   (`80036D50` → `80036FC4`).  The flag was the convenience.  ⚠️ One
   observable does change: a `/proc` read *before* registration now shows 0
   where 2.6.30 showed noop's address, because `tick_setup_device()` — not
   `clockevents_register_device()` — is what assigns it.
3. **The clockevent mode NUMBERING is preserved** with local `#define`s
   (`UNUSED` 0 … `RESUME` 4).  `ce_mode`, `ce_mode_calls` and
   `ce_probe_last_mode` are `/proc` fields that ten boots were validated
   against (`ce_mode=2`, `ce_mode_calls=2`).  A renumbering would compile and
   would make every one of those captures incomparable.
4. **`rtl819x_spi_mtd._write()` and not `mtd_write()`** in the `trywrite`
   verb.  The verb exists to prove *this driver's* write path refuses;
   `mtd_write()` checks `MTD_WRITEABLE` in the core and would return `-EROFS`
   before the driver was reached, so the ported verb would be measuring
   mtdcore's flag check under the old name.  ⚠️ The verb does lose one of its
   six conjuncts — `ei.state == MTD_ERASE_FAILED`, which the erase state
   machine's removal took with it — and that conjunct was the weakest of the
   six: the driver had written the field itself one line earlier.  **Five
   terms remain, all read back from state the verb did not write.**

🟢 **And one place where the drift GAINS something.**  2.6.30's
`gpio_chip.set` returned `void`, so a refusal by this driver's write guard was
invisible to gpiolib and could only be counted in `n_set_no` and read out of
`/proc` afterwards.  Mainline's returns `int`, and **`-EPERM` is already the
value that guard uses at the layer that can report** (量 seating 15: refused
on the die at two layers with `-EPERM` and `-ENODEV`).  The port makes the
refusal visible to the caller and keeps the counter.

### 9.6  What § 6's list still says, unchanged

Everything in § 6's ⚠️ list survives and is not weakened by ② being answered:
**it compiles and has never run**; **compiling is not upstream acceptance** and
the same two objections apply to the three new ports (hand-rolled `/proc`
instrumentation, and — new — `rtl819x-gpio` registers a `gpio_chip` with no
`of_node`/`fwnode` where a modern driver would be a `platform_driver` bound
through the `dt/` bindings this project already wrote);
**`config/rlxfw-src/` is untouched**, so `RECIPE_ID` has not moved and the
image that ran on the silicon is still the image that ran on the silicon.
🔴 **The port lives here as a diff and nowhere else**, which is § 6's own rule
and is why the three new diffs are summarised rather than committed as source.

---

## 10.  The three ports

Comment lines are omitted (§ 6's churn table gives both counts), and the
`/proc` shim is omitted from all three: it is the same shape as § 7's,
differing only in the handler names and — in `spi` — in there being **two**
entries, the map file keeping no write path.

```diff
########## rtl819x-timer.c   (drivers/clocksource/)
-#include <asm/rlxregs.h>
+#include <asm/mipsregs.h>
+#include <linux/seq_file.h>
-static cycle_t rtl819x_tc1_read(struct clocksource *cs)
+static u64 rtl819x_tc1_read(struct clocksource *cs)
-	return (cycle_t)rtl819x_tc1_cycles();
+	return (u64)rtl819x_tc1_cycles();
-		ret = clocksource_register(&rtl819x_tc1_clocksource);
+		ret = __clocksource_register(&rtl819x_tc1_clocksource);
-			del_timer_sync(&rtl819x_ext_timer);        /* 1237 */
-	del_timer_sync(&rtl819x_ext_timer);                /* 1928 -- BOTH */
+			timer_delete_sync(&rtl819x_ext_timer);
+	timer_delete_sync(&rtl819x_ext_timer);
+#define RTL819X_CE_MODE_UNUSED		0    /* the 2.6.30 numbering, kept:  */
+#define RTL819X_CE_MODE_SHUTDOWN	1    /* ce_mode / ce_mode_calls are  */
+#define RTL819X_CE_MODE_PERIODIC	2    /* /proc fields ten boots were  */
+#define RTL819X_CE_MODE_ONESHOT		3    /* validated against            */
+#define RTL819X_CE_MODE_RESUME		4
-	.set_mode	= rtl819x_ce_set_mode,               /* x2 */
-	.event_handler	= clockevents_handle_noop,           /* x2 */
-	.mode		= CLOCK_EVT_MODE_UNUSED,             /* x2 */
+	.set_state_periodic	= rtl819x_ce_state_periodic, /* x2 */
+	.set_state_oneshot	= rtl819x_ce_state_oneshot,
+	.set_state_shutdown	= rtl819x_ce_state_shutdown,
+	.tick_resume		= rtl819x_ce_tick_resume,
-static void rtl819x_ce_set_mode(enum clock_event_mode mode,  /* decl + defn */
+static void rtl819x_ce_set_mode(int mode,
-	case CLOCK_EVT_MODE_PERIODIC:   /* and ONESHOT, SHUTDOWN, UNUSED, RESUME */
+	case RTL819X_CE_MODE_PERIODIC:
+static int rtl819x_ce_state_periodic(struct clock_event_device *evt)
+{ rtl819x_ce_set_mode(RTL819X_CE_MODE_PERIODIC, evt); return 0; }   /* x4 */
-	ret = request_irq(RTL819X_TC1_IRQ, rtl819x_tc1_isr, IRQF_DISABLED,
+	ret = request_irq(RTL819X_TC1_IRQ, rtl819x_tc1_isr, 0,
-	struct timespec ts;                 -	getnstimeofday(&ts);
+	struct timespec64 ts;               +	ktime_get_real_ts64(&ts);
-	len += scnprintf(... "ce_handler_is_noop=%d\n",
-			 (ce_h == (unsigned long)clockevents_handle_noop) ? 1 : 0);
-static void rtl819x_ext_tick(unsigned long data)
+static void rtl819x_ext_tick(struct timer_list *unused)
-	setup_timer(&rtl819x_ext_timer, rtl819x_ext_tick, 0UL);
+	timer_setup(&rtl819x_ext_timer, rtl819x_ext_tick, 0);
-	pde = create_proc_entry(RTL819X_PROC_NAME, 0644, NULL);  /* + shim */
+	if (!proc_create(RTL819X_PROC_NAME, 0644, NULL, &rtl819x_tc_proc_ops))

########## rtl819x-gpio.c   (drivers/gpio/)
+#include <linux/gpio/driver.h>          /* 20 of the 24 diagnostics */
+#include <linux/seq_file.h>
-static void rtl819x_gpio_set(struct gpio_chip *chip, unsigned off, int value)
+static int  rtl819x_gpio_set(struct gpio_chip *chip, unsigned off, int value)
-		return;                  /* off >= NGPIO */
+		return -EINVAL;
-		return;                  /* the write guard refuses */
+		return -EPERM;
+	return 0;
-	rtl819x_gpio_add_rc = gpiochip_add(&rtl819x_gpio_chip);
+	rtl819x_gpio_add_rc = gpiochip_add_data(&rtl819x_gpio_chip, NULL);
-	pde = create_proc_entry(RTL819X_GPIO_PROC_NAME, 0644, NULL);  /* + shim */
+	if (!proc_create(RTL819X_GPIO_PROC_NAME, 0644, NULL, &..._proc_ops)) {

########## rtl819x-spi.c   (drivers/mtd/devices/)
+#include <linux/seq_file.h>
-	d->flags = 0;                        /* shash_desc.flags, gone in 5.x */
-	instr->state = MTD_ERASE_FAILED;     /* the erase state machine, gone */
+	(void)instr;
-	.read/.write/.erase	= rtl819x_spi_mtd_*,
+	._read/._write/._erase	= rtl819x_spi_mtd_*,      /* 3.4 */
-	rcw = rtl819x_spi_mtd.write(&rtl819x_spi_mtd, 0, 1, &rl, &b);
+	rcw = rtl819x_spi_mtd._write(...);   /* NOT mtd_write() -- see 9.5 (4) */
-	ei.mtd = &rtl819x_spi_mtd;
-	     (ei.state == MTD_ERASE_FAILED) &&
-	rtl819x_spi_add_rc = add_mtd_device(&rtl819x_spi_mtd);
+	rtl819x_spi_add_rc = mtd_device_register(&rtl819x_spi_mtd, NULL, 0);
-	pde = create_proc_entry(..._PROC_NAME, 0644, NULL);   /* x2, + 2 shims */
+	if (!proc_create(..._PROC_NAME, 0644, NULL, &..._proc_ops)) {
```

⚠️ **One value changes meaning and it is a `/proc` field.**
`add_mtd_device()` returned **1** for "no free slot" in 2.6.30 — not an errno —
and `mtd_device_register()` returns a negative errno.  The `== 0` test that
sets `rtl819x_spi_added` is correct under both, so `added` stays comparable
across the port; **`add_rc`, which `/proc` prints and mark `S5` carries, does
not.**
