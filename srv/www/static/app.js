/* srv/www/static/app.js -- the page's own code.  No framework, no build step,
 * no dependency: this file is what the browser runs.
 *
 * It exists as a separate file rather than an inline <script> because the
 * Content-Security-Policy httpd sends on every response is
 * `default-src 'self'`, which forbids inline script.  The alternative would be
 * to weaken the policy for the convenience of one file, which is the wrong way
 * round.
 *
 * The CSRF token arrives twice: once in the `rlxc` cookie (which is not
 * HttpOnly, on purpose, so this file can read it) and once in the login
 * response body.  Every state-changing request sends it back in the
 * `X-RLX-CSRF` header, so httpd can compare header against cookie in constant
 * time at the edge and brokerd can compare the header against the session's
 * real token.  The session cookie `rlxs` is HttpOnly and this file never sees
 * it.
 *
 * WHAT THIS PAGE CANNOT DO.  It cannot read the stored password hash, the
 * config file or anything else: every call below is one of eleven routes, and
 * each of those is one typed op on the broker socket.  It also cannot protect
 * the password in transit -- there is no TLS in this release.
 */
"use strict";

var CSRF = "";

/* ------------------------------------------------------------------ helpers */

function el(id) { return document.getElementById(id); }

function say(text, cls) {
	var m = el("msg");
	m.textContent = text || "";
	m.className = cls || "";
}

function cookie(name) {
	var parts = document.cookie ? document.cookie.split(";") : [];
	for (var i = 0; i < parts.length; i++) {
		var kv = parts[i].split("=");
		if (kv[0].trim() === name) { return (kv[1] || "").trim(); }
	}
	return "";
}

/* One place that talks to the server.  Every non-GET carries the CSRF header;
 * a 401 anywhere drops the page back to the sign-in card, because the session
 * lives in brokerd and only brokerd can tell us it expired. */
function api(method, path, body) {
	var opt = { method: method, headers: {}, cache: "no-store" };
	if (method !== "GET") {
		opt.headers["X-RLX-CSRF"] = CSRF || cookie("rlxc");
		opt.headers["Content-Type"] = "application/json";
		opt.body = JSON.stringify(body || {});
	}
	return fetch(path, opt).then(function (r) {
		return r.text().then(function (t) {
			var j = null;
			try { j = t ? JSON.parse(t) : null; } catch (e) { j = null; }
			if (r.status === 401) { showLogin("The session has expired."); }
			return { status: r.status, retry: r.headers.get("Retry-After"),
				 body: j };
		});
	});
}

/* The server's error tokens are a fixed, closed set (routes.c).  Mapping them to
 * sentences here means no server response has to carry prose, and no request
 * byte can be reflected into one. */
var REASONS = {
	auth: "That password is not right.",
	nosession: "Please sign in.",
	csrf: "The request was missing its token. Reload the page.",
	locked: "Too many attempts. Wait and try again.",
	ratelimit: "Too many attempts. Wait and try again.",
	noentropy: "The random pool is not ready, so a password cannot be set " +
		   "safely yet. This unit reads entropy_avail = 0; the firmware " +
		   "refuses rather than using a weak salt.",
	broker: "The privileged helper is not answering.",
	busy: "Busy. Try again in a moment.",
	notsup: "Not implemented in this release.",
	badkey: "One of the fields is not a setting this firmware has.",
	readonly: "One of the fields cannot be changed from the web.",
	badtype: "One of the fields has the wrong kind of value.",
	range: "One of the fields is out of range.",
	pwlen: "The new password must be 8 to 64 characters.",
	target: "That is not a plain IPv4 address.",
	field: "A required field is missing.",
	inval: "The privileged helper refused a value.",
	io: "The configuration store could not be written.",
	empty: "Nothing to save."
};

function explain(r) {
	if (r.body && r.body.error && REASONS[r.body.error]) {
		var s = REASONS[r.body.error];
		if (r.retry) { s += " (" + r.retry + " s)"; }
		if (r.body.error === "inval" && r.body.key !== undefined) {
			s += " Key 0x" + Number(r.body.key).toString(16) + ".";
		}
		return s;
	}
	return "The request failed (HTTP " + r.status + ").";
}

/* ------------------------------------------------------------------- panels */

function showLogin(note) {
	el("app").hidden = true;
	el("login-card").hidden = false;
	el("login-note").textContent = note || "";
	el("login-note").className = note ? "note bad" : "note";
	CSRF = "";
}

function showApp() {
	el("login-card").hidden = true;
	el("app").hidden = false;
	refreshStatus();
	loadConfig();
}

function tab(name) {
	var tabs = document.querySelectorAll(".tab");
	var i;
	for (i = 0; i < tabs.length; i++) {
		tabs[i].className = (tabs[i].getAttribute("data-tab") === name)
			? "tab on" : "tab";
	}
	el("tab-status").hidden = (name !== "status");
	el("tab-config").hidden = (name !== "config");
	el("tab-tools").hidden = (name !== "tools");
}

/* ------------------------------------------------------------------- status */

var STATUS_ROWS = [
	["uptime_s", "Uptime", function (v) {
		var s = Number(v), h = Math.floor(s / 3600);
		return h + " h " + Math.floor((s % 3600) / 60) + " min " +
		       (s % 60) + " s";
	}],
	["version", "Build", null],
	["memfree_kb", "Memory free", function (v) { return v + " kB"; }],
	["load1x100", "Load (1 min)", function (v) {
		return (Number(v) / 100).toFixed(2);
	}],
	["cfg_source", "Config slot", function (v) {
		return Number(v) === 0 ? "0 (defaults: no valid record)"
				       : "slot " + (Number(v) - 1);
	}],
	["cfg_seq", "Config sequence", null],
	["entropy_avail", "Entropy available", function (v) {
		return v + (Number(v) < 128 ? " (below 128: not usable)" : "");
	}],
	["auth_ready", "Password can be set", function (v) {
		return v ? "yes" : "no";
	}]
];

function refreshStatus() {
	api("GET", "/api/status").then(function (r) {
		var tb = el("status-table").getElementsByTagName("tbody")[0];
		var i, row, tr, th, td, v;
		if (r.status !== 200 || !r.body) { return; }
		if (r.body.version) { el("ver").textContent = r.body.version; }
		while (tb.firstChild) { tb.removeChild(tb.firstChild); }
		for (i = 0; i < STATUS_ROWS.length; i++) {
			row = STATUS_ROWS[i];
			v = r.body[row[0]];
			if (v === undefined) { continue; }
			tr = document.createElement("tr");
			th = document.createElement("th");
			td = document.createElement("td");
			th.textContent = row[1];
			td.textContent = row[2] ? row[2](v) : String(v);
			tr.appendChild(th);
			tr.appendChild(td);
			tb.appendChild(tr);
		}
		if (r.body.auth_ready === false) {
			el("entropy-note").textContent = REASONS.noentropy;
			el("entropy-note").className = "note bad";
		} else {
			el("entropy-note").textContent = "";
			el("entropy-note").className = "note";
		}
	});
}

/* ------------------------------------------------------------------- config */

/* The field list is built from whatever /api/config returns, so this page holds
 * no second copy of the schema: httpd renders only the keys the schema marks
 * web-readable, and a key it does not send does not appear. */
var CONFIG_ORDER = [
	"sys.hostname", "lan.ipaddr", "lan.netmask",
	"dhcpd.enable", "dhcpd.start", "dhcpd.end", "dhcpd.lease",
	"dns.upstream",
	"wan.mode", "wan.ipaddr", "wan.netmask", "wan.gateway",
	"fw.nat", "fw.lan_icmp",
	"http.port"
];
var READONLY = { "http.port": true };
var CURRENT = {};

function loadConfig() {
	api("GET", "/api/config").then(function (r) {
		var box = el("config-fields");
		var i, k, v, wrap, lab, inp;
		if (r.status !== 200 || !r.body || !r.body.config) { return; }
		CURRENT = r.body.config;
		while (box.firstChild) { box.removeChild(box.firstChild); }
		for (i = 0; i < CONFIG_ORDER.length; i++) {
			k = CONFIG_ORDER[i];
			if (!(k in CURRENT)) { continue; }
			v = CURRENT[k];
			wrap = document.createElement("div");
			lab = document.createElement("label");
			lab.setAttribute("for", "f-" + k);
			lab.textContent = k;
			inp = document.createElement("input");
			inp.id = "f-" + k;
			inp.setAttribute("data-key", k);
			if (typeof v === "boolean") {
				inp.type = "checkbox";
				inp.checked = v;
			} else if (typeof v === "number") {
				inp.type = "number";
				inp.value = String(v);
			} else {
				inp.type = "text";
				inp.maxLength = 64;
				inp.value = String(v);
			}
			if (READONLY[k]) { inp.disabled = true; }
			wrap.appendChild(lab);
			wrap.appendChild(inp);
			box.appendChild(wrap);
		}
	});
}

/* Only changed fields are sent: a SET that names every key would rewrite the
 * whole record every time, and the store's sequence number is monotonic. */
function saveConfig(ev) {
	ev.preventDefault();
	var inputs = el("config-fields").getElementsByTagName("input");
	var body = {};
	var n = 0, i, k, val;
	for (i = 0; i < inputs.length; i++) {
		if (inputs[i].disabled) { continue; }
		k = inputs[i].getAttribute("data-key");
		if (inputs[i].type === "checkbox") {
			val = inputs[i].checked;
		} else if (inputs[i].type === "number") {
			val = Number(inputs[i].value);
			if (!isFinite(val) || val < 0 || val !== Math.floor(val)) {
				say("“" + k + "” must be a whole number.", "bad");
				return;
			}
		} else {
			val = inputs[i].value;
		}
		if (val !== CURRENT[k]) { body[k] = val; n++; }
	}
	if (n === 0) { say("Nothing changed.", ""); return; }
	say("Saving " + n + " field" + (n === 1 ? "" : "s") + "…", "");
	api("POST", "/api/config", body).then(function (r) {
		if (r.status === 200) {
			say("Saved.", "good");
			loadConfig();
			refreshStatus();
		} else {
			say(explain(r), "bad");
		}
	});
}

/* --------------------------------------------------------------------- wire */

window.addEventListener("DOMContentLoaded", function () {
	var tabs = document.querySelectorAll(".tab");
	var i;
	for (i = 0; i < tabs.length; i++) {
		tabs[i].addEventListener("click", function (e) {
			tab(e.target.getAttribute("data-tab"));
		});
	}

	el("login-form").addEventListener("submit", function (ev) {
		ev.preventDefault();
		var pw = el("pw").value;
		el("login-btn").disabled = true;
		say("Signing in… this takes a moment: the password is checked " +
		    "with a deliberately slow hash.", "");
		api("POST", "/api/login", { password: pw }).then(function (r) {
			el("login-btn").disabled = false;
			el("pw").value = "";
			if (r.status === 200 && r.body && r.body.csrf) {
				CSRF = r.body.csrf;
				say("", "");
				showApp();
			} else {
				el("login-note").textContent = explain(r);
				el("login-note").className = "note bad";
			}
		});
	});

	el("logout").addEventListener("click", function () {
		api("POST", "/api/logout", {}).then(function () {
			showLogin("Signed out.");
		});
	});

	el("config-form").addEventListener("submit", saveConfig);

	el("pw-form").addEventListener("submit", function (ev) {
		ev.preventDefault();
		var o = el("pw-old").value, nw = el("pw-new").value;
		if (nw.length < 8) {
			say("The new password must be at least 8 characters.", "bad");
			return;
		}
		say("Changing the password…", "");
		api("POST", "/api/password", { old: o, "new": nw })
			.then(function (r) {
				el("pw-old").value = "";
				el("pw-new").value = "";
				say(r.status === 200 ? "Password changed."
						     : explain(r),
				    r.status === 200 ? "good" : "bad");
				refreshStatus();
			});
	});

	el("ping-form").addEventListener("submit", function (ev) {
		ev.preventDefault();
		var t = el("ping-target").value;
		var c = Number(el("ping-count").value);
		el("ping-out").textContent = "…";
		api("POST", "/api/ping", { target: t, count: c })
			.then(function (r) {
				el("ping-out").textContent =
					(r.status === 200 && r.body)
					? (r.body.output || "(no output)")
					: explain(r);
			});
	});

	el("reboot").addEventListener("click", function () {
		if (!window.confirm("Reboot the unit now?")) { return; }
		say("Rebooting. This page will stop responding.", "");
		api("POST", "/api/reboot", {}).then(function () {});
	});

	el("fw").addEventListener("click", function () {
		api("POST", "/api/firmware", {}).then(function (r) {
			say(explain(r), "bad");
		});
	});

	/* A reload with a live session should not show the sign-in card: ask the
	 * server, which is the only thing that knows. */
	api("GET", "/api/config").then(function (r) {
		if (r.status === 200) {
			CSRF = cookie("rlxc");
			showApp();
		} else {
			showLogin("");
			refreshStatus();
		}
	});
	window.setInterval(function () {
		if (!el("app").hidden) { refreshStatus(); }
	}, 10000);
});
