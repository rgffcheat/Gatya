from templates_ui import FLASH, ADMIN_NAV

def nav(extra=""):
    return """<div class="nav"><div class="logo">Pay Gateway</div><div><a href="/dashboard">Dashboard</a> &nbsp; <a href="/orders">Orders</a> &nbsp; <a href="/docs">API docs</a> &nbsp; <a href="/logout">Logout</a></div></div>"""

DASH = """{% extends 'base.html' %}{% block title %}Dashboard{% endblock %}
{% block body %}""" + nav() + """<div class="wrap">""" + FLASH + """
<div class="grid">
<div class="card stat"><span>Gateways</span><b>{{gws|length}}</b></div>
<div class="card stat"><span>Total payments</span><b>{{st.total}}</b></div>
<div class="card stat"><span>Successful</span><b>{{st.paid}}</b></div>
<div class="card stat"><span>Received (₹)</span><b>{{st.sum}}</b></div></div>

<div class="card"><h2>My gateways</h2>
<div class="scroll"><table><tr><th>Name</th><th>Type</th><th>UPI ID</th><th>Status</th><th></th></tr>
{% for x in gws %}<tr><td>{{x.name}}</td><td>{{ 'FamPay' if x.type=='fampay' else 'Paytm' }}</td><td>{{x.upi_id}}</td>
<td><span class="tag {{ 'ok' if x.active else 'bad' }}">{{ 'Active' if x.active else 'Off' }}</span></td>
<td><a class="btn sm" href="/gateway/{{x.id}}">Open</a></td></tr>
{% else %}<tr><td colspan="5" class="mut">No gateway yet. Create one below.</td></tr>{% endfor %}</table></div></div>

<div class="card" style="margin-top:18px"><h2>Add gateway</h2>
<form method="post" action="/gateway/add"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Gateway type</label><select name="type" id="gt" onchange="sw()"><option value="fampay">FamPay (Gmail auto verification)</option><option value="paytm">Paytm Business (Merchant ID)</option></select>
<div class="row"><div><label>Gateway name (shown to payer)</label><input name="name" required maxlength="40"></div>
<div><label>UPI ID</label><input name="upi_id" required placeholder="name@fam / name@paytm"></div></div>
<div id="f_fam"><p class="mut">Setup: Google Account → Security → 2-Step Verification ON → App passwords → create one (16 characters). Turn IMAP on in Gmail settings.</p>
<div class="row"><div><label>Gmail that receives FamPay emails</label><input name="gmail" type="email"></div>
<div><label>Gmail app password (16 characters)</label><input name="app_password" autocomplete="off" placeholder="xxxx xxxx xxxx xxxx"></div></div></div>
<div id="f_pt" style="display:none"><p class="mut">Paytm for Business dashboard → Developer Settings → API keys: copy your Merchant ID and Merchant Key. Dynamic QR must be enabled on your account.</p>
<div class="row"><div><label>Merchant ID (MID)</label><input name="mid" autocomplete="off"></div>
<div><label>Merchant Key (16 characters)</label><input name="mkey" autocomplete="off"></div></div></div>
<button class="btn" style="margin-top:16px">Verify &amp; create</button></form></div>
<script>function sw(){const p=document.getElementById('gt').value=='paytm';
document.getElementById('f_fam').style.display=p?'none':'block';document.getElementById('f_pt').style.display=p?'block':'none'}</script>

<div class="card" style="margin-top:18px"><h2>Account</h2>
<table><tr><th>Username</th><td>{{u.username}}</td></tr><tr><th>Phone</th><td>{{u.phone}}</td></tr><tr><th>Gmail</th><td>{{u.email}}</td></tr></table>
<h3 style="margin-top:22px">Change password</h3>
<form method="post" action="/change-password" class="row"><input type="hidden" name="csrf" value="{{csrf}}">
<div><label>Current password</label><input type="password" name="old" required></div>
<div><label>New password</label><input type="password" name="new" required minlength="6"></div>
<div><button class="btn">Update</button></div></form></div>
</div>{% endblock %}"""

GATEWAY = """{% extends 'base.html' %}{% block title %}{{gw.name}}{% endblock %}
{% block body %}""" + nav() + """<div class="wrap">""" + FLASH + """
<a href="/dashboard">← Back</a>
<div class="card" style="margin-top:12px"><h2>{{gw.name}} <span class="tag {{ 'ok' if gw.active else 'bad' }}">{{ 'Active' if gw.active else 'Off' }}</span></h2>
<table><tr><th>Type</th><td>{{ 'FamPay (Gmail auto verification)' if gw.type=='fampay' else 'Paytm Business (Merchant ID)' }}</td></tr><tr><th>UPI ID</th><td>{{gw.upi_id}}</td></tr>
{% if gw.type=='fampay' %}<tr><th>Gmail</th><td>{{gw.gmail}}</td></tr>{% else %}<tr><th>Merchant ID</th><td>{{gw.mid}}</td></tr>{% endif %}<tr><th>Last check</th><td>{{last}}</td></tr>
{% if gw.last_error %}<tr><th>Last error</th><td style="color:#fca5a5">{{gw.last_error}}</td></tr>{% endif %}</table>
<h3 style="margin-top:20px">API key</h3><input readonly value="{{gw.api_key}}" onclick="this.select()">
<p class="mut">Base URL: {{base}}</p>
<div class="row" style="margin-top:14px">
{% for path,label,cls in [('test','Test connection','gray'),('test-order','Create ₹1 test order',''),('toggle','Turn ' + ('off' if gw.active else 'on'),'gray'),('regen','Regenerate API key','gray'),('delete','Delete gateway','red')] %}
<form method="post" action="/gateway/{{gw.id}}/{{path}}" style="flex:0" {% if path in ('delete','regen') %}onsubmit="return confirm('Are you sure?')"{% endif %}>
<input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm {{cls}}">{{label}}</button></form>{% endfor %}</div></div>
<div class="card" style="margin-top:18px"><h2>Recent orders</h2><div class="scroll"><table>
<tr><th>Order</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>UTR</th><th>Created (IST)</th><th>Webhook</th></tr>
{% for o in orders %}<tr><td>{{o.id[:8]}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td>
<td><span class="tag {{ 'ok' if o.status=='paid' else 'bad' if o.status=='expired' else '' }}">{{o.status}}</span></td>
<td>{{o.utr or '-'}}</td><td>{{ist(o.created_ts)}}</td><td>{{o.webhook_status or '-'}}</td></tr>
{% else %}<tr><td colspan="7" class="mut">No orders yet.</td></tr>{% endfor %}</table></div></div>
</div>{% endblock %}"""

CHECKOUT = """{% extends 'base.html' %}{% block title %}Pay ₹{{amt}}{% endblock %}
{% block body %}<div class="wrap"><div class="auth card center">
<div class="logo" style="font-size:22px">{{gw.name}}</div>
<div class="mut" style="margin:6px 0 14px">Order {{o.id[:8]}}</div>
<div id="pending">
<div style="font-size:38px;font-weight:800">₹{{amt}}</div>
<p style="color:#fcd34d;font-size:13px">Pay exactly ₹{{amt}}, including the paise, or it will not be detected.</p>
<div id="qr" style="background:#fff;display:inline-block;padding:12px;border-radius:12px;margin:8px 0"></div>
<div><a class="btn" href="{{upi}}">Open UPI app</a></div>
<p class="mut" style="margin-top:12px">UPI ID: {{gw.upi_id}}</p>
<p class="mut">Time left: <b id="t">--:--</b> &nbsp; Waiting for payment…</p></div>
<div id="ok" style="display:none"><div style="font-size:54px">✅</div><h2>Payment received</h2><p class="mut" id="rd"></p></div>
<div id="ex" style="display:none"><div style="font-size:54px">⌛</div><h2>Order expired</h2><p class="mut">Please start a new payment.</p></div>
</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>
const link={{upi|tojson}}, redirect={{(o.redirect_url or '')|tojson}};
if(window.QRCode)new QRCode(document.getElementById('qr'),{text:link,width:210,height:210});
let left={{remaining}};
function show(id){for(const x of['pending','ok','ex'])document.getElementById(x).style.display=x==id?'block':'none'}
setInterval(()=>{left=Math.max(0,left-1);const m=String(Math.floor(left/60)).padStart(2,'0'),s=String(left%60).padStart(2,'0');document.getElementById('t').textContent=m+':'+s},1000);
const st={{o.status|tojson}};
if(st=='paid')done();else if(st=='expired')show('ex');else poll();
function done(){show('ok');if(redirect){document.getElementById('rd').textContent='Redirecting…';setTimeout(()=>location.href=redirect,2500)}}
async function poll(){try{const r=await fetch('/pay/{{o.id}}/status');const d=await r.json();
if(d.status=='paid')return done();if(d.status=='expired')return show('ex');left=d.remaining}catch(e){}
setTimeout(poll,4000)}
</script>{% endblock %}"""

DOCS = """{% extends 'base.html' %}{% block title %}API docs{% endblock %}
{% block body %}""" + nav() + """<div class="wrap"><div class="card"><h2>API docs</h2>
<p class="mut">Base URL: <b>{{base}}</b> &nbsp; Auth: header <code>X-API-Key: YOUR_GATEWAY_KEY</code></p>
<h3>1. Create order</h3>
<pre style="overflow:auto;background:#0a0c14;padding:14px;border-radius:10px">POST {{base}}/api/v1/orders
Content-Type: application/json

{"amount": 100, "ref": "your-order-id",
 "webhook_url": "https://yoursite.com/hook",
 "redirect_url": "https://yoursite.com/thanks"}</pre>
<p class="mut">Only <code>amount</code> is required. Response:</p>
<pre style="overflow:auto;background:#0a0c14;padding:14px;border-radius:10px">{"order_id":"...","payment_url":"{{base}}/pay/...","amount":"100.00","expires_in":900}</pre>
<p class="mut">Send the user to <code>payment_url</code>. The amount can be a few paise higher than you sent so that each pending payment is unique. Use the returned <code>amount</code>.</p>
<h3>2. Check status</h3>
<pre style="overflow:auto;background:#0a0c14;padding:14px;border-radius:10px">GET {{base}}/api/v1/orders/ORDER_ID   →  {"status":"pending|paid|expired", ...}</pre>
<h3>3. Webhook</h3>
<p class="mut">When paid, we POST JSON <code>{event, order_id, ref, amount, status, utr, paid_at}</code> to your webhook_url with header <code>X-Signature</code> = HMAC-SHA256 of the raw body using your API key. Always verify it, and confirm the order with the status API.</p>
</div></div>{% endblock %}"""

ADMIN_GW = """{% extends 'base.html' %}{% block title %}Gateways{% endblock %}
{% block body %}""" + ADMIN_NAV + """<div class="wrap">""" + FLASH + """
<div class="grid"><div class="card stat"><span>Orders</span><b>{{ost.n}}</b></div><div class="card stat"><span>Paid</span><b>{{ost.p or 0}}</b></div>
<div class="card stat"><span>Revenue total ₹</span><b>{{money(ost.s or 0)}}</b></div><div class="card stat"><span>Revenue today ₹</span><b>{{money(ost.t or 0)}}</b></div></div>
<div class="card"><h2>All gateways</h2><div class="scroll"><table>
<tr><th>ID</th><th>Owner</th><th>Name</th><th>UPI</th><th>Type / Account</th><th>Orders</th><th>Paid</th><th>Status</th><th>Last error</th><th></th></tr>
{% for x in gws %}<tr><td>{{x.id}}</td><td>{{x.username}}</td><td>{{x.name}}</td><td>{{x.upi_id}}</td><td>{{x.type}} · {{x.gmail or x.mid}}</td><td>{{x.n}}</td><td>{{x.p or 0}}</td>
<td><span class="tag {{ 'ok' if x.active else 'bad' }}">{{ 'Active' if x.active else 'Off' }}</span></td><td>{{x.last_error or '-'}}</td>
<td style="white-space:nowrap"><form method="post" action="/admin/gateway/{{x.id}}/toggle" style="display:inline"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm gray">{{ 'Off' if x.active else 'On' }}</button></form>
<form method="post" action="/admin/gateway/{{x.id}}/delete" style="display:inline" onsubmit="return confirm('Delete gateway?')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm red">Delete</button></form></td></tr>
{% else %}<tr><td colspan="10" class="mut">No gateways.</td></tr>{% endfor %}</table></div></div>
<div class="card" style="margin-top:18px"><h2>Latest orders</h2><div class="scroll"><table>
<tr><th>Order</th><th>Gateway</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>UTR</th><th>Created (IST)</th><th>Webhook</th><th></th></tr>
{% for o in orders %}<tr><td>{{o.id[:8]}}</td><td>{{o.gateway_id}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td><td>{{o.status}}</td><td>{{o.utr or '-'}}</td><td>{{ist(o.created_ts)}}</td><td>{{o.webhook_status or '-'}}</td><td>{% if o.status!='paid' %}<form method="post" action="/admin/order/{{o.id}}/paid" onsubmit="return confirm('Mark as paid manually?')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm green">Mark paid</button></form>{% endif %}</td></tr>
{% else %}<tr><td colspan="9" class="mut">No orders.</td></tr>{% endfor %}</table></div></div></div>{% endblock %}"""

ADMIN_SET = """{% extends 'base.html' %}{% block title %}Settings{% endblock %}
{% block body %}""" + ADMIN_NAV + """<div class="wrap">""" + FLASH + """
<div class="card"><h2>Settings</h2><form method="post"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Public base URL (used in API docs and payment links; blank = auto)</label><input name="base_url" value="{{s.base_url}}" placeholder="https://yourname.onrender.com">
<label>FamPay email sender filter (part of the From address)</label><input name="fampay_sender" value="{{s.fampay_sender}}">
<label>Payment-received keywords in the email (comma separated, any one must match)</label><input name="fampay_keywords" value="{{s.fampay_keywords}}">
<label>Order expiry (minutes)</label><input name="order_expiry_min" type="number" min="3" max="120" value="{{s.order_expiry_min}}">
<label>Paytm environment</label><select name="paytm_env"><option value="prod" {{ 'selected' if s.paytm_env!='stage' }}>Production</option><option value="stage" {{ 'selected' if s.paytm_env=='stage' }}>Staging (test)</option></select>
<h3 style="margin-top:22px">Auto backup (every 12 hours)</h3>
<p class="mut">Render free disk can be wiped. Set a Telegram bot token and your chat ID and every backup is sent to you as a file. Restore it from the Users page. Leave the token blank to keep the saved one.</p>
<div class="row"><div><label>Telegram bot token</label><input name="tg_token" type="password" placeholder="{{ 'saved' if s.tg_token else 'not set' }}" autocomplete="off"></div>
<div><label>Telegram chat ID</label><input name="tg_chat" value="{{s.tg_chat}}"></div></div>
<p class="mut">Last backup: {{last_backup}} · {{s.last_backup_msg or '-'}}</p>
<button class="btn full">Save</button></form>
<form method="post" action="/admin/backup-now"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn gray" style="margin-top:12px">Backup now</button></form></div></div>{% endblock %}"""

ORDERS = """{% extends 'base.html' %}{% block title %}Orders{% endblock %}
{% block body %}""" + nav() + """<div class="wrap">""" + FLASH + """<div class="card"><h2>Orders</h2>
<form method="get" class="row" style="margin-bottom:12px">
<div><select name="gateway"><option value="">All gateways</option>{% for x in gws %}<option value="{{x.id}}" {{ 'selected' if gsel==x.id }}>{{x.name}}</option>{% endfor %}</select></div>
<div><select name="status"><option value="">All status</option>{% for s in ['paid','pending','expired'] %}<option {{ 'selected' if ssel==s }}>{{s}}</option>{% endfor %}</select></div>
<div style="flex:0"><button class="btn gray">Filter</button></div>
<div style="flex:0"><a class="btn" href="/orders.csv?gateway={{gsel or ''}}&status={{ssel}}">CSV</a></div></form>
<div class="scroll"><table><tr><th>Order</th><th>Gateway</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>UTR</th><th>Created (IST)</th><th>Paid (IST)</th></tr>
{% for o in orders %}<tr><td>{{o.id[:8]}}</td><td>{{o.gname}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td>
<td><span class="tag {{ 'ok' if o.status=='paid' else 'bad' if o.status=='expired' else '' }}">{{o.status}}</span></td><td>{{o.utr or '-'}}</td><td>{{ist(o.created_ts)}}</td><td>{{ist(o.paid_ts)}}</td></tr>
{% else %}<tr><td colspan="8" class="mut">No orders.</td></tr>{% endfor %}</table></div>
<div class="row" style="margin-top:14px"><div>{% if page>1 %}<a class="btn sm gray" href="?page={{page-1}}&gateway={{gsel or ''}}&status={{ssel}}">← Prev</a>{% endif %}</div>
<div style="text-align:right">{% if more %}<a class="btn sm gray" href="?page={{page+1}}&gateway={{gsel or ''}}&status={{ssel}}">Next →</a>{% endif %}</div></div>
</div></div>{% endblock %}"""

TEMPLATES_GW = {"orders.html": ORDERS, "dash.html": DASH, "gateway.html": GATEWAY, "checkout.html": CHECKOUT, "docs.html": DOCS,
                "admin_gw.html": ADMIN_GW, "admin_set.html": ADMIN_SET}
