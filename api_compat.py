"""Old-gateway compatible API (additive). Does not change the existing /api/v1/orders API.

Endpoints:
  POST /api/v1/payment/create          GET /api/create_order.php
  GET  /api/v1/payment/status/<id>     POST /api/v1/payment/verify    GET /api/verify.php
  POST /api/v1/payment/refund          GET /checkout.php
  GET  /pay/<id>/qr.svg | qr.png       GET /docs.txt
  GET/POST /webhooks  (dashboard page: webhook URL + signing secret)
Webhook: X-Payment-Gateway-Timestamp / X-Payment-Gateway-Signature = sha256=HMAC(secret, ts + "." + body)
"""
import sqlite3, json, hmac, hashlib, secrets, time, re, io, urllib.request
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from flask import Blueprint, request, jsonify, redirect, session, flash, render_template_string, Response, g
from core import conn, money, ist

bp = Blueprint("api_compat", __name__)
_X = {}          # injected by init(): make_order, base_url, login_required
_hits = {}

# ---------------------------------------------------------------- storage
_SCHEMA = """
    CREATE TABLE IF NOT EXISTS compat_orders(
        order_pk TEXT PRIMARY KEY, user_id INTEGER NOT NULL, ext_order_id TEXT NOT NULL,
        pay_id TEXT NOT NULL, gateway TEXT NOT NULL, customer TEXT, created REAL NOT NULL,
        hook_status TEXT, UNIQUE(user_id, ext_order_id));
    CREATE INDEX IF NOT EXISTS ix_compat_pay ON compat_orders(pay_id);
    CREATE TABLE IF NOT EXISTS api_hooks(user_id INTEGER PRIMARY KEY, url TEXT, secret TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS api_keys(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, shop_name TEXT NOT NULL,
        api_key TEXT UNIQUE NOT NULL, created REAL NOT NULL, last_used REAL, calls INTEGER DEFAULT 0, revoked INTEGER DEFAULT 0);
"""

def _ensure(c):
    # also re-creates the tables after an old backup was restored over the database
    n = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name IN ('compat_orders','api_hooks','api_keys')").fetchone()[0]
    if n < 3: c.executescript(_SCHEMA)
    return c

def _c():
    """connection for the current request (closed automatically by the app at the end of the request)"""
    if "db" not in g: g.db = conn()
    return _ensure(g.db)

def _bc():
    """own connection for background threads; the caller closes it"""
    return _ensure(conn())

# ---------------------------------------------------------------- helpers
def _err(msg, code, php=False):
    body = {"success": False, "error": msg}
    if php: body.update(status="error", message=msg)
    return jsonify(body), code

def _body():
    d = request.get_json(silent=True)
    return d if isinstance(d, dict) else {}

def _key():
    k = request.headers.get("X-API-Key")
    if not k:
        a = request.headers.get("Authorization", "")
        if a.lower().startswith("bearer "): k = a[7:].strip()
    if not k: k = request.values.get("api_key")
    if not k: k = _body().get("api_key") if request.is_json else None
    return str(k or "").strip()

def _auth(c, php=False):
    """returns (principal, None) or (None, error_response).
    principal = {user_id, keygw (gateway row or None), shop (shop name or None), kid (api_keys id or None), key}"""
    k = _key(); P = None
    if k:
        r = c.execute("SELECT k.*, u.banned FROM api_keys k JOIN users u ON u.id=k.user_id WHERE k.api_key=?", (k,)).fetchone()
        if r:
            if r["revoked"]: return None, _err("API key has been revoked", 401, php)
            if r["banned"]: return None, _err("account suspended", 403, php)
            P = {"user_id": r["user_id"], "keygw": None, "shop": r["shop_name"], "kid": r["id"], "key": k}
        else:
            gw = c.execute("SELECT g.*, u.banned FROM gateways g JOIN users u ON u.id=g.user_id WHERE g.api_key=?", (k,)).fetchone()
            if gw:
                if gw["banned"]: return None, _err("account suspended", 403, php)
                P = {"user_id": gw["user_id"], "keygw": gw, "shop": None, "kid": None, "key": k}
    if not P: return None, _err("invalid API key", 401, php)
    t = time.time(); q = _hits.setdefault(k, deque())
    while q and t - q[0] > 60: q.popleft()
    if len(q) >= 60: return None, _err("rate limit exceeded (60 requests per minute)", 429, php)
    q.append(t)
    if len(_hits) > 5000:
        for kk in [kk for kk, v in list(_hits.items()) if not v or t - v[-1] > 120]: _hits.pop(kk, None)
    if P["kid"]:
        c.execute("UPDATE api_keys SET last_used=?, calls=calls+1 WHERE id=?", (t, P["kid"])); c.commit()
    return P, None

def _pick_gateway(c, P, want, php=False):
    uid = P["user_id"]; keygw = P["keygw"]
    if want:
        want = str(want).strip().lower()
        if want not in ("paytm", "fampay"): return None, _err('gateway must be "paytm" or "fampay"', 400, php)
        if keygw is not None and keygw["type"] == want and keygw["active"]: return keygw, None
        gw = c.execute("SELECT * FROM gateways WHERE user_id=? AND type=? AND active=1 ORDER BY id LIMIT 1", (uid, want)).fetchone()
        if not gw: return None, _err(f"{want} gateway is not configured or is turned off", 400, php)
        return gw, None
    if keygw is not None:
        if not keygw["active"]: return None, _err("gateway is turned off", 403, php)
        return keygw, None
    gw = c.execute("SELECT * FROM gateways WHERE user_id=? AND active=1 ORDER BY CASE type WHEN 'fampay' THEN 0 ELSE 1 END, id LIMIT 1", (uid,)).fetchone()
    if not gw: return None, _err("no gateway is configured; add one in Gateways first", 400, php)
    return gw, None

def _iso(ts): return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _status(o):
    if o["status"] == "paid": return "SUCCESS"
    if o["status"] == "pending" and o["expires_ts"] < time.time(): return "EXPIRED"
    return {"pending": "PENDING", "expired": "EXPIRED", "failed": "FAILED"}.get(o["status"], o["status"].upper())

def _payment(c, o, cr=None):
    gw = c.execute("SELECT type, upi_id, name FROM gateways WHERE id=?", (o["gateway_id"],)).fetchone()
    base = _X["base_url"]()
    upi = o["qr_data"] or f"upi://pay?pa={quote(gw['upi_id'])}&pn={quote(gw['name'])}&am={money(o['amount'])}&cu=INR&tn={quote('Order ' + o['id'][:8])}"
    pid = cr["pay_id"] if cr else o["id"]
    return {"success": True, "order_id": cr["ext_order_id"] if cr else (o["ref"] or o["id"]), "pay_id": pid,
            "status": _status(o), "amount": float(money(o["amount"])), "currency": "INR", "gateway": gw["type"],
            "transaction_id": o["utr"] or "", "payment_url": f"{base}/pay/{o['id']}",
            "qr_url": f"{base}/pay/{o['id']}/qr.svg", "qr_png_url": f"{base}/pay/{o['id']}/qr.png",
            "upi_uri": upi, "expires_at": _iso(o["expires_ts"])}

def _find(c, uid, ident):
    """order by merchant order_id, pay_id or internal id (only this merchant's)"""
    ident = (ident or "").strip()
    if not ident: return None, None
    cr = c.execute("SELECT * FROM compat_orders WHERE user_id=? AND (ext_order_id=? OR pay_id=?)", (uid, ident, ident)).fetchone()
    if cr:
        o = c.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (cr["order_pk"], uid)).fetchone()
        return (o, cr) if o else (None, None)
    o = c.execute("SELECT * FROM orders WHERE user_id=? AND (id=? OR ref=?) ORDER BY created_ts DESC LIMIT 1", (uid, ident, ident)).fetchone()
    return (o, None) if o else (None, None)

def _create(c, P, amount_raw, ext, want, customer, php=False):
    try:
        amount = Decimal(str(amount_raw)).quantize(Decimal("0.01"))
        if not amount.is_finite(): raise ValueError("not a number")
    except (InvalidOperation, ValueError): return None, _err("amount is required and must be a number", 400, php)
    if not (Decimal("1") <= amount <= Decimal("100000")): return None, _err("amount must be between 1 and 100000", 400, php)
    ext = (str(ext).strip() if ext not in (None, "") else "")[:80]
    if ext:
        o, cr = _find(c, P["user_id"], ext)
        if o and cr and cr["ext_order_id"] == ext: return _payment(c, o, cr), None      # same order_id -> same payment (safe retry)
    gw, e = _pick_gateway(c, P, want, php)
    if e: return None, e
    oid, err = _X["make_order"](gw, amount, ext or None, None, None, None)
    if err: return None, _err(err, 502 if err.startswith("Paytm") else 429, php)
    pid = ("PTM" if gw["type"] == "paytm" else "FMP") + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + secrets.token_hex(3).upper()
    cust = json.dumps(customer)[:2000] if isinstance(customer, (dict, list)) else None
    try:
        c.execute("INSERT INTO compat_orders(order_pk,user_id,ext_order_id,pay_id,gateway,customer,created) VALUES(?,?,?,?,?,?,?)",
                  (oid, gw["user_id"], ext or pid, pid, gw["type"], cust, time.time()))
    except sqlite3.IntegrityError:      # same order_id sent twice at the same moment: keep the first one
        c.execute("UPDATE orders SET status='expired' WHERE id=?", (oid,)); c.commit()
        o, cr = _find(c, P["user_id"], ext)
        if o: return _payment(c, o, cr), None
        return None, _err("could not create the payment, please retry", 429, php)
    if P["shop"]:      # the shop name of the API key is shown as the note on the UPI payment screen
        o0 = c.execute("SELECT qr_data, amount FROM orders WHERE id=?", (oid,)).fetchone()
        if o0["qr_data"]: qr = re.sub(r"&tn=[^&]*$", "&tn=" + quote(P["shop"]), o0["qr_data"])
        else: qr = f"upi://pay?pa={quote(gw['upi_id'])}&pn={quote(gw['name'])}&am={money(o0['amount'])}&cu=INR&tn={quote(P['shop'])}"
        c.execute("UPDATE orders SET qr_data=? WHERE id=?", (qr, oid))
    c.commit()
    o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    cr = c.execute("SELECT * FROM compat_orders WHERE order_pk=?", (oid,)).fetchone()
    return _payment(c, o, cr), None

# ---------------------------------------------------------------- API routes
@bp.route("/api/v1/payment/create", methods=["POST"])
def create_json():
    c = _c(); P, e = _auth(c)
    if e: return e
    d = _body() or request.form
    p, e = _create(c, P, d.get("amount", ""), d.get("order_id"), d.get("gateway"), d.get("customer"))
    return e if e else jsonify(p)

@bp.route("/api/create_order.php", methods=["GET", "POST"])
def create_php():
    c = _c(); P, e = _auth(c, True)
    if e: return e
    d = request.values
    p, e = _create(c, P, d.get("amount", ""), d.get("order_id"), d.get("gateway"), None, True)
    if e: return e
    p = dict(p); p.pop("success", None)
    return jsonify(status="success", data=p)

@bp.route("/api/v1/payment/status/<path:ident>")
def status_get(ident):
    c = _c(); P, e = _auth(c)
    if e: return e
    o, cr = _find(c, P["user_id"], ident)
    return jsonify(_payment(c, o, cr)) if o else _err("order not found", 404)

@bp.route("/api/v1/payment/verify", methods=["POST"])
def verify_json():
    c = _c(); P, e = _auth(c)
    if e: return e
    d = _body() or request.form
    o, cr = _find(c, P["user_id"], d.get("order_id") or d.get("pay_id"))
    return jsonify(_payment(c, o, cr)) if o else _err("order not found", 404)

@bp.route("/api/verify.php", methods=["GET", "POST"])
def verify_php():
    c = _c(); P, e = _auth(c, True)
    if e: return e
    o, cr = _find(c, P["user_id"], request.values.get("order_id") or request.values.get("pay_id"))
    if not o: return _err("order not found", 404, True)
    st = _status(o)
    if st == "SUCCESS":
        return jsonify(status="success", data={"order_id": cr["ext_order_id"] if cr else (o["ref"] or o["id"]),
                       "amount": float(money(o["amount"])), "utr": o["utr"] or "", "payment_time": _iso(o["paid_ts"] or time.time())})
    return jsonify(status=st.lower() if st in ("PENDING", "FAILED", "EXPIRED") else "pending", data=None)

@bp.route("/api/v1/payment/refund", methods=["POST"])
def refund():
    c = _c(); P, e = _auth(c)
    if e: return e
    return _err("refunds are not supported for UPI QR payments; refund the customer manually from your UPI app", 400)

@bp.route("/checkout.php")
def checkout_php():
    c = _c(); P, e = _auth(c)
    if e: return e
    p, e = _create(c, P, request.args.get("amount", ""), request.args.get("order_id"), request.args.get("gateway"), None)
    return e if e else redirect(p["payment_url"])

# ---------------------------------------------------------------- QR images (needs the 'segno' package)
def _upi_for(o, c):
    gw = c.execute("SELECT upi_id, name FROM gateways WHERE id=?", (o["gateway_id"],)).fetchone()
    return o["qr_data"] or f"upi://pay?pa={quote(gw['upi_id'])}&pn={quote(gw['name'])}&am={money(o['amount'])}&cu=INR&tn={quote('Order ' + o['id'][:8])}"

def _qr(oid, kind):
    c = _c(); o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not o: return Response("not found", 404)
    try: import segno
    except ImportError: return Response("QR image support is not installed (pip install segno)", 503)
    q = segno.make(_upi_for(o, c), error="m"); buf = io.BytesIO()
    if kind == "svg":
        q.save(buf, kind="svg", scale=8, border=2, xmldecl=False); mt = "image/svg+xml"
    else:
        q.save(buf, kind="png", scale=8, border=2); mt = "image/png"
    return Response(buf.getvalue(), mimetype=mt, headers={"Cache-Control": "no-store"})

@bp.route("/pay/<oid>/qr.svg")
def qr_svg(oid): return _qr(oid, "svg")

@bp.route("/pay/<oid>/qr.png")
def qr_png(oid): return _qr(oid, "png")

# ---------------------------------------------------------------- webhooks
def _post_hook(url, secret, payload):
    from payments import safe_url, _NoRedirect
    body = json.dumps(payload, separators=(",", ":")).encode()
    for wait in (0, 2, 6, 15):
        time.sleep(wait)
        try:
            if not safe_url(url): return "blocked"
            ts = str(int(time.time()))
            sig = "sha256=" + hmac.new(secret.encode(), (ts + ".").encode() + body, hashlib.sha256).hexdigest()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "PayGateway/1",
                      "X-Payment-Gateway-Timestamp": ts, "X-Payment-Gateway-Signature": sig})
            with urllib.request.build_opener(_NoRedirect).open(req, timeout=10) as r:
                if 200 <= r.status < 300: return "sent"
        except Exception:
            continue
    return "failed"

def on_paid(oid):
    """called from payments.mark_paid (in a background thread)"""
    c = _bc()
    try: _on_paid(c, oid)
    finally: c.close()

def _on_paid(c, oid):
    cr = c.execute("SELECT * FROM compat_orders WHERE order_pk=?", (oid,)).fetchone()
    if not cr: return
    h = c.execute("SELECT * FROM api_hooks WHERE user_id=? AND url IS NOT NULL AND url<>''", (cr["user_id"],)).fetchone()
    o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not h or not o: return
    payload = {"event": "payment.success", "event_id": f"{cr['pay_id']}:payment.success", "order_id": cr["ext_order_id"],
               "pay_id": cr["pay_id"], "transaction_id": o["utr"] or "", "amount": float(money(o["amount"])),
               "currency": "INR", "status": "SUCCESS", "gateway": cr["gateway"]}
    st = _post_hook(h["url"], h["secret"], payload)
    c.execute("UPDATE compat_orders SET hook_status=? WHERE order_pk=?", (st, oid)); c.commit()

_PAGE = """{% extends 'layout_user.html' %}{% set active='docs' %}{% block title %}Webhooks{% endblock %}{% block content %}
<div class="pagehead"><h1>Webhooks</h1></div>
<div class="card"><p class="mut">When a payment is verified we POST a signed JSON event to this URL (use https). See the API docs, section 8.</p>
<form method="post" action="/webhooks"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Webhook URL</label><input name="url" value="{{h.url or ''}}" placeholder="https://yoursite.com/payment-webhook">
<div style="margin-top:10px"><button class="btn" name="do" value="save">Save</button></div></form></div>
<div class="card"><h3>Signing secret</h3><pre>{{h.secret}}</pre>
<form method="post" action="/webhooks" class="row"><input type="hidden" name="csrf" value="{{csrf}}">
<div><button class="btn gray" name="do" value="test">Send test event</button></div>
<div><button class="btn gray" name="do" value="regen" onclick="return confirm('Generate a new secret? Update it in your bot/site.')">Regenerate secret</button></div></form></div>{% endblock %}"""

def _hook_row(c, uid):
    h = c.execute("SELECT * FROM api_hooks WHERE user_id=?", (uid,)).fetchone()
    if not h:
        c.execute("INSERT OR IGNORE INTO api_hooks(user_id,url,secret) VALUES(?,?,?)", (uid, "", "whsec_" + secrets.token_urlsafe(24))); c.commit()
        h = c.execute("SELECT * FROM api_hooks WHERE user_id=?", (uid,)).fetchone()
    return h

def _webhooks():
    c = _c(); uid = g.user["id"]; h = _hook_row(c, uid)
    if request.method == "POST":
        do = request.form.get("do")
        if do == "save":
            u = request.form.get("url", "").strip()
            from payments import safe_url
            if u and not re.match(r"https?://", u): flash("Webhook URL must start with http:// or https://", "err")
            elif u and not safe_url(u): flash("Webhook URL must be a public address.", "err")
            else: c.execute("UPDATE api_hooks SET url=? WHERE user_id=?", (u, uid)); c.commit(); flash("Webhook saved.", "ok")
        elif do == "regen":
            c.execute("UPDATE api_hooks SET secret=? WHERE user_id=?", ("whsec_" + secrets.token_urlsafe(24), uid)); c.commit(); flash("New signing secret generated.", "ok")
        elif do == "test":
            if not h["url"]: flash("Save a webhook URL first.", "err")
            else:
                ts = int(time.time())
                st = _post_hook(h["url"], h["secret"], {"event": "webhook.test", "event_id": f"test:{ts}", "order_id": "TEST", "pay_id": "TEST",
                                "transaction_id": "", "amount": 1.0, "currency": "INR", "status": "SUCCESS", "gateway": "paytm"})
                flash("Test event delivered." if st == "sent" else f"Test event failed ({st}). Your URL must reply with a 2xx status.", "ok" if st == "sent" else "err")
        return redirect("/webhooks")
    return render_template_string(_PAGE, h=h, csrf=session["csrf"])

# ---------------------------------------------------------------- API Keys page
_KEYS = """{% extends 'layout_user.html' %}{% set active='keys' %}{% block title %}API Keys{% endblock %}{% block content %}
<style>
.kc{position:relative;border-radius:22px;padding:22px;margin-bottom:18px;color:#fff;overflow:hidden;background:linear-gradient(135deg,#5b3df0 0,#7c5cff 45%,#3aa0ff 100%);box-shadow:0 18px 50px #5b3df055}
.kc.off{background:linear-gradient(135deg,#3a3f55,#2a2e40);box-shadow:none}
.kc:after{content:"";position:absolute;right:-60px;top:-60px;width:200px;height:200px;border-radius:50%;background:#ffffff14}
.kh{display:flex;align-items:center;justify-content:space-between;gap:10px;position:relative;z-index:1}
.kh .t{font-size:11px;letter-spacing:2px;font-weight:700;opacity:.85}
.pill{border:1.5px solid #fff9;border-radius:999px;padding:4px 14px;font-size:11px;font-weight:800;letter-spacing:1.5px}
.kn{font-size:24px;font-weight:800;margin:14px 0 12px;word-break:break-word;position:relative;z-index:1;text-transform:uppercase}
.kk{background:#00000040;border-radius:14px;padding:13px 14px;font-family:ui-monospace,Menlo,monospace;font-size:13.5px;letter-spacing:1px;overflow-x:auto;white-space:nowrap;position:relative;z-index:1}
.kb{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;position:relative;z-index:1}
.kb button,.kb form button{width:100%;padding:12px;border-radius:13px;border:1px solid #ffffff55;background:#ffffff22;color:#fff;font-weight:700;font-size:14px;font-family:inherit;cursor:pointer}
.kb button:active{transform:scale(.98)}.kb .warn{color:#ffe08a}.kb form{margin:0}
.km{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px;position:relative;z-index:1}
.km small{display:block;font-size:10.5px;letter-spacing:1.6px;opacity:.75;font-weight:700}.km b{font-size:16px}
.kl{margin-top:14px;padding-top:12px;border-top:1px solid #ffffff33;font-size:13px;opacity:.92;position:relative;z-index:1}
.bu{display:flex;gap:10px;align-items:center}.bu input{flex:1}
</style>
<div class="pagehead"><div><h1>API Keys</h1><div class="mut">Manage live integration credentials.</div></div></div>
<div class="card"><h3>Base URL</h3><div class="bu"><input readonly id="bu" value="{{base}}" onclick="this.select()"><button class="btn sm gray" type="button" onclick="cp(document.getElementById('bu').value,this)">Copy</button></div>
<p class="mut" style="margin:10px 0 0">Use this Base URL together with your API key in your bot or website.</p></div>
<div class="card"><h3>Live API cards</h3><p class="mut" style="margin-top:-6px">Production credentials connected to your account</p>
{% for k in keys %}<div class="kc {{ '' if not k.revoked else 'off' }}"><div class="kh"><span class="t">PAYMENT GATEWAY API</span><span class="pill">{{ 'REVOKED' if k.revoked else 'LIVE' }}</span></div>
<div class="kn">{{k.shop_name}}</div>
<div class="kk" id="k{{k.id}}" data-key="{{k.api_key}}" data-shown="0">{{ '•' * 24 }}{{ k.api_key[-4:] }}</div>
<div class="kb"><button type="button" onclick="tg({{k.id}},this)">Show</button><button type="button" onclick="cp(document.getElementById('k{{k.id}}').dataset.key,this)">Copy</button>
{% if not k.revoked %}<form method="post" action="/keys/{{k.id}}/revoke" onsubmit="return confirm('Revoke this key? Bots using it will stop working.')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="warn">Revoke</button></form>{% else %}<span></span>{% endif %}
<form method="post" action="/keys/{{k.id}}/delete" onsubmit="return confirm('Delete this key permanently?')"><input type="hidden" name="csrf" value="{{csrf}}"><button>Delete</button></form></div>
<div class="km"><div><small>ISSUED</small><b>{{ ist(k.created) }}</b></div><div><small>CALLS</small><b>{{k.calls or 0}}</b></div></div>
<div class="kl">Last used: {{ ist(k.last_used) if k.last_used else 'never' }}</div></div>
{% else %}<p class="mut">No API key yet. Enter your shop name below and press Generate.</p>{% endfor %}</div>
<div class="card"><h3>Generate live API key</h3>
<form method="post" action="/keys/new"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Shop name</label><input name="shop" maxlength="40" required placeholder="e.g. RG CHEAT SHOP">
<p class="mut" style="margin:8px 0 0">This name is shown to your customers as the payment note in their UPI app.</p>
<div style="margin-top:14px"><button class="btn">Generate API key</button></div></form></div>
<script>
function tg(id,b){var e=document.getElementById('k'+id),k=e.dataset.key;if(e.dataset.shown=='1'){e.textContent='\u2022'.repeat(24)+k.slice(-4);e.dataset.shown='0';b.textContent='Show'}else{e.textContent=k;e.dataset.shown='1';b.textContent='Hide'}}
function cp(v,b){var t=b.textContent,ok=function(){b.textContent='Copied';setTimeout(function(){b.textContent=t},1500)};
if(navigator.clipboard)navigator.clipboard.writeText(v).then(ok,ok);else{var i=document.createElement('input');i.value=v;document.body.appendChild(i);i.select();document.execCommand('copy');i.remove();ok()}}
</script>{% endblock %}"""

def _keys_page():
    c = _c(); uid = g.user["id"]
    keys = c.execute("SELECT * FROM api_keys WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    return render_template_string(_KEYS, keys=keys, base=_X["base_url"](), csrf=session["csrf"], ist=ist)

def _keys_new():
    c = _c(); uid = g.user["id"]
    shop = re.sub(r"\s+", " ", request.form.get("shop", "")).strip()[:40]
    if not shop: flash("Enter your shop name first.", "err")
    elif c.execute("SELECT COUNT(*) FROM api_keys WHERE user_id=?", (uid,)).fetchone()[0] >= 5: flash("API key limit reached (5). Delete an old key first.", "err")
    else:
        c.execute("INSERT INTO api_keys(user_id,shop_name,api_key,created) VALUES(?,?,?,?)", (uid, shop, "PG_" + secrets.token_hex(20).upper(), time.time())); c.commit()
        flash("API key generated.", "ok")
    return redirect("/keys")

def _keys_act(kid, action):
    c = _c(); uid = g.user["id"]
    if action == "revoke": c.execute("UPDATE api_keys SET revoked=1 WHERE id=? AND user_id=?", (kid, uid)); flash("API key revoked.", "ok")
    elif action == "delete": c.execute("DELETE FROM api_keys WHERE id=? AND user_id=?", (kid, uid)); flash("API key deleted.", "ok")
    c.commit(); return redirect("/keys")

# ---------------------------------------------------------------- docs
def docs_text(base):
    return DOCS_TXT.replace("__BASE__", base)

@bp.route("/docs.txt")
def docs_txt():
    return Response(docs_text(_X["base_url"]()), mimetype="text/plain; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=payment-gateway-api-docs.txt"})

def init(app, make_order, base_url, login_required):
    _X.update(make_order=make_order, base_url=base_url)
    app.add_url_rule("/webhooks", "webhooks", login_required(_webhooks), methods=["GET", "POST"])
    app.add_url_rule("/keys", "keys_page", login_required(_keys_page))
    app.add_url_rule("/keys/new", "keys_new", login_required(_keys_new), methods=["POST"])
    app.add_url_rule("/keys/<int:kid>/<action>", "keys_act", login_required(_keys_act), methods=["POST"])
    app.register_blueprint(bp)

DOCS_TXT = open(__file__.replace("api_compat.py", "api_docs.txt"), encoding="utf-8").read()
