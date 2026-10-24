/* cfg.h -- the config store: SPEC-R7 § 4 (schema) and § 5 (record and store).
 * The declarations between the two PINNED markers are copied from SPEC-R7 § 5
 * and must not change shape; everything else in this header is an addition.
 *
 * ---------------------------------------------------------------------------
 * THE THREE VENDOR DEFECTS THIS REPLACES (plan D8)
 * ---------------------------------------------------------------------------
 *
 *   1. Plaintext credentials (CVE-2019-19823).  There is no plaintext key in
 *      the schema.  `admin.pwhash` is 56 bytes of KDF output and is the only
 *      WEB_HIDDEN key; `cfg_value_to_text` REFUSES a hidden key, so the one
 *      function that turns a value into something printable cannot be the
 *      thing that leaks it.
 *   2. One write clobbering both regions (D-10).  Two slots, and `cfg_store`
 *      writes only the one that does not hold the record currently selected.
 *      A torn write therefore destroys a slot nobody is reading.
 *   3. A TLV length straight into memcpy (CVE-2024-21778's shape).  See tlv.h.
 *
 * And the fourth, which is a behaviour rather than a bug: both regions bad
 * meant "load defaults and open telnet" (D-13, fail-open).  Here both slots
 * bad means defaults with `source == 0`, and `admin.pwhash` has no default, so
 * a caller that authenticates against it cannot authenticate at all.  That is
 * the whole fail-closed claim, and it is a property of the schema (no default)
 * rather than of any code path that could be forgotten.
 *
 * ---------------------------------------------------------------------------
 * ON-DISK RECORD (all big-endian, no struct is ever cast onto these bytes)
 * ---------------------------------------------------------------------------
 *
 *   off size field
 *     0    4 magic 0x524C5843 "RLXC"
 *     4    2 format = 1
 *     6    2 header length = 24
 *     8    4 seq, 1..0xFFFFFFFE  (0 and 0xFFFFFFFF are invalid: erased NOR
 *            reads 0xFF, so the all-ones record must not be a valid one)
 *    12    4 payload length, <= CFG_SLOT_SIZE - CFG_HDR_LEN
 *    16    4 payload CRC-32
 *    20    4 header CRC-32 over bytes 0..19
 *    24  ... payload: TLVs, ids strictly ascending
 *
 * The record's extent is CFG_HDR_LEN + payload length.  Bytes of the slot past
 * that are fill and are not examined -- `cfg_store` writes 0xFF there so that
 * the image is what an erased-then-written NOR sector will hold in R8.
 */
#ifndef RLXFW_CFG_H
#define RLXFW_CFG_H

#include <stddef.h>
#include <stdint.h>

/* ----- PINNED (SPEC-R7 § 5) ---------------------------------------------- */
#define CFG_SLOT_SIZE 4096
#define CFG_VAL_MAX   64
/* ----- end of the pinned defines; CFG_NKEYS follows § 4's row count ------ */

#define CFG_NKEYS     16
#define CFG_HDR_LEN   24
#define CFG_MAGIC     0x524C5843u	/* "RLXC" */
#define CFG_FORMAT    1
#define CFG_NSLOTS    2
#define CFG_FILE_SIZE (CFG_NSLOTS * CFG_SLOT_SIZE)
#define CFG_SEQ_MIN   1u
#define CFG_SEQ_MAX   0xFFFFFFFEu
#define CFG_FILL      0xFFu

/* Longest text form any value can take, plus the NUL.  The widest is a
 * 56-byte BYTES value rendered as hex (112 characters), which only
 * cfg_value_to_hex produces; 32-character hostnames and "255.255.255.255" are
 * far below it.  Every buffer in the CLI is sized from this. */
#define CFG_TEXT_MAX  (2 * CFG_VAL_MAX + 1)

/* ----- PINNED (SPEC-R7 § 5) ---------------------------------------------- */
struct cfg_key {
	uint16_t id;
	const char *name;
	uint8_t type;
	uint8_t web;
	uint32_t min, max;
};

enum { CT_BOOL = 1, CT_U16, CT_U32, CT_IPV4, CT_STR, CT_ENUM, CT_BYTES };
enum { WEB_HIDDEN = 0, WEB_R = 1, WEB_RW = 2 };

struct cfg {
	uint32_t seq;
	int source;		/* 0 defaults, 1 slot 0, 2 slot 1 */
	uint8_t present[CFG_NKEYS];
	uint16_t len[CFG_NKEYS];
	uint8_t val[CFG_NKEYS][CFG_VAL_MAX];
};
/* ----- end PINNED -------------------------------------------------------- */

/* Errors.  Every function returns 0 (or a byte count) or the negation of one
 * of these.  CFGE_OK is never returned negated. */
enum {
	CFGE_OK = 0,
	CFGE_SHORT = 1,		/* fewer bytes than the header or the record needs */
	CFGE_MAGIC,		/* not "RLXC" */
	CFGE_FORMAT,		/* format or header length is not this version's */
	CFGE_CRC,		/* a CRC field does not match the bytes it covers */
	CFGE_SEQ,		/* seq is 0 or 0xFFFFFFFF, or the space is exhausted */
	CFGE_LEN,		/* payload length is impossible for the slot */
	CFGE_TLV,		/* the TLV walk refused: truncation or trailing bytes */
	CFGE_ORDER,		/* ids not strictly ascending */
	CFGE_UNKNOWN,		/* an id the schema does not have */
	CFGE_TYPE,		/* a length that is wrong for the id's type */
	CFGE_RANGE,		/* a value outside the id's bounds */
	CFGE_CROSS,		/* a cross-field rule */
	CFGE_NOENT,		/* absent, and there is no default */
	CFGE_IO,		/* open/read/write/fsync, or a read-back mismatch */
	CFGE_SPACE,		/* the destination buffer is too small */
	CFGE_PERM,		/* refused: a hidden value may not be rendered */
	CFGE_NAME,		/* no such key name */
	CFGE_TEXT,		/* the text is not a value of this type */
	CFGE_LAST
};

/* ----- PINNED (SPEC-R7 § 5) ---------------------------------------------- */
const struct cfg_key *cfg_key_by_id(uint16_t id);
const struct cfg_key *cfg_key_by_name(const char *name);
int  cfg_defaults(struct cfg *c);
int  cfg_parse_record(const uint8_t *buf, size_t n, struct cfg *out);
int  cfg_encode_record(const struct cfg *c, uint32_t seq, uint8_t *buf, size_t n);
int  cfg_load(const char *path, struct cfg *out);
int  cfg_store(const char *path, struct cfg *c);
int  cfg_get(const struct cfg *c, uint16_t id, uint8_t *v, uint16_t *len);
int  cfg_set(struct cfg *c, uint16_t id, const uint8_t *v, uint16_t len);
int  cfg_validate(const struct cfg *c);
int  cfg_text_to_value(const struct cfg_key *k, const char *text, uint8_t *v,
		       uint16_t *len);
int  cfg_value_to_text(const struct cfg_key *k, const uint8_t *v, uint16_t len,
		       char *out, size_t n);
/* ----- end PINNED -------------------------------------------------------- */

/* Additions.  SPEC-R7 § 5 permits functions to be added, not changed. */

/* The key id the last refusal was about, or 0.  Set by cfg_parse_record,
 * cfg_set, cfg_validate and cfg_encode_record.  Single-process, no threads
 * (SPEC-R7 § 2), so a file-static is the whole mechanism. */
uint16_t cfg_last_key(void);

const char *cfg_strerror(int rc);		/* rc may be negative or positive */

int cfg_index_by_id(uint16_t id);		/* 0..CFG_NKEYS-1, or -CFGE_UNKNOWN */
int cfg_present(const struct cfg *c, uint16_t id);	/* 1, 0, or -CFGE_UNKNOWN */
int cfg_unset(struct cfg *c, uint16_t id);	/* the key reverts to its default */

/* Renders BYTES (and anything else) as lower-case hex.  This is the only way
 * to print a WEB_HIDDEN value; cfg_value_to_text refuses one.  Callers that
 * are not tests or `dump` must not use it. */
int cfg_value_to_hex(const uint8_t *v, uint16_t len, char *out, size_t n);

/* What cfg_load found, for a caller that must tell "no store yet" from "a
 * store that is there and broken".  rc[i] is 0 or -CFGE_* for slot i. */
struct cfg_store_info {
	size_t file_bytes;
	int rc[CFG_NSLOTS];
	uint32_t seq[CFG_NSLOTS];
	int selected;		/* 0 none, 1 slot 0, 2 slot 1 */
};

int cfg_load_info(const char *path, struct cfg *out, struct cfg_store_info *info);

/* Builds the CFG_SLOT_SIZE-byte image `cfg_store` would write: the record then
 * 0xFF fill.  Exposed so that the torn-write sweep writes exactly the bytes
 * the store writes, rather than a test's idea of them. */
int cfg_slot_image(const struct cfg *c, uint32_t seq, uint8_t *img, size_t n);

/* ---------------------------------------------------------------------------
 * THE FLASH BACKEND (notes/self-update.md §§ 3.1-3.4; src/lib/cfgflash.c)
 * ---------------------------------------------------------------------------
 *
 * cfg_load_info, cfg_store, cfg_store_fresh and cfg_slot_raw take the flash
 * backend when `path` is the STRING CFG_FLASH_DEV, compared with strcmp and
 * never by pointer: brokerd's -c and cfgstore's --file hand in argv strings,
 * and a pointer test would send `cfgstore --file /dev/mtd2ro` to the file
 * backend, which reads [0, 8192) of the chip -- the loader -- with no guard.
 * Every other path is the file backend: the host suites and the torn-write
 * sweep (notes/config-store.md § 5) run on it.  It reads and writes REGULAR
 * files only, checked on the descriptor before any byte moves, so /dev/mtd0ro,
 * //dev/mtd2ro or any other node spelled as a store is -CFGE_IO, named on
 * fd 2 and by cfg_file_why() ("not a regular file"; "" when none refused).
 *
 * The flash backend has no "absent store": the device node is part of the
 * image, so a slot it cannot read is -CFGE_IO, never "no store yet" -- a store
 * that cannot be read must not be written over as if it were empty.  A slot
 * whose CFG_SLOT_SIZE bytes are all 0xFF reads as absent (got = 0), slot by
 * slot, so two erased regions are "no store yet" exactly as a missing file is.
 *
 * The offsets are the install table's cfg0 and cfg1
 * (kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h, 1.1, two
 * owners of two numbers, § 3.7); a slot is the first CFG_SLOT_SIZE bytes of
 * its 64 KiB region and the rest of the region reads 0xFF.
 */
#define CFG_FLASH_DEV		"/dev/mtd2ro"
#define CFG_FLASH_OFF0		0x3C0000u
#define CFG_FLASH_OFF1		0x3D0000u
#define CFG_FLASH_REGION	0x10000u
#define CFG_FLASH_LOCK_S	30u	/* § 3.2 step 1: LOCK_NB retries, 30 s */
#define CFG_FLASH_NWRITES	32u	/* § 3.3: 16 sector erases + 16 programs */

/* 1 when `path` names the flash backend, else 0. */
int cfg_is_flash(const char *path);

/* Writes `rec`, with seq 1, into slot 0 -- ONLY when neither slot holds a
 * valid record (each one absent or corrupt), and refuses otherwise.  It is
 * the shell-less first-password step's write (§ 3.8): over a corrupt store,
 * without basing anything on the corrupt bytes.  A fresh record must never
 * shadow a valid one (seq 1 below the other slot's) nor replace it (written
 * over it), so a valid record in EITHER slot is -CFGE_SEQ -- "the sequence has
 * no place for seq 1" -- and nothing is written.  An unreadable store is
 * -CFGE_IO: whether it holds a valid record is unknown, so nothing is written
 * either.  On the flash backend the check and the write are under one hold of
 * the flash lock, so no other writer's record can land between them.
 * 0 sets rec->seq = 1 and rec->source = 1.  cfg_validate's refusals as
 * cfg_store's. */
int cfg_store_fresh(const char *path, struct cfg *rec);

/* The raw bytes of slot s as the medium holds them, for `cfgstore dump`:
 * *where is the offset on the medium (CFG_FLASH_OFF0/OFF1, or s *
 * CFG_SLOT_SIZE in the file), *got the bytes read (0 for an erased flash slot
 * or a slot past the end of the file).  0, -CFGE_IO (errno is the failing
 * call's), or -CFGE_SPACE for a bad argument. */
int cfg_slot_raw(const char *path, int s, uint8_t *buf, size_t *got,
		 uint32_t *where);

/* The file backend's last refusal of a path that is not a regular file, or
 * "" (cleared by each file-backend open). */
const char *cfg_file_why(void);

/* src/lib/cfgflash.c.  The slot index is 0 or 1.
 *
 *   cfg_flash_read_slot   CFG_SLOT_SIZE bytes at CFG_FLASH_OFF0/OFF1 through
 *                         spictl_flash_read; all 0xFF -> *got = 0, else
 *                         CFG_SLOT_SIZE.  0 or -CFGE_IO.
 *   cfg_flash_lock        the flash lock, CFG_FLASH_LOCK_S: the fd, or
 *                         -CFGE_IO with the reason logged (flock's ENOSYS on
 *                         a kernel without CONFIG_FILE_LOCKING is named).
 *   cfg_flash_write_slot_locked
 *                         § 3.2 steps 2-8 under a lock the caller holds:
 *                         disarm; img reset; stage 4,096; img_len 4096 and
 *                         img_err none, n_writes noted; arm the region; install
 *                         cfgN sha=<sha256 of img>; inst_reason OK,
 *                         inst_cmp_ok 1, inst_cmp_diff 0, n_writes moved by
 *                         exactly CFG_FLASH_NWRITES; img reset.  Any deviation
 *                         is -CFGE_IO, logged, and is followed by ONE verb only,
 *                         the cleanup `img reset`: never an arm or an install.
 *   cfg_flash_write_slot  the same, taking and releasing the lock itself.
 *   cfg_flash_why         "" after a clean run, else "<step>: <detail>" of the
 *                         last deviation, the text the log line carried. */
int  cfg_flash_read_slot(int s, uint8_t *buf, size_t *got);
int  cfg_flash_lock(void);
void cfg_flash_unlock(int fd);
int  cfg_flash_write_slot_locked(int s, const uint8_t *img);
int  cfg_flash_write_slot(int s, const uint8_t *img);
const char *cfg_flash_why(void);

#endif /* RLXFW_CFG_H */
