"""RockPower - one app: Audit, Quote, Kits and Jobs, Power hubs, Impact.
Rooted Upon The Rock Solar Installation | Soweto
Run:  pip install flask   then   python rockpower_combined.py   ->  http://127.0.0.1:5000
Data is saved in rockpower_combined.db. One customer = one phone number across kits, jobs and bookings.
"""
import sqlite3
from datetime import datetime, timedelta
from math import ceil
from urllib.parse import quote as urlquote
from flask import Flask, request, render_template_string, redirect, url_for

DB = "rockpower_combined.db"
COMPANY_WHATSAPP = "27627873997"  # country code, no + or spaces

# ---- Placeholders: replace with your real figures -------------------------
BUSINESS_WASTE = {"Spaza Shop": 0.30, "Salon": 0.30, "Chisanyama": 0.30, "Butchery": 0.30, "Car Wash": 0.30}
GEN_RAND_PER_HOUR, WEEKS_PER_MONTH, CAPTURE = 45, 4.33, 0.8
APPLIANCES = {"Fridge": 150, "Freezer": 200, "LED lights": 40, "Speaker / sound system": 120, "PlayStation": 150,
              "TV": 100, "WiFi router": 15, "Hair clippers": 50, "Phone charging station": 60, "Sewing machine": 100}
PANEL_W, SUN_HOURS, EFFICIENCY = 450, 4.5, 0.8
PANEL_COST, BATTERY_COST_PER_KWH, FIXED_COST = 3500, 6500, 9000
PLAN_MONTHS, PLAN_MARKUP, GEN_RAND_PER_KWH = 24, 0.15, 12.0
KITS = [
    {"name": "LITE - R199/wk", "powers": "Lights + WiFi + Till", "best": "Spaza / Salon", "need": "R800+"},
    {"name": "SHOP - R399/wk", "powers": "2 Fridges + Lights + CCTV", "best": "Chisanyama", "need": "R1600+"},
    {"name": "FULL - R699/wk", "powers": "Full Shop + Freezer + Battery", "best": "Butchery", "need": "R2800+"},
]
INSTALLERS = [  # Your installers
    # Add "rating" and "jobs" like {"name": "Full Name - Area", "skill": "Wiring", "rating": 4.8, "jobs": 12} only when they are real.
    {"name": "Victoria - Meadowlands Zone 5", "skill": "Wiring"},
    {"name": "Karabo - Dube", "skill": "Solar panels"},
    {"name": "Sunshine - Meadowlands Zone 3", "skill": "Battery"},
]
HUBS = [  # SAMPLE hubs: id, name, place, capacity kWh, status (online / low_power / maintenance / offline)
    {"id": 1, "name": "Vilakazi Street Hub", "loc": "Orlando West, Soweto", "cap": 40, "status": "online"},
    {"id": 2, "name": "Orlando East Youth Hub", "loc": "Near the community hall", "cap": 25, "status": "online"},
    {"id": 3, "name": "Diepkloof Spaza Hub", "loc": "Diepkloof Extension", "cap": 30, "status": "low_power"},
]
TARIFF_ZAR_PER_KWH = 4.5
SKILLS = ["Wiring", "Solar panels", "Battery", "General helper"]
TABS = [("audit", "Audit"), ("quote", "Quote"), ("kits", "Kits & Jobs"), ("power", "Power"), ("impact", "Impact")]
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.jinja_env.filters["rand"] = lambda n: "R{:,.0f}".format(n or 0)


class Obj(dict):
    __getattr__ = dict.get


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


with db() as c:
    c.executescript("""
    create table if not exists customers(phone text primary key, name text, role text);
    create table if not exists audits(id integer primary key, ts text, btype text, bill real, hours real, waste real, diesel real, loss real, saving real);
    create table if not exists quotes(id integer primary key, ts text, biz text, kwh real, panels int, battery real, cost real, monthly real, saving real);
    create table if not exists applications(id integer primary key, ts text, phone text, kit text);
    create table if not exists hires(id integer primary key, ts text, phone text, installer text);
    create table if not exists bookings(id integer primary key, ts text, phone text, hub int, kwh real, start text, end text, cost real);
    create table if not exists points(id integer primary key, ts text, phone text, pts int, why text);
    create table if not exists seekers(id integer primary key, ts text, phone text, skill text, area text);
    """)

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>RockPower</title>
<style>
:root{--night:#14213d;--sun:#ffc107;--card:#fff7cc;--paper:#faf8f2;--green:#1f8a4c;--red:#b3261e;--line:#e2dcc8}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--paper);color:#1a1a1a;line-height:1.5}
header{background:var(--night);color:#fff;padding:14px 16px 0}header h1{margin:0;font-size:1.5rem}header h1 span{color:var(--sun)}
header p{margin:2px 0 8px;color:#c9cfe0;font-size:.85rem}
nav{display:flex;gap:4px;overflow-x:auto}nav a{color:#c9cfe0;text-decoration:none;padding:10px 13px;border-radius:8px 8px 0 0;font-weight:600;white-space:nowrap}
nav a.on{background:var(--paper);color:var(--night)}
main{max-width:640px;margin:0 auto;padding:16px 16px 60px}h2{font-size:1.35rem;margin:.3em 0}h3{margin:16px 0 4px}
label{display:block;font-weight:600;margin:12px 0 4px}
input,select{width:100%;padding:12px;font:inherit;border:1.5px solid var(--line);border-radius:8px;background:#fff}
input[type=range]{padding:0}input:focus,select:focus,button:focus-visible,a:focus-visible{outline:3px solid var(--sun)}
button,a.btn{display:block;margin-top:16px;width:100%;padding:14px;font:inherit;font-weight:800;background:var(--sun);color:var(--night);border:0;border-radius:8px;text-align:center;text-decoration:none}
a.wa{background:#25d366;color:#062b14}
.big-card{background:var(--card);padding:18px;border-radius:15px;border-left:5px solid var(--sun);margin:16px 0}
.big-card h3{margin:0 0 6px}.big-card small,.note{color:#555;font-size:.9rem}
.msg{padding:12px;border-radius:8px;margin:12px 0;background:#e3f4ea;color:#0e5a30}.msg.bad{background:#fbe5e3;color:var(--red)}
.item{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px;margin:10px 0}.item b{display:block}
.row{display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--line);padding:8px 0}.row span{flex:1}.row input{width:80px;text-align:center}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}.stats div{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}
.stats b{display:block;font-size:1.35rem}.online{color:var(--green)}.low_power{color:#a15c00}.maintenance,.offline{color:var(--red)}
table{width:100%;border-collapse:collapse;background:#fff}td,th{padding:8px;border-bottom:1px solid var(--line);text-align:left;font-size:.9rem}
.top{display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:4px 12px}.wachip{display:inline-flex;align-items:center;gap:8px;background:#25d366;color:#062b14;font-weight:800;text-decoration:none;padding:8px 14px;border-radius:999px;font-size:.9rem;margin:2px 0 10px}.wachip:focus-visible{outline:3px solid #ffc107;outline-offset:2px}
</style></head><body>
<header><div class="top"><div><h1>Rock<span>Power</span></h1><p>Rooted Upon The Rock Solar Installation | Soweto</p></div>
{% if wa_top %}<a class="wachip" target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp" href="{{ wa_top.href }}"><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 20.5l1.4-4.4A8.5 8.5 0 1 1 8 19.2z"/><path d="M9 8.5c0 3.800 2.700 6.500 6.500 6.500" stroke-width="2.300"/></svg><span>{{ wa_top.label }}</span></a>{% endif %}</div>
<nav>{% for k, l in tabs %}<a href="/?tab={{ k }}" class="{{ 'on' if tab == k }}">{{ l }}</a>{% endfor %}</nav></header>
<main>
{% if msg %}<div class="msg {{ '' if ok else 'bad' }}" role="status">{{ msg }}</div>
{% if ok and wa %}<a class="btn wa" target="_blank" rel="noopener" href="{{ wa }}">Send on WhatsApp</a>{% endif %}{% endif %}

{% if tab == 'audit' %}
<h2>60-second energy waste audit</h2><p class="note">Cut costs. Create jobs. Keep power.</p>
<form method="post" action="/audit">
<label for="btype">Business type</label><select id="btype" name="btype">{% for b in btypes %}<option>{{ b }}</option>{% endfor %}</select>
<label for="bill">Monthly Eskom bill (R)</label><input id="bill" name="bill" type="number" min="500" max="20000" step="50" value="3000" inputmode="numeric">
<label for="hours">Hours without power per week: <span id="hv">12</span></label>
<input id="hours" name="hours" type="range" min="0" max="60" value="12" oninput="hv.textContent=this.value">
<button>Calculate my waste</button></form>
{% if a %}<div class="big-card"><h3>You lose {{ a.loss|rand }} a month</h3>
<p>Wasted energy: {{ a.waste|rand }}<br>Generator or diesel: {{ a.diesel|rand }}<br><b>RockPower can save you about {{ a.saving|rand }} a month</b></p>
<small>Estimate based on {{ (a.waste / a.bill * 100)|round|int }}% energy waste and R{{ gen }} an hour for a generator. A site visit gives the real figure.</small></div>
<a class="btn" href="/?tab=quote">Next: get a full solar quote</a>{% endif %}

{% elif tab == 'quote' %}
<h2>Solar quote</h2><p class="note">Enter the hours each item runs per day. Leave blank if you don't use it.</p>
<form method="post" action="/quote"><label for="biz">Business name</label><input id="biz" name="biz" value="{{ me_name }}" required>
{% for n, w in appliances.items() %}<div class="row"><span>{{ n }} <small>{{ w }}W</small></span>
<input type="number" name="a{{ loop.index0 }}" min="0" max="24" step="0.5" inputmode="decimal" aria-label="{{ n }} hours per day" placeholder="hrs"></div>{% endfor %}
<button>Get my solar quote</button></form>
{% if q %}<div class="big-card"><h3>{{ q.biz }}</h3><p>Estimated saving: <b>{{ q.saving|rand }} a month</b> compared with a generator</p></div>
<div class="stats"><div>Daily energy<b>{{ '%.1f'|format(q.kwh) }} kWh</b></div><div>Panels<b>{{ q.panels }} x {{ panel_w }}W</b></div>
<div>Battery<b>{{ q.battery }} kWh</b></div><div>Total price<b>{{ q.cost|rand }}</b></div></div>
<p><b>Or pay {{ q.monthly|rand }} a month for {{ months }} months.</b></p><p class="note">Estimate only. The final price depends on a site visit.</p>
<a class="btn wa" target="_blank" rel="noopener" href="{{ qwa }}">Share quote on WhatsApp</a><a class="btn" href="/?tab=kits">Next: apply for a kit</a>{% endif %}

{% elif tab == 'kits' %}
<h2>Pay-as-you-save kits</h2><p class="note">No upfront cost. You pay each week from your savings.</p>
{% for k in kits %}<div class="item"><b>{{ k.name }}</b>Powers: {{ k.powers }}<br>Best for: {{ k.best }}<br>Monthly saving needed: {{ k.need }}</div>{% endfor %}
<form method="post" action="/apply"><label for="kit">Choose a kit</label><select id="kit" name="kit">{% for k in kits %}<option>{{ k.name }}</option>{% endfor %}</select>
<label for="n1">Your name</label><input id="n1" name="name" value="{{ me_name }}" required>
<label for="p1">Phone number (WhatsApp)</label><input id="p1" name="phone" type="tel" value="{{ me_phone }}" required>
<button>Apply for a no-upfront-cost install</button></form>
<h2>Youth installers</h2><p class="note">Every install is a township youth job.</p>
{% for i in installers %}<div class="item"><b>{{ i.name }}</b>{{ i.skill }}{% if i.rating %} &middot; &#9733; {{ i.rating }}{% endif %}{% if i.jobs %} &middot; {{ i.jobs }} jobs{% endif %}</div>{% endfor %}
<form method="post" action="/hire"><label for="inst">Installer</label><select id="inst" name="installer">{% for i in installers %}<option>{{ i.name }}</option>{% endfor %}</select>
<label for="n2">Your name</label><input id="n2" name="name" value="{{ me_name }}" required>
<label for="p2">Phone number</label><input id="p2" name="phone" type="tel" value="{{ me_phone }}" required>
<button>Hire local installer</button></form>
<h2>Looking for work?</h2><p class="note">Young people can join our installer list. Tell us what you can do and where you live.</p>
<form method="post" action="/job"><label for="skill">What can you do?</label><select id="skill" name="skill">{% for k in skills %}<option>{{ k }}</option>{% endfor %}</select>
<label for="area">Your area</label><input id="area" name="area" placeholder="e.g. Meadowlands Zone 5" required>
<label for="n4">Your name</label><input id="n4" name="name" value="{{ me_name }}" required>
<label for="p4">Phone number</label><input id="p4" name="phone" type="tel" value="{{ me_phone }}" required>
<button>Register for work</button></form>

{% elif tab == 'power' %}
<h2>Solar hubs</h2><p class="note">Hubs keep businesses and youth venues running through load shedding. Sample hubs shown.</p>
{% for h in hubs %}<div class="item"><b>{{ h.name }}</b>{{ h.loc }}<br>{{ h.cap }} kWh capacity &middot; <span class="{{ h.status }}">{{ h.status.replace('_', ' ') }}</span></div>{% endfor %}
<h3>Book power</h3>
<form method="post" action="/book"><label for="n3">Your name</label><input id="n3" name="name" value="{{ me_name }}" required>
<label for="p3">Phone number</label><input id="p3" name="phone" type="tel" value="{{ me_phone }}" required>
<label for="role">I am a</label><select id="role" name="role"><option value="small_business">Small business owner</option><option value="youth_organizer">Youth event organizer</option></select>
<label for="hub">Hub</label><select id="hub" name="hub_id">{% for h in hubs %}<option value="{{ h.id }}">{{ h.name }}</option>{% endfor %}</select>
<label for="kwh">Power needed (kWh)</label><input id="kwh" name="kwh" type="number" step="0.5" min="0.5" value="5" inputmode="decimal">
<label for="start">Start</label><input id="start" name="start" type="datetime-local" value="{{ default_start }}" required>
<label for="bh">Hours</label><input id="bh" name="hours" type="number" step="0.5" min="0.5" max="12" value="3">
<button>Book power</button></form>
<h3>Green points leaders</h3>
{% if leaders %}<table><tr><th>Name</th><th>Points</th></tr>{% for r in leaders %}<tr><td>{{ r['name'] }}</td><td>{{ r['t'] }}</td></tr>{% endfor %}</table>
{% else %}<p class="note">No points yet. Book power to earn the first ones.</p>{% endif %}

{% else %}
<h2>Impact dashboard</h2>
<div class="stats"><div>Businesses audited<b>{{ s.audits }}</b></div><div>Monthly savings found<b>{{ s.saving|rand }}</b></div>
<div>Quotes made<b>{{ s.quotes }}</b></div><div>Kit applications<b>{{ s.apps }}</b></div>
<div>Installer job requests<b>{{ s.hires }}</b></div><div>Power bookings<b>{{ s.books }}</b></div>
<div>kWh booked<b>{{ '%.0f'|format(s.kwh) }}</b></div><div>Customers<b>{{ s.customers }}</b></div><div>Work seekers<b>{{ s.seekers }}</b></div></div>
<p class="note">These numbers come from real use of this app. Green economy is not a future cost. It is a present cost township businesses already bear, and Rooted Upon The Rock turns that waste into jobs.</p>
{% endif %}
</main></body></html>"""


def row(c, table, rid):
    r = c.execute(f"select * from {table} where id=?", (rid or 0,)).fetchone()
    return Obj(r) if r else None


def pretty_phone(n):
    return f"+27 {n[2:4]} {n[4:7]} {n[7:]}" if n.startswith("27") and len(n) == 11 else "+" + n


@app.get("/")
def home():
    tab = request.args.get("tab", "audit")
    tab = tab if tab in dict(TABS) else "audit"
    with db() as c:
        a, q = row(c, "audits", request.args.get("audit")), row(c, "quotes", request.args.get("q"))
        one = lambda sql: c.execute(sql).fetchone()[0]
        s = Obj(audits=one("select count(*) from audits"), saving=one("select coalesce(sum(saving),0) from audits"),
                quotes=one("select count(*) from quotes"), apps=one("select count(*) from applications"),
                hires=one("select count(*) from hires"), books=one("select count(*) from bookings"),
                kwh=one("select coalesce(sum(kwh),0) from bookings"), customers=one("select count(*) from customers"),
                seekers=one("select count(*) from seekers"))
        leaders = c.execute("select c.name, sum(p.pts) t from points p join customers c on c.phone=p.phone "
                            "group by p.phone order by t desc limit 5").fetchall()
    msg = request.args.get("msg")
    wa = f"https://wa.me/{COMPANY_WHATSAPP}?text=" + urlquote(request.args.get("wat") or "Hi, I used the RockPower app.") if COMPANY_WHATSAPP and msg else None
    qwa = ""
    if q:
        text = (f"RockPower quote for {q.biz}\nEnergy use: {q.kwh:.1f} kWh/day\nSystem: {q.panels} x {PANEL_W}W panels + {q.battery} kWh battery\n"
                f"Price: R{q.cost:,.0f} (or R{q.monthly:,.0f}/month for {PLAN_MONTHS} months)\nEstimated saving: R{q.saving:,.0f}/month vs generator")
        qwa = "https://wa.me/?text=" + urlquote(text)
    default = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return render_template_string(
        PAGE, tab=tab, tabs=TABS, wa_top=({"href": "https://wa.me/" + COMPANY_WHATSAPP + "?text=" + urlquote("Hi, I found you on the RockPower app."),
                                         "label": pretty_phone(COMPANY_WHATSAPP)} if COMPANY_WHATSAPP else None), a=a, q=q, s=s, leaders=leaders, msg=msg, ok=request.args.get("ok") == "1", wa=wa, qwa=qwa,
        btypes=BUSINESS_WASTE, skills=SKILLS, appliances=APPLIANCES, kits=KITS, installers=INSTALLERS, hubs=HUBS, gen=GEN_RAND_PER_HOUR,
        panel_w=PANEL_W, months=PLAN_MONTHS, default_start=default.strftime("%Y-%m-%dT%H:%M"),
        me_name=request.cookies.get("rp_name", ""), me_phone=request.cookies.get("rp_phone", ""))


def back(tab, msg, ok, name="", phone="", wat=None):
    r = redirect(url_for("home", tab=tab, msg=msg, ok=int(ok), wat=wat))
    if ok and name:
        r.set_cookie("rp_name", name, max_age=31536000)
        r.set_cookie("rp_phone", phone, max_age=31536000)
    return r


def customer(c, name, phone, role="small_business"):
    c.execute("insert or ignore into customers(phone,name,role) values(?,?,?)", (phone, name, role))


def clean(phone):
    return "".join(ch for ch in phone if ch.isdigit() or ch == "+")


@app.post("/audit")
def audit():
    f = request.form
    try:
        bill, hours = min(20000.0, max(500.0, float(f["bill"]))), min(60.0, max(0.0, float(f["hours"])))
    except (KeyError, ValueError):
        return redirect(url_for("home", tab="audit"))
    btype = f.get("btype") if f.get("btype") in BUSINESS_WASTE else "Spaza Shop"
    waste, diesel = bill * BUSINESS_WASTE[btype], hours * WEEKS_PER_MONTH * GEN_RAND_PER_HOUR
    with db() as c:
        cur = c.execute("insert into audits(ts,btype,bill,hours,waste,diesel,loss,saving) values(?,?,?,?,?,?,?,?)",
                        (datetime.now().isoformat(), btype, bill, hours, waste, diesel, waste + diesel, (waste + diesel) * CAPTURE))
    return redirect(url_for("home", tab="audit", audit=cur.lastrowid))


@app.post("/quote")
def quote():
    f = request.form
    wh = 0.0
    for i, w in enumerate(APPLIANCES.values()):
        try:
            wh += w * min(24.0, max(0.0, float(f.get(f"a{i}") or 0)))
        except ValueError:
            pass
    kwh = wh / 1000
    panels = max(1, ceil(kwh / (PANEL_W / 1000 * SUN_HOURS * EFFICIENCY)))
    battery = round(kwh * 0.6, 1)
    cost = FIXED_COST + panels * PANEL_COST + battery * BATTERY_COST_PER_KWH
    with db() as c:
        cur = c.execute("insert into quotes(ts,biz,kwh,panels,battery,cost,monthly,saving) values(?,?,?,?,?,?,?,?)",
                        (datetime.now().isoformat(), f.get("biz", "").strip() or "My business", kwh, panels, battery, cost,
                         cost * (1 + PLAN_MARKUP) / PLAN_MONTHS, kwh * 30 * GEN_RAND_PER_KWH))
    return redirect(url_for("home", tab="quote", q=cur.lastrowid))


@app.post("/apply")
def apply():
    f = request.form
    name, phone, kit = f.get("name", "").strip(), clean(f.get("phone", "")), f.get("kit")
    if not name or not phone or kit not in [k["name"] for k in KITS]:
        return back("kits", "Please add your name, phone number and a kit.", False)
    with db() as c:
        customer(c, name, phone)
        c.execute("insert into applications(ts,phone,kit) values(?,?,?)", (datetime.now().isoformat(), phone, kit))
    text = f"Hi Rooted Upon The Rock, I would like to apply for the {kit} solar kit.\nName: {name}\nPhone: {phone}"
    return back("kits", f"Almost done, {name}! Tap the green button to send your application on WhatsApp. We only receive it once you send it, then we reply on WhatsApp.", True, name, phone, text)


@app.post("/hire")
def hire():
    f = request.form
    name, phone, inst = f.get("name", "").strip(), clean(f.get("phone", "")), f.get("installer")
    if not name or not phone or inst not in [i["name"] for i in INSTALLERS]:
        return back("kits", "Please add your name, phone number and an installer.", False)
    with db() as c:
        customer(c, name, phone)
        c.execute("insert into hires(ts,phone,installer) values(?,?,?)", (datetime.now().isoformat(), phone, inst))
    text = f"Hi Rooted Upon The Rock, I would like to hire {inst}.\nName: {name}\nPhone: {phone}"
    return back("kits", f"Almost done, {name}! Tap the green button to send your request on WhatsApp. We only receive it once you send it.", True, name, phone, text)


@app.post("/job")
def job():
    f = request.form
    name, phone = f.get("name", "").strip(), clean(f.get("phone", ""))
    skill, area = f.get("skill"), f.get("area", "").strip()
    if not name or not phone or not area or skill not in SKILLS:
        return back("kits", "Please add your name, phone number, skill and area.", False)
    with db() as c:
        customer(c, name, phone)
        c.execute("insert into seekers(ts,phone,skill,area) values(?,?,?,?)", (datetime.now().isoformat(), phone, skill, area))
    text = f"Hi Rooted Upon The Rock, I am looking for installer work.\nName: {name}\nPhone: {phone}\nSkill: {skill}\nArea: {area}"
    return back("kits", f"Thanks {name}! Tap the green button to send your details on WhatsApp. We only receive them once you send them.", True, name, phone, text)


@app.post("/book")
def book():
    f = request.form
    name, phone = f.get("name", "").strip(), clean(f.get("phone", ""))
    try:
        kwh, hours = float(f["kwh"]), float(f["hours"])
        start, hub = datetime.fromisoformat(f["start"]), next(h for h in HUBS if h["id"] == int(f["hub_id"]))
    except (KeyError, ValueError, StopIteration):
        return back("power", "Please check your details and try again.", False)
    role = f.get("role") if f.get("role") in ("small_business", "youth_organizer") else "small_business"
    if not name or not phone or kwh <= 0 or not 0.5 <= hours <= 12:
        return back("power", "Please fill in your name, phone, power and hours.", False)
    if hub["status"] in ("maintenance", "offline"):
        return back("power", "That hub is not taking bookings right now. Try another hub.", False)
    s_iso, e_iso = start.isoformat(), (start + timedelta(hours=hours)).isoformat()
    with db() as c:
        used = c.execute("select coalesce(sum(kwh),0) from bookings where hub=? and start<? and end>?",
                         (hub["id"], e_iso, s_iso)).fetchone()[0]
        free = hub["cap"] - used
        if kwh > free:
            return back("power", f"Only {max(free, 0):.1f} kWh is free at that time. Lower the amount or pick another time.", False)
        customer(c, name, phone, role)
        cost = round(kwh * TARIFF_ZAR_PER_KWH, 2)
        daytime = 9 <= start.hour < 15
        pts = int(kwh * (5 if daytime else 2)) or 1
        c.execute("insert into bookings(ts,phone,hub,kwh,start,end,cost) values(?,?,?,?,?,?,?)",
                  (datetime.now().isoformat(), phone, hub["id"], kwh, s_iso, e_iso, cost))
        c.execute("insert into points(ts,phone,pts,why) values(?,?,?,?)",
                  (datetime.now().isoformat(), phone, pts, "Daytime solar use" if daytime else "Evening solar use"))
    text = f"Hi Rooted Upon The Rock, I booked {kwh:g} kWh at {hub['name']} on {start:%d %b %H:%M} for {hours:g} hours.\nName: {name}\nPhone: {phone}"
    return back("power", f"Booked {kwh:g} kWh at {hub['name']} for R{cost:.2f}. You earned {pts} green points. Tap the green button to confirm your booking with us on WhatsApp.", True, name, phone, text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
