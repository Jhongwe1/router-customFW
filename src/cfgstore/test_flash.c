/* test_flash.c -- the config store on flash: cfg.c's dispatch, cfgflash.c's
 * eight steps and spictl.c's bytes, run whole against simkern.c's simulated
 * rtl819x-spi (notes/self-update.md §§ 3.1-3.8).
 *
 * argv[1] a scratch directory (ext4), argv[2] the cfgstore-sim binary:
 * src/cfgstore/main.c linked with the same simulation, for the CLI cases.
 *
 * What is real here: every line of src/lib (spictl.c opens the product's own
 * four device paths), and the kernel's decisions -- the install header's
 * parser, arm agreement, staging admission, payload check, plan and read-back
 * compare.  What is simulated: the glue around them, the flash (a 4 MiB file),
 * the page (regenerated per open), and the faults, each the kernel answering
 * something the step did not produce.  A deviation case asserts four things:
 * the return, the named step (cfg_flash_why), the exact list of writes to
 * /proc in order, and -- for the ones before the install -- that the target
 * region is byte-identical.  The accepted case is the control for all of them.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include "cfg.h"
#include "schema.h"
#include "sha256.h"
#include "simkern.h"
#include "spictl.h"
#include "test_util.h"

#define DIRMAX 400
#define REGION ((size_t)CFG_FLASH_REGION)

static char g_dir[DIRMAX];
static char g_bin[DIRMAX];
static char g_out[DIRMAX + 32];
static char g_buf[65536];

/* ------------------------------------------------------------------------- */
/* Fixtures, written straight into the flash file: no event, no kernel       */
/* ------------------------------------------------------------------------- */

static void base_cfg(struct cfg *c, const char *host)
{
	int i;

	cfg_defaults(c);
	for (i = 0; i < CFG_NKEYS; i++) {
		const uint8_t *dv;
		uint16_t dl;

		if (schema_default(cfg_keys[i].id, &dv, &dl) == 0)
			cfg_set(c, cfg_keys[i].id, dv, dl);
	}
	if (host != NULL)
		cfg_set(c, CFG_ID_HOSTNAME, (const uint8_t *)host,
			(uint16_t)strlen(host));
}

static int flash_io(int wr, uint32_t off, void *b, size_t n)
{
	int fd = open(simk_flash_file(), wr ? O_WRONLY : O_RDONLY);
	ssize_t r;

	if (fd < 0)
		return -1;
	r = wr ? pwrite(fd, b, n, (off_t)off) : pread(fd, b, n, (off_t)off);
	close(fd);
	return (r == (ssize_t)n) ? 0 : -1;
}

static uint32_t base_of(int s)
{
	return (s == 0) ? CFG_FLASH_OFF0 : CFG_FLASH_OFF1;
}

static int slot_put(int s, uint32_t seq, const char *host)
{
	uint8_t img[CFG_SLOT_SIZE];
	struct cfg c;

	base_cfg(&c, host);
	if (cfg_slot_image(&c, seq, img, sizeof img) < 0)
		return -1;
	return flash_io(1, base_of(s), img, sizeof img);
}

static int slot_erase(int s)
{
	static uint8_t ff[CFG_FLASH_REGION];

	memset(ff, 0xFF, sizeof ff);
	return flash_io(1, base_of(s), ff, sizeof ff);
}

/* One byte inside the header: the header CRC fails. */
static int slot_corrupt(int s)
{
	uint8_t b;

	if (flash_io(0, base_of(s) + 9u, &b, 1) != 0)
		return -1;
	b ^= 0x5Au;
	return flash_io(1, base_of(s) + 9u, &b, 1);
}

static int region_get(int s, uint8_t *buf)
{
	return flash_io(0, base_of(s), buf, REGION);
}

/* ------------------------------------------------------------------------- */
/* The event list                                                            */
/* ------------------------------------------------------------------------- */

static void ev_text(const struct simk_ev *e, char *out, size_t cap)
{
	int n;

	switch (e->kind) {
	case 'v':
		n = snprintf(out, cap, "%s", e->text);
		break;
	case 'i':
		n = snprintf(out, cap, "img %lu", (unsigned long)e->len);
		break;
	case 's':
		n = snprintf(out, cap, "seek 0x%lx", (unsigned long)e->off);
		break;
	default:
		n = snprintf(out, cap, "%c", e->kind);
		break;
	}
	if (e->err != 0 && n > 0 && (size_t)n < cap)
		(void)snprintf(out + n, cap - (size_t)n, " !%d", e->err);
}

/* The writes and the lock events in order, seeks left out. */
static int ev_writes(char out[][160], int cap)
{
	int i, k = 0, n = simk_nev();

	for (i = 0; i < n && k < cap; i++) {
		const struct simk_ev *e = simk_ev(i);

		if (e->kind == 's')
			continue;
		ev_text(e, out[k++], 160);
	}
	return (n < 0) ? -1 : k;
}

static int log_is(const char *what, const char *const *want, int nwant)
{
	char got[64][160];
	int n = ev_writes(got, 64), i, same = (n == nwant);

	for (i = 0; same && i < n; i++)
		if (strcmp(got[i], want[i]) != 0)
			same = 0;
	CHECK(same, "%s: the writes to /proc are not the expected %d", what,
	      nwant);
	if (!same) {
		printf("      got  (%d):\n", n);
		for (i = 0; i < n; i++)
			printf("        %s\n", got[i]);
		printf("      want (%d):\n", nwant);
		for (i = 0; i < nwant; i++)
			printf("        %s\n", want[i]);
	}
	return same;
}

static int count_kind_prefix(const char *prefix)
{
	char got[64][160];
	int n = ev_writes(got, 64), i, k = 0;

	for (i = 0; i < n; i++)
		if (strncmp(got[i], prefix, strlen(prefix)) == 0)
			k++;
	return k;
}

/* Every seek on the device: no offset below the guard, only the two slots. */
static int seeks_ok(void)
{
	int i, n = simk_nev(), bad = 0, seen = 0;

	for (i = 0; i < n; i++) {
		const struct simk_ev *e = simk_ev(i);

		if (e->kind != 's')
			continue;
		seen++;
		if (e->off != CFG_FLASH_OFF0 && e->off != CFG_FLASH_OFF1)
			bad++;
	}
	return (bad == 0) ? seen : -1;
}

/* "install cfgN sha=<hex>" for the image `c` makes at `seq`. */
static void install_line(int s, const struct cfg *c, uint32_t seq, char *out,
			 size_t cap)
{
	uint8_t img[CFG_SLOT_SIZE], md[SHA256_DIGEST_LEN];
	int n, i;

	(void)cfg_slot_image(c, seq, img, sizeof img);
	(void)sha256(img, sizeof img, md);
	n = snprintf(out, cap, "install cfg%d sha=", s);
	for (i = 0; i < SHA256_DIGEST_LEN && n + 2 < (int)cap; i++)
		n += snprintf(out + n, cap - (size_t)n, "%02x", md[i]);
}

static const char *arm_line(int s)
{
	return (s == 0) ? "arm 0x3c0000 0x3d0000 0x10000"
			: "arm 0x3d0000 0x3e0000 0x10000";
}

/* ------------------------------------------------------------------------- */
/* A child: fork + execve with a fixed argv and a two-entry environment      */
/* ------------------------------------------------------------------------- */

static int run_bin(const char *bin, char *const *argv, int with_sim)
{
	char envd[DIRMAX + 32];
	char *envp[3];
	pid_t pid;
	int st = -1, fd;
	ssize_t n;

	(void)snprintf(envd, sizeof envd, "RLXFW_SIMKERN_DIR=%s", simk_dir());
	envp[0] = with_sim ? envd : (char *)"RLXFW_NOSIM=1";
	envp[1] = (char *)"PATH=/usr/bin:/bin";
	envp[2] = NULL;
	g_buf[0] = '\0';
	pid = fork();
	if (pid < 0)
		return -1;
	if (pid == 0) {
		int o = open(g_out, O_WRONLY | O_CREAT | O_TRUNC, 0600);
		int i = open("/dev/null", O_RDONLY);

		if (o < 0 || i < 0 || dup2(o, 1) < 0 || dup2(o, 2) < 0 ||
		    dup2(i, 0) < 0)
			_exit(126);
		execve(bin, argv, envp);
		_exit(127);
	}
	if (waitpid(pid, &st, 0) != pid)
		return -1;
	fd = open(g_out, O_RDONLY);
	if (fd >= 0) {
		n = read(fd, g_buf, sizeof g_buf - 1);
		g_buf[(n > 0) ? (size_t)n : 0] = '\0';
		close(fd);
	}
	return WIFEXITED(st) ? WEXITSTATUS(st) : -1;
}

static int has(const char *needle)
{
	return strstr(g_buf, needle) != NULL;
}

static void show_out(void)
{
	printf("      --- output ---\n%s      --------------\n", g_buf);
}

/* ------------------------------------------------------------------------- */
/* Reads                                                                     */
/* ------------------------------------------------------------------------- */

static void t_reads(void)
{
	struct cfg c;
	struct cfg_store_info info;
	uint8_t one;
	int rc;

	T_GROUP("read: both slots erased is no store yet");
	CHECK(simk_init(g_dir) == 0, "a fresh simulated chip");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == 0, "load: %s", cfg_strerror(rc));
	CHECK(info.selected == 0 && c.source == 0 && info.file_bytes == 0,
	      "selected %d, source %d, bytes %lu: want 0, 0, 0 (absent)",
	      info.selected, c.source, (unsigned long)info.file_bytes);
	CHECK(info.rc[0] == -CFGE_SHORT && info.rc[1] == -CFGE_SHORT,
	      "both slots read as absent: %d %d", info.rc[0], info.rc[1]);
	CHECK(seeks_ok() == 2, "two reads, at 0x3C0000 and 0x3D0000 only: %d",
	      seeks_ok());
	CHECK(count_kind_prefix("") == 0, "a read writes nothing");

	T_GROUP("read: one slot erased, the other loads");
	CHECK(slot_put(1, 5, "one") == 0, "slot 1 seq 5");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == 0 && info.selected == 2 && c.seq == 5 &&
	      info.file_bytes == (size_t)CFG_SLOT_SIZE,
	      "slot 0 erased: rc %d selected %d seq %lu bytes %lu", rc,
	      info.selected, (unsigned long)c.seq,
	      (unsigned long)info.file_bytes);
	CHECK(slot_put(0, 6, "two") == 0 && slot_erase(1) == 0, "the mirror");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == 0 && info.selected == 1 && c.seq == 6,
	      "slot 1 erased: selected %d seq %lu", info.selected,
	      (unsigned long)c.seq);

	T_GROUP("read: a corrupt slot with a valid other loads the valid one");
	CHECK(slot_put(1, 5, "one") == 0 && slot_corrupt(0) == 0, "fixture");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == 0 && info.selected == 2 && c.seq == 5,
	      "selected %d seq %lu", info.selected, (unsigned long)c.seq);
	CHECK(info.rc[0] == -CFGE_CRC && info.file_bytes == 2u * CFG_SLOT_SIZE,
	      "slot 0 is CORRUPT, not absent: rc %d, bytes %lu", info.rc[0],
	      (unsigned long)info.file_bytes);
	CHECK(slot_corrupt(1) == 0, "both corrupt");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == 0 && info.selected == 0 && c.source == 0 &&
	      info.file_bytes == 2u * CFG_SLOT_SIZE,
	      "both corrupt: defaults over a store that holds bytes (%lu)",
	      (unsigned long)info.file_bytes);

	T_GROUP("read: one byte that is not 0xFF makes a slot present");
	CHECK(slot_erase(0) == 0 && slot_erase(1) == 0, "both erased");
	one = 0xFE;
	CHECK(flash_io(1, CFG_FLASH_OFF1 + CFG_SLOT_SIZE - 1, &one, 1) == 0,
	      "the last byte of slot 1");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == 0 && info.selected == 0 &&
	      info.file_bytes == (size_t)CFG_SLOT_SIZE &&
	      info.rc[1] == -CFGE_CRC,
	      "slot 1 read as a refused record: bytes %lu rc %d",
	      (unsigned long)info.file_bytes, info.rc[1]);

	T_GROUP("read: a device that cannot be read is an error, never absent");
	CHECK(remove(simk_flash_file()) == 0, "the device gone");
	rc = cfg_load_info(CFG_FLASH_DEV, &c, &info);
	CHECK(rc == -CFGE_IO && info.rc[0] == -CFGE_IO &&
	      info.rc[1] == -CFGE_IO && c.source == 0,
	      "rc %d, slots %d %d: want -CFGE_IO, not no-store-yet", rc,
	      info.rc[0], info.rc[1]);
	CHECK(strncmp(cfg_flash_why(), "read: errno", 11) == 0,
	      "named: \"%s\"", cfg_flash_why());
}

/* ------------------------------------------------------------------------- */
/* The accepted write                                                        */
/* ------------------------------------------------------------------------- */

static int sha256sum_of(const char *path, char *hex65)
{
	char *const av[] = { (char *)"sha256sum", (char *)path, NULL };
	int rc = run_bin("/usr/bin/sha256sum", av, 0);

	if (rc != 0 || strlen(g_buf) < 64)
		return -1;
	memcpy(hex65, g_buf, 64);
	hex65[64] = '\0';
	return 0;
}

static void t_store_ok(void)
{
	static uint8_t r0[CFG_FLASH_REGION], r1[CFG_FLASH_REGION], lo[0x10000];
	static uint8_t lo_before[0x10000];
	uint8_t img[CFG_SLOT_SIZE];
	char inst[200], hex[65];
	struct cfg c, d;
	struct cfg_store_info info;
	unsigned long nw;
	int rc, i, first_s = -1, last_s = -1, li = -1, ui = -1, n;
	size_t k;

	T_GROUP("store: the accepted write, in order");
	CHECK(simk_init(g_dir) == 0, "a fresh simulated chip");
	CHECK(flash_io(0, 0, lo_before, sizeof lo_before) == 0, "the low 64 KiB");
	base_cfg(&c, "alpha");
	install_line(0, &c, 1, inst, sizeof inst);
	nw = simk_nwrites();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == 0, "store: %s (%s)", cfg_strerror(rc), cfg_flash_why());
	CHECK(c.seq == 1 && c.source == 1, "seq %lu slot %d, want 1 and 0",
	      (unsigned long)c.seq, c.source - 1);
	CHECK(cfg_flash_why()[0] == '\0', "no deviation: \"%s\"",
	      cfg_flash_why());
	{
		const char *want[] = { "L", "disarm", "img reset", "img 4096",
				       arm_line(0), inst, "img reset", "U" };

		log_is("the accepted store into slot 0", want, 8);
	}
	CHECK(simk_nwrites() - nw == 32, "n_writes moved %lu, want 32",
	      simk_nwrites() - nw);

	/* The lock covers the read, the decision, the write and the read-back. */
	n = simk_nev();
	for (i = 0; i < n; i++) {
		const struct simk_ev *e = simk_ev(i);

		if (e->kind == 's') {
			if (first_s < 0)
				first_s = i;
			last_s = i;
		}
		if (e->kind == 'L')
			li = i;
		if (e->kind == 'U')
			ui = i;
	}
	CHECK(li >= 0 && first_s > li && last_s < ui && ui == n - 1,
	      "lock at %d, device reads %d..%d, unlock at %d of %d events", li,
	      first_s, last_s, ui, n);
	CHECK(seeks_ok() == 3, "the two slots read, then slot 0 read back: %d",
	      seeks_ok());

	T_GROUP("store: what landed, and what did not move");
	CHECK(region_get(0, r0) == 0 && region_get(1, r1) == 0 &&
	      flash_io(0, 0, lo, sizeof lo) == 0, "read the chip");
	CHECK(cfg_slot_image(&c, 1, img, sizeof img) > 0 &&
	      memcmp(r0, img, sizeof img) == 0, "slot 0 holds the image");
	for (k = CFG_SLOT_SIZE; k < REGION && r0[k] == 0xFF; k++)
		;
	CHECK(k == REGION, "the rest of cfg0 is erased (first other byte at %lu)",
	      (unsigned long)k);
	for (k = 0; k < REGION && r1[k] == 0xFF; k++)
		;
	CHECK(k == REGION, "cfg1 untouched");
	CHECK(memcmp(lo, lo_before, sizeof lo) == 0,
	      "the low 64 KiB (the loader's stand-in) unchanged");
	CHECK(sha256sum_of(simk_staged_file(), hex) == 0 &&
	      strcmp(inst + strlen("install cfg0 sha="), hex) == 0,
	      "the typed digest is sha256sum's of the staged bytes: %s", hex);

	T_GROUP("store: the next two alternate, the other slot byte-identical");
	install_line(1, &c, 2, inst, sizeof inst);
	simk_reset();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == 0 && c.seq == 2 && c.source == 2, "seq 2 into slot 1: %s",
	      cfg_strerror(rc));
	{
		const char *want[] = { "L", "disarm", "img reset", "img 4096",
				       arm_line(1), inst, "img reset", "U" };

		log_is("the second store, slot 1", want, 8);
	}
	CHECK(region_get(0, r1) == 0 && memcmp(r0, r1, REGION) == 0,
	      "cfg0 unchanged by a write to cfg1");
	simk_reset();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == 0 && c.seq == 3 && c.source == 1, "seq 3 back into slot 0");
	rc = cfg_load_info(CFG_FLASH_DEV, &d, &info);
	CHECK(rc == 0 && info.selected == 1 && d.seq == 3 &&
	      info.seq[1] == 2, "load: slot %d seq %lu, the other %lu",
	      info.selected - 1, (unsigned long)d.seq,
	      (unsigned long)info.seq[1]);

	T_GROUP("write_slot: the same eight steps, taking the lock itself");
	(void)cfg_slot_image(&c, 9, img, sizeof img);
	install_line(1, &c, 9, inst, sizeof inst);
	simk_reset();
	rc = cfg_flash_write_slot(1, img);
	CHECK(rc == 0, "cfg_flash_write_slot: %d (%s)", rc, cfg_flash_why());
	{
		const char *want[] = { "L", "disarm", "img reset", "img 4096",
				       arm_line(1), inst, "img reset", "U" };

		log_is("cfg_flash_write_slot(1)", want, 8);
	}
	CHECK(cfg_flash_write_slot(2, img) == -CFGE_IO &&
	      strncmp(cfg_flash_why(), "args", 4) == 0,
	      "slot 2 refused: \"%s\"", cfg_flash_why());
}

/* ------------------------------------------------------------------------- */
/* Deviations                                                                */
/* ------------------------------------------------------------------------- */

struct dev_case {
	int fault;
	const char *why;	/* the prefix cfg_flash_why must carry */
	int stage;		/* the last step reached: 0 disarm, 1 stage, 2 arm,
				 * 3 install, 4 after the install */
	int err;		/* the errno the failing write carries, or 0 */
};

static void t_deviations(void)
{
	static uint8_t before[CFG_FLASH_REGION], after[CFG_FLASH_REGION];
	char inst[200], armx[64], disx[32], imgx[32], instx[220];
	struct cfg c;
	int k, rc;
	const struct dev_case cs[] = {
		{ SIMK_IMGLEN_SHORT, "img_len: 4095 staged, want 4096", 1, 0 },
		{ SIMK_IMGERR, "img_err: POISONED", 1, 0 },
		{ SIMK_STAGE_EFBIG, "stage: errno", 1, EFBIG },
		{ SIMK_DISARM_EIO, "disarm: errno", 0, EIO },
		{ SIMK_ARM_EPERM, "arm: errno", 2, EPERM },
		{ SIMK_INST_SHA, "install: errno", 3, EBADMSG },
		{ SIMK_INST_REASON, "inst_reason: CMP", 4, 0 },
		{ SIMK_CMP_OK0, "inst_cmp_ok: ", 4, 0 },
		{ SIMK_CMP_DIFF, "inst_cmp_diff: 1 bytes differ", 4, 0 },
		{ SIMK_NW_MINUS1, "n_writes: moved by 31, want 32", 4, 0 },
		{ SIMK_NW_PLUS1, "n_writes: moved by 33, want 32", 4, 0 },
	};

	for (k = 0; k < (int)(sizeof cs / sizeof cs[0]); k++) {
		const char *want[12];
		char label[96];
		int nw = 0;

		(void)snprintf(label, sizeof label, "deviation %d (%s)", k,
			       cs[k].why);
		T_GROUP(label);
		CHECK(simk_init(g_dir) == 0 && slot_put(0, 1, "held") == 0,
		      "slot 0 holds seq 1, so the store targets cfg1");
		CHECK(region_get(1, before) == 0, "cfg1 before");
		base_cfg(&c, "deviant");
		install_line(1, &c, 2, inst, sizeof inst);
		(void)snprintf(disx, sizeof disx, "disarm !%d", cs[k].err);
		(void)snprintf(imgx, sizeof imgx, "img 4096 !%d", cs[k].err);
		(void)snprintf(armx, sizeof armx, "%s !%d", arm_line(1),
			       cs[k].err);
		(void)snprintf(instx, sizeof instx, "%s !%d", inst, cs[k].err);

		want[nw++] = "L";
		if (cs[k].stage == 0) {
			want[nw++] = disx;
		} else {
			want[nw++] = "disarm";
			want[nw++] = "img reset";
			want[nw++] = (cs[k].fault == SIMK_STAGE_EFBIG) ? imgx
									: "img 4096";
		}
		if (cs[k].stage >= 2)
			want[nw++] = (cs[k].stage == 2) ? armx : arm_line(1);
		if (cs[k].stage >= 3)
			want[nw++] = (cs[k].stage == 3) ? instx : inst;
		want[nw++] = "img reset";	/* the one cleanup verb */
		want[nw++] = "U";

		simk_fault(cs[k].fault);
		simk_reset();
		rc = cfg_store(CFG_FLASH_DEV, &c);
		simk_fault(SIMK_NONE);
		CHECK(rc == -CFGE_IO, "rc %d (%s), want -CFGE_IO", rc,
		      cfg_strerror(rc));
		CHECK(strncmp(cfg_flash_why(), cs[k].why, strlen(cs[k].why)) == 0,
		      "named \"%s\", want \"%s...\"", cfg_flash_why(), cs[k].why);
		log_is(label, want, nw);
		CHECK(count_kind_prefix("install") == (cs[k].stage >= 3 ? 1 : 0),
		      "%d installs", count_kind_prefix("install"));
		CHECK(c.seq == 0 && c.source == 0,
		      "the caller's record is not marked stored: seq %lu",
		      (unsigned long)c.seq);
		if (cs[k].stage <= 3) {
			CHECK(region_get(1, after) == 0 &&
			      memcmp(before, after, REGION) == 0,
			      "cfg1 byte-identical: the deviation came before"
			      " any flash operation");
		}
	}

	T_GROUP("lock: held by another writer -- nothing at all, after 30 s");
	CHECK(simk_init(g_dir) == 0, "fresh");
	base_cfg(&c, "late");
	CHECK(simk_hold_lock(1) == 0, "a second holder");
	simk_reset();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == -CFGE_IO, "rc %d", rc);
	CHECK(strcmp(cfg_flash_why(),
		     "lock: flock: held by another writer past the timeout") == 0,
	      "named \"%s\"", cfg_flash_why());
	CHECK(simk_nev() == 0, "%d events: no verb, no read, no cleanup",
	      simk_nev());
	CHECK(simk_slept_ms() == 30000ul, "it waited %lu ms of 100 ms steps,"
	      " want 30000", simk_slept_ms());
	simk_reset();
	CHECK(cfg_flash_write_slot(0, before) == -CFGE_IO && simk_nev() == 0,
	      "cfg_flash_write_slot too: %d events", simk_nev());
	CHECK(simk_hold_lock(0) == 0, "released");
	simk_reset();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == 0 && c.seq == 1, "and once released the store goes"
	      " through: %s", cfg_strerror(rc));

	T_GROUP("lock: ENOSYS (no CONFIG_FILE_LOCKING) -- named, nothing sent");
	base_cfg(&c, "nolocks");
	simk_fault(SIMK_LOCK_ENOSYS);
	simk_reset();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == -CFGE_IO, "rc %d", rc);
	CHECK(strcmp(cfg_flash_why(),
		     "lock: flock: ENOSYS, the kernel has no CONFIG_FILE_LOCKING")
	      == 0, "named \"%s\"", cfg_flash_why());
	CHECK(simk_nev() == 0 && simk_slept_ms() == 0,
	      "%d events, %lu ms waited: no retry", simk_nev(), simk_slept_ms());
	simk_reset();
	rc = cfg_store_fresh(CFG_FLASH_DEV, &c);
	CHECK(rc == -CFGE_IO && simk_nev() == 0, "cfg_store_fresh too: %d", rc);
	simk_fault(SIMK_NONE);
	simk_reset();
	rc = cfg_store(CFG_FLASH_DEV, &c);
	CHECK(rc == 0, "the real flock permits: %s (%s)", cfg_strerror(rc),
	      cfg_flash_why());
}

/* ------------------------------------------------------------------------- */
/* cfg_store_fresh                                                           */
/* ------------------------------------------------------------------------- */

static void t_fresh(void)
{
	static uint8_t b0[CFG_FLASH_REGION], b1[CFG_FLASH_REGION];
	static uint8_t a0[CFG_FLASH_REGION], a1[CFG_FLASH_REGION];
	char inst[200], path[DIRMAX + 32];
	struct cfg rec, d;
	struct cfg_store_info info;
	int rc;

	T_GROUP("fresh: both absent -- permitted, slot 0, seq 1");
	CHECK(simk_init(g_dir) == 0, "fresh");
	base_cfg(&rec, "first");
	install_line(0, &rec, 1, inst, sizeof inst);
	rc = cfg_store_fresh(CFG_FLASH_DEV, &rec);
	CHECK(rc == 0 && rec.seq == 1 && rec.source == 1,
	      "rc %d seq %lu slot %d", rc, (unsigned long)rec.seq,
	      rec.source - 1);
	{
		const char *want[] = { "L", "disarm", "img reset", "img 4096",
				       arm_line(0), inst, "img reset", "U" };

		log_is("fresh over an erased store", want, 8);
	}

	T_GROUP("fresh: both corrupt -- permitted, slot 1 left as it was");
	CHECK(slot_put(0, 5, "old0") == 0 && slot_put(1, 6, "old1") == 0 &&
	      slot_corrupt(0) == 0 && slot_corrupt(1) == 0, "both corrupt");
	CHECK(region_get(1, b1) == 0, "cfg1 before");
	base_cfg(&rec, "second");
	simk_reset();
	rc = cfg_store_fresh(CFG_FLASH_DEV, &rec);
	CHECK(rc == 0 && rec.seq == 1, "rc %d (%s)", rc, cfg_flash_why());
	CHECK(region_get(1, a1) == 0 && memcmp(b1, a1, REGION) == 0,
	      "the corrupt cfg1 was not written");
	rc = cfg_load_info(CFG_FLASH_DEV, &d, &info);
	CHECK(rc == 0 && info.selected == 1 && d.seq == 1,
	      "and slot 0 loads, seq 1: selected %d", info.selected);

	T_GROUP("fresh: one corrupt, one absent -- permitted");
	CHECK(slot_corrupt(0) == 0 && slot_erase(1) == 0, "fixture");
	simk_reset();
	CHECK(cfg_store_fresh(CFG_FLASH_DEV, &rec) == 0, "permitted");

	T_GROUP("fresh: a valid record in either slot -- refused, nothing sent");
	{
		static const struct {
			int s0, s1;	/* 0 erased, 1 corrupt, else a seq */
			const char *what;
		} rf[] = {
			{ 3, 0, "slot 0 valid, slot 1 erased (would REPLACE it)" },
			{ 1, 7, "slot 0 corrupt, slot 1 valid seq 7 (would be SHADOWED)" },
			{ 0, 7, "slot 0 erased, slot 1 valid (would be SHADOWED)" },
			{ 4, 5, "both valid" },
		};
		int k;

		for (k = 0; k < (int)(sizeof rf / sizeof rf[0]); k++) {
			CHECK(simk_init(g_dir) == 0, "fresh");
			if (rf[k].s0 >= 2)
				CHECK(slot_put(0, (uint32_t)rf[k].s0, "keep0") == 0,
				      "s0");
			if (rf[k].s0 == 1)
				CHECK(slot_put(0, 9, "bad0") == 0 &&
				      slot_corrupt(0) == 0, "s0 corrupt");
			if (rf[k].s1 >= 2)
				CHECK(slot_put(1, (uint32_t)rf[k].s1, "keep1") == 0,
				      "s1");
			CHECK(region_get(0, b0) == 0 && region_get(1, b1) == 0,
			      "before");
			base_cfg(&rec, "intruder");
			simk_reset();
			rc = cfg_store_fresh(CFG_FLASH_DEV, &rec);
			CHECK(rc == -CFGE_SEQ, "%s: rc %d, want -CFGE_SEQ",
			      rf[k].what, rc);
			{
				const char *want[] = { "L", "U" };

				log_is(rf[k].what, want, 2);
			}
			CHECK(region_get(0, a0) == 0 && region_get(1, a1) == 0 &&
			      memcmp(a0, b0, REGION) == 0 &&
			      memcmp(a1, b1, REGION) == 0,
			      "%s: both regions byte-identical", rf[k].what);
			CHECK(rec.seq == 0, "%s: not marked stored", rf[k].what);
		}
	}

	T_GROUP("fresh: an unreadable store -- refused, nothing sent");
	CHECK(simk_init(g_dir) == 0 && remove(simk_flash_file()) == 0,
	      "the device gone");
	simk_reset();
	rc = cfg_store_fresh(CFG_FLASH_DEV, &rec);
	CHECK(rc == -CFGE_IO, "rc %d, want -CFGE_IO", rc);
	CHECK(count_kind_prefix("") == 2 && count_kind_prefix("disarm") == 0,
	      "the lock and its release, and no verb");
	CHECK(simk_init(g_dir) == 0, "restored");

	T_GROUP("fresh: an invalid record -- refused before the lock");
	base_cfg(&rec, "x");
	{
		uint8_t ip[4] = { 10, 1, 1, 150 };	/* inside the pool */

		CHECK(cfg_set(&rec, CFG_ID_LAN_IP, ip, 4) == 0, "set");
	}
	simk_reset();
	rc = cfg_store_fresh(CFG_FLASH_DEV, &rec);
	CHECK(rc == -CFGE_CROSS && simk_nev() == 0, "rc %d, %d events", rc,
	      simk_nev());

	T_GROUP("fresh: the file backend, the same rules");
	(void)snprintf(path, sizeof path, "%s/fresh.bin", g_dir);
	remove(path);
	base_cfg(&rec, "filed");
	simk_reset();
	rc = cfg_store_fresh(path, &rec);
	CHECK(rc == 0 && rec.seq == 1 && rec.source == 1, "absent file: %d", rc);
	CHECK(simk_nev() == 0, "the file backend touched the device: %d events",
	      simk_nev());
	rc = cfg_load_info(path, &d, &info);
	CHECK(rc == 0 && info.selected == 1 && d.seq == 1 &&
	      info.file_bytes == (size_t)CFG_FILE_SIZE, "it loads");
	rc = cfg_store_fresh(path, &rec);
	CHECK(rc == -CFGE_SEQ, "a valid record now: %d, want -CFGE_SEQ", rc);
	rc = cfg_store(path, &rec);
	CHECK(rc == 0 && rec.seq == 2 && rec.source == 2, "cfg_store: seq 2");
	{
		int fd = open(path, O_RDWR);
		uint8_t x = 0;

		CHECK(fd >= 0 && pread(fd, &x, 1, 9) == 1, "open");
		x ^= 0x5Au;
		CHECK(pwrite(fd, &x, 1, 9) == 1, "corrupt slot 0");
		CHECK(pread(fd, &x, 1, CFG_SLOT_SIZE + 9) == 1, "read");
		x ^= 0x5Au;
		CHECK(pwrite(fd, &x, 1, CFG_SLOT_SIZE + 9) == 1,
		      "corrupt slot 1");
		close(fd);
	}
	rc = cfg_store_fresh(path, &rec);
	CHECK(rc == 0 && rec.seq == 1, "both corrupt: %d", rc);
	remove(path);
}

/* ------------------------------------------------------------------------- */
/* The dispatch                                                              */
/* ------------------------------------------------------------------------- */

static void t_dispatch(void)
{
	char copy[32], path[DIRMAX + 32];
	struct cfg c;
	int rc;

	T_GROUP("dispatch: by string, never by pointer");
	(void)snprintf(copy, sizeof copy, "%s", "/dev/mtd2ro");
	CHECK(cfg_is_flash(CFG_FLASH_DEV) == 1, "the macro");
	CHECK(cfg_is_flash(copy) == 1, "an argv-like copy of the string");
	CHECK(cfg_is_flash("/dev/mtd2ro/") == 0 && cfg_is_flash("/dev/mtd2") == 0 &&
	      cfg_is_flash("/dev/mtd2ro ") == 0 && cfg_is_flash(NULL) == 0,
	      "and nothing else");
	CHECK(simk_init(g_dir) == 0, "fresh");
	base_cfg(&c, "copied");
	simk_reset();
	rc = cfg_store(copy, &c);
	CHECK(rc == 0 && count_kind_prefix("install cfg0") == 1,
	      "a copy of the path reaches the flash backend: rc %d", rc);
	(void)snprintf(path, sizeof path, "%s/plain.bin", g_dir);
	remove(path);
	simk_reset();
	rc = cfg_store(path, &c);
	CHECK(rc == 0 && simk_nev() == 0,
	      "any other path is a file: rc %d, %d device events", rc,
	      simk_nev());
	remove(path);
}

/* ------------------------------------------------------------------------- */
/* The CLI, linked with the same simulation                                  */
/* ------------------------------------------------------------------------- */

static int log_has(const char *line)
{
	char lp[DIRMAX + 32];
	int fd;
	ssize_t n;
	static char txt[16384];

	(void)snprintf(lp, sizeof lp, "%s/writes.log", simk_dir());
	fd = open(lp, O_RDONLY);
	if (fd < 0)
		return 0;
	n = read(fd, txt, sizeof txt - 1);
	close(fd);
	txt[(n > 0) ? (size_t)n : 0] = '\0';
	return line == NULL ? (int)n : strstr(txt, line) != NULL;
}

static void t_cli(void)
{
	char plain[DIRMAX + 32], inst[200];
	struct cfg c;
	int rc, before;

	T_GROUP("cli: show on an erased store is source default (option A)");
	CHECK(simk_init(g_dir) == 0, "fresh");
	{
		char *const a[] = { (char *)"cfgstore", (char *)"show", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 0, "show with the DEFAULT path: exit %d", rc);
		CHECK(has("store  /dev/mtd2ro  bytes 0  source default"),
		      "the default path is the flash backend, no store yet");
		CHECK(has("<unset>"), "admin.pwhash unset");
		if (rc != 0 || !has("source default"))
			show_out();
	}

	T_GROUP("cli: set writes one slot through the verbs");
	{
		char *const a[] = { (char *)"cfgstore", (char *)"set",
				    (char *)"sys.hostname=simbox", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 0 && has("written: slot 0, seq 1"), "set: exit %d", rc);
		if (rc != 0)
			show_out();
	}
	/* The record `set` builds over an empty store: the defaults, absent,
	 * and the one key it was given. */
	cfg_defaults(&c);
	CHECK(cfg_set(&c, CFG_ID_HOSTNAME, (const uint8_t *)"simbox", 6) == 0,
	      "the expected record");
	install_line(0, &c, 1, inst, sizeof inst);
	{
		char want[400];

		/* The lock, both slots read under it, the eight steps, the
		 * read-back of slot 0, the release: every line, in order. */
		(void)snprintf(want, sizeof want,
			       "L\ns 0x3c0000\ns 0x3d0000\nv disarm\nv img reset\n"
			       "i 4096\nv %s\nv %s\nv img reset\ns 0x3c0000\nU\n",
			       arm_line(0), inst);
		CHECK(log_has(want), "writes.log holds the store's lines in order");
		if (!log_has(want))
			printf("      want:\n%s", want);
	}
	{
		char *const a[] = { (char *)"cfgstore", (char *)"--file",
				    (char *)CFG_FLASH_DEV, (char *)"show", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 0 && has("source slot0  seq 1") && has("simbox"),
		      "show: exit %d", rc);
		if (rc != 0 || !has("source slot0"))
			show_out();
	}

	T_GROUP("cli: dump --hex reads through the backend");
	{
		char *const a[] = { (char *)"cfgstore", (char *)"dump",
				    (char *)"--hex", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 0, "dump: exit %d", rc);
		CHECK(has("slot 0  offset 3932160  read 4096"),
		      "slot 0 at 0x3C0000");
		CHECK(has("slot 1  offset 3997696  read 0"),
		      "slot 1 at 0x3D0000, erased, read as absent");
		CHECK(has("3c0000 524c5843"), "the magic at its flash offset");
		if (rc != 0 || !has("3c0000 524c5843"))
			show_out();
	}

	T_GROUP("cli: one slot erased loads the other; both corrupt exits 4");
	CHECK(slot_erase(0) == 0 && slot_put(1, 4, "slotone") == 0, "fixture");
	{
		char *const a[] = { (char *)"cfgstore", (char *)"show", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 0 && has("source slot1  seq 4") && has("slotone"),
		      "show: exit %d", rc);
		CHECK(slot_put(0, 3, "zero") == 0 && slot_corrupt(0) == 0 &&
		      slot_corrupt(1) == 0, "both corrupt");
		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 4 && has("no valid record"), "show: exit %d, want 4",
		      rc);
	}

	T_GROUP("cli: --file is the file backend, and sends nothing");
	(void)snprintf(plain, sizeof plain, "%s/cli-plain.bin", g_dir);
	remove(plain);
	before = log_has(NULL);
	{
		char *const a[] = { (char *)"cfgstore", (char *)"--file", plain,
				    (char *)"init", (char *)"--force", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 0, "init --force on a file: exit %d", rc);
		CHECK(log_has(NULL) == before, "writes.log did not grow");
	}
	remove(plain);
}

/* ------------------------------------------------------------------------- */
/* The file backend takes regular files only (the 21:4x ruling on item 7)    */
/* ------------------------------------------------------------------------- */

static void t_nonregular(void)
{
	static const char *const bad[] = { "/dev/mtd0ro", "//dev/mtd2ro" };
	uint8_t buf[CFG_SLOT_SIZE];
	char plain[DIRMAX + 32];
	struct cfg c;
	struct cfg_store_info info;
	uint32_t where = 0;
	size_t got = 1;
	int k, rc;

	for (k = 0; k < 2; k++) {
		char label[80];

		(void)snprintf(label, sizeof label,
			       "file backend: %s is refused, never read", bad[k]);
		T_GROUP(label);
		CHECK(simk_init(g_dir) == 0, "fresh");
		CHECK(cfg_is_flash(bad[k]) == 0, "not CFG_FLASH_DEV, so a file");
		rc = cfg_load_info(bad[k], &c, &info);
		CHECK(rc == -CFGE_IO && c.source == 0 && info.file_bytes == 0,
		      "load: rc %d bytes %lu, want -CFGE_IO and none", rc,
		      (unsigned long)info.file_bytes);
		CHECK(strcmp(cfg_file_why(), "not a regular file") == 0,
		      "named \"%s\"", cfg_file_why());
		rc = cfg_slot_raw(bad[k], 0, buf, &got, &where);
		CHECK(rc == -CFGE_IO && got == 0, "slot_raw: rc %d got %lu", rc,
		      (unsigned long)got);
		base_cfg(&c, "never");
		rc = cfg_store(bad[k], &c);
		CHECK(rc == -CFGE_IO && c.seq == 0, "store: rc %d", rc);
		rc = cfg_store_fresh(bad[k], &c);
		CHECK(rc == -CFGE_IO && c.seq == 0, "fresh: rc %d", rc);
		CHECK(simk_nev() == 0, "%d events: no lseek on the node, so no"
		      " read; no lock, no verb", simk_nev());
	}

	T_GROUP("file backend: a regular file is permitted");
	(void)snprintf(plain, sizeof plain, "%s/regular.bin", g_dir);
	remove(plain);
	base_cfg(&c, "regular");
	rc = cfg_store(plain, &c);
	CHECK(rc == 0 && c.seq == 1 && cfg_file_why()[0] == '\0',
	      "store: rc %d, \"%s\"", rc, cfg_file_why());
	rc = cfg_load_info(plain, &c, &info);
	CHECK(rc == 0 && info.selected == 1 && cfg_file_why()[0] == '\0',
	      "load: rc %d selected %d", rc, info.selected);
	rc = cfg_slot_raw(plain, 0, buf, &got, &where);
	CHECK(rc == 0 && got == (size_t)CFG_SLOT_SIZE && where == 0,
	      "slot_raw: rc %d got %lu", rc, (unsigned long)got);
	remove(plain);

	T_GROUP("cli: --file //dev/mtd2ro and /dev/mtd0ro exit 3, nothing dumped");
	{
		char *const a[] = { (char *)"cfgstore", (char *)"--file",
				    (char *)"//dev/mtd2ro", (char *)"dump",
				    (char *)"--hex", NULL };
		char *const b[] = { (char *)"cfgstore", (char *)"--file",
				    (char *)"/dev/mtd0ro", (char *)"show", NULL };

		rc = run_bin(g_bin, a, 1);
		CHECK(rc == 3 && has("not a regular file") && !has("slot 0  offset"),
		      "dump //dev/mtd2ro: exit %d", rc);
		if (rc != 3)
			show_out();
		rc = run_bin(g_bin, b, 1);
		CHECK(rc == 3 && has("not a regular file") && !has("source"),
		      "show /dev/mtd0ro: exit %d", rc);
	}
}

int main(int argc, char **argv)
{
	if (argc < 3 || strlen(argv[1]) >= DIRMAX - 32 ||
	    strlen(argv[2]) >= DIRMAX) {
		fputs("usage: test_flash <scratch dir> <cfgstore-sim>\n", stderr);
		return 2;
	}
	(void)snprintf(g_dir, sizeof g_dir, "%s/flashsim", argv[1]);
	(void)snprintf(g_bin, sizeof g_bin, "%s", argv[2]);
	(void)snprintf(g_out, sizeof g_out, "%s/cli.out", argv[1]);
	(void)mkdir(g_dir, 0755);
	if (schema_self_check() != 0 || simk_init(g_dir) != 0) {
		printf("FAIL setup: the schema or the simulated chip\n");
		return 1;
	}
	printf("  simulated chip: %s\n", simk_flash_file());

	t_reads();
	t_store_ok();
	t_deviations();
	t_fresh();
	t_dispatch();
	t_cli();
	t_nonregular();
	return t_done("flash");
}
