# src/

rlxfw's own userspace and its loader: six programs that run on the router, the
code they share, and `rlxboot`, which runs before Linux.

`make test` at the top of the tree builds every program and its tests with the
host's gcc-13 and clang-18 and runs them, plain and under ASan and UBSan; it is
what CI's `build-host` job runs. [`Makefile`](Makefile) here iterates the six
programs, each with an output directory of its own (`make -C src <goal>
O=<absolute dir>`): `host`, `test`, `target` -- the big-endian MIPS build, which
needs the pinned vendor toolchain -- `install` and `sizes`. Each program's own
Makefile owns its flags, its tests and its gates.

## The six programs, in the order the image starts them

| directory | what it is | notes |
|---|---|---|
| [`init/`](init/) | PID 1 | [init](../notes/init.md) |
| [`cfgstore/`](cfgstore/) | the config store and its CLI | [config-store](../notes/config-store.md) |
| [`brokerd/`](brokerd/) | the privileged broker | [broker](../notes/broker.md) |
| [`httpd/`](httpd/) | the web server, and the password KDF | [httpd](../notes/httpd.md) |
| [`dnsfwd/`](dnsfwd/) | the DNS forwarder | [dnsfwd](../notes/dnsfwd.md) |
| [`ifupd/`](ifupd/) | the compiled replacement for `udhcpc -s`'s shell script | [init](../notes/init.md) |

How they fit together on the device: [`notes/userspace-integration.md`](../notes/userspace-integration.md).

## The rest

- [`lib/`](lib/) -- code compiled into each program, not a library of its own:
  the config record and its schema, TLV and CRC-32, the broker protocol and its
  client, JSON, SHA-256 and SHA-512, Ed25519, the password KDF, network helpers.
- [`rlxboot/`](rlxboot/) -- the second-stage loader: it runs after the stock
  loader, verifies a signed container and boots it. Its host suite is
  `make -C src/rlxboot hosttest STAGE=<absolute dir>`; [notes/rlxboot.md](../notes/rlxboot.md).
- [`fuzz/`](fuzz/) -- five afl++ harnesses (`cfg`, `dns`, `http`, `json`,
  `proto`) and the seed corpus each one starts from. The `fuzz` targets of
  `brokerd`, `dnsfwd` and `httpd` build four of them; `fuzz_cfg` has no build
  recipe in the tree ([notes/config-store.md](../notes/config-store.md) § 7
  says how it was built).
