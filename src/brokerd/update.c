/* src/brokerd/update.c -- UPDATE_BEGIN, UPDATE_DATA, UPDATE_END, and the
 * install that runs after END's reply.  The design is notes/self-update.md
 * §§ 4.2-4.6; the wire format is src/lib/proto.h's, one definition httpd's
 * upload.c reads too.
 *
 * WHAT IS DECIDED HERE AND WHAT IS rlxboot's.  Every verdict about a container
 * is rlxboot's own code, linked unchanged: rlxu_verify and
 * rlxu_counter_from_bitmap (src/rlxboot/container.c), rlxb_slot_run and
 * rlxb_choose (src/rlxboot/slots.c), over the bytes rlxboot would read and with
 * rlxboot's environment.  This file adds only what rlxboot has no reason to
 * know: which slot is running (/proc/rlxfw-boot), that the counter caught up,
 * that flash agrees with the handoff, and that the slot written would be the
 * slot booted -- each a refusal, none a second judgement of a container.
 *
 * THE ORDER OF UPDATE_END (notes/self-update.md § 4.4), and the reason each
 * refusal is answered with, so a card can predict the NAME:
 *
 *    0  no staging                                   INVAL   sequence
 *       another caller's staging, or one verified    BUSY    busy
 *       a body that is not the u32 total             INVAL   badlen
 *    1  poisoned                                     INVAL   sequence
 *       received != total, or END's total != BEGIN's INVAL   incomplete
 *    2  /proc/rlxfw-boot is not `slot X ver N`       INVAL   handoff
 *    3  the 512-byte bitmap at 0x3F0000, read        IO      io
 *    4  counter < N (the boot's advance not yet run) BUSY    ctr_behind
 *    5  slot A then slot B, each read and verified   IO      io / nomem
 *    6  rlxb_choose(A, B) is not X at version N      INVAL   handoff_mismatch
 *    7  the destination is the other slot
 *    8  rlxu_verify of the staging for it            INVAL   <rlxu_reason_name>
 *       and the staged length is the container's     INVAL   trailing
 *    9  rlxb_choose with it there does not pick it   INVAL   would_not_boot
 *   10  OK: UPD_T_DEST, UPD_T_VERSION; the install waits for the reply
 *
 * `trailing` is this file's addition, after step 8 and refusing only: the
 * kernel's installer refuses a staging longer than 160 + payload_len
 * (HDR_LEN, kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h
 * rlxfw_spi_inst_chk_rlxu), which rlxu_verify, reading `avail` bytes as a
 * lower bound, accepts; without it END would answer OK for an install the
 * kernel then refuses.  `busy`, `badlen`, `io` and `nomem` are names for the
 * refusals § 4.4 does not name.  ctr_behind is BUSY and not INVAL because it
 * is the one refusal that a later retry of the same container passes.
 *
 * NOTHING IS STAGED FOR FLASH BEFORE STEP 10.  Steps 1-9 read /proc/rlxfw-boot
 * and /dev/mtd2ro and write nothing; the first write to /proc/rtl819x-spi or
 * its image node is upd_install()'s, which runs only from bk_upd_after_reply()
 * with delivered = 1, i.e. after loop.c wrote the last byte of END's OK.
 *
 * BEGIN (§ 4.2): handoff (a RAM boot never receives the body), badlen,
 * too_big above one slot, short below a header, busy, then the buffer.  DATA:
 * the owner's staging, offset == received and the piece inside the total,
 * else `sequence` and POISONED -- which no DATA clears; only the owner's next
 * BEGIN does.  One staging at a time; dropped 30 s after its last accepted
 * DATA and when the session that began it ends (bk_upd_sweep).
 *
 * WHAT THIS FILE DOES NOT ESTABLISH.  Nothing here has run on the device: the
 * host suites drive it against src/cfgstore/simkern.c, a simulation of
 * rtl819x-spi built from the same install header but not from the driver's
 * glue, and against a /proc/rlxfw-boot that is a file.  The time END takes on
 * this core (§ 4.7's 4-6 s, INFERRED) and the reboot after an install
 * (bk_upd_reboot_real) are unmeasured; § 4.4's fallback for a measured
 * timeout is not built.
 */
#define _GNU_SOURCE 1     /* sync() */

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/reboot.h>
#include <unistd.h>

#include "brokerd.h"
#include "sha256.h"
#include "spictl.h"

#include "../rlxboot/rlxboot.h"
#include "../rlxboot/container.h"
#include "../rlxboot/slots.h"

/* THE KEY.  The production build compiles in src/rlxboot/prodkey.h, the file
 * rlxboot compiles in -- not a copy of its bytes.  The host build defines
 * BK_UPD_KEY_DEV and trusts the development key, as rlxboot's host tests do;
 * the target rule refuses that define and reads the artefact for which key it
 * holds (src/brokerd/Makefile). */
#ifdef BK_UPD_KEY_DEV
#include "../rlxboot/devkey.h"
#define BK_UPD_PK  rlxboot_devkey
#else
#include "../rlxboot/prodkey.h"
#ifndef RLXBOOT_PRODKEY_HEX
#error "src/rlxboot/prodkey.h holds no production key (src/rlxboot/mkprodkey.py)"
#endif
#define BK_UPD_PK  rlxboot_prodkey
#endif

/* rlxboot's own range.  Its linker symbols give it to rlxboot (main.c
 * _rlxboot_start, _stack_top); no file here can see them, so this is
 * notes/update-chain.md § 2's 0x81800000-0x818FFFFF, a superset: a destination
 * rlxboot would accept is never accepted here unless rlxboot accepts it. */
#define UPD_SELF_BASE 0x81800000UL
#define UPD_SELF_END  0x81900000UL

/* § 4.5 step 4: n_writes moves by one sector erase per erase step across the
 * slot and one page program per 256 staged bytes.  The step is
 * RLXFW_SPI_WR_ERASE_GRAIN (0x1000, rtl819x-spi-wrpolicy.h), 288 across a
 * slot; MEASURED `FW-246`: 4,621 = 288 + 4,333 for 1,109,152 bytes. */
#define UPD_ERASE_STEP 0x1000UL
#define UPD_PAGE       256UL
#define UPD_NW_ERASES  (RLXB_SLOT_SIZE / UPD_ERASE_STEP)
typedef char upd_nw_erases_is_288[(UPD_NW_ERASES == 288UL) ? 1 : -1];

/* The reasons (UPD_T_REASON), each spelled once. */
#define R_HANDOFF          "handoff"
#define R_TOO_BIG          "too_big"
#define R_SHORT            "short"
#define R_BUSY             "busy"
#define R_BADLEN           "badlen"
#define R_SEQUENCE         "sequence"
#define R_INCOMPLETE       "incomplete"
#define R_CTR_BEHIND       "ctr_behind"
#define R_HANDOFF_MISMATCH "handoff_mismatch"
#define R_WOULD_NOT_BOOT   "would_not_boot"
#define R_TRAILING         "trailing"
#define R_NOMEM            "nomem"
#define R_IO               "io"
/* STATUS only: what became of an END that answered OK. */
#define R_UNDELIVERED      "undelivered"
#define R_INSTALL          "install"

typedef char upd_reason_fits[(sizeof(R_HANDOFF_MISMATCH) - 1 <= UPD_REASON_MAX) ? 1 : -1];
/* "ok B 4294967294" is 15 bytes */
typedef char upd_last_fits[(BKS_UPDATE_LAST_MAX >= 15) ? 1 : -1];

/* ------------------------------------------------------------- helpers */

static void upd_note(struct broker *bk, const char *text)
{
	(void)snprintf(bk->upd.last_result, sizeof(bk->upd.last_result), "%s", text);
}

static void upd_ok(struct proto_resp *rs)
{
	memset(rs, 0, sizeof(*rs));
	rs->version = PROTO_VERSION;
	rs->status = ST_OK;
}

/* A refusal: the status, UPD_T_REASON, STATUS's line, and the console mark
 * § 4.6 names.  The mark is not the gate; /proc is. */
static int upd_refuse(struct broker *bk, struct proto_resp *rs, uint8_t st,
                      const char *why)
{
	size_t off = 0, n = strlen(why);

	memset(rs, 0, sizeof(*rs));
	rs->version = PROTO_VERSION;
	rs->status = st;
	if (n > UPD_REASON_MAX)
		n = UPD_REASON_MAX;
	if (proto_tlv_put(rs->body, sizeof(rs->body), &off, UPD_T_REASON,
	                  (const uint8_t *)why, (uint16_t)n) != 0)
		off = 0;
	rs->body_len = (uint32_t)off;
	upd_note(bk, why);
	bk_log("brokerd: UPDATE refused: %s", why);
	return 0;
}

/* END's refusals after the owner check: the staging is this END's, and it is
 * gone whatever END answers but OK. */
static int upd_end_refuse(struct broker *bk, struct proto_resp *rs, uint8_t st,
                          const char *why)
{
	bk_upd_discard(bk);
	return upd_refuse(bk, rs, st, why);
}

static int upd_owner(const struct broker *bk, const struct proto_req *rq,
                     uid_t uid)
{
	return bk->upd.uid == uid &&
	       bk_ct_eq(bk->upd.tok, rq->session, PROTO_TOK_LEN);
}

static void upd_poison(struct broker *bk)
{
	free(bk->upd.buf);
	bk->upd.buf = 0;
	bk->upd.state = BK_UPD_POISONED;
}

static unsigned long upd_base(char s)
{
	return (s == 'A') ? RLXB_SLOT_A_FLASH : RLXB_SLOT_B_FLASH;
}

static unsigned long upd_rambuf(char s)
{
	return (s == 'A') ? RLXB_SLOT_A_BUF : RLXB_SLOT_B_BUF;
}

static char upd_other(char s)
{
	return (s == 'A') ? 'B' : 'A';
}

/* /proc/rlxfw-boot: `slot A ver 5\n` or `slot B ver 6\n` -> 0 and the two
 * values; anything else -- `none\n`, a file that cannot be read, any other
 * text -- is -1, the fail-closed reading.  Strict on purpose: the kernel prints
 * exactly `slot %c ver %u\n` (arch/rlx/kernel/rlxfw-boot.c), the version in
 * 1..0xFFFFFFFE (the handoff's own bound), and a reader that accepted more
 * would be guessing what some other kernel meant. */
static int upd_handoff(const struct broker *bk, char *slot, uint32_t *ver)
{
	char b[64];
	const char *p;
	size_t n = 0;
	uint32_t v = 0;
	int fd, i;

	if (bk->boot_path == 0)
		return -1;
	fd = open(bk->boot_path, O_RDONLY);
	if (fd < 0)
		return -1;
	(void)fcntl(fd, F_SETFD, FD_CLOEXEC);
	while (n < sizeof(b) - 1) {
		ssize_t r = read(fd, b + n, sizeof(b) - 1 - n);

		if (r < 0) {
			if (errno == EINTR)
				continue;
			(void)close(fd);
			return -1;
		}
		if (r == 0)
			break;
		n += (size_t)r;
	}
	(void)close(fd);
	b[n] = '\0';
	if (n < 13 || memcmp(b, "slot ", 5) != 0 || (b[5] != 'A' && b[5] != 'B') ||
	    memcmp(b + 6, " ver ", 5) != 0)
		return -1;
	p = b + 11;
	if (p[0] < '1' || p[0] > '9')
		return -1;
	for (i = 0; p[i] >= '0' && p[i] <= '9'; i++) {
		uint32_t d = (uint32_t)(p[i] - '0');

		if (i >= 10 || v > (0xFFFFFFFFu - d) / 10u)
			return -1;
		v = v * 10u + d;
	}
	if (p[i] != '\n' || p[i + 1] != '\0' || v == 0xFFFFFFFFu)
		return -1;
	*slot = b[5];
	*ver = v;
	return 0;
}

/* rlxboot's environment, field by field as src/rlxboot/main.c fills it in the
 * slots build (BOOT=slots): RAM, its own range (UPD_SELF_*, above), no buffer
 * and no flash comparison -- rlxb_slot_run gives each slot its own -- the
 * stage-2 window, the counter, the key. */
static void upd_env(struct rlxu_env *e, unsigned long ctr)
{
	memset(e, 0, sizeof(*e));
	e->ram_base   = RLXB_RAM_BASE;
	e->ram_end    = RLXB_RAM_END;
	e->self_base  = UPD_SELF_BASE;
	e->self_end   = UPD_SELF_END;
	e->buf_base   = 0;
	e->buf_limit  = 0;
	e->ldr_base   = RLXB_LDR_BASE;
	e->ldr_end    = RLXB_LDR_END;
	e->counter    = ctr;
	e->write_at   = RLXU_FLASH_NONE;
	e->write_form = RLXU_FORM_NONE;
	e->pk         = BK_UPD_PK;
}

/* rlxb_slot_run's console: rlxboot's READ and VERDICT lines, not wanted here. */
static void upd_emit_none(int c)
{
	(void)c;
}

static const struct rlxb_io upd_quiet = { upd_emit_none };

/* Step 5, one slot.  The whole slot is read through spictl_flash_read, header
 * then the rest, into `buf`; rlxb_slot_run then "copies" it from `buf` to `buf`
 * -- a word copy onto itself -- and verifies it.  So the bytes judged, and how
 * many of them, are decided by rlxboot's own rule (the 160-byte header first,
 * the rest only if it begins RLXU and its length fits, slots.c), applied to a
 * snapshot of the slot; this file never decides how much of a slot to read, and
 * so restates nothing.  What that costs: an erased slot is read whole, about a
 * second on this part (INFERRED, `FW-48`'s rate), where rlxboot reads 160 bytes. */
static int upd_slot(struct rlxb_slot *s, char name, unsigned int *buf,
                    const struct rlxu_env *e)
{
	int rc;

	memset(s, 0, sizeof(*s));
	s->name      = name;
	s->flash_off = upd_base(name);
	s->size      = RLXB_SLOT_SIZE;
	s->buf_addr  = upd_rambuf(name);
	rc = spictl_flash_read(&spictl_dev, (uint32_t)s->flash_off, buf,
	                       (size_t)RLXU_BODY_OFF);
	if (rc == 0)
		rc = spictl_flash_read(&spictl_dev,
		                       (uint32_t)(s->flash_off + RLXU_BODY_OFF),
		                       (unsigned char *)buf + RLXU_BODY_OFF,
		                       (size_t)(RLXB_SLOT_SIZE - RLXU_BODY_OFF));
	if (rc != 0)
		return rc;
	s->src = buf;
	s->buf = buf;
	(void)rlxb_slot_run(s, e, 0, &upd_quiet);
	return 0;
}

/* ------------------------------------------------------------ the sweep */

void bk_upd_discard(struct broker *bk)
{
	struct bk_upd *u = &bk->upd;
	char keep[sizeof(u->last_result)];

	memcpy(keep, u->last_result, sizeof(keep));
	free(u->buf);
	memset(u, 0, sizeof(*u));
	memcpy(u->last_result, keep, sizeof(keep));
}

void bk_upd_sweep(struct broker *bk)
{
	struct bk_upd *u = &bk->upd;

	if (u->state != BK_UPD_STAGING && u->state != BK_UPD_POISONED)
		return;
	if (bk_now(bk) - u->last >= BK_UPD_IDLE_S) {
		bk_log("brokerd: UPDATE staging dropped: no DATA for %d s",
		       BK_UPD_IDLE_S);
		bk_upd_discard(bk);
		return;
	}
	/* A uid-100 staging lives exactly as long as the session that began it:
	 * LOGOUT, PWSET, a changed admin.pwhash, the idle TTL and LRU eviction
	 * all end it here, before the next request is served. */
	if (u->uid == BK_UID_HTTPD && bk_sess_find(bk, u->tok) == 0) {
		bk_log("brokerd: UPDATE staging dropped: its session ended");
		bk_upd_discard(bk);
	}
}

size_t bk_upd_last(const struct broker *bk, const char **text)
{
	*text = bk->upd.last_result;
	return strlen(bk->upd.last_result);
}

/* ------------------------------------------------------------- the ops */

int bk_upd_begin(struct broker *bk, const struct proto_req *rq, uid_t uid,
                 struct proto_resp *rs)
{
	struct bk_upd *u = &bk->upd;
	uint32_t total, ver = 0;
	uint8_t *buf;
	size_t off = 0;
	char run = 0;

	bk_upd_sweep(bk);
	if (upd_handoff(bk, &run, &ver) != 0)
		return upd_refuse(bk, rs, ST_INVAL, R_HANDOFF);
	if (rq->body_len != 4)
		return upd_refuse(bk, rs, ST_INVAL, R_BADLEN);
	total = proto_be32(rq->body);
	if (total > (uint32_t)RLXB_SLOT_SIZE)
		return upd_refuse(bk, rs, ST_INVAL, R_TOO_BIG);
	if (total < (uint32_t)RLXU_BODY_OFF)
		return upd_refuse(bk, rs, ST_INVAL, R_SHORT);
	if (u->state == BK_UPD_VERIFIED ||
	    (u->state != BK_UPD_NONE && !upd_owner(bk, rq, uid)))
		return upd_refuse(bk, rs, ST_BUSY, R_BUSY);
	/* The caller's own earlier staging, poisoned or not, ends here. */
	bk_upd_discard(bk);
	buf = malloc((size_t)total);
	if (buf == 0)
		return upd_refuse(bk, rs, ST_IO, R_NOMEM);
	u->state = BK_UPD_STAGING;
	u->uid = uid;
	memcpy(u->tok, rq->session, PROTO_TOK_LEN);
	u->buf = buf;
	u->total = total;
	u->received = 0;
	u->last = bk_now(bk);
	u->dest = upd_other(run);
	u->version = 0;
	upd_ok(rs);
	if (proto_tlv_put_u8(rs->body, sizeof(rs->body), &off, UPD_T_DEST,
	                     (uint8_t)u->dest) != 0) {
		bk_upd_discard(bk);
		return upd_refuse(bk, rs, ST_IO, R_IO);
	}
	rs->body_len = (uint32_t)off;
	bk_log("brokerd: UPDATE_BEGIN total %lu dest %c", (unsigned long)total,
	       u->dest);
	return 0;
}

int bk_upd_data(struct broker *bk, const struct proto_req *rq, uid_t uid,
                struct proto_resp *rs)
{
	struct bk_upd *u = &bk->upd;
	uint32_t at, n;
	size_t off = 0;

	bk_upd_sweep(bk);
	if (u->state == BK_UPD_NONE)
		return upd_refuse(bk, rs, ST_INVAL, R_SEQUENCE);
	if (!upd_owner(bk, rq, uid) || u->state == BK_UPD_VERIFIED)
		return upd_refuse(bk, rs, ST_BUSY, R_BUSY);
	if (u->state == BK_UPD_POISONED)
		return upd_refuse(bk, rs, ST_INVAL, R_SEQUENCE);
	if (rq->body_len < 5) {
		upd_poison(bk);
		return upd_refuse(bk, rs, ST_INVAL, R_BADLEN);
	}
	at = proto_be32(rq->body);
	n = rq->body_len - 4;
	if (at != u->received || n > u->total - u->received) {
		upd_poison(bk);
		return upd_refuse(bk, rs, ST_INVAL, R_SEQUENCE);
	}
	memcpy(u->buf + u->received, rq->body + 4, n);
	u->received += n;
	u->last = bk_now(bk);
	upd_ok(rs);
	if (proto_tlv_put_u32(rs->body, sizeof(rs->body), &off, UPD_T_RECEIVED,
	                      u->received) != 0) {
		upd_poison(bk);
		return upd_refuse(bk, rs, ST_IO, R_IO);
	}
	rs->body_len = (uint32_t)off;
	return 0;
}

int bk_upd_end(struct broker *bk, const struct proto_req *rq, uid_t uid,
               struct proto_resp *rs)
{
	struct bk_upd *u = &bk->upd;
	struct rlxu_env env, de;
	struct rlxb_slot sa, sb, up, *w;
	struct rlxu ur;
	unsigned char bm[RLXU_CTR_BYTES];
	unsigned int *sbuf;
	unsigned long ctr;
	uint32_t total, ver = 0;
	size_t off = 0;
	char run = 0, dest;
	int malformed = 0, rc;

	bk_upd_sweep(bk);
	if (u->state == BK_UPD_NONE)
		return upd_refuse(bk, rs, ST_INVAL, R_SEQUENCE);
	if (!upd_owner(bk, rq, uid) || u->state == BK_UPD_VERIFIED)
		return upd_refuse(bk, rs, ST_BUSY, R_BUSY);
	if (rq->body_len != 4)
		return upd_end_refuse(bk, rs, ST_INVAL, R_BADLEN);

	/* 1: the staging complete, and not poisoned. */
	if (u->state == BK_UPD_POISONED)
		return upd_end_refuse(bk, rs, ST_INVAL, R_SEQUENCE);
	total = proto_be32(rq->body);
	if (u->received != u->total || total != u->total)
		return upd_end_refuse(bk, rs, ST_INVAL, R_INCOMPLETE);

	/* 2: the handoff, read again -- it is what this END acts on. */
	if (upd_handoff(bk, &run, &ver) != 0)
		return upd_end_refuse(bk, rs, ST_INVAL, R_HANDOFF);

	/* 3: the counter, from flash, by rlxboot's function. */
	rc = spictl_flash_read(&spictl_dev, (uint32_t)RLXB_CTR_FLASH, bm, sizeof(bm));
	if (rc != 0) {
		bk_log("brokerd: UPDATE counter read: errno %d", -rc);
		return upd_end_refuse(bk, rs, ST_IO, R_IO);
	}
	ctr = rlxu_counter_from_bitmap(bm, &malformed);
	if (malformed)
		bk_log("brokerd: UPDATE ctr-bitmap malformed: using the total "
		       "zero count, %lu", ctr);

	/* 4: the boot's advance (§ 5) has run. */
	if (ctr < (unsigned long)ver)
		return upd_end_refuse(bk, rs, ST_BUSY, R_CTR_BEHIND);

	/* 5: both slots as rlxboot reads and verifies them, one buffer reused. */
	upd_env(&env, ctr);
	sbuf = (unsigned int *)malloc((size_t)RLXB_SLOT_SIZE);
	if (sbuf == 0)
		return upd_end_refuse(bk, rs, ST_IO, R_NOMEM);
	rc = upd_slot(&sa, 'A', sbuf, &env);
	if (rc == 0)
		rc = upd_slot(&sb, 'B', sbuf, &env);
	free(sbuf);
	if (rc != 0) {
		bk_log("brokerd: UPDATE slot read: errno %d", -rc);
		return upd_end_refuse(bk, rs, ST_IO, R_IO);
	}
	bk_log("brokerd: UPDATE flash: A %s ver %lu, B %s ver %lu, ctr %lu, "
	       "running %c ver %lu", rlxu_reason_name(sa.reason), sa.r.version,
	       rlxu_reason_name(sb.reason), sb.r.version, ctr, run,
	       (unsigned long)ver);

	/* 6: what rlxboot would boot now is what it says it booted. */
	w = rlxb_choose(&sa, &sb);
	if (w == 0 || w->name != run || w->r.version != (unsigned long)ver)
		return upd_end_refuse(bk, rs, ST_INVAL, R_HANDOFF_MISMATCH);

	/* 7 */
	dest = upd_other(run);

	/* 8: the upload, by rlxu_verify, as rlxboot will verify it in `dest`. */
	de = env;
	de.buf_base   = upd_rambuf(dest);
	de.buf_limit  = de.buf_base + RLXB_SLOT_SIZE;
	de.write_at   = upd_base(dest);
	de.write_form = RLXU_FORM_WHOLE;
	if (rlxu_verify(u->buf, (unsigned long)u->total, &de, &ur, 0) != RLXU_OK)
		return upd_end_refuse(bk, rs, ST_INVAL, rlxu_reason_name(ur.reason));
	if ((unsigned long)RLXU_BODY_OFF + ur.payload_len != (unsigned long)u->total)
		return upd_end_refuse(bk, rs, ST_INVAL, R_TRAILING);

	/* 9: and rlxboot, given it, boots it.  A tie boots A. */
	memset(&up, 0, sizeof(up));
	up.name      = dest;
	up.flash_off = de.write_at;
	up.size      = RLXB_SLOT_SIZE;
	up.buf_addr  = de.buf_base;
	up.reason    = RLXU_OK;
	up.r         = ur;
	w = (dest == 'A') ? rlxb_choose(&up, w) : rlxb_choose(w, &up);
	if (w != &up)
		return upd_end_refuse(bk, rs, ST_INVAL, R_WOULD_NOT_BOOT);

	/* 10 */
	u->state = BK_UPD_VERIFIED;
	u->dest = dest;
	u->version = (uint32_t)ur.version;
	upd_ok(rs);
	if (proto_tlv_put_u8(rs->body, sizeof(rs->body), &off, UPD_T_DEST,
	                     (uint8_t)dest) != 0 ||
	    proto_tlv_put_u32(rs->body, sizeof(rs->body), &off, UPD_T_VERSION,
	                      u->version) != 0)
		return upd_end_refuse(bk, rs, ST_IO, R_IO);
	rs->body_len = (uint32_t)off;
	(void)snprintf(u->last_result, sizeof(u->last_result), "ok %c %lu", dest,
	               (unsigned long)u->version);
	bk->pending_update = 1;
	bk_log("brokerd: UPDATE_END verified: slot %c version %lu, %lu bytes",
	       dest, (unsigned long)u->version, (unsigned long)u->total);
	return 0;
}

/* ---------------------------------------------------------- the install */

/* A deviation once the lock is held: the step, ONE cleanup verb (`img reset`,
 * which frees the kernel's copy and stages nothing), the lock released.  No
 * retry, no second arm -- src/lib/cfgflash.c's rule, for the same reasons. */
static int upd_abort(int *lockfd, const char *step, const char *detail)
{
	int rc;

	bk_log("brokerd: UPDATE install failed at %s: %s", step, detail);
	rc = spictl_verb(&spictl_dev, "img reset");
	if (rc != 0)
		bk_log("brokerd: UPDATE cleanup img reset: errno %d", -rc);
	spictl_unlock(*lockfd);
	*lockfd = -1;
	return -1;
}

static int upd_abort_errno(int *lockfd, const char *step, int rc)
{
	char d[32];

	(void)snprintf(d, sizeof(d), "errno %d", (rc < 0) ? -rc : rc);
	return upd_abort(lockfd, step, d);
}

/* § 4.5 steps 1-4, and step 5's `img reset`.  0 with *lockfd held (the caller
 * reboots with it held); -1 with it released. */
static int upd_install(struct broker *bk, int *lockfd)
{
	static const char hx[] = "0123456789abcdef";
	const struct spictl_paths *p = &spictl_dev;
	const struct bk_upd *u = &bk->upd;
	uint8_t md[SHA256_DIGEST_LEN];
	char line[128], v[32], d[64];
	unsigned long base = upd_base(u->dest), want;
	uint32_t ilen = 0, nw0 = 0, nw1 = 0, x = 0;
	long long t0;
	int fd, rc, i, n;

	/* 1: held until reboot(2), so no cfgstore write starts in the last
	 * second and is cut by it. */
	fd = spictl_lock(p, BK_UPD_LOCK_S);
	if (fd < 0) {
		bk_log("brokerd: UPDATE install failed at lock: %s",
		       spictl_lock_why(fd));
		return -1;
	}
	*lockfd = fd;
	t0 = bk_now_ms(bk);

	/* 2 */
	rc = spictl_verb(p, "disarm");
	if (rc != 0)
		return upd_abort_errno(lockfd, "disarm", rc);
	rc = spictl_verb(p, "img reset");
	if (rc != 0)
		return upd_abort_errno(lockfd, "img reset", rc);
	rc = spictl_stage(p, u->buf, (size_t)u->total);
	if (rc != 0)
		return upd_abort_errno(lockfd, "stage", rc);
	rc = spictl_field_u32(p, "img_len", &ilen);
	if (rc != 0)
		return upd_abort_errno(lockfd, "img_len", rc);
	if (ilen != u->total) {
		(void)snprintf(d, sizeof(d), "%lu staged, want %lu",
		               (unsigned long)ilen, (unsigned long)u->total);
		return upd_abort(lockfd, "img_len", d);
	}
	rc = spictl_field(p, "img_err", v, sizeof(v));
	if (rc != 0)
		return upd_abort_errno(lockfd, "img_err", rc);
	if (strcmp(v, "none") != 0)
		return upd_abort(lockfd, "img_err", v);
	rc = spictl_field_u32(p, "n_writes", &nw0);
	if (rc != 0)
		return upd_abort_errno(lockfd, "n_writes", rc);

	/* 3: the slot exactly, its size the budget; then this writer's digest of
	 * this writer's buffer. */
	n = snprintf(line, sizeof(line), "arm 0x%lx 0x%lx 0x%lx", base,
	             base + RLXB_SLOT_SIZE, (unsigned long)RLXB_SLOT_SIZE);
	if (n <= 0 || (size_t)n >= sizeof(line))
		return upd_abort(lockfd, "arm", "line");
	rc = spictl_verb(p, line);
	if (rc != 0)
		return upd_abort_errno(lockfd, "arm", rc);
	if (sha256(u->buf, (size_t)u->total, md) != 0)
		return upd_abort(lockfd, "sha256", "the digest failed");
	n = snprintf(line, sizeof(line), "install slot%c sha=", u->dest);
	if (n <= 0 || (size_t)n + 2u * SHA256_DIGEST_LEN >= sizeof(line))
		return upd_abort(lockfd, "install", "line");
	for (i = 0; i < SHA256_DIGEST_LEN; i++) {
		line[n + 2 * i] = hx[(md[i] >> 4) & 0x0Fu];
		line[n + 2 * i + 1] = hx[md[i] & 0x0Fu];
	}
	line[n + 2 * SHA256_DIGEST_LEN] = '\0';
	rc = spictl_verb(p, line);
	if (rc != 0) {
		if (spictl_field(p, "inst_reason", v, sizeof(v)) != 0)
			(void)snprintf(v, sizeof(v), "?");
		(void)snprintf(d, sizeof(d), "errno %d, inst_reason %s", -rc, v);
		return upd_abort(lockfd, "install", d);
	}

	/* 4: the kernel's verdict, re-read, and the count of flash operations. */
	rc = spictl_field(p, "inst_reason", v, sizeof(v));
	if (rc != 0)
		return upd_abort_errno(lockfd, "inst_reason", rc);
	if (strcmp(v, "OK") != 0)
		return upd_abort(lockfd, "inst_reason", v);
	rc = spictl_field_u32(p, "inst_cmp_ok", &x);
	if (rc != 0)
		return upd_abort_errno(lockfd, "inst_cmp_ok", rc);
	if (x != 1u)
		return upd_abort(lockfd, "inst_cmp_ok", "the read-back compare did not pass");
	rc = spictl_field_u32(p, "inst_cmp_diff", &x);
	if (rc != 0)
		return upd_abort_errno(lockfd, "inst_cmp_diff", rc);
	if (x != 0u) {
		(void)snprintf(d, sizeof(d), "%lu bytes differ", (unsigned long)x);
		return upd_abort(lockfd, "inst_cmp_diff", d);
	}
	rc = spictl_field_u32(p, "n_writes", &nw1);
	if (rc != 0)
		return upd_abort_errno(lockfd, "n_writes", rc);
	want = UPD_NW_ERASES + ((unsigned long)u->total + UPD_PAGE - 1UL) / UPD_PAGE;
	if ((unsigned long)(uint32_t)(nw1 - nw0) != want) {
		(void)snprintf(d, sizeof(d), "moved by %lu, want %lu",
		               (unsigned long)(uint32_t)(nw1 - nw0), want);
		return upd_abort(lockfd, "n_writes", d);
	}
	bk_log("brokerd: UPDATE slot %c written: %s cmp_diff %lu n_writes +%lu "
	       "ms %lld", u->dest, v, (unsigned long)x,
	       (unsigned long)(uint32_t)(nw1 - nw0), bk_now_ms(bk) - t0);

	/* 5's first verb.  The slot is written and read back by now, so a
	 * failure here is logged and the reboot still happens. */
	rc = spictl_verb(p, "img reset");
	if (rc != 0)
		bk_log("brokerd: UPDATE img reset after the install: errno %d", -rc);
	return 0;
}

int bk_upd_reboot_real(void)
{
	sync();
	(void)sleep(1);
	(void)reboot(RB_AUTOBOOT);
	return -errno;
}

int bk_upd_after_reply(struct broker *bk, int delivered)
{
	struct bk_upd *u = &bk->upd;
	int lockfd = -1, rc;

	bk->pending_update = 0;
	if (u->state != BK_UPD_VERIFIED)
		return -1;
	if (!delivered) {
		bk_log("brokerd: UPDATE not installed: END's reply did not reach "
		       "the client");
		upd_note(bk, R_UNDELIVERED);
		bk_upd_discard(bk);
		return -1;
	}
	if (upd_install(bk, &lockfd) != 0) {
		upd_note(bk, R_INSTALL);
		bk_upd_discard(bk);
		return -1;
	}
	bk_upd_discard(bk);
	rc = (bk->upd_reboot != 0) ? bk->upd_reboot() : -ENOSYS;
	/* reboot(2) returned: not privileged.  The slot is written; serve on. */
	bk_log("brokerd: reboot() failed, errno %d", (rc < 0) ? -rc : rc);
	spictl_unlock(lockfd);
	return 0;
}
