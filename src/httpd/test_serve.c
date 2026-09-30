/* src/httpd/test_serve.c -- srv_conn() over a socketpair: the whole read-parse-
 * answer path, without a listening socket, a fork or a root process.
 *
 * WHY THERE IS NO --no-chroot FLAG TO TEST WITH.  A binary that can be told to
 * skip its privilege drop is a binary that will one day be started that way, so
 * main() has no such switch.  The connection handler is a separate function
 * instead, and this file calls it directly.  What that means is that srv_drop()
 * itself is NOT covered by a host test -- it needs to be root to run at all -- and
 * the report says so rather than implying otherwise.
 *
 * The cases here are the ones the parser tests cannot reach: a peer that sends
 * nothing, a peer that closes mid-request, a request that arrives in two writes,
 * and the exact bytes of the response head.
 */

#include "http.h"
#include "rl.h"
#include "routes.h"
#include "serve.h"
#include "testlib.h"

#include "client.h"

#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

/* The broker is not reachable from a test, and it does not need to be: every
 * case below is either static content or a deliberate 503. */
int bk_call(const char *sock_path, const struct bk_req *rq, struct bk_resp *rs)
{
	(void)sock_path;
	(void)rq;
	(void)rs;
	return -111;
}

static int grant(void *ctx, uint32_t *retry_s)
{
	(void)ctx;
	*retry_s = 0;
	return 1;
}

/* Run one exchange.  `parts` is a NULL-terminated list of writes, so a request
 * can be delivered in pieces.  Returns the number of bytes read back. */
static size_t exchange(const char **parts, char *out, size_t cap, int *status)
{
	int sv[2];
	struct route_env env;
	size_t got = 0;
	unsigned i;

	memset(&env, 0, sizeof(env));
	env.sock = "/nonexistent/broker.sock";
	env.client_ip = 0x0a010164u;
	env.kdf_grant = grant;

	if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0)
		return 0;
	for (i = 0; parts != NULL && parts[i] != NULL; i++) {
		size_t l = strlen(parts[i]);

		if (write(sv[1], parts[i], l) != (ssize_t)l)
			break;
	}
	(void)shutdown(sv[1], SHUT_WR);

	*status = srv_conn(sv[0], &env);
	(void)shutdown(sv[0], SHUT_WR);

	for (;;) {
		ssize_t r = read(sv[1], out + got, cap - 1 - got);

		if (r <= 0)
			break;
		got += (size_t)r;
		if (got + 1 >= cap)
			break;
	}
	out[got] = '\0';
	(void)close(sv[0]);
	(void)close(sv[1]);
	return got;
}

int main(void)
{
	char out[8192];
	int st;
	size_t n;

	/* A well-formed GET for a file that is not there: 404, and the head has
	 * every header SPEC-R7 requires.  The point is the wire bytes, not the
	 * struct. */
	{
		const char *p[] = { "GET /static/none.css HTTP/1.1\r\n"
				    "Host: 10.1.1.1\r\n\r\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 404, "404 on the wire", st, 404);
		t_ok(n > 100, "a response was written", NULL);
		t_ok(strncmp(out, "HTTP/1.1 404 Not Found\r\n", 24) == 0,
		     "the status line", out);
		t_ok(strstr(out, "\r\nX-Frame-Options: DENY\r\n") != NULL,
		     "X-Frame-Options", NULL);
		t_ok(strstr(out,
			    "\r\nContent-Security-Policy: default-src 'self'\r\n")
		     != NULL, "Content-Security-Policy", NULL);
		t_ok(strstr(out, "\r\nX-Content-Type-Options: nosniff\r\n") != NULL,
		     "X-Content-Type-Options", NULL);
		t_ok(strstr(out, "\r\nConnection: close\r\n") != NULL,
		     "Connection: close", NULL);
		t_ok(strstr(out, "\r\nContent-Length: ") != NULL, "Content-Length",
		     NULL);
		t_ok(strstr(out, "\r\n\r\n") != NULL, "the blank line", NULL);
		/* the body length on the wire equals the Content-Length */
		{
			const char *b = strstr(out, "\r\n\r\n");
			unsigned long cl = 0;
			const char *c = strstr(out, "Content-Length: ");

			if (c != NULL)
				cl = strtoul(c + 16, NULL, 10);
			t_okf(b != NULL && strlen(b + 4) == cl,
			      "the body is exactly Content-Length bytes",
			      b != NULL ? (long)strlen(b + 4) : -1, (long)cl);
		}
		t_ok(strstr(out, "none.css") == NULL,
		     "the requested name is not echoed anywhere in the answer",
		     NULL);
	}

	/* A peer that sends nothing and closes: no answer is owed, and nothing
	 * hangs.  This is the case a server that blocks on a first read gets
	 * wedged by. */
	{
		const char *p[] = { NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == -1, "a silent peer gets no response", st, -1);
		t_okf(n == 0, "and no bytes are written", (long)n, 0);
	}

	/* A peer that closes mid-request: one answer, and it is a refusal. */
	{
		const char *p[] = { "GET /api/sta", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 400, "a truncated request is 400", st, 400);
		t_ok(strncmp(out, "HTTP/1.1 400 Bad Request\r\n", 26) == 0,
		     "with the right status line", out);
	}

	/* A request delivered in five writes still parses as one request. */
	{
		const char *p[] = { "POST /api/lo", "gin HTTP/1.1\r\nHost: x\r\n",
				    "Content-Type: application/json\r\n",
				    "Content-Length: 23\r\n\r\n",
				    "{\"password\":\"abcdefgh\"}", NULL };

		n = exchange(p, out, sizeof(out), &st);
		/* The broker is unreachable in this test, so a correctly parsed
		 * login must come back 503 -- which is itself the evidence that
		 * the five writes were reassembled into one request. */
		t_okf(st == 503, "a request split across five writes reaches the"
		      " broker call", st, 503);
		t_ok(strstr(out, "\"broker\"") != NULL,
		     "and the answer names the unreachable broker", out);
	}
	{
		/* The same request with Content-Length one byte too high: the
		 * parser must still be waiting when the peer closes, so it is 400
		 * and not 503.  Without this case the one above would pass even if
		 * the length check did nothing. */
		const char *p[] = { "POST /api/login HTTP/1.1\r\nHost: x\r\n"
				    "Content-Type: application/json\r\n"
				    "Content-Length: 24\r\n\r\n"
				    "{\"password\":\"abcdefgh\"}", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 400, "a body one byte shorter than announced is 400",
		      st, 400);
	}

	/* chunked is 501 on the wire, not an ignored header. */
	{
		const char *p[] = { "POST /api/login HTTP/1.1\r\nHost: x\r\n"
				    "Transfer-Encoding: chunked\r\n\r\n"
				    "4\r\nabcd\r\n0\r\n\r\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 501, "chunked is 501", st, 501);
		t_ok(strncmp(out, "HTTP/1.1 501 Not Implemented\r\n", 30) == 0,
		     "with the right status line", out);
	}

	/* An over-long request line is refused with 414 and the answer is small:
	 * a refusal must not be proportional to the input. */
	{
		static char big[4096];
		const char *p[2];
		size_t i = 0;

		memcpy(big, "GET /", 5);
		i = 5;
		while (i < 2000)
			big[i++] = 'a';
		memcpy(big + i, " HTTP/1.1\r\n\r\n", 13);
		i += 13;
		big[i] = '\0';
		p[0] = big;
		p[1] = NULL;
		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 414, "a 2000-byte target is 414", st, 414);
		t_ok(n < 400, "and the answer is under 400 bytes", NULL);
		t_ok(strstr(out, "aaaa") == NULL,
		     "with none of the target in it", NULL);
	}

	/* A method the program does not implement is 405 on the wire, with the
	 * Allow header, and a bare-LF request line is 400 -- both decided in the
	 * parser but only visible as bytes here. */
	{
		const char *p[] = { "DELETE / HTTP/1.1\r\nHost: x\r\n\r\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 405, "DELETE is 405 on the wire", st, 405);
		t_ok(strstr(out, "\r\nAllow: GET, POST\r\n") != NULL,
		     "with an Allow header", NULL);
	}
	{
		const char *p[] = { "GET / HTTP/1.1\nHost: x\n\n", NULL };

		n = exchange(p, out, sizeof(out), &st);
		t_okf(st == 400, "a bare-LF request is 400 on the wire", st, 400);
	}

	/* ---------------------------------------- the parent's ONE KDF grant
	 * 量 on the device on 2026-09-30, image r78a: POST /api/login answered
	 * `429 {"ok":false,"error":"ratelimit","retry_s":2}` in 0.030 s and went
	 * on answering it -- after 20 s of idle, and after a further 90 s of no
	 * requests at all -- while GET /api/status kept answering 200 from the
	 * same httpd.  The administrator could not log in again for the life of
	 * the process.
	 *
	 * These cases are that sequence, run against srv_loop()'s own arbitration
	 * with the clock supplied, so there is no sleep, no fork and no socket.
	 * The bucket in rl.c is NOT what did it, and test_rl.c's sweep is the
	 * evidence: a 90 s gap refills a login bucket to its burst from every
	 * state it can be in, and the smallest retry_s an empty login bucket can
	 * name is 5.  A constant 2 has one source, SRV_KDF_BUSY_S, and reaching it
	 * needs a holder -- so the holder was one that no longer existed.
	 */
	{
		uint32_t retry = 999u;
		const uint32_t ipa = 0x0a010164u;      /* 10.1.1.100 */
		const uint32_t ipb = 0x0a010165u;
		int got;

		srv_kdf_reset();
		got = srv_kdf_ask(0, ipa, 640000u, &retry);
		t_okf(got == 1, "control: a first login is granted the KDF", got,
		      1);
		retry = 999u;
		got = srv_kdf_ask(1, ipb, 640050u, &retry);
		t_okf(got == 0,
		      "control: a second asker is refused while one is in flight",
		      got, 0);
		t_okf(retry == SRV_KDF_BUSY_S,
		      "and the refusal is the busy constant", (long)retry,
		      (long)SRV_KDF_BUSY_S);

		/* The holder exited and was reaped before the parent read its
		 * release byte or its EOF.  srv_kdf_gone() is the line reap()
		 * runs, so this is that event and not a model of it. */
		srv_kdf_gone(0);
		retry = 999u;
		got = srv_kdf_ask(1, ipb, 640060u, &retry);
		t_okf(got == 1, "a grant whose holder was reaped is not still"
		      " held", got, 1);
		srv_kdf_gone(1);
		retry = 999u;
		got = srv_kdf_ask(2, ipa, 660060u, &retry);
		t_okf(got == 1, "and after 20 s of no requests a login is"
		      " granted", got, 1);
		srv_kdf_gone(2);
		retry = 999u;
		got = srv_kdf_ask(3, ipa, 750060u, &retry);
		t_okf(got == 1, "and after a further 90 s of no requests at all",
		      got, 1);
		srv_kdf_gone(3);
	}

	/* The property brokerd's own bucket suite asserts and this one did not:
	 * once the wait the limiter ANNOUNCED has passed, a correct password gets
	 * through.  The wait is read back from the refusal, not assumed. */
	{
		uint32_t retry = 999u, waited;
		const uint32_t ipc = 0x0a0101c8u;
		unsigned k;
		int ngrant = 0;

		srv_kdf_reset();
		for (k = 0; k < 8u; k++) {
			if (srv_kdf_ask(0, ipc, 100000u, &retry))
				ngrant++;
			srv_kdf_gone(0);
		}
		t_okf(ngrant == RL_KDF_IP_BURST, "the burst, and only the burst",
		      ngrant, RL_KDF_IP_BURST);
		waited = retry;
		t_okf(waited >= 1u, "a refusal names a time to come back",
		      (long)waited, 11);
		retry = 999u;
		ngrant = srv_kdf_ask(0, ipc, 100000u + waited * 1000u, &retry);
		t_okf(ngrant == 1, "and at that time the login IS granted", ngrant,
		      1);
		srv_kdf_gone(0);
	}

	/* A refused attempt must not push the next grant further out.  Two runs
	 * from the same drained state: one that waits quietly, one that is refused
	 * at every 100 ms tick of the wait.  Both must be granted at the same
	 * clock reading, or a client that retries can never get in. */
	{
		const uint32_t ipd = 0x0a0101c9u;
		const uint32_t t0 = 200000u;
		uint32_t retry = 0u;
		unsigned k, quiet = 0u, noisy = 0u;

		for (k = 1u; k <= 300u && quiet == 0u; k++) {
			unsigned j;

			srv_kdf_reset();
			for (j = 0; j < 4u; j++) {
				(void)srv_kdf_ask(0, ipd, t0, &retry);
				srv_kdf_gone(0);
			}
			if (srv_kdf_ask(0, ipd, t0 + k * 100u, &retry))
				quiet = k;
			srv_kdf_gone(0);
		}
		srv_kdf_reset();
		for (k = 0; k < 4u; k++) {
			(void)srv_kdf_ask(0, ipd, t0, &retry);
			srv_kdf_gone(0);
		}
		for (k = 1u; k <= 300u; k++) {
			if (srv_kdf_ask(0, ipd, t0 + k * 100u, &retry)) {
				noisy = k;
				break;
			}
			srv_kdf_gone(0);
		}
		/* The tick a quiet client gets in at, re-derived from the rate
		 * rather than copied: the slower bucket needs one whole token at
		 * RL_KDF_IP_RATE milli per second, in 100 ms ticks. */
		t_okf(quiet == (1000u / RL_KDF_IP_RATE) * 10u,
		      "a client that waits quietly is granted at the tick its"
		      " rate says", (long)quiet,
		      (long)((1000u / RL_KDF_IP_RATE) * 10u));
		t_okf(noisy == quiet,
		      "and a client refused at every tick of that wait is granted"
		      " at the same tick", (long)noisy, (long)quiet);
	}

	/* And a refusal must not charge a bucket that did not cause it.  Three
	 * other addresses drain the GLOBAL bucket; then one address is refused by
	 * it three times at a single instant, so no refill can hide the
	 * arithmetic.  Four seconds later the global holds exactly one token, and
	 * that address may have it only if its own bucket kept its burst. */
	{
		const uint32_t ipx = 0x0a0101d0u;
		const uint32_t t0 = 300000u;
		uint32_t retry = 0u;
		unsigned k;
		int got;

		srv_kdf_reset();
		for (k = 0; k < (unsigned)RL_KDF_BURST; k++) {
			(void)srv_kdf_ask(0, 0x0a0102f0u + k, t0, &retry);
			srv_kdf_gone(0);
		}
		for (k = 0; k < 3u; k++) {
			retry = 999u;
			got = srv_kdf_ask(0, ipx, t0, &retry);
			t_okf(got == 0, "the global bucket refuses an address that"
			      " never asked", got, 0);
			srv_kdf_gone(0);
		}
		t_okf(retry == (1000u + RL_KDF_RATE_MILLI - 1u) /
		      RL_KDF_RATE_MILLI + 1u,
		      "and by that bucket's own wait, not the busy constant",
		      (long)retry,
		      (long)((1000u + RL_KDF_RATE_MILLI - 1u) /
			     RL_KDF_RATE_MILLI + 1u));
		retry = 999u;
		got = srv_kdf_ask(0, ipx, t0 + 4000u, &retry);
		t_okf(got == 1, "a refusal the global caused did not charge the"
		      " address' own bucket", got, 1);
		srv_kdf_gone(0);
	}

	/* The guard shown permitting and refusing, and the refusal that is
	 * CORRECT: a holder that is still there keeps the grant for as long as it
	 * takes, because the bound on a running evaluation is the child's own
	 * alarm() and not a timer in the parent. */
	{
		uint32_t retry = 999u;
		const uint32_t ipe = 0x0a0101d8u;
		int got;

		srv_kdf_reset();
		got = srv_kdf_ask(0, ipe, 400000u, &retry);
		t_okf(got == 1, "control: the arbitration permits", got, 1);
		retry = 999u;
		got = srv_kdf_ask(1, ipe, 1000000u, &retry);
		t_okf(got == 0, "control: and refuses ten minutes later while a"
		      " live holder still holds it", got, 0);
		t_okf(retry == SRV_KDF_BUSY_S, "with the busy constant",
		      (long)retry, (long)SRV_KDF_BUSY_S);
		srv_kdf_gone(0);
	}

	return t_done(45);
}
