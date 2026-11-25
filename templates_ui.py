BASE = """<!doctype html><html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Pay Gateway{% endblock %}</title>
<style>
:root{--bg:#07080d;--card:#0f111a;--line:#1d2130;--txt:#e8eaf3;--mut:#8a90a6;--a:#7c5cff;--b:#00d4ff;--ok:#22c55e;--bad:#ef4444}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 500px at 15% -10%,#1b1550 0,transparent 60%),radial-gradient(700px 400px at 100% 0,#06344a 0,transparent 55%),var(--bg);color:var(--txt);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;min-height:100vh}
a{color:var(--b);text-decoration:none}
.wrap{max-width:1100px;margin:0 auto;padding:20px}
.nav{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--line);backdrop-filter:blur(8px);position:sticky;top:0;background:#07080dcc;z-index:5}
.logo{font-weight:800;letter-spacing:.3px;background:linear-gradient(90deg,var(--a),var(--b));-webkit-background-clip:text;color:transparent;font-size:20px}
.card{background:linear-gradient(180deg,#12142080,#0c0e16);border:1px solid var(--line);border-radius:16px;padding:22px;box-shadow:0 0 40px #7c5cff12}
.auth{max-width:420px;margin:7vh auto}
h1,h2,h3{margin:0 0 14px}h1{font-size:26px}
label{display:block;font-size:13px;color:var(--mut);margin:12px 0 6px}
input,select{width:100%;padding:12px 14px;border-radius:10px;border:1px solid var(--line);background:#0a0c14;color:var(--txt);font-size:15px;outline:none}
input:focus{border-color:var(--a);box-shadow:0 0 0 3px #7c5cff30}
.btn{display:inline-block;border:0;cursor:pointer;padding:12px 18px;border-radius:10px;font-weight:700;color:#fff;background:linear-gradient(90deg,var(--a),#4f8cff);font-size:14px}
.btn.full{width:100%;margin-top:18px;padding:14px}
.btn.sm{padding:7px 12px;font-size:12px;border-radius:8px}
.btn.gray{background:#232738}.btn.red{background:#b91c1c}.btn.green{background:#15803d}
.flash{padding:11px 14px;border-radius:10px;margin-bottom:12px;font-size:14px;border:1px solid}
.flash.ok{background:#22c55e18;border-color:#22c55e55;color:#86efac}
.flash.err{background:#ef444418;border-color:#ef444455;color:#fca5a5}
.flash.warn{background:#f59e0b18;border-color:#f59e0b55;color:#fcd34d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:18px}
.stat b{display:block;font-size:28px;margin-top:6px}.stat span{color:var(--mut);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:11px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.6px}
.tag{padding:3px 9px;border-radius:99px;font-size:12px;font-weight:700}
.tag.ok{background:#22c55e22;color:#86efac}.tag.bad{background:#ef444422;color:#fca5a5}
.scroll{overflow-x:auto}
details{background:#0a0c14;border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:4px 0}
summary{cursor:pointer;color:var(--b);font-size:13px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:end}.row>*{flex:1;min-width:140px}
.mut{color:var(--mut);font-size:13px}.center{text-align:center}
</style></head><body>{% block body %}{% endblock %}</body></html>"""

FLASH = """{% with m=get_flashed_messages(with_categories=true) %}{% for c,t in m %}<div class="flash {{c}}">{{t}}</div>{% endfor %}{% endwith %}"""

AUTH = """{% extends 'base.html' %}{% block title %}{{ 'Sign up' if mode=='signup' else 'Login' }}{% endblock %}
{% block body %}<div class="wrap"><div class="auth card">
<div class="center" style="margin-bottom:18px"><div class="logo" style="font-size:28px">Pay Gateway</div>
<div class="mut">Auto payment verification</div></div>
<h1>{{ 'Create account' if mode=='signup' else 'Welcome back' }}</h1>
""" + FLASH + """
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Username</label><input name="username" required minlength="3" maxlength="30" autocomplete="username">
{% if mode=='signup' %}
<label>Phone number</label><input name="phone" required inputmode="numeric" pattern="[0-9+ ]{10,15}">
<label>Gmail</label><input name="email" type="email" required>
{% endif %}
<label>Password</label><input name="password" type="password" required minlength="6" autocomplete="{{ 'new-password' if mode=='signup' else 'current-password' }}">
<button class="btn full">{{ 'Sign up' if mode=='signup' else 'Login' }}</button></form>
<p class="center mut" style="margin-top:16px">
{% if mode=='signup' %}Already have an account? <a href="/login">Login</a>{% else %}New here? <a href="/signup">Create account</a>{% endif %}</p>
</div></div>{% endblock %}"""

DASH = """{% extends 'base.html' %}{% block title %}Dashboard{% endblock %}
{% block body %}<div class="nav"><div class="logo">Pay Gateway</div>
<div><span class="mut">{{u.username}}</span> &nbsp; <a href="/logout">Logout</a></div></div>
<div class="wrap">""" + FLASH + """
<div class="grid">
<div class="card stat"><span>Total payments</span><b>0</b></div>
<div class="card stat"><span>Successful</span><b>0</b></div>
<div class="card stat"><span>Gateways</span><b>0</b></div></div>
<div class="card"><h2>Your profile</h2>
<table><tr><th>Username</th><td>{{u.username}}</td></tr>
<tr><th>Phone</th><td>{{u.phone}}</td></tr><tr><th>Gmail</th><td>{{u.email}}</td></tr>
<tr><th>Joined</th><td>{{u.created}}</td></tr></table>
<h3 style="margin-top:22px">Change password</h3>
<form method="post" action="/change-password" class="row"><input type="hidden" name="csrf" value="{{csrf}}">
<div><label>Current password</label><input type="password" name="old" required></div>
<div><label>New password</label><input type="password" name="new" required minlength="6"></div>
<div><button class="btn">Update</button></div></form></div>
<p class="mut center" style="margin-top:18px">FamPay and Paytm gateways will be added in the next steps.</p>
</div>{% endblock %}"""

ADMIN_LOGIN = """{% extends 'base.html' %}{% block title %}Admin{% endblock %}
{% block body %}<div class="wrap"><div class="auth card"><h1>Admin login</h1>""" + FLASH + """
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}">
<label>Admin username</label><input name="username" required>
<label>Password</label><input name="password" type="password" required>
<button class="btn full">Login</button></form></div></div>{% endblock %}"""

ADMIN_NAV = """<div class="nav"><div class="logo">Admin panel</div><div><a href="/admin">Users</a> &nbsp; <a href="/admin/gateways">Gateways</a> &nbsp; <a href="/admin/settings">Settings</a> &nbsp; <a href="/admin/logout">Logout</a></div></div>"""

ADMIN = """{% extends 'base.html' %}{% block title %}Admin panel{% endblock %}
{% block body %}""" + ADMIN_NAV + """
<div class="wrap">""" + FLASH + """
{% if default_pw %}<div class="flash warn">ADMIN_PASSWORD is not set in Render env. Using the default password. Change it now.</div>{% endif %}
<div class="grid">
<div class="card stat"><span>Total users</span><b>{{stats.total}}</b></div>
<div class="card stat"><span>Active</span><b>{{stats.active}}</b></div>
<div class="card stat"><span>Banned</span><b>{{stats.banned}}</b></div></div>
<div class="card"><h2>Users</h2>
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
{% else %}<tr><td colspan="7" class="mut">No users yet.</td></tr>{% endfor %}</table></div></div>
<div class="card" style="margin-top:18px"><h2>Backup</h2>
<p class="mut">Render free disk resets on redeploy. Download a backup often, and restore it after a deploy.</p>
<a class="btn" href="/admin/backup">Download backup</a>
<form method="post" action="/admin/restore" enctype="multipart/form-data" class="row" style="margin-top:14px"><input type="hidden" name="csrf" value="{{csrf}}">
<input type="file" name="file" required><button class="btn gray" style="flex:0">Restore</button></form></div>
</div>{% endblock %}"""

TEMPLATES = {"base.html": BASE, "auth.html": AUTH, "dash.html": DASH,
             "admin_login.html": ADMIN_LOGIN, "admin.html": ADMIN}
