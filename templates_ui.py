FLASH = """{% with m=get_flashed_messages(with_categories=true) %}{% for c,t in m %}<div class="flash {{c}}">{{t}}</div>{% endfor %}{% endwith %}"""

BASE = """<!doctype html><html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Pay Gateway{% endblock %}</title>
<style>
:root{--bg:#07080d;--card:#0f111a;--line:#1d2130;--txt:#e8eaf3;--mut:#8a90a6;--a:#7c5cff;--b:#00d4ff;--ok:#22c55e;--bad:#ef4444}
*{box-sizing:border-box}html{-webkit-tap-highlight-color:transparent}
body{margin:0;background:radial-gradient(900px 500px at 15% -10%,#1b1550 0,transparent 60%),radial-gradient(700px 400px at 100% 0,#06344a 0,transparent 55%),var(--bg);color:var(--txt);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;min-height:100vh;background-attachment:fixed}
body.open{overflow:hidden}
a{color:var(--b);text-decoration:none}
.logo{font-weight:800;letter-spacing:.3px;background:linear-gradient(90deg,var(--a),var(--b));-webkit-background-clip:text;color:transparent;font-size:20px}
.topbar{position:sticky;top:0;display:flex;align-items:center;gap:12px;padding:10px 16px;background:#07080ddd;backdrop-filter:blur(12px);border-bottom:1px solid var(--line);z-index:20}
.menu-btn{width:42px;height:42px;display:grid;place-items:center;border-radius:12px;border:1px solid var(--line);background:#11141f;color:var(--txt);cursor:pointer}
.menu-btn svg{width:22px;height:22px}
.grow{flex:1}
.overlay{position:fixed;inset:0;background:#000b;opacity:0;pointer-events:none;transition:opacity .25s;z-index:30}
body.open .overlay{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;left:0;bottom:0;width:280px;max-width:84vw;background:linear-gradient(180deg,#0e1019,#090a11);border-right:1px solid var(--line);transform:translateX(-103%);transition:transform .28s cubic-bezier(.3,.8,.3,1);z-index:40;padding:20px 14px;display:flex;flex-direction:column;gap:4px;box-shadow:0 0 60px #7c5cff22}
body.open .drawer{transform:none}
.drawer .who{padding:6px 10px 16px;border-bottom:1px solid var(--line);margin-bottom:10px}
.drawer .who small{display:block;color:var(--mut);margin-top:4px;font-size:13px}
.drawer a{display:flex;align-items:center;gap:13px;padding:12px 14px;border-radius:12px;color:#aab0c6;font-weight:600;font-size:15px}
.drawer a:hover,.drawer a.active{background:linear-gradient(90deg,#7c5cff2b,#00d4ff14);color:#fff}
.drawer a.active .ic{color:var(--b)}
.drawer .sp{flex:1}
.ic{width:20px;height:20px;flex:none}
.page{max-width:1000px;margin:0 auto;padding:20px 16px 60px}
.pagehead{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:2px 0 18px;flex-wrap:wrap}
.pagehead h1{margin:0;font-size:24px}
.card{background:linear-gradient(180deg,#121420a0,#0c0e16);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 0 40px #7c5cff10;margin-bottom:16px}
.auth{max-width:420px;margin:6vh auto}
h1,h2,h3{margin:0 0 14px}h2{font-size:19px}h3{font-size:16px}
label{display:block;font-size:13px;color:var(--mut);margin:12px 0 6px}
input,select{width:100%;padding:12px 14px;border-radius:10px;border:1px solid var(--line);background:#0a0c14;color:var(--txt);font-size:15px;outline:none}
input:focus,select:focus{border-color:var(--a);box-shadow:0 0 0 3px #7c5cff30}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;cursor:pointer;padding:12px 18px;border-radius:10px;font-weight:700;color:#fff;background:linear-gradient(90deg,var(--a),#4f8cff);font-size:14px}
.btn.full{width:100%;margin-top:18px;padding:14px}
.btn.sm{padding:8px 13px;font-size:12px;border-radius:9px}
.btn.gray{background:#232738}.btn.red{background:#b91c1c}.btn.green{background:#15803d}
.flash{padding:11px 14px;border-radius:10px;margin-bottom:12px;font-size:14px;border:1px solid;word-break:break-word}
.flash.ok{background:#22c55e18;border-color:#22c55e55;color:#86efac}
.flash.err{background:#ef444418;border-color:#ef444455;color:#fca5a5}
.flash.warn{background:#f59e0b18;border-color:#f59e0b55;color:#fcd34d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.grid .card{margin:0}
.stat span{color:var(--mut);font-size:13px}
.stat b{display:block;font-size:26px;margin-top:6px;background:linear-gradient(90deg,#fff,#b9c2ff);-webkit-background-clip:text;color:transparent}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:11px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.6px}
.tag{padding:3px 9px;border-radius:99px;font-size:12px;font-weight:700;background:#ffffff14}
.tag.ok{background:#22c55e22;color:#86efac}.tag.bad{background:#ef444422;color:#fca5a5}
.scroll{overflow-x:auto}
details{background:#0a0c14;border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:4px 0}
summary{cursor:pointer;color:var(--b);font-size:13px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:end}.row>*{flex:1;min-width:150px}
.mut{color:var(--mut);font-size:13px}.center{text-align:center}
.gl{display:flex;align-items:center;gap:14px;padding:14px;border:1px solid var(--line);border-radius:14px;background:#0a0c14;margin-bottom:10px}
.gl .gi{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(135deg,#7c5cff33,#00d4ff22);color:var(--b)}
.gl .gt{flex:1;min-width:0}.gl .gt b{display:block}.gl .gt span{color:var(--mut);font-size:13px;word-break:break-all}
code{background:#0a0c14;padding:2px 6px;border-radius:6px}
pre{overflow:auto;background:#0a0c14;padding:14px;border-radius:10px}
</style></head><body>{% block body %}{% endblock %}</body></html>"""

ICONS = """{% macro ico(n) %}{% set P={
'home':'<path d="M3 11l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/>',
'grid':'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
'list':'<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
'book':'<path d="M4 4h12a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3z"/><path d="M4 17a3 3 0 0 1 3-3h12"/>',
'user':'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
'users':'<circle cx="9" cy="8" r="3.5"/><path d="M2 20a7 7 0 0 1 14 0"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14a5 5 0 0 1 5 5"/>',
'gear':'<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
'logout':'<path d="M9 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h4"/><path d="M16 8l4 4-4 4M20 12H9"/>',
'chart':'<path d="M4 20V4M4 20h16"/><path d="M8 16v-5M12 16V7M16 16v-8"/>',
'plus':'<path d="M12 5v14M5 12h14"/>'} %}<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{{ P[n]|safe }}</svg>{% endmacro %}"""

def _layout(items, who, tail):
    links = "".join(
        '<a href="%s" class="{{ \'active\' if active==\'%s\' }}">{{ ico(\'%s\') }}<span>%s</span></a>' % (h, k, i, t)
        for k, h, t, i in items)
    return ("{% extends 'base.html' %}{% from 'icons.html' import ico %}{% block body %}"
      '<div class="topbar"><button class="menu-btn" onclick="tgl()" aria-label="Menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>'
      '<div class="logo">Pay Gateway</div><div class="grow"></div></div>'
      '<div class="overlay" onclick="tgl()"></div>'
      '<aside class="drawer"><div class="who"><div class="logo" style="font-size:22px">Pay Gateway</div><small>' + who + '</small></div>'
      + links + '<div class="sp"></div>' + tail + '</aside>'
      '<main class="page">' + FLASH + '{% block content %}{% endblock %}</main>'
      '<script>function tgl(){document.body.classList.toggle("open")}</script>{% endblock %}')

USER_ITEMS = [("dash", "/dashboard", "Dashboard", "home"), ("gateways", "/gateways", "Gateways", "grid"),
              ("orders", "/orders", "Orders", "list"), ("docs", "/docs", "API docs", "book"), ("account", "/account", "Account", "user")]
ADMIN_ITEMS = [("home", "/admin", "Overview", "chart"), ("users", "/admin/users", "Users", "users"),
               ("gws", "/admin/gateways", "Gateways &amp; Orders", "grid"), ("set", "/admin/settings", "Settings &amp; Backup", "gear")]
LAYOUT_USER = _layout(USER_ITEMS, "{{ g.user.username }}", '<a href="/logout">{{ ico(\'logout\') }}<span>Logout</span></a>')
LAYOUT_ADMIN = _layout(ADMIN_ITEMS, "Administrator", '<a href="/admin/logout">{{ ico(\'logout\') }}<span>Logout</span></a>')

def page(layout, active, title, content):
    return ("{% extends '" + layout + "' %}{% set active='" + active + "' %}{% block title %}" + title + "{% endblock %}{% block content %}" + content + "{% endblock %}")

AUTH = """{% extends 'base.html' %}{% block title %}{{ 'Sign up' if mode=='signup' else 'Login' }}{% endblock %}
{% block body %}<div class="page"><div class="auth card">
<div class="center" style="margin-bottom:18px"><div class="logo" style="font-size:28px">Pay Gateway</div>
<div class="mut">Auto payment verification</div></div>
<h1>{{ 'Create account' if mode=='signup' else 'Welcome back' }}</h1>""" + FLASH + """
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Username</label><input name="username" required maxlength="30" autocomplete="username" autocapitalize="off">
{% if mode=='signup' %}
<label>Phone number</label><input name="phone" required inputmode="numeric" pattern="[0-9+ ]{10,15}">
<label>Gmail</label><input name="email" type="email" required>
{% endif %}
<label>Password</label><input name="password" type="password" required autocomplete="{{ 'new-password' if mode=='signup' else 'current-password' }}">
<button class="btn full">{{ 'Sign up' if mode=='signup' else 'Login' }}</button></form>
<p class="center mut" style="margin-top:16px">
{% if mode=='signup' %}Already have an account? <a href="/login">Login</a>{% else %}New here? <a href="/signup">Create account</a>{% endif %}</p>
</div></div>{% endblock %}"""

ADMIN_LOGIN = """{% extends 'base.html' %}{% block title %}Admin{% endblock %}
{% block body %}<div class="page"><div class="auth card"><h1>Admin login</h1>""" + FLASH + """
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Admin username</label><input name="username" required autocapitalize="off">
<label>Password</label><input name="password" type="password" required>
<button class="btn full">Login</button></form></div></div>{% endblock %}"""

def stat(label, val): return '<div class="card stat"><span>%s</span><b>%s</b></div>' % (label, val)

ORDER_ROWS = """{% for o in rows %}<tr><td>{{o.id[:8]}}</td><td>{{o.gname}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td>
<td><span class="tag {{ 'ok' if o.status=='paid' else 'bad' if o.status=='expired' else '' }}">{{o.status}}</span></td><td>{{ist(o.created_ts)}}</td></tr>
{% else %}<tr><td colspan="6" class="mut">No orders yet.</td></tr>{% endfor %}"""
ORDER_HEAD = "<tr><th>Order</th><th>Gateway</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>Time (IST)</th></tr>"

DASH = page('layout_user.html', 'dash', 'Dashboard', """
<div class="pagehead"><h1>Hi, {{u.username}}</h1><a class="btn sm" href="/gateway/new">{{ ico('plus') }} Add gateway</a></div>
<div class="grid">""" + stat("Gateways", "{{gcount}}") + stat("Payments", "{{st.total}}") + stat("Successful", "{{st.paid}}") + stat("Received ₹", "{{st.sum}}") + """</div>
<div class="card"><h2>Recent orders</h2><div class="scroll"><table>""" + ORDER_HEAD + ORDER_ROWS + """</table></div>
<p style="margin:14px 0 0"><a href="/orders">View all orders →</a></p></div>""")

GATEWAYS = page('layout_user.html', 'gateways', 'Gateways', """
<div class="pagehead"><h1>Gateways</h1><a class="btn sm" href="/gateway/new">{{ ico('plus') }} Add gateway</a></div>
{% for x in gws %}<a class="gl" href="/gateway/{{x.id}}" style="color:inherit"><div class="gi">{{ ico('grid') }}</div>
<div class="gt"><b>{{x.name}}</b><span>{{ 'FamPay' if x.type=='fampay' else 'Paytm' }} · {{x.upi_id}}</span></div>
<span class="tag {{ 'ok' if x.active else 'bad' }}">{{ 'Active' if x.active else 'Off' }}</span></a>
{% else %}<div class="card center mut">No gateway yet. Tap “Add gateway” to create one.</div>{% endfor %}""")

GATEWAY_NEW = page('layout_user.html', 'gateways', 'Add gateway', """
<div class="pagehead"><h1>Add gateway</h1></div>
<div class="card"><form method="post" action="/gateway/add"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Gateway type</label><select name="type" id="gt" onchange="sw()"><option value="fampay">FamPay (Gmail auto verification)</option><option value="paytm">Paytm Business (Merchant ID)</option></select>
<div class="row"><div><label>Shop name (shown to payer)</label><input name="name" required maxlength="40"></div>
<div><label>UPI ID</label><input name="upi_id" required placeholder="name@fam / name@paytm" autocapitalize="off"></div></div>
<div id="f_fam"><p class="mut">Google Account → Security → 2-Step Verification ON → App passwords → create one (16 characters). Turn IMAP on in Gmail settings.</p>
<div class="row"><div><label>Gmail that receives FamPay emails</label><input name="gmail" type="email"></div>
<div><label>Gmail app password (16 characters)</label><input name="app_password" autocomplete="off" placeholder="xxxx xxxx xxxx xxxx"></div></div></div>
<div id="f_pt" style="display:none"><p class="mut">Paytm for Business dashboard → Developer Settings → API keys.</p>
<div class="row"><div><label>Merchant ID (MID)</label><input name="mid" autocomplete="off"></div>
<div><label>Merchant Key</label><input name="mkey" autocomplete="off"></div></div></div>
<button class="btn full">Verify &amp; create</button></form></div>
<script>function sw(){const p=document.getElementById('gt').value=='paytm';
document.getElementById('f_fam').style.display=p?'none':'block';document.getElementById('f_pt').style.display=p?'block':'none'}</script>""")

GATEWAY = page('layout_user.html', 'gateways', '{{gw.name}}', """
<div class="pagehead"><h1>{{gw.name}} <span class="tag {{ 'ok' if gw.active else 'bad' }}">{{ 'Active' if gw.active else 'Off' }}</span></h1><a href="/gateways">← Back</a></div>
<div class="card"><table><tr><th>Type</th><td>{{ 'FamPay (Gmail auto verification)' if gw.type=='fampay' else 'Paytm Business (Merchant ID)' }}</td></tr><tr><th>UPI ID</th><td>{{gw.upi_id}}</td></tr>
{% if gw.type=='fampay' %}<tr><th>Gmail</th><td>{{gw.gmail}}</td></tr>{% else %}<tr><th>Merchant ID</th><td>{{gw.mid}}</td></tr>{% endif %}<tr><th>Last check</th><td>{{last}}</td></tr>
{% if gw.last_error %}<tr><th>Last error</th><td style="color:#fca5a5">{{gw.last_error}}</td></tr>{% endif %}</table>
<h3 style="margin-top:20px">API key</h3><input readonly value="{{gw.api_key}}" onclick="this.select()">
<p class="mut">Base URL: {{base}}</p>
<div class="row" style="margin-top:14px">
{% for path,label,cls in [('test','Test connection','gray'),('test-order','Create ₹1 test order',''),('toggle','Turn ' + ('off' if gw.active else 'on'),'gray'),('regen','Regenerate API key','gray'),('delete','Delete gateway','red')] %}
<form method="post" action="/gateway/{{gw.id}}/{{path}}" style="flex:0" {% if path in ('delete','regen') %}onsubmit="return confirm('Are you sure?')"{% endif %}>
<input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm {{cls}}">{{label}}</button></form>{% endfor %}</div></div>
<div class="card"><h2>Recent orders</h2><div class="scroll"><table>
<tr><th>Order</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>UTR</th><th>Created (IST)</th><th>Webhook</th></tr>
{% for o in orders %}<tr><td>{{o.id[:8]}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td>
<td><span class="tag {{ 'ok' if o.status=='paid' else 'bad' if o.status=='expired' else '' }}">{{o.status}}</span></td>
<td>{{o.utr or '-'}}</td><td>{{ist(o.created_ts)}}</td><td>{{o.webhook_status or '-'}}</td></tr>
{% else %}<tr><td colspan="7" class="mut">No orders yet.</td></tr>{% endfor %}</table></div></div>""")

ORDERS = page('layout_user.html', 'orders', 'Orders', """
<div class="pagehead"><h1>Orders</h1><a class="btn sm" href="/orders.csv?gateway={{gsel or ''}}&status={{ssel}}">Download CSV</a></div>
<div class="card"><form method="get" class="row" style="margin-bottom:12px">
<div><select name="gateway"><option value="">All gateways</option>{% for x in gws %}<option value="{{x.id}}" {{ 'selected' if gsel==x.id }}>{{x.name}}</option>{% endfor %}</select></div>
<div><select name="status"><option value="">All status</option>{% for s in ['paid','pending','expired'] %}<option {{ 'selected' if ssel==s }}>{{s}}</option>{% endfor %}</select></div>
<div style="flex:0"><button class="btn gray">Filter</button></div></form>
<div class="scroll"><table><tr><th>Order</th><th>Gateway</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>UTR</th><th>Created (IST)</th><th>Paid (IST)</th></tr>
{% for o in orders %}<tr><td>{{o.id[:8]}}</td><td>{{o.gname}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td>
<td><span class="tag {{ 'ok' if o.status=='paid' else 'bad' if o.status=='expired' else '' }}">{{o.status}}</span></td><td>{{o.utr or '-'}}</td><td>{{ist(o.created_ts)}}</td><td>{{ist(o.paid_ts)}}</td></tr>
{% else %}<tr><td colspan="8" class="mut">No orders.</td></tr>{% endfor %}</table></div>
<div class="row" style="margin-top:14px"><div>{% if page>1 %}<a class="btn sm gray" href="?page={{page-1}}&gateway={{gsel or ''}}&status={{ssel}}">← Prev</a>{% endif %}</div>
<div style="text-align:right">{% if more %}<a class="btn sm gray" href="?page={{page+1}}&gateway={{gsel or ''}}&status={{ssel}}">Next →</a>{% endif %}</div></div></div>""")

DOCS = page('layout_user.html', 'docs', 'API docs', """
<div class="pagehead"><h1>API docs</h1></div><div class="card">
<p class="mut">Base URL: <b>{{base}}</b> &nbsp; Auth: header <code>X-API-Key: YOUR_GATEWAY_KEY</code></p>
<h3>1. Create order</h3>
<pre>POST {{base}}/api/v1/orders
Content-Type: application/json

{"amount": 100, "ref": "your-order-id",
 "webhook_url": "https://yoursite.com/hook",
 "redirect_url": "https://yoursite.com/thanks",
 "cancel_url": "https://yoursite.com/cart"}</pre>
<p class="mut">Only <code>amount</code> is required. Response:</p>
<pre>{"order_id":"...","payment_url":"{{base}}/pay/...","amount":"100.00","expires_in":300}</pre>
<p class="mut">Send the user to <code>payment_url</code>. Orders expire in 5 minutes. For FamPay the amount can be a few paise higher so each pending payment is unique; use the returned <code>amount</code>. The Back button on the payment page goes to <code>cancel_url</code> (or <code>redirect_url</code>).</p>
<h3>2. Check status</h3>
<pre>GET {{base}}/api/v1/orders/ORDER_ID   →  {"status":"pending|paid|expired", ...}</pre>
<h3>3. Webhook</h3>
<p class="mut">When paid, we POST JSON <code>{event, order_id, ref, amount, status, utr, paid_at}</code> to your webhook_url with header <code>X-Signature</code> = HMAC-SHA256 of the raw body using your API key. Always verify it, and confirm the order with the status API.</p></div>""")

ACCOUNT = page('layout_user.html', 'account', 'Account', """
<div class="pagehead"><h1>Account</h1></div>
<div class="card"><table><tr><th>Username</th><td>{{u.username}}</td></tr><tr><th>Phone</th><td>{{u.phone}}</td></tr><tr><th>Gmail</th><td>{{u.email}}</td></tr><tr><th>Joined</th><td>{{u.created}}</td></tr></table></div>
<div class="card"><h3>Change password</h3>
<form method="post" action="/change-password" class="row"><input type="hidden" name="csrf" value="{{csrf}}">
<div><label>Current password</label><input type="password" name="old" required></div>
<div><label>New password</label><input type="password" name="new" required minlength="6"></div>
<div><button class="btn">Update</button></div></form></div>""")

CHECKOUT = """{% extends 'base.html' %}{% block title %}Pay ₹{{amt}}{% endblock %}
{% block body %}<div class="page"><div style="max-width:420px;margin:0 auto 10px"><a href="#" onclick="goBack();return false" style="display:inline-flex;align-items:center;gap:6px;font-weight:700">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>Back</a></div>
<div class="auth card center" style="margin-top:0">
<div class="logo" style="font-size:22px">{{gw.name}}</div>
<div class="mut" style="margin:6px 0 14px">Order {{o.id[:8]}}</div>
<div id="pending">
<div style="font-size:38px;font-weight:800">₹{{amt}}</div>
{% if gw.type=='fampay' %}<p style="color:#fcd34d;font-size:13px">Pay exactly ₹{{amt}}, including the paise, or it will not be detected.</p>{% endif %}
<div id="qr" style="background:#fff;display:inline-block;padding:12px;border-radius:12px;margin:8px 0"></div>
<div><a class="btn" href="{{upi}}">Open UPI app</a></div>
<p class="mut" style="margin-top:12px">UPI ID: {{gw.upi_id}}</p>
<p class="mut">QR expires in <b id="t">--:--</b> &nbsp; Waiting for payment…</p></div>
<div id="ok" style="display:none"><div style="font-size:54px">✅</div><h2>Payment received</h2><p class="mut" id="rd"></p></div>
<div id="ex" style="display:none"><div style="font-size:54px">⌛</div><h2>QR expired</h2><p class="mut">Please go back and start a new payment.</p><a class="btn" href="#" onclick="goBack();return false">Back</a></div>
</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>
const link={{upi|tojson}}, redirect={{(o.redirect_url or '')|tojson}}, back={{(o.cancel_url or o.redirect_url or '')|tojson}};
function goBack(){if(back)location.href=back;else if(history.length>1)history.back();else location.href='/'}
if(window.QRCode)new QRCode(document.getElementById('qr'),{text:link,width:210,height:210});
let left={{remaining}};
function show(id){for(const x of['pending','ok','ex'])document.getElementById(x).style.display=x==id?'block':'none'}
setInterval(()=>{left=Math.max(0,left-1);const m=String(Math.floor(left/60)).padStart(2,'0'),s=String(left%60).padStart(2,'0');document.getElementById('t').textContent=m+':'+s;if(left==0&&document.getElementById('pending').style.display!='none')poll(true)},1000);
const st={{o.status|tojson}};
if(st=='paid')done();else if(st=='expired')show('ex');else poll();
function done(){show('ok');if(redirect){document.getElementById('rd').textContent='Redirecting…';setTimeout(()=>location.href=redirect,2000)}}
let busy=false;
async function poll(once){if(busy&&!once)return;busy=true;try{const r=await fetch('/pay/{{o.id}}/status');const d=await r.json();
if(d.status=='paid')return done();if(d.status=='expired')return show('ex');left=d.remaining}catch(e){}busy=false;if(!once)setTimeout(poll,1500)}
</script>{% endblock %}"""

ADMIN_HOME = page('layout_admin.html', 'home', 'Overview', """
<div class="pagehead"><h1>Overview</h1></div>
<div class="grid">""" + stat("Users", "{{us.n}}") + stat("Gateways", "{{gw.n}}") + stat("Paid orders", "{{ost.p or 0}}") + stat("Revenue today ₹", "{{money(ost.t or 0)}}") + stat("Revenue total ₹", "{{money(ost.s or 0)}}") + """</div>
<div class="card"><h2>Latest orders</h2><div class="scroll"><table>""" + ORDER_HEAD + ORDER_ROWS + """</table></div></div>
<div class="card"><h2>New users</h2><div class="scroll"><table><tr><th>Username</th><th>Phone</th><th>Gmail</th><th>Joined</th></tr>
{% for x in newu %}<tr><td>{{x.username}}</td><td>{{x.phone}}</td><td>{{x.email}}</td><td>{{x.created}}</td></tr>{% else %}<tr><td colspan="4" class="mut">No users yet.</td></tr>{% endfor %}</table></div></div>""")

ADMIN_USERS = page('layout_admin.html', 'users', 'Users', """
<div class="pagehead"><h1>Users</h1></div>
<div class="grid">""" + stat("Total", "{{stats.total}}") + stat("Active", "{{stats.active}}") + stat("Banned", "{{stats.banned}}") + """</div>
<div class="card">
<form method="get" class="row" style="margin-bottom:12px"><input name="q" value="{{q}}" placeholder="Search username / phone / gmail"><button class="btn gray" style="flex:0">Search</button></form>
<div class="scroll"><table><tr><th>ID</th><th>Username</th><th>Phone</th><th>Gmail</th><th>Status</th><th>Joined</th><th>Actions</th></tr>
{% for x in users %}<tr><td>{{x.id}}</td><td>{{x.username}}</td><td>{{x.phone}}</td><td>{{x.email}}</td>
<td><span class="tag {{ 'bad' if x.banned else 'ok' }}">{{ 'Banned' if x.banned else 'Active' }}</span></td><td>{{x.created}}</td>
<td style="min-width:260px">
<details><summary>Edit / Password</summary>
<form method="post" action="/admin/user/{{x.id}}/update"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Phone</label><input name="phone" value="{{x.phone}}"><label>Gmail</label><input name="email" value="{{x.email}}">
<button class="btn sm" style="margin-top:8px">Save</button></form>
<form method="post" action="/admin/user/{{x.id}}/password"><input type="hidden" name="csrf" value="{{csrf}}">
<label>New password (blank = auto-generate)</label><input name="password">
<button class="btn sm gray" style="margin-top:8px">Set / Reset password</button></form></details>
<form method="post" action="/admin/user/{{x.id}}/toggle" style="display:inline"><input type="hidden" name="csrf" value="{{csrf}}">
<button class="btn sm {{ 'green' if x.banned else 'gray' }}">{{ 'Unban' if x.banned else 'Ban' }}</button></form>
<form method="post" action="/admin/user/{{x.id}}/delete" style="display:inline" onsubmit="return confirm('Delete this user?')"><input type="hidden" name="csrf" value="{{csrf}}">
<button class="btn sm red">Delete</button></form></td></tr>
{% else %}<tr><td colspan="7" class="mut">No users yet.</td></tr>{% endfor %}</table></div></div>""")

ADMIN_GW = page('layout_admin.html', 'gws', 'Gateways', """
<div class="pagehead"><h1>Gateways &amp; Orders</h1></div>
<div class="grid">""" + stat("Orders", "{{ost.n}}") + stat("Paid", "{{ost.p or 0}}") + stat("Revenue total ₹", "{{money(ost.s or 0)}}") + stat("Revenue today ₹", "{{money(ost.t or 0)}}") + """</div>
<div class="card"><h2>All gateways</h2><div class="scroll"><table>
<tr><th>ID</th><th>Owner</th><th>Name</th><th>UPI</th><th>Type / Account</th><th>Orders</th><th>Paid</th><th>Status</th><th>Last error</th><th></th></tr>
{% for x in gws %}<tr><td>{{x.id}}</td><td>{{x.username}}</td><td>{{x.name}}</td><td>{{x.upi_id}}</td><td>{{x.type}} · {{x.gmail or x.mid}}</td><td>{{x.n}}</td><td>{{x.p or 0}}</td>
<td><span class="tag {{ 'ok' if x.active else 'bad' }}">{{ 'Active' if x.active else 'Off' }}</span></td><td>{{x.last_error or '-'}}</td>
<td style="white-space:nowrap"><form method="post" action="/admin/gateway/{{x.id}}/toggle" style="display:inline"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm gray">{{ 'Off' if x.active else 'On' }}</button></form>
<form method="post" action="/admin/gateway/{{x.id}}/delete" style="display:inline" onsubmit="return confirm('Delete gateway?')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm red">Delete</button></form></td></tr>
{% else %}<tr><td colspan="10" class="mut">No gateways.</td></tr>{% endfor %}</table></div></div>
<div class="card"><h2>Latest orders</h2><div class="scroll"><table>
<tr><th>Order</th><th>Gateway</th><th>Ref</th><th>Amount ₹</th><th>Status</th><th>UTR</th><th>Created (IST)</th><th>Webhook</th><th></th></tr>
{% for o in orders %}<tr><td>{{o.id[:8]}}</td><td>{{o.gateway_id}}</td><td>{{o.ref or '-'}}</td><td>{{money(o.amount)}}</td><td>{{o.status}}</td><td>{{o.utr or '-'}}</td><td>{{ist(o.created_ts)}}</td><td>{{o.webhook_status or '-'}}</td>
<td>{% if o.status!='paid' %}<form method="post" action="/admin/order/{{o.id}}/paid" onsubmit="return confirm('Mark as paid manually?')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn sm green">Mark paid</button></form>{% endif %}</td></tr>
{% else %}<tr><td colspan="9" class="mut">No orders.</td></tr>{% endfor %}</table></div></div>""")

ADMIN_SET = page('layout_admin.html', 'set', 'Settings', """
<div class="pagehead"><h1>Settings &amp; Backup</h1></div>
<div class="card"><h2>Settings</h2><form method="post"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Public base URL (used in API docs and payment links; blank = auto)</label><input name="base_url" value="{{s.base_url}}" placeholder="https://yourname.onrender.com">
<label>FamPay email sender filter (part of the From address)</label><input name="fampay_sender" value="{{s.fampay_sender}}">
<label>Payment-received keywords in the email (comma separated, any one must match)</label><input name="fampay_keywords" value="{{s.fampay_keywords}}">
<label>Order / QR expiry (minutes)</label><input name="order_expiry_min" type="number" min="3" max="120" value="{{s.order_expiry_min}}">
<label>Paytm environment</label><select name="paytm_env"><option value="prod" {{ 'selected' if s.paytm_env!='stage' }}>Production</option><option value="stage" {{ 'selected' if s.paytm_env=='stage' }}>Staging (test)</option></select>
<h3 style="margin-top:22px">Auto backup (every 12 hours)</h3>
<p class="mut">Set a Telegram bot token and your chat ID and every backup is sent to you as a file. Leave the token blank to keep the saved one.</p>
<div class="row"><div><label>Telegram bot token</label><input name="tg_token" type="password" placeholder="{{ 'saved' if s.tg_token else 'not set' }}" autocomplete="off"></div>
<div><label>Telegram chat ID</label><input name="tg_chat" value="{{s.tg_chat}}"></div></div>
<p class="mut">Last backup: {{last_backup}} · {{s.last_backup_msg or '-'}}</p>
<button class="btn full">Save</button></form></div>
<div class="card"><h2>Backup &amp; restore</h2>
<div class="row"><a class="btn" href="/admin/backup" style="flex:0">Download backup</a>
<form method="post" action="/admin/backup-now" style="flex:0"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn gray">Backup now (Telegram)</button></form></div>
<form method="post" action="/admin/restore" enctype="multipart/form-data" class="row" style="margin-top:16px"><input type="hidden" name="csrf" value="{{csrf}}">
<input type="file" name="file" required><button class="btn gray" style="flex:0">Restore</button></form></div>""")

TEMPLATES = {"base.html": BASE, "icons.html": ICONS, "layout_user.html": LAYOUT_USER, "layout_admin.html": LAYOUT_ADMIN,
  "auth.html": AUTH, "admin_login.html": ADMIN_LOGIN, "dash.html": DASH, "gateways.html": GATEWAYS, "gateway_new.html": GATEWAY_NEW,
  "gateway.html": GATEWAY, "orders.html": ORDERS, "docs.html": DOCS, "account.html": ACCOUNT, "checkout.html": CHECKOUT,
  "admin_home.html": ADMIN_HOME, "admin_users.html": ADMIN_USERS, "admin_gw.html": ADMIN_GW, "admin_set.html": ADMIN_SET}
