import time, threading
from core import conn
import fampay, paytm, backup

def check(gid):
    c = conn(); r = c.execute("SELECT type FROM gateways WHERE id=?", (gid,)).fetchone(); c.close()
    if r: (fampay if r["type"] == "fampay" else paytm).check_gateway(gid)

def loop():
    n = 0
    while True:
        try:
            c = conn()
            c.execute("UPDATE orders SET status='expired' WHERE status='pending' AND expires_ts<?", (time.time(),)); c.commit()
            ids = [r[0] for r in c.execute("""SELECT DISTINCT g.id FROM gateways g JOIN orders o ON o.gateway_id=g.id
                   WHERE g.active=1 AND o.status='pending'""")]
            c.close()
            for gid in ids: check(gid)
        except Exception:
            pass
        try:
            if n % 4 == 0: backup.maybe_auto()
        except Exception:
            pass
        n += 1; time.sleep(15)

def start():
    threading.Thread(target=loop, daemon=True).start()
