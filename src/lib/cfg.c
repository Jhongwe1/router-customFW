/* cfg.c -- the config record and the two-slot store.  cfg.h holds the on-disk
 * layout and the argument for the design; this file holds the rules.
 *
 * ---------------------------------------------------------------------------
 * READ ORDER IN cfg_parse_record, AND WHY IT IS THAT ORDER
 * ---------------------------------------------------------------------------
 *
 * Nothing is trusted before the field that proves it:
 *
 *   1. n >= CFG_HDR_LEN                 -- there is a header to read at all
 *   2. header CRC over bytes 0..19      -- every field below is now trustworthy
 *   3. magic, format, header length     -- is this our record
 *   4. seq in 1..0xFFFFFFFE             -- an erased slot (all 0xFF) is refused
 *      here and a zeroed one is refused too
 *   5. payload length <= slot - header, and 24 + length <= n
 *   6. payload CRC                      -- the value bytes are now trustworthy
 *   7. the TLV walk, then the cross-field rules
 *
 * Checking the header CRC FIRST is deliberate and is the opposite of the
 * obvious order.  The alternative -- magic, then length, then CRC -- means the
 * length that decides how many bytes get CRC'd was itself never checked, and
 * that is one bounds check away from the defect this whole file exists to
 * remove.  Here the length is only ever used after the CRC that covers it
 * matched, and it is still range-checked afterwards, because a CRC is not an
 * authenticator: an attacker who can write the store can compute it.  Every
 * bound below therefore holds against chosen bytes, not merely against noise.
 *
 * Bytes between CFG_HDR_LEN + payload_len and n are fill and are not examined.
 * That is what lets a caller hand the whole 4096-byte slot to this function.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "cfg.h"
#include "crc32.h"
#include "schema.h"
#include "tlv.h"

/* Single-process, no threads (SPEC-R7 § 2). */
static uint16_t cfg_errkey;

uint16_t cfg_last_key(void)
{
	return cfg_errkey;
}

static int fail(int rc, uint16_t id)
{
	cfg_errkey = id;
	return rc;
}

/* ------------------------------------------------------------------------- */
/* Schema lookup.  cfg_key_by_id, cfg_key_by_name and cfg_key_at live in       */
/* schema.c, beside the table they walk (`R7-8`; schema.h says why).           */
/* ------------------------------------------------------------------------- */

int cfg_index_by_id(uint16_t id)
{
	int i;

	for (i = 0; i < CFG_NKEYS; i++) {
		if (cfg_keys[i].id == id)
			return i;
	}
	return -CFGE_UNKNOWN;
}

/* ------------------------------------------------------------------------- */
/* In-memory accessors                                                       */
/* ------------------------------------------------------------------------- */

int cfg_defaults(struct cfg *c)
{
	if (c == NULL)
		return -CFGE_SPACE;
	memset(c, 0, sizeof *c);
	c->seq = 0;
	c->source = 0;
	/* Every key is absent; cfg_get falls back to schema_default.  The keys
	 * are not materialised here so that "absent" and "explicitly set to the
	 * default value" stay distinguishable, which is what `show`'s source
	 * column reports and what `cfg_encode_record` encodes. */
	return 0;
}

int cfg_present(const struct cfg *c, uint16_t id)
{
	int i;

	if (c == NULL)
		return -CFGE_SPACE;
	i = cfg_index_by_id(id);
	if (i < 0)
		return i;
	return c->present[i] ? 1 : 0;
}

int cfg_get(const struct cfg *c, uint16_t id, uint8_t *v, uint16_t *len)
{
	int i;
	const uint8_t *dv;
	uint16_t dl;
	int rc;

	if (c == NULL || v == NULL || len == NULL)
		return fail(-CFGE_SPACE, id);
	i = cfg_index_by_id(id);
	if (i < 0)
		return fail(-CFGE_UNKNOWN, id);

	if (c->present[i]) {
		if (c->len[i] > (uint16_t)CFG_VAL_MAX)
			return fail(-CFGE_TYPE, id);	/* a corrupt struct cfg */
		memcpy(v, c->val[i], (size_t)c->len[i]);
		*len = c->len[i];
		return 0;
	}

	rc = schema_default(id, &dv, &dl);
	if (rc != 0)
		return fail(rc, id);		/* -CFGE_NOENT for admin.pwhash */
	memcpy(v, dv, (size_t)dl);
	*len = dl;
	return 0;
}

int cfg_set(struct cfg *c, uint16_t id, const uint8_t *v, uint16_t len)
{
	const struct cfg_key *k;
	int i, rc;

	if (c == NULL)
		return fail(-CFGE_SPACE, id);
	k = cfg_key_by_id(id);
	if (k == NULL)
		return fail(-CFGE_UNKNOWN, id);
	i = cfg_index_by_id(id);
	if (i < 0)
		return fail(-CFGE_UNKNOWN, id);

	rc = schema_check_value(k, v, len);
	if (rc != 0)
		return fail(rc, id);
	if ((size_t)len > (size_t)CFG_VAL_MAX)
		return fail(-CFGE_TYPE, id);	/* schema_check_value already did */

	memset(c->val[i], 0, sizeof c->val[i]);
	if (len != 0)
		memcpy(c->val[i], v, (size_t)len);
	c->len[i] = len;
	c->present[i] = 1;
	return 0;
}

int cfg_unset(struct cfg *c, uint16_t id)
{
	int i;

	if (c == NULL)
		return fail(-CFGE_SPACE, id);
	i = cfg_index_by_id(id);
	if (i < 0)
		return fail(-CFGE_UNKNOWN, id);
	memset(c->val[i], 0, sizeof c->val[i]);
	c->len[i] = 0;
	c->present[i] = 0;
	return 0;
}

/* ------------------------------------------------------------------------- */
/* Cross-field rules (SPEC-R7 § 4)                                           */
/* ------------------------------------------------------------------------- */

static int get_u32(const struct cfg *c, uint16_t id, uint32_t *out)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;
	int rc = cfg_get(c, id, v, &len);

	if (rc != 0)
		return rc;
	if (len != 4)
		return fail(-CFGE_TYPE, id);
	*out = tlv_get_be32(v);
	return 0;
}

static int get_u8(const struct cfg *c, uint16_t id, uint8_t *out)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;
	int rc = cfg_get(c, id, v, &len);

	if (rc != 0)
		return rc;
	if (len != 1)
		return fail(-CFGE_TYPE, id);
	*out = v[0];
	return 0;
}

int cfg_validate(const struct cfg *c)
{
	uint32_t lan, mask, start, end, wip, wmask, wgw, net, bcast;
	uint8_t wmode;
	int rc;

	if (c == NULL)
		return fail(-CFGE_SPACE, 0);

	rc = get_u32(c, CFG_ID_LAN_IP, &lan);
	if (rc != 0)
		return rc;
	rc = get_u32(c, CFG_ID_LAN_MASK, &mask);
	if (rc != 0)
		return rc;
	rc = get_u32(c, CFG_ID_DHCPD_START, &start);
	if (rc != 0)
		return rc;
	rc = get_u32(c, CFG_ID_DHCPD_END, &end);
	if (rc != 0)
		return rc;

	net = lan & mask;
	bcast = net | ~mask;

	/* R1  dhcpd.start <= dhcpd.end.  Blamed on dhcpd.start: it is the value
	 * a caller changes to fix the pair, and § 6's INVAL body carries one id. */
	if (start > end)
		return fail(-CFGE_CROSS, CFG_ID_DHCPD_START);

	/* R2  both pool ends inside the LAN subnet. */
	if ((start & mask) != net)
		return fail(-CFGE_CROSS, CFG_ID_DHCPD_START);
	if ((end & mask) != net)
		return fail(-CFGE_CROSS, CFG_ID_DHCPD_END);

	/* R3  and neither is the network or the broadcast address. */
	if (start == net || start == bcast)
		return fail(-CFGE_CROSS, CFG_ID_DHCPD_START);
	if (end == net || end == bcast)
		return fail(-CFGE_CROSS, CFG_ID_DHCPD_END);

	/* R4  lan.ipaddr is a host address of its own subnet.  "inside the
	 * subnet" is true by construction, so what this rule can actually
	 * refuse is the network and broadcast addresses. */
	if (lan == net || lan == bcast)
		return fail(-CFGE_CROSS, CFG_ID_LAN_IP);

	/* R5  lan.ipaddr outside [dhcpd.start, dhcpd.end]. */
	if (lan >= start && lan <= end)
		return fail(-CFGE_CROSS, CFG_ID_LAN_IP);

	/* R6  wan.mode = 2 (static) requires a usable WAN triple. */
	rc = get_u8(c, CFG_ID_WAN_MODE, &wmode);
	if (rc != 0)
		return rc;
	if (wmode == 2) {
		rc = get_u32(c, CFG_ID_WAN_IP, &wip);
		if (rc != 0)
			return rc;
		rc = get_u32(c, CFG_ID_WAN_MASK, &wmask);
		if (rc != 0)
			return rc;
		rc = get_u32(c, CFG_ID_WAN_GW, &wgw);
		if (rc != 0)
			return rc;
		if (wip == 0)
			return fail(-CFGE_CROSS, CFG_ID_WAN_IP);
		if (wmask == 0)
			return fail(-CFGE_CROSS, CFG_ID_WAN_MASK);
		if ((wgw & wmask) != (wip & wmask))
			return fail(-CFGE_CROSS, CFG_ID_WAN_GW);
	}

	cfg_errkey = 0;
	return 0;
}

/* ------------------------------------------------------------------------- */
/* Record decode                                                             */
/* ------------------------------------------------------------------------- */

int cfg_parse_record(const uint8_t *buf, size_t n, struct cfg *out)
{
	struct cfg tmp;
	struct tlv_reader r;
	uint32_t magic, seq, paylen, paycrc, hdrcrc;
	uint16_t format, hdrlen;
	int rc;

	cfg_errkey = 0;
	if (buf == NULL || out == NULL)
		return -CFGE_SPACE;

	/* 1. a header must be there. */
	if (n < (size_t)CFG_HDR_LEN)
		return -CFGE_SHORT;

	/* 2. the header's own CRC, before any header field is used. */
	hdrcrc = tlv_get_be32(buf + 20);
	if (crc32_ieee(0, buf, 20) != hdrcrc)
		return -CFGE_CRC;

	/* 3. is it ours. */
	magic = tlv_get_be32(buf + 0);
	if (magic != CFG_MAGIC)
		return -CFGE_MAGIC;
	format = tlv_get_be16(buf + 4);
	hdrlen = tlv_get_be16(buf + 6);
	if (format != CFG_FORMAT || hdrlen != CFG_HDR_LEN)
		return -CFGE_FORMAT;

	/* 4. seq.  An erased slot is 0xFF..FF, whose seq field is 0xFFFFFFFF;
	 * a zeroed slot's is 0.  Both are refused here, which is why neither
	 * can ever be selected -- independently of their CRC. */
	seq = tlv_get_be32(buf + 8);
	if (seq < CFG_SEQ_MIN || seq > CFG_SEQ_MAX)
		return -CFGE_SEQ;

	/* 5. payload length, against the slot AND against the bytes we hold. */
	paylen = tlv_get_be32(buf + 12);
	if (paylen > (uint32_t)(CFG_SLOT_SIZE - CFG_HDR_LEN))
		return -CFGE_LEN;
	if ((size_t)paylen > n - (size_t)CFG_HDR_LEN)
		return -CFGE_SHORT;

	/* 6. the payload's CRC, before any payload byte is used. */
	paycrc = tlv_get_be32(buf + 16);
	if (crc32_ieee(0, buf + CFG_HDR_LEN, (size_t)paylen) != paycrc)
		return -CFGE_CRC;

	/* 7. the TLV walk. */
	rc = cfg_defaults(&tmp);
	if (rc != 0)
		return rc;
	tmp.seq = seq;

	tlv_reader_init(&r, buf + CFG_HDR_LEN, (size_t)paylen);
	for (;;) {
		uint16_t type = 0, len = 0;
		const uint8_t *val = NULL;
		const struct cfg_key *k;
		int i;

		rc = tlv_next(&r, &type, &len, &val);
		if (rc == 1)
			break;			/* clean end */
		if (rc == -TLVE_ORDER)
			return -CFGE_ORDER;
		if (rc < 0)
			return -CFGE_TLV;	/* truncation or trailing bytes */

		k = cfg_key_by_id(type);
		if (k == NULL)
			return fail(-CFGE_UNKNOWN, type);
		if ((size_t)len > (size_t)CFG_VAL_MAX)
			return fail(-CFGE_TYPE, type);

		rc = schema_check_value(k, val, len);
		if (rc != 0)
			return fail(rc, type);

		i = cfg_index_by_id(type);
		if (i < 0)
			return fail(-CFGE_UNKNOWN, type);
		/* tlv_next refuses a non-ascending id, so this cannot already
		 * be present; the check is a bound, not a comment. */
		if (tmp.present[i])
			return fail(-CFGE_ORDER, type);
		if (len != 0)
			memcpy(tmp.val[i], val, (size_t)len);
		tmp.len[i] = len;
		tmp.present[i] = 1;
	}

	/* 8. the cross-field rules.  A record that cannot be a configuration is
	 * not a valid record, so the loader falls back rather than booting a
	 * machine into a state no SET could have produced. */
	rc = cfg_validate(&tmp);
	if (rc != 0)
		return rc;

	tmp.source = 0;			/* the caller knows which slot this was */
	*out = tmp;
	cfg_errkey = 0;
	return 0;
}

/* ------------------------------------------------------------------------- */
/* Record encode                                                             */
/* ------------------------------------------------------------------------- */

int cfg_encode_record(const struct cfg *c, uint32_t seq, uint8_t *buf, size_t n)
{
	struct tlv_writer w;
	size_t paylen;
	int i, rc;

	cfg_errkey = 0;
	if (c == NULL || buf == NULL)
		return -CFGE_SPACE;
	if (seq < CFG_SEQ_MIN || seq > CFG_SEQ_MAX)
		return -CFGE_SEQ;
	if (n < (size_t)CFG_HDR_LEN)
		return -CFGE_SPACE;

	/* The payload may not exceed a slot even if `n` is larger. */
	paylen = n - (size_t)CFG_HDR_LEN;
	if (paylen > (size_t)(CFG_SLOT_SIZE - CFG_HDR_LEN))
		paylen = (size_t)(CFG_SLOT_SIZE - CFG_HDR_LEN);

	tlv_writer_init(&w, buf + CFG_HDR_LEN, paylen);

	/* In table order, which schema_self_check proves is ascending id order.
	 * This is the whole of "ids strictly ascending on encode". */
	for (i = 0; i < CFG_NKEYS; i++) {
		const struct cfg_key *k = &cfg_keys[i];

		if (!c->present[i])
			continue;
		if (c->len[i] > (uint16_t)CFG_VAL_MAX)
			return fail(-CFGE_TYPE, k->id);
		rc = schema_check_value(k, c->val[i], c->len[i]);
		if (rc != 0)
			return fail(rc, k->id);
		rc = tlv_write(&w, k->id, c->val[i], c->len[i]);
		if (rc == -TLVE_SPACE)
			return fail(-CFGE_SPACE, k->id);
		if (rc != 0)
			return fail(-CFGE_ORDER, k->id);
	}

	paylen = tlv_writer_len(&w);

	tlv_put_be32(buf + 0, CFG_MAGIC);
	tlv_put_be16(buf + 4, (uint16_t)CFG_FORMAT);
	tlv_put_be16(buf + 6, (uint16_t)CFG_HDR_LEN);
	tlv_put_be32(buf + 8, seq);
	tlv_put_be32(buf + 12, (uint32_t)paylen);
	tlv_put_be32(buf + 16, crc32_ieee(0, buf + CFG_HDR_LEN, paylen));
	tlv_put_be32(buf + 20, crc32_ieee(0, buf, 20));

	return (int)((size_t)CFG_HDR_LEN + paylen);
}

int cfg_slot_image(const struct cfg *c, uint32_t seq, uint8_t *img, size_t n)
{
	int used;

	if (img == NULL || n < (size_t)CFG_SLOT_SIZE)
		return -CFGE_SPACE;
	memset(img, CFG_FILL, (size_t)CFG_SLOT_SIZE);
	used = cfg_encode_record(c, seq, img, (size_t)CFG_SLOT_SIZE);
	if (used < 0)
		return used;
	/* Re-fill past the record: cfg_encode_record wrote only `used` bytes,
	 * but a shorter record than a previous call must not leave that call's
	 * tail behind in a reused buffer. */
	memset(img + used, CFG_FILL, (size_t)CFG_SLOT_SIZE - (size_t)used);
	return used;
}

/* ------------------------------------------------------------------------- */
/* File I/O.  lseek + read/write loops, not pread/pwrite: uClibc 0.9.30 is the
 * target libc and a loop we wrote is one fewer thing to be surprised by.
 * ------------------------------------------------------------------------- */

static int read_at(int fd, off_t off, uint8_t *buf, size_t want, size_t *got)
{
	size_t done = 0;

	*got = 0;
	if (lseek(fd, off, SEEK_SET) == (off_t)-1)
		return -CFGE_IO;
	while (done < want) {
		ssize_t r = read(fd, buf + done, want - done);

		if (r < 0) {
			if (errno == EINTR)
				continue;
			return -CFGE_IO;
		}
		if (r == 0)
			break;			/* EOF */
		done += (size_t)r;
	}
	*got = done;
	return 0;
}

static int write_at(int fd, off_t off, const uint8_t *buf, size_t n)
{
	size_t done = 0;

	if (lseek(fd, off, SEEK_SET) == (off_t)-1)
		return -CFGE_IO;
	while (done < n) {
		ssize_t w = write(fd, buf + done, n - done);

		if (w < 0) {
			if (errno == EINTR)
				continue;
			return -CFGE_IO;
		}
		if (w == 0)
			return -CFGE_IO;
		done += (size_t)w;
	}
	return 0;
}

/* ------------------------------------------------------------------------- */
/* Load                                                                      */
/* ------------------------------------------------------------------------- */

int cfg_load_info(const char *path, struct cfg *out, struct cfg_store_info *info)
{
	struct cfg_store_info local;
	struct cfg tmp;
	uint8_t slot[CFG_SLOT_SIZE];
	uint32_t best = 0;
	int fd, s, rc, ret = 0;

	if (info == NULL)
		info = &local;
	memset(info, 0, sizeof *info);
	info->rc[0] = -CFGE_SHORT;
	info->rc[1] = -CFGE_SHORT;

	if (out == NULL || path == NULL)
		return -CFGE_SPACE;
	rc = cfg_defaults(out);
	if (rc != 0)
		return rc;

	fd = open(path, O_RDONLY);
	if (fd < 0) {
		if (errno == ENOENT)
			return 0;	/* no store yet: defaults, source 0 */
		return -CFGE_IO;
	}

	for (s = 0; s < CFG_NSLOTS; s++) {
		size_t got = 0;

		rc = read_at(fd, (off_t)s * (off_t)CFG_SLOT_SIZE, slot,
			     (size_t)CFG_SLOT_SIZE, &got);
		if (rc != 0) {
			ret = -CFGE_IO;
			info->rc[s] = -CFGE_IO;
			continue;
		}
		info->file_bytes += got;
		if (got == 0) {
			info->rc[s] = -CFGE_SHORT;
			continue;
		}
		info->rc[s] = cfg_parse_record(slot, got, &tmp);
		if (info->rc[s] != 0)
			continue;
		info->seq[s] = tmp.seq;
		/* Strictly greater: a tie cannot happen (seq is unique by
		 * construction) and if it did, preferring slot 0 silently would
		 * hide it.  The first of the two wins and the tie is visible in
		 * info->seq. */
		if (tmp.seq > best) {
			best = tmp.seq;
			*out = tmp;
			out->source = s + 1;
			info->selected = s + 1;
		}
	}

	close(fd);
	if (info->selected == 0 && ret == 0) {
		/* Fail-closed: defaults, source 0.  cfg_defaults already ran. */
		(void)cfg_defaults(out);
	}
	return ret;
}

int cfg_load(const char *path, struct cfg *out)
{
	return cfg_load_info(path, out, NULL);
}

/* ------------------------------------------------------------------------- */
/* Store                                                                     */
/* ------------------------------------------------------------------------- */

int cfg_store(const char *path, struct cfg *c)
{
	uint8_t img[CFG_SLOT_SIZE];
	uint8_t back[CFG_SLOT_SIZE];
	struct cfg probe;
	struct cfg_store_info info;
	struct stat st;
	uint32_t newseq, maxseq = 0;
	int fd, s, target, rc, used;
	size_t got = 0;

	if (path == NULL || c == NULL)
		return -CFGE_SPACE;

	/* Refuse to write a record that could not be loaded back.  SPEC-R7 does
	 * not require this; a store that accepts an invalid record would create
	 * a file whose only effect is to make the next boot fall back. */
	rc = cfg_validate(c);
	if (rc != 0)
		return rc;

	/* Where the current record is, read from the file rather than from
	 * c->source: c may be minutes old. */
	{
		struct cfg unused;

		rc = cfg_load_info(path, &unused, &info);
		if (rc != 0)
			return rc;
	}
	for (s = 0; s < CFG_NSLOTS; s++) {
		if (info.rc[s] == 0 && info.seq[s] > maxseq)
			maxseq = info.seq[s];
	}
	if (maxseq >= CFG_SEQ_MAX)
		return -CFGE_SEQ;		/* the sequence space is spent */
	newseq = maxseq + 1;

	/* The slot NOT holding the current record; both invalid -> slot 0. */
	target = (info.selected == 1) ? 1 : 0;

	used = cfg_slot_image(c, newseq, img, sizeof img);
	if (used < 0)
		return used;

	fd = open(path, O_RDWR | O_CREAT, 0600);
	if (fd < 0)
		return -CFGE_IO;

	/* A file that does not yet hold two slots is extended first.  The bytes
	 * ftruncate adds are zero, and a zeroed slot is invalid (seq 0), so the
	 * extension cannot make a slot selectable.  This is the only case in
	 * which anything outside the target slot is written, and it happens
	 * only when there was no other slot to protect. */
	if (fstat(fd, &st) != 0) {
		close(fd);
		return -CFGE_IO;
	}
	if (st.st_size < (off_t)CFG_FILE_SIZE) {
		if (ftruncate(fd, (off_t)CFG_FILE_SIZE) != 0) {
			close(fd);
			return -CFGE_IO;
		}
	}

	rc = write_at(fd, (off_t)target * (off_t)CFG_SLOT_SIZE, img, sizeof img);
	if (rc != 0) {
		close(fd);
		return rc;
	}
	if (fsync(fd) != 0) {
		close(fd);
		return -CFGE_IO;
	}

	/* Read back and verify.  Both the bytes and the parse: the bytes catch
	 * a device that took the write and stored something else, the parse
	 * catches an encoder that produced something this loader would reject. */
	rc = read_at(fd, (off_t)target * (off_t)CFG_SLOT_SIZE, back, sizeof back,
		     &got);
	if (rc != 0 || got != (size_t)CFG_SLOT_SIZE) {
		close(fd);
		return -CFGE_IO;
	}
	if (memcmp(img, back, sizeof img) != 0) {
		close(fd);
		return -CFGE_IO;
	}
	if (cfg_parse_record(back, sizeof back, &probe) != 0 ||
	    probe.seq != newseq) {
		close(fd);
		return -CFGE_IO;
	}
	if (close(fd) != 0)
		return -CFGE_IO;

	c->seq = newseq;
	c->source = target + 1;
	return 0;
}

/* ------------------------------------------------------------------------- */
/* Text conversion                                                           */
/* ------------------------------------------------------------------------- */

/* Strict unsigned decimal.  No sign, no space, no leading zero unless the
 * whole number is "0", no trailing anything, and overflow refused rather than
 * wrapped.  The vendor habit this avoids is strtoul with an unread endptr. */
static int parse_u32(const char *s, uint32_t *out)
{
	uint32_t v = 0;
	int n = 0;

	if (s == NULL || s[0] == '\0')
		return -CFGE_TEXT;
	if (s[0] == '0' && s[1] != '\0')
		return -CFGE_TEXT;
	while (s[n] != '\0') {
		uint32_t d;

		if (s[n] < '0' || s[n] > '9')
			return -CFGE_TEXT;
		d = (uint32_t)(s[n] - '0');
		if (v > (0xFFFFFFFFu - d) / 10u)
			return -CFGE_TEXT;	/* would overflow */
		v = v * 10u + d;
		n++;
		if (n > 10)
			return -CFGE_TEXT;
	}
	*out = v;
	return 0;
}

/* Strict dotted quad: exactly four fields, 1..3 digits each, no leading zero
 * unless the field is "0", each <= 255, nothing after the fourth.  This
 * refuses everything inet_aton famously accepts -- "10.1", "0x0a.1.1.1",
 * "010.1.1.1" -- because a config value that means one thing to the parser and
 * another to the reader is how a firewall rule ends up on the wrong subnet. */
static int parse_ipv4(const char *s, uint8_t *v)
{
	int part, i = 0;

	for (part = 0; part < 4; part++) {
		int digits = 0;
		uint32_t o = 0;

		if (part > 0) {
			if (s[i] != '.')
				return -CFGE_TEXT;
			i++;
		}
		if (s[i] == '0' && s[i + 1] >= '0' && s[i + 1] <= '9')
			return -CFGE_TEXT;
		while (s[i] >= '0' && s[i] <= '9') {
			o = o * 10u + (uint32_t)(s[i] - '0');
			i++;
			digits++;
			if (digits > 3)
				return -CFGE_TEXT;
		}
		if (digits == 0 || o > 255u)
			return -CFGE_TEXT;
		v[part] = (uint8_t)o;
	}
	if (s[i] != '\0')
		return -CFGE_TEXT;
	return 0;
}

static int hexval(char c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

int cfg_text_to_value(const struct cfg_key *k, const char *text, uint8_t *v,
		      uint16_t *len)
{
	uint32_t n = 0;
	size_t tl;
	int rc;

	cfg_errkey = 0;
	if (k == NULL || text == NULL || v == NULL || len == NULL)
		return -CFGE_TEXT;
	cfg_errkey = k->id;

	switch (k->type) {
	case CT_BOOL:
	case CT_ENUM:
		rc = parse_u32(text, &n);
		if (rc != 0)
			return rc;
		if (n > 255u)
			return -CFGE_RANGE;
		v[0] = (uint8_t)n;
		*len = 1;
		break;

	case CT_U16:
		rc = parse_u32(text, &n);
		if (rc != 0)
			return rc;
		if (n > 0xFFFFu)
			return -CFGE_RANGE;
		tlv_put_be16(v, (uint16_t)n);
		*len = 2;
		break;

	case CT_U32:
		rc = parse_u32(text, &n);
		if (rc != 0)
			return rc;
		tlv_put_be32(v, n);
		*len = 4;
		break;

	case CT_IPV4:
		rc = parse_ipv4(text, v);
		if (rc != 0)
			return rc;
		*len = 4;
		break;

	case CT_STR:
		tl = strlen(text);
		if (tl > (size_t)CFG_VAL_MAX)
			return -CFGE_TYPE;
		if (tl != 0)
			memcpy(v, text, tl);
		*len = (uint16_t)tl;
		break;

	case CT_BYTES:
		tl = strlen(text);
		if ((tl & 1u) != 0 || tl / 2u > (size_t)CFG_VAL_MAX)
			return -CFGE_TEXT;
		{
			size_t i;

			for (i = 0; i < tl; i += 2) {
				int hi = hexval(text[i]);
				int lo = hexval(text[i + 1]);

				if (hi < 0 || lo < 0)
					return -CFGE_TEXT;
				v[i / 2] = (uint8_t)((hi << 4) | lo);
			}
		}
		*len = (uint16_t)(tl / 2u);
		break;

	default:
		return -CFGE_TYPE;
	}

	/* One gate for every type: the field rules decide, never the parser. */
	rc = schema_check_value(k, v, *len);
	if (rc != 0)
		return rc;
	return 0;
}

int cfg_value_to_hex(const uint8_t *v, uint16_t len, char *out, size_t n)
{
	static const char h[] = "0123456789abcdef";
	uint16_t i;

	if (v == NULL || out == NULL)
		return -CFGE_SPACE;
	if (n < (size_t)len * 2u + 1u)
		return -CFGE_SPACE;
	for (i = 0; i < len; i++) {
		out[2 * i] = h[(v[i] >> 4) & 0x0Fu];
		out[2 * i + 1] = h[v[i] & 0x0Fu];
	}
	out[2 * len] = '\0';
	return (int)(2u * (unsigned)len);
}

int cfg_value_to_text(const struct cfg_key *k, const uint8_t *v, uint16_t len,
		      char *out, size_t n)
{
	int w;

	cfg_errkey = 0;
	if (k == NULL || v == NULL || out == NULL || n == 0)
		return -CFGE_SPACE;
	cfg_errkey = k->id;

	/* The one function that turns a value into something printable refuses
	 * a hidden key.  A caller that wants those bytes has to name
	 * cfg_value_to_hex, which no daemon does. */
	if (k->web == WEB_HIDDEN)
		return -CFGE_PERM;

	if (schema_check_value(k, v, len) != 0)
		return -CFGE_TYPE;

	switch (k->type) {
	case CT_BOOL:
	case CT_ENUM:
		w = snprintf(out, n, "%u", (unsigned)v[0]);
		break;
	case CT_U16:
		w = snprintf(out, n, "%lu", (unsigned long)tlv_get_be16(v));
		break;
	case CT_U32:
		w = snprintf(out, n, "%lu", (unsigned long)tlv_get_be32(v));
		break;
	case CT_IPV4:
		w = snprintf(out, n, "%u.%u.%u.%u", (unsigned)v[0],
			     (unsigned)v[1], (unsigned)v[2], (unsigned)v[3]);
		break;
	case CT_STR:
		if (n < (size_t)len + 1u)
			return -CFGE_SPACE;
		if (len != 0)
			memcpy(out, v, (size_t)len);
		out[len] = '\0';
		return (int)len;
	case CT_BYTES:
		return cfg_value_to_hex(v, len, out, n);
	default:
		return -CFGE_TYPE;
	}

	if (w < 0 || (size_t)w >= n)
		return -CFGE_SPACE;
	return w;
}

/* ------------------------------------------------------------------------- */

const char *cfg_strerror(int rc)
{
	static const char *const m[CFGE_LAST] = {
		"ok",
		"too few bytes for the record",
		"not a config record (magic)",
		"unsupported format or header length",
		"CRC mismatch",
		"sequence number invalid or exhausted",
		"payload length impossible",
		"malformed TLV payload",
		"TLV ids not strictly ascending",
		"unknown key id",
		"wrong length for the type",
		"value out of bounds",
		"cross-field rule violated",
		"absent and no default",
		"I/O error",
		"destination too small",
		"refused: hidden value",
		"no such key name",
		"not a value of this type"
	};
	int i = (rc < 0) ? -rc : rc;

	if (i >= CFGE_LAST || i < 0)
		return "unknown error";
	return m[i];
}
