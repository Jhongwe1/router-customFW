/* src/brokerd/test_update.c -- the update ops (update.c) and the install after
 * END's reply, against a simulated rtl819x-spi.  notes/self-update.md § 4.8.
 *
 *   test_update <fixture dir> <scratch dir>
 *
 * The fixture dir is src/brokerd/mkfix.sh's: containers made by
 * tools/mkfw2.py with the development seed.  The scratch dir holds
 * src/cfgstore/simkern.c's 4 MiB part, its event log and the stub
 * /proc/rlxfw-boot.  This binary links with simkern's --wrap list, so
 * update.c opens the five real device paths of spictl_dev and simkern answers
 * them with the kernel's own install header: the verb parser, the arm check,
 * the staging admission, the payload check (HDR_LEN included), the plan of
 * erases and programs, the read-back compare.  Every write update.c makes to
 * /proc/rtl819x-spi and /proc/rtl819x-spi-img is an event, kept in order.
 *
 * What is asserted, case by case: the reply's status and UPD_T_REASON by
 * name; that EVERY refusal leaves the event list without one verb, one
 * staging write or one lock; that an accepted container produces exactly the
 * lock, disarm, img reset, the staging writes, the arm line, the install line
 * and img reset, in that order, then the reboot with the lock still held;
 * that each failure of the install sequence (simkern's faults) reboots
 * nothing; and through loop.c, that END's OK installs only when its reply was
 * written, never when the client had gone.
 *
 * Built twice.  With BK_UPD_KEY_DEV (the host build) it runs everything.
 * Without it -- update.c holding src/rlxboot/prodkey.h, as on the device --
 * it runs two cases (P01, P02): with only dev-signed slots in flash, nothing
 * verifies under the production key and END refuses at step 6, where the
 * development-key build answers OK for the same bytes (E01).  § 4.6's own
 * development-key row -- `sig` at step 8 -- needs a running slot signed with
 * the production key's private half, so on the host it is case E05 (a seed the
 * build does not trust) and on the device it is the card's.
 *
 * WHAT IT DOES NOT ESTABLISH.  simkern restates the driver's glue (its own
 * file says so), does not model the running-slot fence, and its flash is a
 * file; /proc/rlxfw-boot is a file this test writes.  Nothing here ran on the
 * device or under the vendor toolchain.
 */
#define _GNU_SOURCE 1

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "brokerd.h"
#include "sha256.h"
#include "simkern.h"
#include "../rlxboot/rlxboot.h"
#include "../rlxboot/container.h"

static int fails, nchecks;

#define CHECK(cond, ...) do { \
	nchecks++; \
	if (!(cond)) { \
		fails++; \
		(void)printf("  FAIL %s:%d ", __FILE__, __LINE__); \
		(void)printf(__VA_ARGS__); \
		(void)printf("\n"); \
	} \
} while (0)

static const char *fixdir, *rundir;
static char boot_file[600], store_file[600];

struct blob {
	uint8_t *p;
	size_t   n;
};

static struct blob fx_a5, fx_a6, fx_a7, fx_b5, fx_b6, fx_b7, fx_b6big, fx_b6key;
static struct blob fx_b6buf, fx_b6ldr, fx_b6self, fx_b6selfhi;

static void load(struct blob *b, const char *name)
{
	char path[700];
	struct stat st;
	FILE *f;

	(void)snprintf(path, sizeof(path), "%s/%s.rlxu", fixdir, name);
	if (stat(path, &st) != 0 || st.st_size <= 0) {
		(void)printf("  FAIL fixture %s is missing: run src/brokerd/mkfix.sh\n", path);
		exit(2);
	}
	b->n = (size_t)st.st_size;
	b->p = malloc(b->n + 8);
	f = fopen(path, "rb");
	if (b->p == 0 || f == 0 || fread(b->p, 1, b->n, f) != b->n) {
		(void)printf("  FAIL fixture %s unreadable\n", path);
		exit(2);
	}
	(void)fclose(f);
}

/* ---------------------------------------------------------- the broker */

static struct broker bk;
static int reboots, reboot_nev;

static int fake_reboot(void)
{
	reboots++;
	reboot_nev = simk_nev();
	return -EPERM;
}

static void fixture(void)
{
	bk_upd_discard(&bk);
	bk_init(&bk);
	bk.use_fake_clock = 1;
	bk.fake_now = 10000;
	bk.cfg_path = store_file;
	bk.boot_path = boot_file;
	bk.upd_reboot = fake_reboot;
	reboots = 0;
	reboot_nev = -1;
}

static void set_boot(const char *text)
{
	FILE *f;

	if (text == 0) {
		(void)unlink(boot_file);
		return;
	}
	f = fopen(boot_file, "w");
	if (f == 0 || fputs(text, f) < 0 || fclose(f) != 0) {
		(void)printf("  FAIL cannot write %s\n", boot_file);
		exit(2);
	}
}

/* A fresh 4 MiB part (simk_init: the low 64 KiB a pattern, the rest 0xFF),
 * slot A and slot B as given (0 = erased), the counter at `ctr`, and the
 * handoff; then an empty event list. */
static void layout(const struct blob *a, const struct blob *b, unsigned ctr,
                   const char *boot)
{
	uint8_t bm[RLXU_CTR_BYTES];
	unsigned i;
	int fd, bad = 0;

	if (simk_init(rundir) != 0) {
		(void)printf("  FAIL simk_init(%s)\n", rundir);
		exit(2);
	}
	fd = open(simk_flash_file(), O_WRONLY);
	if (fd < 0)
		bad = 1;
	if (!bad && a != 0 &&
	    pwrite(fd, a->p, a->n, (off_t)RLXB_SLOT_A_FLASH) != (ssize_t)a->n)
		bad = 1;
	if (!bad && b != 0 &&
	    pwrite(fd, b->p, b->n, (off_t)RLXB_SLOT_B_FLASH) != (ssize_t)b->n)
		bad = 1;
	memset(bm, 0xFF, sizeof(bm));
	for (i = 0; i < ctr; i++)
		bm[i / 8] = (uint8_t)(bm[i / 8] & ~(0x80u >> (i % 8)));
	if (!bad && pwrite(fd, bm, sizeof(bm), (off_t)RLXB_CTR_FLASH) != (ssize_t)sizeof(bm))
		bad = 1;
	if (fd >= 0)
		(void)close(fd);
	if (bad) {
		(void)printf("  FAIL cannot lay out %s\n", simk_flash_file());
		exit(2);
	}
	set_boot(boot);
	simk_reset();
}

struct who {
	uid_t   uid;
	uint8_t tok[PROTO_TOK_LEN];
	uint8_t csrf[PROTO_TOK_LEN];
};

static void sess(struct who *w)
{
	struct bk_sess *s = bk_sess_new(&bk);

	memset(w, 0, sizeof(*w));
	w->uid = BK_UID_HTTPD;
	if (s == 0) {
		(void)printf("  FAIL no session (urandom?)\n");
		exit(2);
	}
	memcpy(w->tok, s->tok, PROTO_TOK_LEN);
	memcpy(w->csrf, s->csrf, PROTO_TOK_LEN);
}

static uint8_t call(const struct who *w, uint8_t op, const uint8_t *body,
                    uint32_t n, struct proto_resp *rs)
{
	static struct proto_req rq;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = op;
	memcpy(rq.session, w->tok, PROTO_TOK_LEN);
	memcpy(rq.csrf, w->csrf, PROTO_TOK_LEN);
	if (n > 0)
		memcpy(rq.body, body, n);
	rq.body_len = n;
	memset(rs, 0, sizeof(*rs));
	if (bk_dispatch(&bk, &rq, w->uid, rs) != 0)
		return 0xFF;
	return rs->status;
}

static uint8_t begin(const struct who *w, uint32_t total, struct proto_resp *rs)
{
	uint8_t b[4];

	proto_put_be32(b, total);
	return call(w, OP_UPDATE_BEGIN, b, 4, rs);
}

static uint8_t data(const struct who *w, uint32_t at, const uint8_t *p,
                    uint32_t n, struct proto_resp *rs)
{
	static uint8_t b[PROTO_REQ_BODY_MAX];

	if (n > UPD_DATA_MAX) {
		(void)printf("  FAIL the test sent a %lu-byte piece; a request holds %d\n",
		             (unsigned long)n, UPD_DATA_MAX);
		exit(2);
	}
	proto_put_be32(b, at);
	if (n > 0)
		memcpy(b + 4, p, n);
	return call(w, OP_UPDATE_DATA, b, 4 + n, rs);
}

static uint8_t end(const struct who *w, uint32_t total, struct proto_resp *rs)
{
	uint8_t b[4];

	proto_put_be32(b, total);
	return call(w, OP_UPDATE_END, b, 4, rs);
}

/* The first TLV of `type`: 0 and its value, or -1. */
static int tlv(const struct proto_resp *rs, uint16_t type, const uint8_t **v,
               uint16_t *l)
{
	size_t off = 0;
	uint16_t t;

	while (proto_tlv_get(rs->body, rs->body_len, &off, &t, v, l) == 0)
		if (t == type)
			return 0;
	return -1;
}

static int reason_is(const struct proto_resp *rs, const char *why)
{
	const uint8_t *v;
	uint16_t l;

	if (why == 0)
		return tlv(rs, UPD_T_REASON, &v, &l) != 0;
	return tlv(rs, UPD_T_REASON, &v, &l) == 0 && l == strlen(why) &&
	       memcmp(v, why, l) == 0;
}

static const char *reason_of(const struct proto_resp *rs)
{
	static char b[UPD_REASON_MAX + 1];
	const uint8_t *v;
	uint16_t l;

	if (tlv(rs, UPD_T_REASON, &v, &l) != 0)
		return "(none)";
	if (l > UPD_REASON_MAX)
		l = UPD_REASON_MAX;
	memcpy(b, v, l);
	b[l] = '\0';
	return b;
}

static long tlv_num(const struct proto_resp *rs, uint16_t type)
{
	const uint8_t *v;
	uint16_t l;

	if (tlv(rs, type, &v, &l) != 0)
		return -1;
	if (l == 1)
		return v[0];
	if (l == 4)
		return (long)proto_be32(v);
	return -2;
}

/* BEGIN, the pieces of UPD_DATA_MAX, END.  0 when END answered (rs is its
 * reply); 1 or 2 when BEGIN or a DATA refused (rs is that refusal). */
static int upload(const struct who *w, const uint8_t *p, size_t n,
                  struct proto_resp *rs)
{
	uint32_t off = 0;

	if (begin(w, (uint32_t)n, rs) != ST_OK)
		return 1;
	while (off < n) {
		uint32_t k = (uint32_t)n - off;

		if (k > UPD_DATA_MAX)
			k = UPD_DATA_MAX;
		if (data(w, off, p + off, k, rs) != ST_OK)
			return 2;
		off += k;
	}
	(void)end(w, (uint32_t)n, rs);
	return 0;
}

/* STATUS's BKS_UPDATE_LAST as text, "" when absent. */
static const char *status_last(const struct who *w)
{
	static char b[BKS_UPDATE_LAST_MAX + 1];
	struct proto_resp rs;
	const uint8_t *v;
	uint16_t l;

	b[0] = '\0';
	if (call(w, OP_STATUS, 0, 0, &rs) != ST_OK)
		return "(status refused)";
	if (tlv(&rs, BKS_UPDATE_LAST, &v, &l) != 0)
		return "";
	if (l > BKS_UPDATE_LAST_MAX)
		return "(too long)";
	memcpy(b, v, l);
	b[l] = '\0';
	return b;
}

/* ------------------------------------------------------------ events */

static int ev_kind(char kind)
{
	int i, n = 0, nev = simk_nev();

	for (i = 0; i < nev; i++)
		if (simk_ev(i)->kind == kind)
			n++;
	return n;
}

/* Verbs, staging writes, lock and unlock: the events a refusal must not make. */
static int ev_writes(void)
{
	return ev_kind('v') + ev_kind('i') + ev_kind('L') + ev_kind('U');
}

static void ev_dump(const char *why)
{
	int i, nev = simk_nev();

	(void)printf("    events (%s): %d\n", why, nev);
	for (i = 0; i < nev && i < 40; i++) {
		const struct simk_ev *e = simk_ev(i);

		(void)printf("      %c %-60.60s len=%lu err=%d off=0x%lx\n", e->kind,
		             e->text, (unsigned long)e->len, e->err,
		             (unsigned long)e->off);
	}
}

#ifdef BK_UPD_KEY_DEV
/* The cases that need a container the build trusts: the development key's
 * build only.  The production-key build runs end_refused() and main()'s two. */
static void hexof(const uint8_t *p, size_t n, char *out)
{
	static const char hx[] = "0123456789abcdef";
	size_t i;

	for (i = 0; i < n; i++) {
		out[2 * i] = hx[p[i] >> 4];
		out[2 * i + 1] = hx[p[i] & 15];
	}
	out[2 * n] = '\0';
}

/* The accepted install's events, exactly: every one but the flash reads,
 * which END made before it.  Returns 0, or the index of the first event that
 * is not the one wanted (and prints it). */
static int expect_install(const uint8_t *img, size_t n, char dest)
{
	char want[160], hex[65];
	uint8_t md[SHA256_DIGEST_LEN];
	unsigned long base = (dest == 'A') ? RLXB_SLOT_A_FLASH : RLXB_SLOT_B_FLASH;
	int i, k = 0, nev = simk_nev();
	size_t staged = 0;
	int stage = 0;          /* 0 before, 1 in the staging writes, 2 after */
	int step = 0;

	(void)sha256(img, n, md);
	hexof(md, sizeof(md), hex);
	for (i = 0; i < nev; i++) {
		const struct simk_ev *e = simk_ev(i);

		if (e->kind == 's')
			continue;
		k++;
		switch (step) {
		case 0:
			if (e->kind != 'L') goto bad;
			step++;
			break;
		case 1:
			if (e->kind != 'v' || strcmp(e->text, "disarm") != 0) goto bad;
			step++;
			break;
		case 2:
			if (e->kind != 'v' || strcmp(e->text, "img reset") != 0) goto bad;
			step++;
			break;
		case 3:
			if (e->kind == 'i') {
				size_t w = n - staged > 4096 ? 4096 : n - staged;

				if (e->len != w || e->err != 0) goto bad;
				staged += e->len;
				stage = 1;
				if (staged == n)
					step++;
				break;
			}
			goto bad;
		case 4:
			(void)snprintf(want, sizeof(want), "arm 0x%lx 0x%lx 0x%lx",
			               base, base + RLXB_SLOT_SIZE,
			               (unsigned long)RLXB_SLOT_SIZE);
			if (e->kind != 'v' || strcmp(e->text, want) != 0 || e->err) goto bad;
			step++;
			break;
		case 5:
			(void)snprintf(want, sizeof(want), "install slot%c sha=%s", dest, hex);
			if (e->kind != 'v' || strcmp(e->text, want) != 0 || e->err) goto bad;
			step++;
			break;
		case 6:
			if (e->kind != 'v' || strcmp(e->text, "img reset") != 0) goto bad;
			step++;
			break;
		case 7:
			if (e->kind != 'U') goto bad;
			step++;
			break;
		default:
			goto bad;
		}
	}
	(void)stage;
	if (step != 8) {
		(void)printf("    the install stopped at step %d of 8\n", step);
		return 999;
	}
	return 0;
bad:
	(void)printf("    install event %d (step %d) is not the one wanted\n", k, step);
	return k;
}

/* After an accepted install: the slot holds the container then 0xFF, the other
 * slot and the low 64 KiB are as laid out. */
static int flash_is(const struct blob *a, const uint8_t *img, size_t n, char dest)
{
	static uint8_t chip[SIMK_CHIP];
	unsigned long dbase = (dest == 'A') ? RLXB_SLOT_A_FLASH : RLXB_SLOT_B_FLASH;
	unsigned long obase = (dest == 'A') ? RLXB_SLOT_B_FLASH : RLXB_SLOT_A_FLASH;
	FILE *f = fopen(simk_flash_file(), "rb");
	size_t i;
	int ok = 1;

	if (f == 0 || fread(chip, 1, sizeof(chip), f) != sizeof(chip)) {
		if (f)
			(void)fclose(f);
		return 0;
	}
	(void)fclose(f);
	for (i = 0; i < 0x10000u; i++)
		if (chip[i] != (uint8_t)((i * 7u + 1u) & 0x7Fu))
			ok = 0;
	if (memcmp(chip + dbase, img, n) != 0)
		ok = 0;
	for (i = n; i < RLXB_SLOT_SIZE; i++)
		if (chip[dbase + i] != 0xFF)
			ok = 0;
	if (a != 0 && memcmp(chip + obase, a->p, a->n) != 0)
		ok = 0;
	return ok;
}

/* ------------------------------------------------------------- G: the gate */

static void group_gate(void)
{
	struct who s1, none, other;
	struct proto_resp rs;

	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	memset(&none, 0, sizeof(none));
	none.uid = BK_UID_HTTPD;

	CHECK(begin(&none, 3160, &rs) == ST_AUTH && reason_is(&rs, 0),
	      "G01 BEGIN without a session: %u, want AUTH with no reason", rs.status);
	other = s1;
	other.csrf[3] ^= 0x40;
	CHECK(begin(&other, 3160, &rs) == ST_PERM && reason_is(&rs, 0),
	      "G02 BEGIN with a wrong CSRF token: %u, want PERM", rs.status);
	other = s1;
	other.uid = BK_UID_DNSFWD;
	CHECK(begin(&other, 3160, &rs) == ST_PERM,
	      "G03 BEGIN from uid 101: %u, want PERM", rs.status);
	other.uid = 1000;
	CHECK(begin(&other, 3160, &rs) == ST_PERM,
	      "G04 BEGIN from uid 1000: %u, want PERM", rs.status);
	CHECK(bk.upd.state == BK_UPD_NONE, "G01-G04 left a staging behind");
	CHECK(data(&none, 0, (const uint8_t *)"x", 1, &rs) == ST_AUTH &&
	      end(&none, 3160, &rs) == ST_AUTH, "G05 DATA and END without a session: AUTH");
	CHECK(begin(&s1, 3160, &rs) == ST_OK && tlv_num(&rs, UPD_T_DEST) == 'B',
	      "G06 control: the same BEGIN with the session is OK, dest B: %u %ld",
	      rs.status, tlv_num(&rs, UPD_T_DEST));
	other = s1;
	other.csrf[0] ^= 1;
	CHECK(data(&other, 0, fx_b6.p, 100, &rs) == ST_PERM && bk.upd.received == 0,
	      "G07 DATA with a wrong CSRF: PERM, nothing taken");
	CHECK(ev_writes() == 0, "G: the gate wrote");
}

/* ----------------------------------------------------------- B: BEGIN */

static void begin_handoff(const char *name, const char *boot, int want_ok,
                          int want_dest)
{
	struct who s1;
	struct proto_resp rs;

	fixture();
	layout(&fx_a5, 0, 5, boot);
	sess(&s1);
	(void)begin(&s1, 3160, &rs);
	if (want_ok)
		CHECK(rs.status == ST_OK && tlv_num(&rs, UPD_T_DEST) == want_dest,
		      "%s: %u %s dest %ld, want OK dest %c", name, rs.status,
		      reason_of(&rs), tlv_num(&rs, UPD_T_DEST), want_dest);
	else
		CHECK(rs.status == ST_INVAL && reason_is(&rs, "handoff") &&
		      bk.upd.state == BK_UPD_NONE,
		      "%s: %u %s, want INVAL handoff and no staging", name,
		      rs.status, reason_of(&rs));
	CHECK(ev_writes() == 0, "%s: BEGIN wrote", name);
}

static void group_begin(void)
{
	struct who s1, s2, root;
	struct proto_resp rs;
	uint8_t three[3] = { 0, 0, 0 };

	begin_handoff("B01 handoff `none`", "none\n", 0, 0);
	begin_handoff("B02 no /proc/rlxfw-boot", 0, 0, 0);
	begin_handoff("B03 slot C", "slot C ver 5\n", 0, 0);
	begin_handoff("B04 ver 0", "slot A ver 0\n", 0, 0);
	begin_handoff("B05 a leading zero", "slot A ver 05\n", 0, 0);
	begin_handoff("B06 no newline", "slot A ver 5", 0, 0);
	begin_handoff("B07 ver 4294967295", "slot A ver 4294967295\n", 0, 0);
	begin_handoff("B08 trailing text", "slot A ver 5\nx", 0, 0);
	begin_handoff("B09 control: slot A ver 5", "slot A ver 5\n", 1, 'B');
	begin_handoff("B10 control: slot B ver 4294967294",
	              "slot B ver 4294967294\n", 1, 'A');

	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	sess(&s2);
	CHECK(begin(&s1, 1179649, &rs) == ST_INVAL && reason_is(&rs, "too_big") &&
	      bk.upd.state == BK_UPD_NONE,
	      "B11 total 1,179,649: %u %s, want INVAL too_big", rs.status, reason_of(&rs));
	CHECK(begin(&s1, 1179648, &rs) == ST_OK && bk.upd.total == 1179648,
	      "B12 control: total 1,179,648 is a staging: %u %s", rs.status, reason_of(&rs));
	CHECK(begin(&s1, 159, &rs) == ST_INVAL && reason_is(&rs, "short"),
	      "B13 total 159: %u %s, want INVAL short", rs.status, reason_of(&rs));
	CHECK(begin(&s1, 160, &rs) == ST_OK && bk.upd.total == 160,
	      "B14 control: total 160: %u %s", rs.status, reason_of(&rs));
	CHECK(call(&s1, OP_UPDATE_BEGIN, three, 3, &rs) == ST_INVAL &&
	      reason_is(&rs, "badlen"), "B15 a 3-byte BEGIN: %u %s, want badlen",
	      rs.status, reason_of(&rs));

	CHECK(begin(&s1, 3160, &rs) == ST_OK, "B16 S1 BEGIN: %u", rs.status);
	CHECK(data(&s1, 0, fx_b6.p, 1000, &rs) == ST_OK, "B16 S1 DATA: %u", rs.status);
	CHECK(begin(&s2, 3160, &rs) == ST_BUSY && reason_is(&rs, "busy"),
	      "B17 S2 BEGIN while S1 stages: %u %s, want BUSY busy", rs.status,
	      reason_of(&rs));
	CHECK(bk.upd.state == BK_UPD_STAGING && bk.upd.received == 1000,
	      "B17 S1's staging untouched by S2's BEGIN");
	CHECK(data(&s1, 1000, fx_b6.p + 1000, 1000, &rs) == ST_OK &&
	      tlv_num(&rs, UPD_T_RECEIVED) == 2000,
	      "B18 S1 goes on: RECEIVED %ld, want 2000", tlv_num(&rs, UPD_T_RECEIVED));
	CHECK(begin(&s1, 3160, &rs) == ST_OK && bk.upd.received == 0,
	      "B19 S1's own new BEGIN replaces its staging");

	memset(&root, 0, sizeof(root));
	root.uid = BK_UID_ROOT;
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	CHECK(begin(&root, 3160, &rs) == ST_OK, "B20 root, no session: BEGIN OK: %u",
	      rs.status);
	CHECK(ev_writes() == 0, "B: BEGIN wrote");
}

/* ------------------------------------------------------------- D: DATA */

static void group_data(void)
{
	struct who s1, s2;
	struct proto_resp rs;
	uint8_t z = 0;

	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	sess(&s2);
	CHECK(data(&s1, 0, fx_b6.p, 10, &rs) == ST_INVAL && reason_is(&rs, "sequence"),
	      "D01 DATA with no staging: %u %s, want INVAL sequence", rs.status,
	      reason_of(&rs));
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK, "D02 BEGIN");
	CHECK(data(&s1, 0, fx_b6.p, UPD_DATA_MAX, &rs) == ST_OK &&
	      tlv_num(&rs, UPD_T_RECEIVED) == UPD_DATA_MAX,
	      "D02 a full piece: RECEIVED %ld", tlv_num(&rs, UPD_T_RECEIVED));
	CHECK(data(&s2, UPD_DATA_MAX, fx_b6.p + UPD_DATA_MAX, 10, &rs) == ST_BUSY &&
	      reason_is(&rs, "busy") && bk.upd.state == BK_UPD_STAGING,
	      "D03 another session's DATA: %u %s, want BUSY and no poison",
	      rs.status, reason_of(&rs));
	CHECK(data(&s1, UPD_DATA_MAX + 1, fx_b6.p, 10, &rs) == ST_INVAL &&
	      reason_is(&rs, "sequence") && bk.upd.state == BK_UPD_POISONED &&
	      bk.upd.buf == 0,
	      "D04 an offset one past: %u %s, want INVAL sequence, poisoned, freed",
	      rs.status, reason_of(&rs));
	CHECK(data(&s1, UPD_DATA_MAX, fx_b6.p + UPD_DATA_MAX, 10, &rs) == ST_INVAL &&
	      reason_is(&rs, "sequence") && bk.upd.state == BK_UPD_POISONED,
	      "D05 the right offset after the poison is still refused: %u %s",
	      rs.status, reason_of(&rs));
	CHECK(end(&s1, (uint32_t)fx_b6.n, &rs) == ST_INVAL &&
	      reason_is(&rs, "sequence") && bk.upd.state == BK_UPD_NONE,
	      "D06 END over a poisoned staging: %u %s, want INVAL sequence",
	      rs.status, reason_of(&rs));
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, 10, &rs) == ST_OK,
	      "D07 control: a new BEGIN clears it");

	CHECK(data(&s1, 10, fx_b6.p + 10, 0, &rs) == ST_INVAL &&
	      reason_is(&rs, "badlen") && bk.upd.state == BK_UPD_POISONED,
	      "D08 a DATA with no bytes: %u %s, want badlen, poisoned", rs.status,
	      reason_of(&rs));
	CHECK(begin(&s1, 200, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, 200, &rs) == ST_OK &&
	      data(&s1, 200, &z, 1, &rs) == ST_INVAL && reason_is(&rs, "sequence") &&
	      bk.upd.state == BK_UPD_POISONED,
	      "D09 one byte past the total: %u %s, want sequence, poisoned",
	      rs.status, reason_of(&rs));

	/* 30 s after the last DATA */
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, 10, &rs) == ST_OK, "D10 BEGIN, DATA");
	bk.fake_now += BK_UPD_IDLE_S - 1;
	CHECK(data(&s1, 10, fx_b6.p + 10, 10, &rs) == ST_OK,
	      "D10 control: 29 s after the last DATA the staging is there: %u %s",
	      rs.status, reason_of(&rs));
	bk.fake_now += BK_UPD_IDLE_S;
	CHECK(data(&s1, 20, fx_b6.p + 20, 10, &rs) == ST_INVAL &&
	      reason_is(&rs, "sequence") && bk.upd.state == BK_UPD_NONE,
	      "D11 30 s after it the staging is gone: %u %s", rs.status, reason_of(&rs));

	/* the session ends: LOGOUT */
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	sess(&s2);
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, 10, &rs) == ST_OK, "D12 BEGIN, DATA");
	CHECK(call(&s1, OP_LOGOUT, 0, 0, &rs) == ST_OK, "D12 LOGOUT");
	CHECK(data(&s1, 10, fx_b6.p + 10, 10, &rs) == ST_AUTH,
	      "D12 the logged-out session's DATA is AUTH: %u", rs.status);
	CHECK(begin(&s2, (uint32_t)fx_b6.n, &rs) == ST_OK,
	      "D13 S2's BEGIN after S1's LOGOUT is OK, not busy: %u %s", rs.status,
	      reason_of(&rs));
	/* and every session dropped at once (PWSET's and a changed pwhash's way) */
	bk_sess_drop_all(&bk);
	bk_upd_sweep(&bk);
	CHECK(bk.upd.state == BK_UPD_NONE && bk.upd.buf == 0,
	      "D14 bk_sess_drop_all: the sweep frees the staging");
	CHECK(ev_writes() == 0, "D: DATA wrote");
}
#endif /* BK_UPD_KEY_DEV */

/* ------------------------------------------------- E: END, every row */

static int status_after(const char *want)
{
	struct who r;

	memset(&r, 0, sizeof(r));
	r.uid = BK_UID_ROOT;
	return strcmp(status_last(&r), want) == 0;
}

static void end_refused(const char *name, const struct blob *a,
                        const struct blob *b, unsigned ctr, const char *boot,
                        const uint8_t *img, size_t n, uint8_t want_st,
                        const char *want_why)
{
	struct who s1;
	struct proto_resp rs;
	int rc;

	fixture();
	layout(a, b, ctr, boot);
	sess(&s1);
	rc = upload(&s1, img, n, &rs);
	CHECK(rc == 0 && rs.status == want_st && reason_is(&rs, want_why),
	      "%s: step %d answered %u %s, want %u %s", name, rc, rs.status,
	      reason_of(&rs), want_st, want_why);
	CHECK(tlv_num(&rs, UPD_T_DEST) == -1 && tlv_num(&rs, UPD_T_VERSION) == -1,
	      "%s: a refusal carries no DEST or VERSION", name);
	CHECK(bk.upd.state == BK_UPD_NONE && bk.upd.buf == 0 &&
	      bk.pending_update == 0, "%s: the staging outlived its END", name);
	CHECK(ev_writes() == 0, "%s: a refusal wrote", name);
	if (ev_writes() != 0)
		ev_dump(name);
	CHECK(status_after(want_why), "%s: STATUS says %s", name, want_why);
	/* Told "delivered" anyway: there is nothing to install. */
	CHECK(bk_upd_after_reply(&bk, 1) == -1 && ev_writes() == 0 && reboots == 0,
	      "%s: an install after a refusal", name);
}

#ifdef BK_UPD_KEY_DEV
static uint8_t flipped[RLXB_SLOT_SIZE + 8];

static const uint8_t *flip(const struct blob *b, size_t byte, int bit)
{
	memcpy(flipped, b->p, b->n);
	flipped[byte] = (uint8_t)(flipped[byte] ^ (1u << bit));
	return flipped;
}

static void group_end(void)
{
	struct who s1, s2;
	struct proto_resp rs;

	/* § 4.6, row by row */
	end_refused("E02 a payload bit flipped", &fx_a5, 0, 5, "slot A ver 5\n",
	            flip(&fx_b6, 1000, 3), fx_b6.n, ST_INVAL, "digest");
	end_refused("E03 bit 0 of header byte 28 (the digest field)", &fx_a5, 0, 5,
	            "slot A ver 5\n", flip(&fx_b6, 28, 0), fx_b6.n, ST_INVAL, "sig");
	end_refused("E04 signed for the running slot (B7 while B6 runs)", &fx_a5,
	            &fx_b6, 6, "slot B ver 6\n", fx_b7.p, fx_b7.n, ST_INVAL,
	            "flash_match");
	end_refused("E05 a key the build does not trust", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b6key.p, fx_b6key.n, ST_INVAL, "sig");
	end_refused("E06 below the counter (A5 with B6 running, ctr 6)", &fx_a5,
	            &fx_b6, 6, "slot B ver 6\n", fx_a5.p, fx_a5.n, ST_INVAL,
	            "rollback");
	/* the three of § 4.4 */
	end_refused("E07 the counter behind the running version", &fx_a5, &fx_b6, 5,
	            "slot B ver 6\n", fx_a7.p, fx_a7.n, ST_BUSY, "ctr_behind");
	end_refused("E08 the handoff names B6, flash would boot A7", &fx_a7,
	            &fx_b6, 6, "slot B ver 6\n", fx_a7.p, fx_a7.n, ST_INVAL,
	            "handoff_mismatch");
	end_refused("E09 the handoff names A5, slot A is erased", 0, &fx_b6, 5,
	            "slot A ver 5\n", fx_b7.p, fx_b7.n, ST_INVAL, "handoff_mismatch");
	end_refused("E10 the handoff names A5, a valid B6 is in flash", &fx_a5,
	            &fx_b6, 5, "slot A ver 5\n", fx_b7.p, fx_b7.n, ST_INVAL,
	            "handoff_mismatch");
	end_refused("E11 an equal version to B (A5 runs)", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b5.p, fx_b5.n, ST_INVAL, "would_not_boot");
	/* this file's one addition after step 8 */
	memcpy(flipped, fx_b6.p, fx_b6.n);
	memset(flipped + fx_b6.n, 0, 4);
	end_refused("E12 four bytes past the container", &fx_a5, 0, 5,
	            "slot A ver 5\n", flipped, fx_b6.n + 4, ST_INVAL, "trailing");
	/* rlxu_verify's own reasons, by its names */
	end_refused("E13 truncated: the container less its last byte", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b6.p, fx_b6.n - 1, ST_INVAL, "truncated");
	end_refused("E14 not RLXU", &fx_a5, 0, 5, "slot A ver 5\n",
	            flip(&fx_b6, 0, 1), fx_b6.n, ST_INVAL, "magic");
	/* rlxboot's ENVIRONMENT, field by field: each container is valid but for
	 * where it would land, and each is refused by the field a looser
	 * environment would have left open (E01 is their permitting twin, the
	 * same container at 0x80500000). */
	end_refused("E29 landing on slot B's RAM buffer (0x81200000)", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b6buf.p, fx_b6buf.n, ST_INVAL, "dst_buf");
	end_refused("E30 landing on stage 2's window (0x80400000)", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b6ldr.p, fx_b6ldr.n, ST_INVAL, "dst_loader");
	end_refused("E31 landing on rlxboot (0x81800000)", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b6self.p, fx_b6self.n, ST_INVAL, "dst_self");
	end_refused("E32 landing in the superset's last page (0x818FF000)", &fx_a5,
	            0, 5, "slot A ver 5\n", fx_b6selfhi.p, fx_b6selfhi.n, ST_INVAL,
	            "dst_self");

	/* the permitting twins: each row above, with the one thing changed */
	{
		static const struct {
			const char *name;
			const struct blob *a, *b, *img;
			unsigned ctr;
			const char *boot;
			char dest;
			long ver;
		} ok[] = {
			{ "E01 B6 with A5 running", &fx_a5, 0, &fx_b6, 5, "slot A ver 5\n", 'B', 6 },
			{ "E15 A7 with B6 running, ctr 6", &fx_a5, &fx_b6, &fx_a7, 6, "slot B ver 6\n", 'A', 7 },
			{ "E16 an equal version to A (B5 runs)", 0, &fx_b5, &fx_a5, 5, "slot B ver 5\n", 'A', 5 },
			{ "E17 A6 equal to the counter, B6 running", &fx_a5, &fx_b6, &fx_a6, 6, "slot B ver 6\n", 'A', 6 },
			{ "E18 B7 with A5 running", &fx_a5, 0, &fx_b7, 5, "slot A ver 5\n", 'B', 7 },
		};
		size_t i;

		for (i = 0; i < sizeof(ok) / sizeof(ok[0]); i++) {
			int rc;

			fixture();
			layout(ok[i].a, ok[i].b, ok[i].ctr, ok[i].boot);
			sess(&s1);
			rc = upload(&s1, ok[i].img->p, ok[i].img->n, &rs);
			CHECK(rc == 0 && rs.status == ST_OK &&
			      tlv_num(&rs, UPD_T_DEST) == ok[i].dest &&
			      tlv_num(&rs, UPD_T_VERSION) == ok[i].ver,
			      "%s: step %d answered %u %s dest %ld ver %ld", ok[i].name,
			      rc, rs.status, reason_of(&rs), tlv_num(&rs, UPD_T_DEST),
			      tlv_num(&rs, UPD_T_VERSION));
			CHECK(bk.upd.state == BK_UPD_VERIFIED && bk.pending_update == 1,
			      "%s: END OK leaves the install pending", ok[i].name);
			CHECK(ev_writes() == 0, "%s: END wrote before its reply", ok[i].name);
			bk_upd_discard(&bk);
		}
	}
	/* A counter past the running version: A5 runs and the counter reads 6,
	 * so step 5 refuses A5's own slot as rollback and step 6 cannot name
	 * A -- handoff_mismatch, by name, and never rollback for the upload. */
	end_refused("E19 the counter past the running version", &fx_a5, 0, 6,
	            "slot A ver 5\n", fx_b7.p, fx_b7.n, ST_INVAL, "handoff_mismatch");

	/* step 1 and step 2 */
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	sess(&s2);
	CHECK(end(&s1, 3160, &rs) == ST_INVAL && reason_is(&rs, "sequence"),
	      "E20 END with no staging: %u %s", rs.status, reason_of(&rs));
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, UPD_DATA_MAX, &rs) == ST_OK &&
	      data(&s1, UPD_DATA_MAX, fx_b6.p + UPD_DATA_MAX, 3000 - UPD_DATA_MAX,
	           &rs) == ST_OK, "E21 BEGIN, 3,000 bytes in two pieces");
	CHECK(end(&s2, (uint32_t)fx_b6.n, &rs) == ST_BUSY && reason_is(&rs, "busy") &&
	      bk.upd.state == BK_UPD_STAGING,
	      "E21 another session's END: %u %s, and the staging stays", rs.status,
	      reason_of(&rs));
	CHECK(end(&s1, (uint32_t)fx_b6.n, &rs) == ST_INVAL &&
	      reason_is(&rs, "incomplete") && bk.upd.state == BK_UPD_NONE,
	      "E22 END at 3,000 of 3,160: %u %s, want incomplete", rs.status,
	      reason_of(&rs));
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, UPD_DATA_MAX, &rs) == ST_OK &&
	      data(&s1, UPD_DATA_MAX, fx_b6.p + UPD_DATA_MAX,
	           (uint32_t)fx_b6.n - UPD_DATA_MAX, &rs) == ST_OK &&
	      end(&s1, (uint32_t)fx_b6.n + 4, &rs) == ST_INVAL &&
	      reason_is(&rs, "incomplete"),
	      "E23 END naming another total: %u %s, want incomplete", rs.status,
	      reason_of(&rs));
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK &&
	      data(&s1, 0, fx_b6.p, UPD_DATA_MAX, &rs) == ST_OK &&
	      data(&s1, UPD_DATA_MAX, fx_b6.p + UPD_DATA_MAX,
	           (uint32_t)fx_b6.n - UPD_DATA_MAX, &rs) == ST_OK,
	      "E24 BEGIN and every byte");
	set_boot("none\n");
	CHECK(end(&s1, (uint32_t)fx_b6.n, &rs) == ST_INVAL && reason_is(&rs, "handoff"),
	      "E24 the handoff gone by END: %u %s, want handoff", rs.status,
	      reason_of(&rs));
	CHECK(ev_writes() == 0, "E20-E24 wrote");

	/* STATUS: nothing before the first update op, then the last word */
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	CHECK(strcmp(status_last(&s1), "") == 0,
	      "E25 STATUS before any update carries no BKS_UPDATE_LAST: '%s'",
	      status_last(&s1));
	(void)upload(&s1, flip(&fx_b6, 2000, 0), fx_b6.n, &rs);
	CHECK(strcmp(status_last(&s1), "digest") == 0, "E26 STATUS after digest: '%s'",
	      status_last(&s1));
	(void)upload(&s1, fx_b6.p, fx_b6.n, &rs);
	CHECK(strcmp(status_last(&s1), "ok B 6") == 0, "E27 STATUS after OK: '%s'",
	      status_last(&s1));
	{
		struct who anon;
		struct proto_resp st;
		const uint8_t *v;
		uint16_t l;

		memset(&anon, 0, sizeof(anon));
		anon.uid = BK_UID_HTTPD;
		CHECK(call(&anon, OP_STATUS, 0, 0, &st) == ST_OK &&
		      tlv(&st, BKS_UPDATE_LAST, &v, &l) != 0,
		      "E28 the public STATUS never carries it");
	}
	bk_upd_discard(&bk);
}

/* ---------------------------------------- I: the install after the reply */

static void install_ok(const char *name, const struct blob *img)
{
	struct who s1;
	struct proto_resp rs;
	unsigned long nw0;
	int rc;

	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	rc = upload(&s1, img->p, img->n, &rs);
	CHECK(rc == 0 && rs.status == ST_OK, "%s: END %u %s", name, rs.status,
	      reason_of(&rs));
	CHECK(ev_writes() == 0, "%s: END wrote before the reply", name);
	nw0 = simk_nwrites();
	rc = bk_upd_after_reply(&bk, 1);
	CHECK(rc == 0 && reboots == 1, "%s: installed %d, rebooted %d", name, rc,
	      reboots);
	CHECK(expect_install(img->p, img->n, 'B') == 0,
	      "%s: the install's events are not exactly the sequence", name);
	if (expect_install(img->p, img->n, 'B') != 0)
		ev_dump(name);
	/* the reboot came after the last verb and before the unlock */
	CHECK(reboot_nev > 0 && simk_ev(reboot_nev) != 0 &&
	      simk_ev(reboot_nev)->kind == 'U' && simk_ev(reboot_nev - 1)->kind == 'v',
	      "%s: the reboot ran with the lock held (event %d)", name, reboot_nev);
	CHECK(simk_nwrites() - nw0 == 288ul + (img->n + 255ul) / 256ul,
	      "%s: n_writes moved %lu, want %lu", name, simk_nwrites() - nw0,
	      288ul + (img->n + 255ul) / 256ul);
	CHECK(flash_is(&fx_a5, img->p, img->n, 'B'),
	      "%s: slot B is not the container then 0xFF, or something else moved",
	      name);
	CHECK(bk.upd.state == BK_UPD_NONE && bk.upd.buf == 0,
	      "%s: the staging outlived the install", name);
	CHECK(status_after("ok B 6"), "%s: STATUS", name);
	CHECK(ev_kind('c') == 0, "%s: another flash node was read", name);
}

static void install_fault(const char *name, int fault, int want_verbs)
{
	struct who s1;
	struct proto_resp rs;
	int rc, nev, last_v = -1, i, nL, nU;

	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	rc = upload(&s1, fx_b6.p, fx_b6.n, &rs);
	CHECK(rc == 0 && rs.status == ST_OK, "%s: END %u", name, rs.status);
	simk_fault(fault);
	rc = bk_upd_after_reply(&bk, 1);
	simk_fault(SIMK_NONE);
	CHECK(rc == -1 && reboots == 0, "%s: installed %d, rebooted %d (want -1, 0)",
	      name, rc, reboots);
	nev = simk_nev();
	for (i = 0; i < nev; i++)
		if (simk_ev(i)->kind == 'v')
			last_v = i;
	nL = ev_kind('L');
	nU = ev_kind('U');
	if (want_verbs) {
		CHECK(last_v >= 0 && strcmp(simk_ev(last_v)->text, "img reset") == 0,
		      "%s: the last verb is not the cleanup img reset", name);
		CHECK(nL == 1 && nU == 1, "%s: lock %d unlock %d", name, nL, nU);
	} else {
		CHECK(ev_kind('v') == 0 && ev_kind('i') == 0, "%s: a verb was sent", name);
	}
	CHECK(status_after("install"), "%s: STATUS says install", name);
	CHECK(bk.upd.state == BK_UPD_NONE && bk.upd.buf == 0, "%s: staging kept", name);
	if (reboots != 0 || rc != -1)
		ev_dump(name);
}

static void group_install(void)
{
	struct who s1;
	struct proto_resp rs;

	install_ok("I01 B6, 3,160 bytes", &fx_b6);
	install_ok("I02 B6, 1,109,152 bytes (FW-246's length: n_writes +4,621)",
	           &fx_b6big);

	install_fault("I03 img_len short", SIMK_IMGLEN_SHORT, 1);
	install_fault("I04 img_err POISONED", SIMK_IMGERR, 1);
	install_fault("I05 the staging refused EFBIG", SIMK_STAGE_EFBIG, 1);
	install_fault("I06 inst_reason not OK", SIMK_INST_REASON, 1);
	install_fault("I07 the kernel refuses the digest", SIMK_INST_SHA, 1);
	install_fault("I08 inst_cmp_diff 1", SIMK_CMP_DIFF, 1);
	install_fault("I09 inst_cmp_ok 0", SIMK_CMP_OK0, 1);
	install_fault("I10 n_writes one short", SIMK_NW_MINUS1, 1);
	install_fault("I11 n_writes one over", SIMK_NW_PLUS1, 1);
	install_fault("I12 disarm refused", SIMK_DISARM_EIO, 1);
	install_fault("I13 arm refused", SIMK_ARM_EPERM, 1);
	install_fault("I14 flock ENOSYS", SIMK_LOCK_ENOSYS, 0);

	/* the lock held by another writer: 30 s asked for, nothing sent */
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	CHECK(upload(&s1, fx_b6.p, fx_b6.n, &rs) == 0 && rs.status == ST_OK, "I15 END");
	CHECK(simk_hold_lock(1) == 0, "I15 a second holder");
	CHECK(bk_upd_after_reply(&bk, 1) == -1 && reboots == 0 && ev_kind('v') == 0 &&
	      ev_kind('i') == 0 && simk_slept_ms() >= 30000ul,
	      "I15 the lock held: no verb, no reboot, %lu ms asked for",
	      simk_slept_ms());
	(void)simk_hold_lock(0);

	/* not delivered */
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	CHECK(upload(&s1, fx_b6.p, fx_b6.n, &rs) == 0 && rs.status == ST_OK, "I16 END");
	CHECK(bk_upd_after_reply(&bk, 0) == -1 && ev_writes() == 0 && reboots == 0 &&
	      bk.upd.state == BK_UPD_NONE && status_after("undelivered"),
	      "I16 a reply that did not leave: nothing written, nothing rebooted");
	CHECK(bk_upd_after_reply(&bk, 1) == -1 && ev_writes() == 0,
	      "I17 and a second call finds nothing to install");

	/* while the install waits for its reply, nothing else moves */
	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	CHECK(upload(&s1, fx_b6.p, fx_b6.n, &rs) == 0 && rs.status == ST_OK, "I18 END");
	CHECK(begin(&s1, 3160, &rs) == ST_BUSY && data(&s1, 0, fx_b6.p, 10, &rs) == ST_BUSY &&
	      end(&s1, 3160, &rs) == ST_BUSY && bk.upd.state == BK_UPD_VERIFIED,
	      "I18 BEGIN, DATA, END while verified: BUSY, and it stays verified");
	bk.fake_now += 3600;
	bk_sess_drop_all(&bk);
	bk_upd_sweep(&bk);
	CHECK(bk.upd.state == BK_UPD_VERIFIED,
	      "I19 an hour and every session gone: the sweep leaves a verified staging");
	CHECK(bk_upd_after_reply(&bk, 1) == 0 && reboots == 1, "I19 then it installs");
}

/* -------------------------------------------- L: through loop.c */

static int wire_req(uint8_t *out, const struct who *w, uint8_t op,
                    const uint8_t *body, uint32_t n)
{
	struct proto_req rq;

	memset(&rq, 0, sizeof(rq));
	rq.version = PROTO_VERSION;
	rq.op = op;
	memcpy(rq.session, w->tok, PROTO_TOK_LEN);
	memcpy(rq.csrf, w->csrf, PROTO_TOK_LEN);
	memcpy(rq.body, body, n);
	rq.body_len = n;
	return proto_encode_req(&rq, out, PROTO_REQ_MAX);
}

/* mode 0: the client reads the reply; 1: it closes before brokerd writes;
 * 2: its receive buffer is full, so the reply sits, and the loop is shut. */
static void loop_case(const char *name, int mode)
{
	static uint8_t junk[65536];
	struct bk_loop L;
	struct who s1;
	struct proto_resp rs;
	uint8_t req[PROTO_REQ_MAX], b4[4], back[PROTO_RESP_MAX];
	int sv[2], n, i, got = 0;

	fixture();
	layout(&fx_a5, 0, 5, "slot A ver 5\n");
	sess(&s1);
	CHECK(begin(&s1, (uint32_t)fx_b6.n, &rs) == ST_OK, "%s: BEGIN", name);
	for (i = 0; (size_t)i < fx_b6.n; i += UPD_DATA_MAX) {
		uint32_t k = (uint32_t)fx_b6.n - (uint32_t)i;

		if (k > UPD_DATA_MAX)
			k = UPD_DATA_MAX;
		(void)data(&s1, (uint32_t)i, fx_b6.p + i, k, &rs);
	}
	CHECK(bk.upd.received == fx_b6.n, "%s: every byte staged", name);
	if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0) {
		CHECK(0, "%s: socketpair", name);
		return;
	}
	if (mode == 2) {
		/* fill the client's receive queue from brokerd's side */
		(void)fcntl(sv[0], F_SETFL, O_NONBLOCK);
		memset(junk, 0x5A, sizeof(junk));
		while (write(sv[0], junk, sizeof(junk)) > 0)
			;
	}
	bk_loop_init(&L);
	CHECK(bk_loop_adopt(&L, sv[0], BK_UID_HTTPD) == 0, "%s: adopt", name);
	proto_put_be32(b4, (uint32_t)fx_b6.n);
	n = wire_req(req, &s1, OP_UPDATE_END, b4, 4);
	CHECK(n > 0 && write(sv[1], req, (size_t)n) == n, "%s: the END request", name);
	if (mode == 1)
		(void)close(sv[1]);
	for (i = 0; i < 20 && L.c[0].fd >= 0; i++) {
		(void)bk_loop_step(&bk, &L, -1, 20);
		if (mode == 2 && L.c[0].fd >= 0 && L.c[0].writing && i >= 3)
			break;
	}
	if (mode == 0) {
		ssize_t r = read(sv[1], back, sizeof(back));

		if (r > 0)
			got = (int)r;
		CHECK(got > 0 && proto_decode_resp(back, (size_t)got, &rs) > 0 &&
		      rs.status == ST_OK && tlv_num(&rs, UPD_T_DEST) == 'B',
		      "%s: the client read END's OK", name);
		CHECK(reboots == 1 && expect_install(fx_b6.p, fx_b6.n, 'B') == 0,
		      "%s: delivered, and installed once (%d reboots)", name, reboots);
	} else {
		if (mode == 2) {
			CHECK(L.c[0].fd >= 0 && L.c[0].writing &&
			      L.c[0].install_after_write == 1,
			      "%s: the reply waits in the slot, the install with it", name);
			bk_loop_close_all(&bk, &L);
		}
		CHECK(ev_writes() == 0 && reboots == 0,
		      "%s: not delivered, yet something was written or rebooted", name);
		if (ev_writes() != 0)
			ev_dump(name);
		CHECK(bk.upd.state == BK_UPD_NONE && status_after("undelivered"),
		      "%s: the staging is dropped and STATUS says undelivered", name);
	}
	bk_loop_close_all(&bk, &L);
	if (mode != 1)
		(void)close(sv[1]);
}

static void group_loop(void)
{
	loop_case("L01 the reply read by the client", 0);
	loop_case("L02 the client gone before the reply", 1);
	loop_case("L03 the reply stuck in the socket when the loop shuts", 2);
}
#endif /* BK_UPD_KEY_DEV */

/* -------------------------------------------------------------- main */

int main(int argc, char **argv)
{
	if (argc != 3) {
		(void)fprintf(stderr, "usage: test_update <fixture dir> <scratch dir>\n");
		return 2;
	}
	fixdir = argv[1];
	rundir = argv[2];
	/* line-buffered: an abort (a sanitizer, _FORTIFY_SOURCE) keeps what ran */
	(void)setvbuf(stdout, NULL, _IOLBF, 0);
	(void)signal(SIGPIPE, SIG_IGN);
	if (mkdir(rundir, 0700) != 0 && errno != EEXIST) {
		(void)printf("  FAIL mkdir %s\n", rundir);
		return 2;
	}
	(void)snprintf(boot_file, sizeof(boot_file), "%s/rlxfw-boot", rundir);
	(void)snprintf(store_file, sizeof(store_file), "%s/cfg-store.bin", rundir);
	(void)unlink(store_file);
	load(&fx_a5, "a5");
	load(&fx_a6, "a6");
	load(&fx_a7, "a7");
	load(&fx_b5, "b5");
	load(&fx_b6, "b6");
	load(&fx_b7, "b7");
	load(&fx_b6big, "b6big");
	load(&fx_b6key, "b6key");
	load(&fx_b6buf, "b6buf");
	load(&fx_b6ldr, "b6ldr");
	load(&fx_b6self, "b6self");
	load(&fx_b6selfhi, "b6selfhi");
#ifdef BK_UPD_KEY_DEV
	(void)printf("test_update (the development key)\n");
	group_gate();
	group_begin();
	group_data();
	group_end();
	group_install();
	group_loop();
#else
	/* The production key, on the host.  Every slot here is signed with the
	 * development key or another seed, so under prodkey.h NO slot verifies
	 * (step 5), rlxb_choose names none, and END stops at step 6 --
	 * handoff_mismatch -- before the upload is looked at.  Its twin is E01
	 * of the development-key build: the same layout and the same upload,
	 * OK.  § 4.6's "development key" row (`sig` at step 8) needs a running
	 * slot that verifies under the production key, i.e. one signed with its
	 * private half, which is not in this repository: the device's case. */
	(void)printf("test_update (src/rlxboot/prodkey.h, the device's key)\n");
	end_refused("P01 dev-signed slots and upload, on the production build",
	            &fx_a5, 0, 5, "slot A ver 5\n", fx_b6.p, fx_b6.n, ST_INVAL,
	            "handoff_mismatch");
	end_refused("P02 and an upload signed with another seed", &fx_a5, 0, 5,
	            "slot A ver 5\n", fx_b6key.p, fx_b6key.n, ST_INVAL,
	            "handoff_mismatch");
#endif
	bk_upd_discard(&bk);
	bk_sess_drop_all(&bk);
	free(fx_a5.p); free(fx_a6.p); free(fx_a7.p); free(fx_b5.p);
	free(fx_b6.p); free(fx_b7.p); free(fx_b6big.p); free(fx_b6key.p);
	free(fx_b6buf.p); free(fx_b6ldr.p); free(fx_b6self.p); free(fx_b6selfhi.p);
	(void)printf("test_update: %d checks, %d failures\n", nchecks, fails);
	return fails == 0 ? 0 : 1;
}
