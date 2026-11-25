"""Old-gateway compatible API (additive). Does not change the existing /api/v1/orders API.

Endpoints:
  POST /api/v1/payment/create          GET /api/create_order.php
  GET  /api/v1/payment/status/<id>     POST /api/v1/payment/verify    GET /api/verify.php
  POST /api/v1/payment/refund          GET /checkout.php
  GET  /pay/<id>/qr.svg | qr.png       GET /docs.txt
  GET/POST /webhooks  (dashboard page: webhook URL + signing secret)
Webhook: X-Payment-Gateway-Timestamp / X-Payment-Gateway-Signature = sha256=HMAC(secret, ts + "." + body)
"""
import json, hmac, hashlib, secrets, time, re, io, urllib.request
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from flask import Blueprint, request, jsonify, redirect, session, flash, render_template_string, Response, g
from core import conn, money

bp = Blueprint("api_compat", __name__)
_X = {}          # injected by init(): make_order, base_url, login_required
_hits = {}

# ---------------------------------------------------------------- storage
def _c():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS compat_orders(
        order_pk TEXT PRIMARY KEY, user_id INTEGER NOT NULL, ext_order_id TEXT NOT NULL,
        pay_id TEXT NOT NULL, gateway TEXT NOT NULL, customer TEXT, created REAL NOT NULL,
        hook_status TEXT, UNIQUE(user_id, ext_order_id));
    CREATE INDEX IF NOT EXISTS ix_compat_pay ON compat_orders(pay_id);
    CREATE TABLE IF NOT EXISTS api_hooks(user_id INTEGER PRIMARY KEY, url TEXT, secret TEXT NOT NULL);
    """)
    return c

# ---------------------------------------------------------------- helpers
def _err(msg, code, php=False):
    body = {"success": False, "error": msg}
    if php: body.update(status="error", message=msg)
    return jsonify(body), code

def _key():
    k = request.headers.get("X-API-Key")
    if not k:
        a = request.headers.get("Authorization", "")
        if a.lower().startswith("bearer "): k = a[7:].strip()
    if not k: k = request.values.get("api_key")
    if not k: k = (request.get_json(silent=True) or {}).get("api_key") if request.is_json else None
    return (k or "").strip()

def _auth(c, php=False):
    """returns (key_gateway_row, None) or (None, error_response)"""
    k = _key()
    gw = c.execute("SELECT g.*, u.banned FROM gateways g JOIN users u ON u.id=g.user_id WHERE g.api_key=?", (k,)).fetchone() if k else None
    if not gw: return None, _err("invalid API key", 401, php)
    if gw["banned"]: return None, _err("account suspended", 403, php)
    t = time.time(); q = _hits.setdefault(gw["api_key"], deque())
    while q and t - q[0] > 60: q.popleft()
    if len(q) >= 60: return None, _err("rate limit exceeded (60 requests per minute)", 429, php)
    q.append(t)
    if len(_hits) > 5000:
        for kk in [kk for kk, v in list(_hits.items()) if not v or t - v[-1] > 120]: _hits.pop(kk, None)
    return gw, None

def _pick_gateway(c, keygw, want, php=False):
    if want:
        want = str(want).strip().lower()
        if want not in ("paytm", "fampay"): return None, _err('gateway must be "paytm" or "fampay"', 400, php)
        if keygw["type"] == want and keygw["active"]: return keygw, None
        gw = c.execute("SELECT * FROM gateways WHERE user_id=? AND type=? AND active=1 ORDER BY id LIMIT 1", (keygw["user_id"], want)).fetchone()
        if not gw: return None, _err(f"{want} gateway is not configured or is turned off", 400, php)
        return gw, None
    if not keygw["active"]: return None, _err("gateway is turned off", 403, php)
    return keygw, None

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

def _create(c, keygw, amount_raw, ext, want, customer, php=False):
    try: amount = Decimal(str(amount_raw)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError): return None, _err("amount is required and must be a number", 400, php)
    if not (Decimal("1") <= amount <= Decimal("100000")): return None, _err("amount must be between 1 and 100000", 400, php)
    ext = (str(ext).strip() if ext not in (None, "") else "")[:80]
    if ext:
        o, cr = _find(c, keygw["user_id"], ext)
        if o and cr and cr["ext_order_id"] == ext: return _payment(c, o, cr), None      # same order_id -> same payment (safe retry)
    gw, e = _pick_gateway(c, keygw, want, php)
    if e: return None, e
    oid, err = _X["make_order"](gw, amount, ext or None, None, None, None)
    if err: return None, _err(err, 502 if err.startswith("Paytm") else 429, php)
    pid = ("PTM" if gw["type"] == "paytm" else "FMP") + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + secrets.token_hex(3).upper()
    cust = json.dumps(customer)[:2000] if isinstance(customer, (dict, list)) else None
    c.execute("INSERT INTO compat_orders(order_pk,user_id,ext_order_id,pay_id,gateway,customer,created) VALUES(?,?,?,?,?,?,?)",
              (oid, gw["user_id"], ext or pid, pid, gw["type"], cust, time.time()))
    c.commit()
    o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    cr = c.execute("SELECT * FROM compat_orders WHERE order_pk=?", (oid,)).fetchone()
    return _payment(c, o, cr), None

# ---------------------------------------------------------------- API routes
@bp.route("/api/v1/payment/create", methods=["POST"])
def create_json():
    c = _c(); keygw, e = _auth(c)
    if e: return e
    d = request.get_json(silent=True) or request.form
    p, e = _create(c, keygw, d.get("amount", ""), d.get("order_id"), d.get("gateway"), d.get("customer"))
    return e if e else jsonify(p)

@bp.route("/api/create_order.php", methods=["GET", "POST"])
def create_php():
    c = _c(); keygw, e = _auth(c, True)
    if e: return e
    d = request.values
    p, e = _create(c, keygw, d.get("amount", ""), d.get("order_id"), d.get("gateway"), None, True)
    if e: return e
    p = dict(p); p.pop("success", None)
    return jsonify(status="success", data=p)

@bp.route("/api/v1/payment/status/<path:ident>")
def status_get(ident):
    c = _c(); keygw, e = _auth(c)
    if e: return e
    o, cr = _find(c, keygw["user_id"], ident)
    return jsonify(_payment(c, o, cr)) if o else _err("order not found", 404)

@bp.route("/api/v1/payment/verify", methods=["POST"])
def verify_json():
    c = _c(); keygw, e = _auth(c)
    if e: return e
    d = request.get_json(silent=True) or request.form
    o, cr = _find(c, keygw["user_id"], d.get("order_id") or d.get("pay_id"))
    return jsonify(_payment(c, o, cr)) if o else _err("order not found", 404)

@bp.route("/api/verify.php", methods=["GET", "POST"])
def verify_php():
    c = _c(); keygw, e = _auth(c, True)
    if e: return e
    o, cr = _find(c, keygw["user_id"], request.values.get("order_id") or request.values.get("pay_id"))
    if not o: return _err("order not found", 404, True)
    st = _status(o)
    if st == "SUCCESS":
        return jsonify(status="success", data={"order_id": cr["ext_order_id"] if cr else (o["ref"] or o["id"]),
                       "amount": float(money(o["amount"])), "utr": o["utr"] or "", "payment_time": _iso(o["paid_ts"] or time.time())})
    return jsonify(status=st.lower() if st in ("PENDING", "FAILED", "EXPIRED") else "pending", data=None)

@bp.route("/api/v1/payment/refund", methods=["POST"])
def refund():
    c = _c(); keygw, e = _auth(c)
    if e: return e
    return _err("refunds are not supported for UPI QR payments; refund the customer manually from your UPI app", 400)

@bp.route("/checkout.php")
def checkout_php():
    c = _c(); keygw, e = _auth(c)
    if e: return e
    p, e = _create(c, keygw, request.args.get("amount", ""), request.args.get("order_id"), request.args.get("gateway"), None)
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
    c = _c()
    cr = c.execute("SELECT * FROM compat_orders WHERE order_pk=?", (oid,)).fetchone()
    if not cr: c.close(); return
    h = c.execute("SELECT * FROM api_hooks WHERE user_id=? AND url IS NOT NULL AND url<>''", (cr["user_id"],)).fetchone()
    o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not h or not o: c.close(); return
    payload = {"event": "payment.success", "event_id": f"{cr['pay_id']}:payment.success", "order_id": cr["ext_order_id"],
               "pay_id": cr["pay_id"], "transaction_id": o["utr"] or "", "amount": float(money(o["amount"])),
               "currency": "INR", "status": "SUCCESS", "gateway": cr["gateway"]}
    st = _post_hook(h["url"], h["secret"], payload)
    c.execute("UPDATE compat_orders SET hook_status=? WHERE order_pk=?", (st, oid)); c.commit(); c.close()

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
    app.register_blueprint(bp)

DOCS_TXT = open(__file__.replace("api_compat.py", "api_docs.txt"), encoding="utf-8").read()
