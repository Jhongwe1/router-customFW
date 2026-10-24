/* src/httpd/upload.h -- POST /api/firmware, the one route whose body is streamed.
 *
 * notes/self-update.md § 4.1.  Every other route's body is capped at
 * HTTP_BODY_MAX and held whole in struct http_req; a `.rlxu` container is about
 * 1.1 MB, so this route's body never is.  The parser stops at the blank line
 * (http_feed() returns HTTP_FEED_STREAM), srv_conn() hands the socket and the
 * bytes it already read past the headers to upload_run(), and upload_run()
 * forwards the body to brokerd as UPDATE_DATA pieces of UPD_DATA_MAX bytes, the
 * last one short, holding one piece at a time.
 *
 * THE ORDER, each step a point where the upload is refused and answered:
 *   1. the route's gate: route_dispatch()'s own lookup and its RF_SESS, RF_CSRF
 *      and empty-body checks (routes.c route_stream_gate()), so no session or a
 *      CSRF mismatch is answered before any broker call;
 *   2. UPDATE_BEGIN, body u32 total: brokerd checks the session and the CSRF
 *      token itself, and a refusal is answered before one body byte is sent;
 *   3. only after BEGIN's OK, the child's alarm becomes HTTP_UPLOAD_ALARM_S;
 *   4. the pieces, offsets exact and contiguous, each confirmed by brokerd's
 *      UPD_T_RECEIVED; the first refusal is the answer -- no further DATA, no END;
 *   5. UPDATE_END, body u32 total, with bk_set_timeouts(UPLOAD_END_CONNECT_S,
 *      UPLOAD_END_IO_S) -- sent only while the alarm still holds
 *      UPLOAD_END_NEED_S, so the child's bound never cuts END's verdict off
 *      after brokerd has acted on it;
 *   6. END's verdict as JSON, {"ok":true,"slot":"A","version":7}, or a refusal
 *      {"ok":false,"error":"update","reason":"<UPD_T_REASON>"} with the HTTP
 *      status every route gives that broker status (route_map_status()).
 *
 * WHAT IT DOES NOT ESTABLISH.  Nothing here has spoken to a brokerd that speaks
 * the update ops: the host suites drive a stand-in written to src/lib/proto.h's
 * wire format (test_upd.h), and brokerd's side is its own program's.  Nothing has
 * run on the device.
 */
#ifndef RLXFW_HTTPD_UPLOAD_H
#define RLXFW_HTTPD_UPLOAD_H

#include <stddef.h>
#include <stdint.h>

#include "http.h"
#include "routes.h"

#define UPLOAD_END_CONNECT_S  5    /* bk_set_timeouts() for UPDATE_END only */
#define UPLOAD_END_IO_S      60
/* What must be left of the alarm when END is sent: its connect, its I/O
 * deadline, and five seconds to write the answer.  Less, and the upload is
 * answered 408 without END; brokerd drops the staging on its own timer. */
#define UPLOAD_END_NEED_S (UPLOAD_END_CONNECT_S + UPLOAD_END_IO_S + 5)

/* Run the whole route on `fd`, the peer's socket, with p[0..npre) the body bytes
 * srv_conn() read past the blank line (bytes past rq->clen are not the body and
 * are ignored).  fd < 0 means no socket: the body is p[0..npre) or it is short.
 * Fills *rs with the answer and returns its status, or -1 when nothing is to be
 * sent because the peer is gone.  Opens no file. */
int upload_run(int fd, const struct http_req *rq, const uint8_t *pre,
	       size_t npre, const struct route_env *env, struct http_rsp *rs);

#endif /* RLXFW_HTTPD_UPLOAD_H */
