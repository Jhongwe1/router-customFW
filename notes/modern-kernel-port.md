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
host has installed; upstream stopped maintaining 6.8 long before this segment.
A claim of the form *"it builds against a modern kernel"* backed by 6.8 in
September 2026 is a claim about a kernel nobody ships.  The target here is
**6.18.50**, the newest longterm.

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
distinct APIs.**  Of the 46 added lines, **34 are the `/proc` shim** and 6 of
those are its comment; the other three APIs are **one line each**.

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

| driver | lines | census said (vs 6.8) | gcc diagnostics (vs 6.18.50) | |
|---|---:|---:|---:|---|
| `rtl819x-timer` | 2,813 | 8 | **1, and it is FATAL** | `asm/rlxregs.h` not found |
| `rtl819x-gpio` | 673 | 3 | **24** | 21 cascade from one incomplete type |
| `rtl819x-spi` | 1,738 | 5 | **18** | five or six distinct API changes |
| `rtl819x-wdt` | 1,547 | 3 | **6** | 4 root causes, measured by § 3's ladder |

⚠️ **A diagnostic count is not a root-cause count and must not be quoted as
one.**  Only `rtl819x-wdt` has a *measured* root-cause count — 4 — because only
it was put through a ladder in which each rung removed exactly its own
diagnostics.  For the others the count below is a count of lines gcc printed.

### 🔴 `gpio` and `spi`: the census's DECLARED blind spot dominates

`rtl819x-gpio`: 21 of the 24 are `struct gpio_chip` used as an **incomplete
type** — `has no member named ‘label’`, `‘owner’`, `‘request’`, `‘free’`,
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
drivers/clocksource/rlxfw_v0_timer.c:409:10: fatal error: asm/rlxregs.h: No such file or directory
```

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

🟢 **`rtl819x-wdt` compiles in a current-longterm kernel tree** — 4 APIs,
56 changed lines, 3.62 % of the file.

🔴 **And ② is NOT answered for the other three, which § 5 measures rather than
assumes.**  The plan's ~0.3-segment estimate survives *for this driver*; on
`gpio` and `spi` the census's declared blind spot is the majority of the
diagnostics, and on `timer` the driver does not compile far enough to be
measured at all.  **Generalising the wdt result to the DoD would be
generalising from the driver that was chosen for being the easiest.**

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
