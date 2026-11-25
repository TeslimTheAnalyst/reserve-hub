import zlib
from datetime import date, datetime, time
from html import escape as esc

import pandas as pd
import streamlit as st

st.set_page_config(page_title="ReserveHub", page_icon="🅿️", layout="wide")

# ---------------------------------------------------------------
# 1. SETTINGS (change the data source, the name and the colours here)
# ---------------------------------------------------------------
SOURCE = "reserve_demo_data.csv"      # later: your Google Sheet CSV link
BRAND_A, BRAND_B = "Reserve", "Hub"
TAGLINE = "Every pass under control"

STATES = ["Tied up", "Sold", "Cancelled", "Lost"]
PRESETS = {                            # brand colour, sidebar colour, page background
    "Ocean": ("#2563eb", "#1e3a8a", "#f3f5f9"),
    "Emerald": ("#10b981", "#064e3b", "#f0f7f4"),
    "Violet": ("#7c3aed", "#3b1d8f", "#f4f2fb"),
    "Sunset": ("#f97316", "#7c2d12", "#faf3ee"),
    "Rose": ("#e11d48", "#881337", "#fbf1f3"),
    "Midnight": ("#38bdf8", "#0b1220", "#e9eef5"),
}
PILL = {"CANCEL NOW": "red", "CANCEL SOON": "yellow", "ON TRACK": "blue",
        "MISSED": "orange", "CANCELLED": "grey", "DONE": "green"}

# ---------------------------------------------------------------
# 2. THEME (colour grading lives in the 🎨 button at the top)
# ---------------------------------------------------------------
ss = st.session_state


def use_preset():
    ss["c_brand"], ss["c_side"], ss["c_bg"] = PRESETS[ss["preset"]]


if "c_brand" not in ss:
    ss["preset"] = "Ocean"
    use_preset()

# ---- navigation drawer state (True = sidebar slid in) ----
if "nav_open" not in ss:
    ss["nav_open"] = False          # default closed; set to True to start open

PRIMARY, SIDE, BG = ss["c_brand"], ss["c_side"], ss["c_bg"]
COL = {"Tied up": "#94a3b8", "Sold": PRIMARY, "Cancelled": "#ef4444", "Lost": "#f59e0b"}


def shade(hex_, f):
    """f > 0 makes the colour lighter, f < 0 makes it darker."""
    r, g, b = [int(hex_[i:i + 2], 16) for i in (1, 3, 5)]
    mix = lambda c: int(c + (255 - c) * f) if f > 0 else int(c * (1 + f))
    return "#%02x%02x%02x" % (mix(r), mix(g), mix(b))


THEME_VARS = (":root{--brand:%s;--brand-soft:%s;--brand-light:%s;--side-top:%s;--side-bot:%s;--bg:%s;"
              "--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e6eaf2}"
              % (PRIMARY, shade(PRIMARY, .88), shade(PRIMARY, .55), shade(SIDE, .12), shade(SIDE, -.3), BG))

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
.stApp{background:var(--bg);font-family:'Poppins',sans-serif;color:var(--ink)}
input,button,textarea,select{font-family:inherit}
[data-testid="stHeader"],[data-testid="stToolbar"],footer,#MainMenu,[data-testid="stSidebarHeader"],[data-testid="stSidebarCollapseButton"]{display:none!important}
.block-container{padding:0 2rem 2.5rem!important;max-width:100%!important}

/* ---- sidebar is now a fixed drawer that slides in/out ---- */
section[data-testid="stSidebar"]{position:fixed!important;left:0!important;top:0!important;height:100vh!important;
width:280px!important;min-width:280px!important;background:linear-gradient(180deg,var(--side-top),var(--side-bot));
border:0;z-index:999998!important;box-shadow:0 12px 44px #0f172a55;transform:translateX(-106%);
-webkit-transform:translateX(-106%);transition:transform .3s ease}
section[data-testid="stSidebar"]>div{background:transparent;height:100%}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding:20px 16px;height:100%;overflow-y:auto}
.logo{display:flex;align-items:center;gap:12px;margin:4px 6px 26px}
.lg{width:44px;height:44px;border-radius:12px;background:#fff;display:grid;place-items:center;font-size:20px;font-weight:700;color:var(--brand)}
.lt{color:#fff;font-size:24px;font-weight:600;line-height:1}.lt b{color:var(--brand-light)}
.ls{color:#ffffffb3;font-size:11px;margin-top:5px}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:8px}
section[data-testid="stSidebar"] div[role="radiogroup"] label{width:100%;margin:0;padding:13px 16px;border-radius:12px;cursor:pointer;transition:background .15s}
section[data-testid="stSidebar"] div[role="radiogroup"] label>div:first-child{display:none}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{color:#e8eeff;font-size:15px;font-weight:500}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:#ffffff1a}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:var(--brand);box-shadow:0 6px 16px #00000033}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{color:#fff;font-weight:600}
.promo{margin-top:30px;padding:18px;border-radius:16px;background:#ffffff1a;border:1px solid #ffffff2e;color:#fff}
.promo .pn{font-size:32px;font-weight:700;line-height:1.1}.promo .pt{font-size:13px;color:#ffffffcc;margin-top:6px}

/* ---- hamburger button in the top bar ---- */
.st-key-nav_btn button{width:40px;height:40px;border-radius:10px!important;border:1px solid var(--line)!important;
background:var(--card)!important;color:var(--ink)!important;font-size:17px!important;line-height:1!important;
box-shadow:0 1px 3px #1018280a}
/* ---- backdrop (invisible full-screen button that closes the drawer) ---- */
.st-key-nav_backdrop,.st-key-nav_backdrop>div{position:fixed!important;top:0!important;left:0!important;
width:100vw!important;height:100vh!important;margin:0!important;padding:0!important;z-index:999997!important}
.st-key-nav_backdrop button{position:fixed!important;top:0!important;left:0!important;width:100vw!important;
height:100vh!important;background:#0f172a!important;opacity:.45!important;border:0!important;border-radius:0!important;
cursor:default!important}
.st-key-nav_backdrop button p{display:none}

.st-key-topbar{background:var(--card);margin:0 -2rem 26px;padding:14px 2rem;border-bottom:1px solid var(--line);box-shadow:0 2px 10px #1018280d}
.datepill,.bell{display:flex;align-items:center;gap:8px;font-weight:500;color:var(--ink);font-size:15px;white-space:nowrap}
.bell{font-size:20px;position:relative;justify-content:center}
.bell .dot{position:absolute;top:-2px;right:calc(50% - 14px);width:10px;height:10px;border-radius:50%;background:#ef4444;border:2px solid #fff}
.testtag{background:#fef3c7;color:#92400e;font-size:10px;font-weight:700;padding:2px 6px;border-radius:6px}
.prof{display:flex;align-items:center;gap:12px;justify-content:flex-end}
.av{position:relative;width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--brand),var(--side-top));color:#fff;display:grid;place-items:center;font-weight:600}
.av:after{content:"";position:absolute;right:0;bottom:1px;width:11px;height:11px;border-radius:50%;background:#22c55e;border:2px solid #fff}
.prof b{display:block;font-size:14px;color:var(--ink)}.prof small{color:var(--muted);font-size:12px}
div[data-baseweb="select"]>div,
div[data-baseweb="select"]>div>div,
div[data-baseweb="input"],
div[data-baseweb="input"]>div,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input{border-radius:10px!important;border:1px solid var(--line)!important;background:var(--card)!important;background-color:var(--card)!important;color:var(--ink)!important}
div[data-baseweb="select"] span,div[data-baseweb="select"] div,div[data-baseweb="select"] svg{color:var(--ink)!important;fill:var(--ink)!important}
input{background:var(--card)!important;background-color:var(--card)!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important}
input::placeholder{color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important;opacity:1}
.st-key-topbar div[data-baseweb="input"],
.st-key-topbar div[data-baseweb="input"]>div,
.st-key-topbar input{background:var(--bg)!important;background-color:var(--bg)!important}
[data-testid="stPopover"] button{border-radius:10px!important;border:1px solid var(--line)!important;background:var(--card)!important;color:var(--ink)!important;font-weight:500!important}
[data-testid="stPopover"] button p,[data-testid="stPopover"] button span{color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important}
[data-testid="stPopoverBody"],div[data-baseweb="popover"]>div{background:var(--card)!important;color:var(--ink)!important;border:1px solid var(--line)!important;border-radius:12px!important}
[data-testid="stPopoverBody"] label,[data-testid="stPopoverBody"] p,[data-testid="stPopoverBody"] span{color:var(--ink)!important}
ul[role="listbox"],div[data-baseweb="menu"]{background:var(--card)!important;color:var(--ink)!important;border:1px solid var(--line)!important}
li[role="option"]{color:var(--ink)!important;background:var(--card)!important}
li[role="option"]:hover{background:var(--brand-soft)!important}
button[kind="primary"],[data-testid="stBaseButton-primary"]{background:var(--brand)!important;border:0!important;color:#fff!important;border-radius:10px!important;font-weight:600}
button[kind="primary"] *, [data-testid="stBaseButton-primary"] *{color:#fff!important;-webkit-text-fill-color:#fff!important}
.pgt{font-size:34px;font-weight:700;color:var(--ink);line-height:1.15}.pgs{font-size:16px;color:var(--muted);margin-top:2px}
[class*="st-key-card"]{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;box-shadow:0 1px 3px #1018280a}
.ct{font-size:17px;font-weight:600;color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:4px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:0 1px 3px #1018280a}
.kt{display:flex;align-items:center;gap:14px}.ki{width:46px;height:46px;border-radius:12px;display:grid;place-items:center;font-size:18px;font-weight:700}
.kl{font-size:13px;font-weight:600;color:var(--ink)}.kv{font-size:28px;font-weight:700;color:var(--ink);line-height:1.2}
.kv small{font-size:12px;font-weight:500;color:var(--muted);margin-left:6px}
.kb{display:flex;justify-content:space-between;align-items:flex-end;margin-top:12px;font-size:12px}
.dl{font-weight:700}.dl.up{color:#16a34a}.dl.dn{color:#ef4444}.muted{color:var(--muted);font-size:13px}
.tw{overflow-x:auto;margin-top:12px}.tbl{width:100%;border-collapse:collapse;min-width:820px}
.tbl th{background:var(--brand-soft);color:var(--ink);font-weight:600;font-size:14px;text-align:left;padding:14px 16px;white-space:nowrap}
.tbl th:first-child{border-radius:10px 0 0 10px}.tbl th:last-child{border-radius:0 10px 10px 0}
.tbl td{padding:14px 16px;border-bottom:1px solid var(--line);font-size:14px;color:var(--ink);vertical-align:middle}
.tbl td small{color:var(--muted);font-size:12px}.tbl tr:hover td{background:#f8fafc}
.idc{color:var(--brand)!important;font-weight:600}.dots{font-size:22px;color:var(--muted);text-align:center}
.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:7px;font-size:10.5px;font-weight:700;letter-spacing:.4px;white-space:nowrap}
.pill:before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor}
.pill.red{background:#fee2e2;color:#b91c1c}.pill.yellow{background:#fef3c7;color:#b45309}.pill.blue{background:var(--brand-soft);color:var(--brand)}
.pill.green{background:#dcfce7;color:#15803d}.pill.orange{background:#ffedd5;color:#c2410c}.pill.grey{background:#f1f5f9;color:#475569}
.mini{display:flex;height:6px;width:110px;border-radius:99px;overflow:hidden;background:var(--line);margin-top:6px}.mini i{display:block;height:100%}
.alarm{display:flex;align-items:center;gap:14px;border-radius:14px;padding:14px 18px;margin-bottom:12px;font-size:14.5px}
.alarm.red{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}.alarm.amber{background:#fffbeb;border:1px solid #fde68a;color:#92400e}
.blink{width:12px;height:12px;border-radius:50%;background:currentColor;flex:none;animation:pulse 1.4s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 #ef444466}70%{box-shadow:0 0 0 10px #ef444400}100%{box-shadow:0 0 0 0 #ef444400}}
.empty,.empty-card{color:var(--muted);text-align:center;padding:26px 10px}
.empty-card{background:var(--card);border:1px dashed var(--line);border-radius:16px;margin-top:14px}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0 14px;font-size:12px;color:var(--muted)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.hrow{display:grid;grid-template-columns:140px 1fr 70px;gap:12px;align-items:center;margin:11px 0;font-size:13px}
.hl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink)}.hrow b{text-align:right;color:var(--ink)}
.htrack{display:flex;height:14px;background:var(--bg);border-radius:99px;overflow:hidden}.htrack i{display:block;height:100%}
.vwrap{display:flex;gap:10px;align-items:flex-end;overflow-x:auto;padding-bottom:4px}
.vcol{flex:1;min-width:48px;display:flex;flex-direction:column;align-items:center;gap:6px;font-size:12px;color:var(--muted)}.vcol b{color:var(--ink);font-size:12px}
.vtrack{display:flex;flex-direction:column-reverse;height:150px;width:70%;max-width:44px;border-radius:8px 8px 4px 4px;overflow:hidden;background:var(--bg)}.vtrack i{display:block;width:100%}
@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi,.kpis>div{min-width:0!important;max-width:100%!important}
@media(max-width:640px){
.block-container{padding:1rem .85rem 2rem!important}
.st-key-topbar{margin:0 -.85rem 16px!important;padding:12px .85rem!important}
.st-key-topbar [data-testid="stHorizontalBlock"]{gap:8px!important}
.kpis{grid-template-columns:1fr!important;gap:12px!important}
.kpi{padding:14px 16px!important}
.kv{font-size:24px!important}
.pgt{font-size:24px!important}
.pgs{font-size:13.5px!important}
[class*="st-key-card"]{padding:14px!important;border-radius:14px!important}
.ct{font-size:15px!important}
.prof{justify-content:flex-start!important;margin-top:4px}
.datepill{font-size:13.5px!important}
.hrow{grid-template-columns:95px 1fr 58px!important;gap:8px!important;font-size:12px!important}
.alarm{padding:11px 14px!important;font-size:13px!important;gap:10px!important}
}
 @media(max-width:768px){
.st-key-nav_btn{width:auto!important}
.st-key-nav_btn button{
width:auto!important;
min-width:86px!important;
height:38px!important;
padding:0 12px!important;
border-radius:10px!important;
border:1.5px solid var(--brand)!important;
background:var(--brand-soft)!important;
color:var(--brand)!important;
-webkit-text-fill-color:var(--brand)!important;
font-size:13.5px!important;
font-weight:700!important;
display:inline-flex!important;
align-items:center!important;
gap:6px!important;
box-shadow:0 2px 6px #10182814!important
}
.st-key-nav_btn button::after{
content:"Menu";
font-size:13px;
font-weight:700;
letter-spacing:.2px
}
}"""
st.markdown(f"<style>{THEME_VARS}{' '.join(CSS.split())}</style>", unsafe_allow_html=True)
if ss["nav_open"]:
    st.markdown(
        "<style>"
        "section[data-testid='stSidebar']{"
        "display:block!important;visibility:visible!important;"
        "transform:translateX(0)!important;-webkit-transform:translateX(0)!important;"
        "}"
        "</style>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------
# 3. LOAD AND CLEAN THE DATA
# ---------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    d = pd.read_csv(SOURCE).dropna(how="all")
    d["Date of Event"] = pd.to_datetime(d["Date of Event"], format="%m/%d/%Y")
    d["Buying Price"] = pd.to_numeric(d["Buying Price"])
    d["Status"] = d["Status"].astype(str).str.strip().str.title()
    d["Event Start"] = pd.to_datetime(
        d["Date of Event"].dt.strftime("%Y-%m-%d") + " " + d["Event Start Time"],
        format="%Y-%m-%d %I:%M %p",
    )
    return d


df = load_data()

# the clock (use 🎨 > "Test the alarm" to pretend it is another date or time)
if ss.get("test"):
    now = datetime.combine(ss.get("p_date", date.today()), ss.get("p_time", time(14, 0)))
else:
    now = datetime.now()
today = pd.Timestamp(now.date())

# Tied up = unsold and the event has not started (cancel it in time!)  |  Lost = unsold and already started
df["State"] = df["Status"]
unsold = df["Status"] == "Unsold"
df.loc[unsold & (df["Event Start"] >= now), "State"] = "Tied up"
df.loc[unsold & (df["Event Start"] < now), "State"] = "Lost"


# ---------------------------------------------------------------
# 4. HELPERS
# ---------------------------------------------------------------
def money(v):
    return f"${v:,.0f}"


def hhmm(ts):
    return ts.strftime("%I:%M %p").lstrip("0")


def money_of(data, state):
    return data.loc[data["State"] == state, "Buying Price"].sum()


def sell_through(data):
    sold = (data["State"] == "Sold").sum()
    total = sold + data["State"].isin(["Tied up", "Lost"]).sum()
    return f"{sold / total:.0%}" if total else "n/a"


def countdown(m):
    if m < 0:
        return "started"
    if m < 60:
        return f"in {m} min"
    if m < 1440:
        return f"in {m // 60}h {m % 60}m"
    return f"in {m // 1440}d"


def status_of(r):
    if r.Unsold > 0:
        return "CANCEL NOW" if r.Minutes <= 60 else "CANCEL SOON" if r.Minutes <= 180 else "ON TRACK"
    if r.Lost > 0:
        return "MISSED"
    return "CANCELLED" if r.Sold == 0 else "DONE"


def events(data):
    """One row per event (venue + name + start time) with pass counts and money."""
    d = data.copy()
    d["Tied"] = d["Buying Price"].where(d["State"] == "Tied up", 0)
    for k, s in (("Unsold", "Tied up"), ("Sold", "Sold"), ("Cancelled", "Cancelled"), ("Lost", "Lost")):
        d[k] = (d["State"] == s).astype(int)
    out = d.groupby(["Event Start", "Event Venue", "Event Name"], as_index=False).agg(
        Buyer=("Name of Buyer", "first"), Passes=("State", "size"), Unsold=("Unsold", "sum"),
        Sold=("Sold", "sum"), Cancelled=("Cancelled", "sum"), Lost=("Lost", "sum"),
        Tied=("Tied", "sum"), Cost=("Buying Price", "sum"),
    ).rename(columns={"Event Start": "Start", "Event Venue": "Venue", "Event Name": "Name"})
    if out.empty:
        return out.assign(Minutes=0, Status="", ID="")
    out["Minutes"] = ((out["Start"] - now).dt.total_seconds() // 60).astype(int)
    out["Status"] = out.apply(status_of, axis=1)
    out["ID"] = [f"RV-{zlib.crc32(f'{v}{n}{s}'.encode()) % 100000:05d}"
                 for v, n, s in zip(out.Venue, out.Name, out.Start)]
    return out


def pivot(data, index, cash=False):
    if data.empty:
        return pd.DataFrame(columns=STATES)
    return data.pivot_table(index=index, columns="State", values="Buying Price",
                            aggfunc="sum" if cash else "count", fill_value=0
                            ).reindex(columns=STATES, fill_value=0)


def sort_rows(pv):
    return pv.loc[pv.sum(axis=1).sort_values(ascending=False).index] if len(pv) else pv


def period_slice(p):
    D = df["Date of Event"]
    if p == "All Time":
        return df, None
    if p == "Today":
        s = e = today
        ps = pe = today - pd.Timedelta(days=1)
    elif p == "This Week":
        s = today - pd.Timedelta(days=today.weekday())
        e = s + pd.Timedelta(days=6)
        ps, pe = s - pd.Timedelta(days=7), s - pd.Timedelta(days=1)
    else:
        s = today.replace(day=1)
        e = s + pd.offsets.MonthEnd(0)
        pe = s - pd.Timedelta(days=1)
        ps = pe.replace(day=1)
    return df[D.between(s, e)], df[D.between(ps, pe)]


all_ev = events(df)
now_ev = all_ev[(all_ev.Unsold > 0) & (all_ev.Minutes <= 60)]
soon_ev = all_ev[(all_ev.Unsold > 0) & (all_ev.Minutes > 60) & (all_ev.Minutes <= 180)]


# ---------------------------------------------------------------
# 5. BUILDING BLOCKS
# ---------------------------------------------------------------
def head(t, s):
    return f'<div class="pgt">{t}</div><div class="pgs">{s}</div>'


def spark(vals, color):
    if len(vals) < 2:
        vals = (vals or [0]) * 2
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i * 80 / (len(vals) - 1):.1f},{26 - (v - lo) / rng * 22:.1f}" for i, v in enumerate(vals))
    return (f'<svg width="80" height="30" viewBox="0 0 80 30"><polygon points="0,30 {pts} 80,30" fill="{color}" opacity=".13"/>'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/></svg>')


def kpi_row(data, prior):
    specs = [("◫", PRIMARY, "Total Bought", lambda d: d["Buying Price"].sum(), True, True),
             ("◷", "#d97706", "Money Tied Up", lambda d: money_of(d, "Tied up"), False, True),
             ("✓", "#16a34a", "Passes Sold", lambda d: (d["State"] == "Sold").sum(), True, False),
             ("▲", "#dc2626", "Money Lost", lambda d: money_of(d, "Lost"), False, True)]
    cards = ""
    for icon, color, label, fn, up_good, is_money in specs:
        cur = fn(data)
        fmt = money if is_money else (lambda v: f"{v:,.0f}")
        series = [fn(g) for _, g in data.groupby("Date of Event")]
        prev = fn(prior) if prior is not None else 0
        if prev > 0:
            ch = (cur - prev) / prev * 100
            cls = "up" if (ch >= 0) == up_good else "dn"
            arrow = "↑" if ch >= 0 else "↓"
            delta = f'<span class="dl {cls}">{arrow} {abs(ch):.0f}%</span> <span class="muted">vs previous</span>'
        else:
            delta = '<span class="muted">no earlier period</span>'
        sub = f"<small>{sell_through(data)} sold</small>" if label == "Passes Sold" else ""
        cards += (f'<div class="kpi"><div class="kt"><div class="ki" style="background:{shade(color, .85)};color:{color}">{icon}</div>'
                  f'<div><div class="kl">{label}</div><div class="kv">{fmt(cur)}{sub}</div></div></div>'
                  f'<div class="kb"><div>{delta}</div>{spark(series, color)}</div></div>')
    st.html(f'<div class="kpis">{cards}</div>')


def table_html(part):
    if part.empty:
        return '<div class="empty">No events match. Clear the search or filter.</div>'
    rows = ""
    for _, r in part.iterrows():
        mini = "".join(f'<i style="width:{r[k] / r.Passes * 100:.1f}%;background:{COL[s]}"></i>'
                       for k, s in (("Sold", "Sold"), ("Unsold", "Tied up"), ("Cancelled", "Cancelled"), ("Lost", "Lost")))
        tied = money(r.Tied) if r.Tied > 0 else "—"
        rows += (f'<tr><td class="idc">{r.ID}</td><td><b>{esc(r.Name)}</b></td><td>📍 {esc(r.Venue)}</td>'
                 f'<td>{esc(str(r.Buyer))}</td><td><span class="pill {PILL[r.Status]}">{r.Status}</span></td>'
                 f'<td>{r.Start:%b %d, %Y}<br><small>{hhmm(r.Start)} · {countdown(r.Minutes)}</small></td>'
                 f'<td><b>{r.Sold}</b> / {r.Passes} sold<div class="mini">{mini}</div></td>'
                 f'<td><b>{tied}</b></td><td class="dots">⋮</td></tr>')
    heads = "".join(f"<th>{h}</th>" for h in
                    ["Event ID", "Event", "Venue", "Buyer", "Status", "Date & Time", "Passes", "Tied Up", "Actions"])
    return f'<div class="tw"><table class="tbl"><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div>'


def render_events(data, key, title):
    ev = events(data)
    q = ss.get("q", "").strip().lower()
    if q and not ev.empty:
        hay = (ev.ID + " " + ev.Name + " " + ev.Venue + " " + ev.Buyer.astype(str) + " " + ev.Status).str.lower()
        ev = ev[hay.str.contains(q, regex=False)]
    if ss.get(f"{key}_fs"):
        ev = ev[ev.Status.isin(ss[f"{key}_fs"])]
    if ss.get(f"{key}_fv"):
        ev = ev[ev.Venue.isin(ss[f"{key}_fv"])]
    urgent = (ev.Unsold > 0) & (ev.Minutes >= 0)
    ev = pd.concat([ev[urgent].sort_values("Start"), ev[~urgent].sort_values("Start", ascending=False)])

    with st.container(key=f"card_{key}"):
        h, f1, f2 = st.columns([5, 1.2, 1.4], vertical_alignment="center")
        h.html(f'<div class="ct">☰ &nbsp;{title}</div>')
        with f1.popover("Filter"):
            st.multiselect("Status", list(PILL), key=f"{key}_fs")
            st.multiselect("Venue", sorted(df["Event Venue"].unique()), key=f"{key}_fv")
        f2.download_button("⬇ Export", ev.drop(columns=["Minutes"]).to_csv(index=False).encode(),
                           f"{key}_events.csv", "text/csv", type="primary", key=f"{key}_dl")

        rpp, n = ss.get(f"{key}_rpp", 5), len(ev)
        pages = max(1, -(-n // rpp))
        if ss.get(f"{key}_pg", 1) > pages:
            ss[f"{key}_pg"] = 1
        pg = ss.get(f"{key}_pg", 1)
        st.html(table_html(ev.iloc[(pg - 1) * rpp: pg * rpp]))

        a, b, c = st.columns([3, 2, 2], vertical_alignment="center")
        a.html(f'<span class="muted">Showing {min(n, (pg - 1) * rpp + 1)} to {min(n, pg * rpp)} of {n} entries</span>')
        b.number_input("Page", 1, pages, key=f"{key}_pg", label_visibility="collapsed")
        c.selectbox("Rows", [5, 10, 20, 50], key=f"{key}_rpp", format_func=lambda v: f"{v} rows per page",
                    label_visibility="collapsed")


def stacked(pv, horizontal=True, cash=False):
    if pv.empty:
        return '<div class="empty">No data for this selection.</div>'
    leg = "".join(f'<span><i style="background:{COL[s]}"></i>{s}</span>' for s in STATES)
    mx = pv.sum(axis=1).max() or 1
    fmt = money if cash else (lambda v: f"{v:,.0f}")

    if horizontal:
        rows = ""
        for idx, row in pv.iterrows():
            tot = row.sum()
            bars = "".join(f'<i style="width:{row[s] / mx * 100:.1f}%;background:{COL[s]}" title="{s}: {fmt(row[s])}"></i>'
                           for s in STATES if row[s] > 0)
            rows += (f'<div class="hrow"><div class="hl" title="{esc(str(idx))}">{esc(str(idx))}</div>'
                     f'<div class="htrack">{bars}</div><b>{fmt(tot)}</b></div>')
        return f'<div class="legend">{leg}</div>{rows}'

    cols = ""
    for idx, row in pv.iterrows():
        tot = row.sum()
        lbl = idx.strftime("%b %d") if hasattr(idx, "strftime") else str(idx)
        segs = "".join(f'<i style="height:{row[s] / mx * 100:.1f}%;background:{COL[s]}" title="{s}: {fmt(row[s])}"></i>'
                       for s in STATES if row[s] > 0)
        cols += f'<div class="vcol"><b>{fmt(tot)}</b><div class="vtrack">{segs}</div><span>{esc(lbl)}</span></div>'
    return f'<div class="legend">{leg}</div><div class="vwrap">{cols}</div>'


def alarms_html():
    out = ""
    for _, r in now_ev.iterrows():
        out += (f'<div class="alarm red"><div class="blink"></div><div><b>CANCEL NOW:</b> '
                f'{esc(r.Venue)} ({esc(r.Name)}) starts {countdown(r.Minutes)} — '
                f'<b>{r.Unsold} unsold</b> ({money(r.Tied)} at risk)</div></div>')
    for _, r in soon_ev.iterrows():
        out += (f'<div class="alarm amber"><div class="blink"></div><div><b>CANCEL SOON:</b> '
                f'{esc(r.Venue)} ({esc(r.Name)}) starts {countdown(r.Minutes)} — '
                f'<b>{r.Unsold} unsold</b> ({money(r.Tied)} tied up)</div></div>')
    return out


# ---------------------------------------------------------------
# 6. SIDEBAR NAVIGATION (slides in/out as a drawer)
# ---------------------------------------------------------------
with st.sidebar:
    _, c_x = st.columns([4.4, 0.6])
    c_x.button("✕", key="nav_close", help="Close menu",
               on_click=lambda: ss.update(nav_open=False))
    st.html(f"""
        <div class="logo">
            <div class="lg">P</div>
            <div>
                <div class="lt">{BRAND_A}<b>{BRAND_B}</b></div>
                <div class="ls">{TAGLINE}</div>
            </div>
        </div>
    """)

    page = st.radio(
        "Nav",
        ["Dashboard", "Today", "Upcoming", "Venues", "Analytics"],
        label_visibility="collapsed",
    )

    st.html(f"""
        <div class="promo">
            <div class="pn">{money(money_of(df, 'Tied up'))}</div>
            <div class="pt">Active exposure across {(df['State'] == 'Tied up').sum()} unsold passes</div>
        </div>
    """)

# auto-close the drawer after the user picks a page
if ss.get("last_page") != page:
    ss["last_page"] = page
    if ss["nav_open"]:
        ss["nav_open"] = False
        st.rerun()


# ---------------------------------------------------------------
# 7. TOP NAVIGATION BAR
# ---------------------------------------------------------------
with st.container(key="topbar"):
    c_menu, c_search, c_date, c_bell, c_theme, c_prof = st.columns(
        [0.55, 3.0, 1.6, 0.55, 0.75, 2.0], vertical_alignment="center"
    )
    if c_menu.button("☰", key="nav_btn", help="Open menu"):
        ss["nav_open"] = not ss["nav_open"]
        st.rerun()

    c_search.text_input(
        "Search",
        placeholder="Search events, venues, buyers...",
        key="q",
        label_visibility="collapsed",
    )

    test_badge = '<span class="testtag">TEST</span>' if ss.get("test") else ""
    c_date.html(f'<div class="datepill">{now:%b %d, %Y} {test_badge}</div>')

    has_alarm = not (now_ev.empty and soon_ev.empty)
    dot = '<span class="dot"></span>' if has_alarm else ""
    c_bell.html(f'<div class="bell">{dot}</div>')

    with c_theme.popover(""):
        st.selectbox("Theme", list(PRESETS), key="preset", on_change=use_preset)
        st.divider()
        st.checkbox("Test the alarm", key="test")
        if ss.get("test"):
            st.date_input("Pretend date", value=df["Date of Event"].min().date(), key="p_date")
            st.time_input("Pretend time", value=time(12, 30), key="p_time")

    c_prof.html("""
        <div class="prof">
            <div class="av">AT</div>
            <div><b>Abdullahi Teslim</b><small>Reserve Manager</small></div>
        </div>
    """)

# dark backdrop behind the drawer: clicking anywhere closes it
if ss["nav_open"]:
    st.button("Close menu", key="nav_backdrop", on_click=lambda: ss.update(nav_open=False))


# ---------------------------------------------------------------
# 8. PAGE ROUTING
# ---------------------------------------------------------------
if "Dashboard" in page:
    h_left, h_right = st.columns([4, 1.2], vertical_alignment="center")
    h_left.html(head("Dashboard", "Overview of your parking reserve operations"))
    period = h_right.selectbox(
        "Period", ["All Time", "Today", "This Week", "This Month"], label_visibility="collapsed"
    )

    cur_df, prev_df = period_slice(period)
    if alarms_html():
        st.html(alarms_html())

    kpi_row(cur_df, prev_df)
    st.html("<div style='height:14px'></div>")
    render_events(cur_df, "dash", "Recent & Upcoming Reserves")

elif "Today" in page:
    st.html(head("Today's Operations", f"Live schedule for {now:%A, %d %B %Y}"))
    day_df = df[df["Date of Event"] == today]
    if alarms_html():
        st.html(alarms_html())
    if day_df.empty:
        st.html(
            '<div class="empty-card">No parking passes scheduled for today. '
            'Use in the top bar to test another date.</div>'
        )
    else:
        kpi_row(day_df, df[df["Date of Event"] == today - pd.Timedelta(days=1)])
        st.html("<div style='height:14px'></div>")
        render_events(day_df, "today", "Today's Events")

elif "Upcoming" in page:
    st.html(head("Upcoming Reserves", "Future inventory exposure & pre-sold velocity"))
    avail_dates = sorted(df["Date of Event"].dt.date.unique())
    if not avail_dates:
        st.html('<div class="empty-card">No event dates found in the dataset.</div>')
    else:
        after_today = [d for d in avail_dates if pd.Timestamp(d) > today]
        default_d = after_today[0] if after_today else avail_dates[-1]
        fut_df = df[df["Date of Event"] > today] if after_today else df

        kpi_row(fut_df, None)
        st.html("<div style='height:14px'></div>")

        with st.container(key="card_fut_pick"):
            p_left, p_right = st.columns([3.5, 1.5], vertical_alignment="center")
            p_left.html('<div class="ct">Select or Type a Date</div>')
            picked_date = p_right.date_input(
                "Pick or type a date",
                value=ss.get("fut_date_pick", default_d),
                min_value=avail_dates[0],
                max_value=avail_dates[-1],
                key="fut_date_pick",
                label_visibility="collapsed",
            )
            day_pick = df[df["Date of Event"] == pd.Timestamp(picked_date)]
            st.html("<div style='height:10px'></div>")
            kpi_row(day_pick, None)
            st.html("<div style='height:10px'></div>")
            st.html(
                stacked(sort_rows(pivot(day_pick, "Event Venue", cash=False)), horizontal=True, cash=False)
            )

        st.html("<div style='height:14px'></div>")
        render_events(day_pick, "future_day", f"Events on {pd.Timestamp(picked_date):%a %d %b %Y}")

elif "Venues" in page:
    st.html(head("Venue Exposure", "Capital tied up and pass breakdown by stadium & arena"))
    c1, c2 = st.columns(2)
    with c1:
        with st.container(key="card_v_cash"):
            st.html('<div class="ct">Capital by Venue ($)</div>')
            st.html(stacked(sort_rows(pivot(df, "Event Venue", cash=True)), horizontal=True, cash=True))
    with c2:
        with st.container(key="card_v_cnt"):
            st.html('<div class="ct">Pass Count by Venue</div>')
            st.html(stacked(sort_rows(pivot(df, "Event Venue", cash=False)), horizontal=True, cash=False))

elif "Analytics" in page:
    st.html(head("Analytics & Trends", "Daily timeline and buyer performance"))
    with st.container(key="card_a_time"):
        st.html('<div class="ct">Daily Capital Allocation ($)</div>')
        st.html(stacked(pivot(df, "Date of Event", cash=True), horizontal=False, cash=True))
    st.html("<div style='height:14px'></div>")
    with st.container(key="card_a_buyer"):
        st.html('<div class="ct">Breakdown by Buyer</div>')
        st.html(stacked(sort_rows(pivot(df, "Name of Buyer", cash=True)), horizontal=True, cash=True))
