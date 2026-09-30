/* tlv.c -- the bounded TLV reader and writer.  tlv.h holds the argument for
 * the shape; this file holds the arithmetic, and the arithmetic is the point.
 */

#include <string.h>

#include "tlv.h"

uint16_t tlv_get_be16(const uint8_t *p)
{
	return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

uint32_t tlv_get_be32(const uint8_t *p)
{
	return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
	       ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

void tlv_put_be16(uint8_t *p, uint16_t v)
{
	p[0] = (uint8_t)(v >> 8);
	p[1] = (uint8_t)(v & 0xFFu);
}

void tlv_put_be32(uint8_t *p, uint32_t v)
{
	p[0] = (uint8_t)(v >> 24);
	p[1] = (uint8_t)((v >> 16) & 0xFFu);
	p[2] = (uint8_t)((v >> 8) & 0xFFu);
	p[3] = (uint8_t)(v & 0xFFu);
}

void tlv_reader_init(struct tlv_reader *r, const uint8_t *buf, size_t len)
{
	r->buf = buf;
	r->len = (buf == NULL) ? 0 : len;
	r->pos = 0;
	r->last = 0;
	r->started = 0;
}

int tlv_next(struct tlv_reader *r, uint16_t *type, uint16_t *len,
	     const uint8_t **val)
{
	size_t avail;
	uint16_t t, l;

	if (r == NULL || type == NULL || len == NULL || val == NULL)
		return -TLVE_ARG;

	/* pos <= len is the invariant every advance below preserves, so this
	 * subtraction cannot wrap.  It is written as a subtraction rather than
	 * as `pos + 4 <= len` on purpose: `pos + 4` can overflow a size_t for
	 * a hostile `len`, and `len - pos` cannot. */
	if (r->pos > r->len)
		return -TLVE_TRUNC;	/* unreachable; kept as a bound, not a comment */
	avail = r->len - r->pos;

	if (avail == 0)
		return 1;		/* clean end */
	if (avail < TLV_HDR_LEN)
		return -TLVE_TRUNC;	/* a partial header is trailing garbage */

	t = tlv_get_be16(r->buf + r->pos);
	l = tlv_get_be16(r->buf + r->pos + 2);

	/* THE CHECK.  `avail - TLV_HDR_LEN` is the number of value bytes that
	 * exist; `l` is the number the buffer claims.  Everything downstream is
	 * allowed to trust `l` only because of this line. */
	if ((size_t)l > avail - TLV_HDR_LEN)
		return -TLVE_TRUNC;

	if (r->started && t <= r->last)
		return -TLVE_ORDER;

	*type = t;
	*len = l;
	*val = r->buf + r->pos + TLV_HDR_LEN;

	r->pos += (size_t)TLV_HDR_LEN + (size_t)l;
	r->last = t;
	r->started = 1;
	return 0;
}

void tlv_writer_init(struct tlv_writer *w, uint8_t *buf, size_t cap)
{
	w->buf = buf;
	w->cap = (buf == NULL) ? 0 : cap;
	w->pos = 0;
	w->last = 0;
	w->started = 0;
}

int tlv_write(struct tlv_writer *w, uint16_t type, const uint8_t *val,
	      uint16_t len)
{
	size_t room;

	if (w == NULL)
		return -TLVE_ARG;
	if (len != 0 && val == NULL)
		return -TLVE_ARG;
	if (w->started && type <= w->last)
		return -TLVE_ORDER;
	if (w->pos > w->cap)
		return -TLVE_SPACE;

	room = w->cap - w->pos;
	if (room < TLV_HDR_LEN || (size_t)len > room - TLV_HDR_LEN)
		return -TLVE_SPACE;

	tlv_put_be16(w->buf + w->pos, type);
	tlv_put_be16(w->buf + w->pos + 2, len);
	if (len != 0)
		memcpy(w->buf + w->pos + TLV_HDR_LEN, val, (size_t)len);

	w->pos += (size_t)TLV_HDR_LEN + (size_t)len;
	w->last = type;
	w->started = 1;
	return 0;
}

size_t tlv_writer_len(const struct tlv_writer *w)
{
	return w->pos;
}
