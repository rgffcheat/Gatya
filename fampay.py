import imaplib, email, re, html, time, threading
from email.utils import parsedate_to_datetime
from email.header import decode_header, make_header
from core import conn, dec, get_setting
from payments import mark_paid

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
AMT = re.compile(r"(?:₹|Rs\.?|INR)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I)
UTR = re.compile(r"\b(\d{12})\b")
_locks, _last = {}, {}

def test_login(gmail, app_pw):
    try:
        m = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=20)
        m.login(gmail, app_pw.replace(" ", "")); m.logout()
        return True, "Connected to Gmail."
    except imaplib.IMAP4.error:
        return False, "Gmail login failed. Check Gmail, the 16-digit app password, and that IMAP is enabled."
    except Exception as e:
        return False, f"Could not reach Gmail: {e}"

def _text(msg):
    out = []
    for p in msg.walk():
        ct = p.get_content_type()
        if ct not in ("text/plain", "text/html"): continue
        try: s = p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "replace")
        except Exception: continue
        if ct == "text/html": s = html.unescape(re.sub(r"<[^>]+>", " ", s))
        out.append(s)
    return " ".join(out)

def _paise(s):
    s = s.replace(",", "")
    whole, _, frac = s.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2]) if frac else int(whole) * 100

def check_gateway(gid, min_gap=8):
    lock = _locks.setdefault(gid, threading.Lock())
    if not lock.acquire(blocking=False): return
    try:
        if time.time() - _last.get(gid, 0) < min_gap: return
        _last[gid] = time.time()
        c = conn()
        now = time.time()
        c.execute("UPDATE orders SET status='expired' WHERE status='pending' AND expires_ts<?", (now,))
        c.commit()
        g = c.execute("SELECT * FROM gateways WHERE id=? AND active=1 AND type='fampay'", (gid,)).fetchone()
        pend = c.execute("SELECT * FROM orders WHERE gateway_id=? AND status='pending'", (gid,)).fetchall()
        if not g or not pend: c.close(); return
        err = None
        try:
            pw = dec(g["app_pw_enc"])
            m = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=25)
            m.login(g["gmail"], pw)
            m.select("INBOX", readonly=True)
            since = time.gmtime(min(o["created_ts"] for o in pend) - 86400)
            crit = ["SINCE", f"{since.tm_mday:02d}-{MONTHS[since.tm_mon-1]}-{since.tm_year}"]
            sender = get_setting("fampay_sender").strip()
            if sender: crit += ["FROM", sender]
            typ, data = m.search(None, *crit)
            kws = [k.strip().lower() for k in get_setting("fampay_keywords").split(",") if k.strip()]
            for num in (data[0].split() if data and data[0] else [])[-40:]:
                typ, d = m.fetch(num, "(BODY.PEEK[])")
                msg = email.message_from_bytes(d[0][1])
                mid = (msg.get("Message-ID") or num.decode()).strip()
                if c.execute("SELECT 1 FROM seen_mail WHERE gateway_id=? AND msgid=?", (gid, mid)).fetchone(): continue
                try: mts = parsedate_to_datetime(msg.get("Date")).timestamp()
                except Exception: mts = now
                subj = str(make_header(decode_header(msg.get("Subject", ""))))
                body = subj + " " + _text(msg)
                low = body.lower()
                if kws and not any(k in low for k in kws): continue
                amts = {_paise(a) for a in AMT.findall(body)[:2]}
                for o in pend:
                    if o["amount"] in amts and o["created_ts"] - 120 <= mts <= o["expires_ts"] + 300:
                        u = UTR.search(body)
                        if mark_paid(o["id"], u.group(1) if u else None):
                            c.execute("INSERT OR IGNORE INTO seen_mail VALUES(?,?)", (gid, mid)); c.commit()
                        break
            m.logout()
        except imaplib.IMAP4.error:
            err = "Gmail login failed (check Gmail / app password / IMAP)."
        except Exception as e:
            err = f"Check error: {str(e)[:120]}"
        c.execute("UPDATE gateways SET last_check=?, last_error=? WHERE id=?", (time.time(), err, gid))
        c.commit(); c.close()
    finally:
        lock.release()

def poll_loop():
    while True:
        try:
            c = conn()
            ids = [r[0] for r in c.execute("""SELECT DISTINCT g.id FROM gateways g JOIN orders o ON o.gateway_id=g.id
                   WHERE g.active=1 AND g.type='fampay' AND o.status='pending'""")]
            c.close()
            for gid in ids: check_gateway(gid, min_gap=10)
        except Exception:
            pass
        time.sleep(15)

def start():
    threading.Thread(target=poll_loop, daemon=True).start()
