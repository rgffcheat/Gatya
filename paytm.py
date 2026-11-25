import json, base64, hashlib, secrets, string, time, threading, urllib.request
from decimal import Decimal
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from core import conn, dec, get_setting
from payments import mark_paid

IV = b"@@@@&&&&####$$$$"
_locks, _last = {}, {}

def _host():
    return "https://securegw-stage.paytm.in" if get_setting("paytm_env") == "stage" else "https://securegw.paytm.in"

def _enc(text, key):
    p = padding.PKCS7(128).padder(); d = p.update(text.encode()) + p.finalize()
    e = Cipher(algorithms.AES(key.encode()), modes.CBC(IV)).encryptor()
    return base64.b64encode(e.update(d) + e.finalize()).decode()

def _dec(tok, key):
    dd = Cipher(algorithms.AES(key.encode()), modes.CBC(IV)).decryptor()
    raw = dd.update(base64.b64decode(tok)) + dd.finalize()
    u = padding.PKCS7(128).unpadder(); return (u.update(raw) + u.finalize()).decode()

def signature(body_str, key):
    salt = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(4))
    return _enc(hashlib.sha256((body_str + "|" + salt).encode()).hexdigest() + salt, key)

def verify(body_str, sig, key):
    try:
        d = _dec(sig, key); salt = d[-4:]
        return d == hashlib.sha256((body_str + "|" + salt).encode()).hexdigest() + salt
    except Exception:
        return False

def _post(path, body, key, head=None):
    body_str = json.dumps(body, separators=(",", ":"))
    h = dict(head or {}); h["signature"] = signature(body_str, key)
    data = ('{"body":' + body_str + ',"head":' + json.dumps(h, separators=(",", ":")) + '}').encode()
    req = urllib.request.Request(_host() + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def create_qr(mid, key, order_id, amount):
    """Dynamic UPI QR for one order. Returns (True, upi_link) or (False, error)."""
    try:
        res = _post("/paymentservices/qr/create",
                    {"mid": mid, "orderId": order_id, "amount": amount, "businessType": "UPI_QR_CODE", "posId": "S1234_P1235"},
                    key, {"clientId": "C11", "version": "v1"})
        b = res.get("body", {}); info = b.get("resultInfo", {})
        if info.get("resultStatus") == "SUCCESS" and b.get("qrData"): return True, b["qrData"]
        return False, f"{info.get('resultCode', '')} {info.get('resultMsg', 'unknown error')}".strip()
    except Exception as e:
        return False, f"cannot reach Paytm ({str(e)[:80]})"

def order_status(mid, key, order_id):
    res = _post("/v3/order/status", {"mid": mid, "orderId": order_id}, key)
    return res.get("body", {})

def test_creds(mid, key):
    try:
        b = order_status(mid, key, "TESTCHK" + secrets.token_hex(6))
    except Exception as e:
        return False, f"Could not reach Paytm: {str(e)[:100]}"
    info = b.get("resultInfo", {}); code = str(info.get("resultCode", "")); msg = info.get("resultMsg", "")
    low = msg.lower()
    if code == "330" or "checksum" in low or "signature" in low: return False, f"Merchant Key looks wrong ({msg})."
    if "mid" in low and ("invalid" in low or "not" in low): return False, f"Merchant ID looks wrong ({msg})."
    return True, f"Paytm accepted the credentials ({msg or 'ok'})."

def check_gateway(gid, min_gap=6):
    lock = _locks.setdefault(gid, threading.Lock())
    if not lock.acquire(blocking=False): return
    try:
        if time.time() - _last.get(gid, 0) < min_gap: return
        _last[gid] = time.time()
        c = conn()
        g = c.execute("SELECT * FROM gateways WHERE id=? AND active=1 AND type='paytm'", (gid,)).fetchone()
        pend = c.execute("SELECT * FROM orders WHERE gateway_id=? AND status='pending' AND expires_ts>? ORDER BY created_ts DESC LIMIT 20",
                         (gid, time.time())).fetchall()
        if not g or not pend: c.close(); return
        err = None
        try:
            key = dec(g["key_enc"])
            for o in pend:
                b = order_status(g["mid"], key, o["pt_order"])
                if b.get("resultInfo", {}).get("resultStatus") == "TXN_SUCCESS":
                    try: ok = int((Decimal(str(b.get("txnAmount", "0"))) * 100).to_integral_value()) == o["amount"]
                    except Exception: ok = False
                    if ok: mark_paid(o["id"], b.get("bankTxnId") or b.get("txnId"))
        except Exception as e:
            err = f"Paytm check error: {str(e)[:100]}"
        c.execute("UPDATE gateways SET last_check=?, last_error=? WHERE id=?", (time.time(), err, gid)); c.commit(); c.close()
    finally:
        lock.release()
