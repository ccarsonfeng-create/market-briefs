"""
build_index.py — regenerates index.html for the market-briefs GitHub Pages site.

Scans the repo for brief HTML files matching:
  - US-Brief-YYYY-MM-DD.html       (US overnight wrap)
  - US-PreMarket-YYYY-MM-DD.html   (US pre-market brief)
  - APAC-Brief-YYYY-MM-DD.html     (APAC afternoon wrap)

Extracts title/headline from each file's <h1> tag where possible
and renders an interactive monthly calendar view with click-to-expand day panel.

Usage: python3 build_index.py <repo_path>
"""
import sys
import re
import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import html

REPO_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/market-briefs"))

BRIEF_PATTERNS = {
    "us-wrap":      (re.compile(r"^US-Brief-(\d{4})-(\d{2})-(\d{2})\.html$"),     "US Overnight Wrap",  "us-wrap"),
    "us-premarket": (re.compile(r"^US-PreMarket-(\d{4})-(\d{2})-(\d{2})\.html$"), "US Pre-Market",       "us-premarket"),
    "apac":         (re.compile(r"^APAC-Brief-(\d{4})-(\d{2})-(\d{2})\.html$"),   "APAC Wrap",            "apac"),
}

KIND_EMOJI = {
    "us-wrap":      "🇺🇸",
    "us-premarket": "🇺🇸",
    "apac":         "🌏",
}


def extract_headline(filepath: Path) -> str:
    """Try to pull the <h1> text from the file. Falls back to '' if not found."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(80000)  # large enough to clear the inline <style> block
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.DOTALL | re.IGNORECASE)
        if not m:
            return ""
        inner = m.group(1)
        inner = re.sub(r"<[^>]+>", "", inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        inner = re.sub(r"^(🇺🇸|🌏|🇨🇳|🇪🇺)\s*", "", inner)
        inner = re.sub(r"\s*—\s*[A-Z][a-z]+,?\s+\w+\s+\d+,?\s+\d{4}.*$", "", inner)
        inner = re.sub(r"^[A-Z][a-z]+,?\s+\w+\s+\d+,?\s+\d{4}\s*—\s*", "", inner)
        return inner.strip(" —–-")
    except Exception:
        return ""


def collect_briefs():
    briefs = []
    for fp in REPO_PATH.iterdir():
        if not fp.is_file() or not fp.name.endswith(".html"):
            continue
        if fp.name in ("index.html",):
            continue
        for kind, (pattern, label, css_class) in BRIEF_PATTERNS.items():
            m = pattern.match(fp.name)
            if m:
                d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                headline = extract_headline(fp)
                briefs.append({
                    "date": d.isoformat(),
                    "kind": kind,
                    "label": label,
                    "css_class": css_class,
                    "emoji": KIND_EMOJI.get(kind, "📊"),
                    "filename": fp.name,
                    "headline": headline,
                })
                break
    briefs.sort(key=lambda b: (b["date"], b["kind"]), reverse=True)
    return briefs


def render_index(briefs):
    if briefs:
        latest = date.fromisoformat(briefs[0]["date"])
    else:
        latest = date.today()

    briefs_json = json.dumps(briefs, indent=2)
    today_iso = date.today().isoformat()
    initial_month = latest.strftime("%Y-%m")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Carson's Market Briefs — Daily S&T / IB / ER Interview Prep</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #f1f5f9;
    color: #0f172a;
    margin: 0;
    padding: 16px;
    line-height: 1.5;
    font-size: 15px;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}

  /* HERO */
  header.hero {{
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    padding: 22px 24px 18px;
    border-radius: 14px;
    border-left: 6px solid #3b82f6;
    border-top: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 14px;
    box-shadow: 0 2px 6px rgba(15,23,42,0.05);
    position: relative;
    overflow: hidden;
  }}
  header.hero::after {{
    content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #f59e0b 100%);
  }}
  header.hero .eyebrow {{ font-size: 10.5px; color: #3b82f6; text-transform: uppercase; letter-spacing: 1.4px; font-weight: 700; margin-bottom: 4px; }}
  header.hero h1 {{ margin: 0; font-size: 24px; letter-spacing: -0.5px; font-weight: 800; }}

  /* FILTER BAR */
  .filter-bar {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;
    background: #ffffff;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
  }}
  .filter-btn {{
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    color: #475569;
    padding: 7px 14px;
    border-radius: 18px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: 0.3px;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }}
  .filter-btn::before {{
    content: ""; display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #94a3b8;
  }}
  .filter-btn.us-wrap::before      {{ background: #1d4ed8; }}
  .filter-btn.us-premarket::before {{ background: #047857; }}
  .filter-btn.apac::before         {{ background: #b91c1c; }}
  .filter-btn:hover {{ background: #e2e8f0; color: #0f172a; }}
  .filter-btn.active {{ background: #3b82f6; color: #fff; border-color: #3b82f6; box-shadow: 0 1px 3px rgba(59,130,246,0.3); }}
  .filter-btn.active::before {{ background: #fff; }}
  .filter-btn.us-wrap.active      {{ background: #1d4ed8; border-color: #1d4ed8; }}
  .filter-btn.us-premarket.active {{ background: #047857; border-color: #047857; }}
  .filter-btn.apac.active         {{ background: #b91c1c; border-color: #b91c1c; }}

  /* CALENDAR CONTAINER */
  .cal-card {{
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 16px 18px 18px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
  }}

  /* CALENDAR NAV */
  .cal-nav {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid #eef0f3;
  }}
  .cal-month-label {{
    font-size: 17px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.3px;
    flex: 1;
    text-align: center;
    min-width: 0;
  }}
  .cal-btn {{
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    color: #475569;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 800;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    padding: 0;
  }}
  .cal-btn:hover {{ background: #e2e8f0; color: #0f172a; }}
  .cal-btn.today-btn {{
    width: auto; padding: 0 12px; font-size: 11px;
    background: #3b82f6; color: #fff; border-color: #3b82f6;
    letter-spacing: 0.5px;
  }}
  .cal-btn.today-btn:hover {{ background: #2563eb; color: #fff; }}

  /* CALENDAR GRID */
  .cal-weekdays {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
    margin-bottom: 4px;
  }}
  .cal-weekday {{
    text-align: center;
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 4px 0;
  }}
  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
  }}
  .cal-cell {{
    aspect-ratio: 1 / 1;
    min-height: 56px;
    background: #f8fafc;
    border: 1px solid #eef0f3;
    border-radius: 8px;
    padding: 6px 6px 8px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    position: relative;
    transition: all 0.15s;
    overflow: hidden;
  }}
  .cal-cell:hover {{
    background: #f1f5f9;
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(15,23,42,0.06);
  }}
  .cal-cell.muted {{
    background: #fafbfc;
    color: #cbd5e1;
    cursor: default;
  }}
  .cal-cell.muted:hover {{ background: #fafbfc; transform: none; box-shadow: none; border-color: #eef0f3; }}
  .cal-cell.no-brief {{ cursor: default; }}
  .cal-cell.no-brief:hover {{ background: #f8fafc; transform: none; box-shadow: none; }}
  .cal-cell.has-brief {{ background: #ffffff; border-color: #e2e8f0; }}
  .cal-cell.today {{
    background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
    border-color: #93c5fd;
    box-shadow: inset 0 0 0 1px #93c5fd;
  }}
  .cal-cell.selected {{
    background: linear-gradient(180deg, #fef3c7 0%, #fde68a 100%);
    border-color: #f59e0b;
    box-shadow: inset 0 0 0 1.5px #f59e0b, 0 2px 6px rgba(245,158,11,0.18);
  }}
  .cal-day-num {{
    font-size: 13px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1;
  }}
  .cal-cell.muted .cal-day-num {{ color: #cbd5e1; font-weight: 500; }}
  .cal-cell.today .cal-day-num {{ color: #1d4ed8; font-weight: 800; }}
  .cal-cell.selected .cal-day-num {{ color: #92400e; font-weight: 800; }}
  .cal-badges {{
    margin-top: auto;
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
    align-items: flex-end;
    min-height: 16px;
  }}
  .cal-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    box-shadow: 0 0 0 1.5px #fff;
  }}
  .cal-dot.us-wrap      {{ background: #1d4ed8; }}
  .cal-dot.us-premarket {{ background: #047857; }}
  .cal-dot.apac         {{ background: #b91c1c; }}
  .cal-dot.hidden-by-filter {{ display: none; }}

  /* DAY EXPANSION PANEL */
  .cal-expand {{
    margin-top: 18px;
    padding-top: 16px;
    border-top: 1px dashed #e2e8f0;
    min-height: 40px;
  }}
  .cal-expand-empty {{
    text-align: center;
    color: #94a3b8;
    font-size: 13px;
    padding: 20px 0;
    font-style: italic;
  }}
  .cal-expand-date {{
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #f59e0b;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .cal-expand-date .today-badge {{
    background: #3b82f6;
    color: #fff;
    padding: 2px 7px;
    border-radius: 8px;
    font-size: 9px;
    letter-spacing: 0.6px;
  }}

  /* BRIEF CARD INSIDE EXPANSION */
  .brief-card {{
    display: flex;
    align-items: stretch;
    gap: 12px;
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #94a3b8;
    padding: 12px 14px;
    margin-bottom: 8px;
    text-decoration: none;
    color: inherit;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    transition: all 0.15s;
  }}
  .brief-card:hover {{ transform: translateY(-1px); box-shadow: 0 4px 10px rgba(15,23,42,0.08); }}
  .brief-card.us-wrap {{ border-left-color: #1d4ed8; }}
  .brief-card.us-premarket {{ border-left-color: #047857; }}
  .brief-card.apac {{ border-left-color: #b91c1c; }}
  .brief-card-emoji {{
    font-size: 22px;
    flex-shrink: 0;
    align-self: center;
    line-height: 1;
  }}
  .brief-card-meta {{ flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 3px; }}
  .brief-card-label {{ font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.4px; text-transform: uppercase; }}
  .brief-card.us-wrap .brief-card-label {{ color: #1d4ed8; }}
  .brief-card.us-premarket .brief-card-label {{ color: #047857; }}
  .brief-card.apac .brief-card-label {{ color: #b91c1c; }}
  .brief-card-headline {{ font-size: 14px; font-weight: 700; color: #0f172a; line-height: 1.35; }}
  .brief-card-filename {{ font-size: 10.5px; color: #94a3b8; font-family: ui-monospace, monospace; }}
  .brief-card-arrow {{ color: #cbd5e1; font-size: 18px; align-self: center; font-weight: 600; }}
  .brief-card:hover .brief-card-arrow {{ color: #3b82f6; }}

  /* LEGEND */
  .cal-legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 11px;
    color: #64748b;
    padding-top: 12px;
    margin-top: 12px;
    border-top: 1px dashed #eef0f3;
    justify-content: center;
  }}
  .cal-legend-item {{ display: inline-flex; align-items: center; gap: 5px; font-weight: 600; }}

  /* RECENT LIST FALLBACK (mobile lookup convenience) */
  .recent-list {{ margin-top: 16px; }}
  .recent-list-title {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #64748b;
    font-weight: 700;
    margin: 18px 4px 8px;
  }}

  /* FOOTER */
  footer.foot {{
    text-align: center;
    color: #94a3b8;
    font-size: 11px;
    padding: 24px 8px 8px;
    line-height: 1.6;
  }}
  footer.foot .badge {{
    display: inline-block;
    background: #f1f5f9;
    padding: 2px 8px;
    border-radius: 10px;
    margin-right: 6px;
    font-weight: 600;
  }}

  /* MOBILE */
  @media (max-width: 640px) {{
    body {{ padding: 12px; font-size: 14px; }}
    header.hero {{ padding: 18px 16px 14px; }}
    header.hero h1 {{ font-size: 20px; }}
    .filter-btn {{ font-size: 11px; padding: 6px 11px; }}
    .cal-card {{ padding: 12px 12px 14px; }}
    .cal-month-label {{ font-size: 15px; }}
    .cal-cell {{ min-height: 44px; padding: 4px 4px 6px; }}
    .cal-day-num {{ font-size: 12px; }}
    .cal-dot {{ width: 5px; height: 5px; box-shadow: 0 0 0 1px #fff; }}
    .cal-weekday {{ font-size: 9px; }}
    .brief-card {{ padding: 10px 12px; gap: 10px; }}
    .brief-card-emoji {{ font-size: 18px; }}
    .brief-card-headline {{ font-size: 13px; }}
    .brief-card-filename {{ font-size: 10px; }}
    .cal-legend {{ font-size: 10px; gap: 8px; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <div class="eyebrow">Daily Market Briefs · Mon-Fri</div>
    <h1>US &amp; APAC Market Overview</h1>
  </header>

  <div class="filter-bar">
    <button class="filter-btn active" data-filter="all">All Briefs</button>
    <button class="filter-btn us-wrap" data-filter="us-wrap">US Overnight</button>
    <button class="filter-btn us-premarket" data-filter="us-premarket">US Pre-Market</button>
    <button class="filter-btn apac" data-filter="apac">APAC Wrap</button>
  </div>

  <div class="cal-card">
    <div class="cal-nav">
      <button class="cal-btn" id="cal-prev" aria-label="Previous month">‹</button>
      <div class="cal-month-label" id="cal-month-label">—</div>
      <button class="cal-btn" id="cal-next" aria-label="Next month">›</button>
      <button class="cal-btn today-btn" id="cal-today">Today</button>
    </div>

    <div class="cal-weekdays">
      <div class="cal-weekday">Sun</div>
      <div class="cal-weekday">Mon</div>
      <div class="cal-weekday">Tue</div>
      <div class="cal-weekday">Wed</div>
      <div class="cal-weekday">Thu</div>
      <div class="cal-weekday">Fri</div>
      <div class="cal-weekday">Sat</div>
    </div>

    <div class="cal-grid" id="cal-grid"></div>

    <div class="cal-expand" id="cal-expand">
      <div class="cal-expand-empty">Click any highlighted day to see its briefs.</div>
    </div>

    <div class="cal-legend">
      <span class="cal-legend-item"><span class="cal-dot us-wrap"></span> US Overnight</span>
      <span class="cal-legend-item"><span class="cal-dot us-premarket"></span> US Pre-Market</span>
      <span class="cal-legend-item"><span class="cal-dot apac"></span> APAC Wrap</span>
    </div>
  </div>

  <footer class="foot">
    <span class="badge">Last updated {latest.strftime("%b %d, %Y")}</span>
    Built by Carson · Auto-published Mon-Fri · No investment advice<br>
    Sources: BLS, FRED, US Treasury, Bloomberg, CNBC, Reuters, EIA · WebSearch-verified for APAC
  </footer>

</div>

<script>
  const BRIEFS = {briefs_json};
  const TODAY = "{today_iso}";
  let currentFilter = "all";
  // initial month from latest brief's date
  let viewYear = {latest.year};
  let viewMonth = {latest.month}; // 1-12
  let selectedDate = null;

  // Group briefs by date for quick lookup
  const briefsByDate = {{}};
  BRIEFS.forEach(b => {{
    if (!briefsByDate[b.date]) briefsByDate[b.date] = [];
    briefsByDate[b.date].push(b);
  }});

  const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];

  function pad(n) {{ return String(n).padStart(2, "0"); }}
  function isoDate(y, m, d) {{ return `${{y}}-${{pad(m)}}-${{pad(d)}}`; }}

  function renderCalendar() {{
    const grid = document.getElementById("cal-grid");
    const label = document.getElementById("cal-month-label");
    label.textContent = `${{MONTH_NAMES[viewMonth-1]}} ${{viewYear}}`;

    // First day of month, last day, day-of-week of first day (0=Sun)
    const firstDay = new Date(viewYear, viewMonth-1, 1);
    const lastDay = new Date(viewYear, viewMonth, 0);
    const startDow = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    // Previous-month tail days to fill the first row
    const prevLastDay = new Date(viewYear, viewMonth-1, 0).getDate();
    const cells = [];

    // Leading muted cells from previous month
    for (let i = startDow - 1; i >= 0; i--) {{
      const d = prevLastDay - i;
      const m = viewMonth - 1 || 12;
      const y = viewMonth - 1 ? viewYear : viewYear - 1;
      cells.push({{ y, m, d, muted: true }});
    }}
    // Current month
    for (let d = 1; d <= daysInMonth; d++) {{
      cells.push({{ y: viewYear, m: viewMonth, d, muted: false }});
    }}
    // Trailing muted cells to fill the grid (always show 6 rows = 42 cells, or trim to 5 if possible)
    const targetCells = cells.length <= 35 ? 35 : 42;
    let nextDay = 1;
    while (cells.length < targetCells) {{
      const m = viewMonth === 12 ? 1 : viewMonth + 1;
      const y = viewMonth === 12 ? viewYear + 1 : viewYear;
      cells.push({{ y, m, d: nextDay, muted: true }});
      nextDay++;
    }}

    grid.innerHTML = "";
    cells.forEach(c => {{
      const iso = isoDate(c.y, c.m, c.d);
      const cellBriefs = briefsByDate[iso] || [];
      const cell = document.createElement("div");
      cell.className = "cal-cell";
      cell.dataset.date = iso;
      if (c.muted) cell.classList.add("muted");
      if (iso === TODAY) cell.classList.add("today");
      if (cellBriefs.length > 0 && !c.muted) {{
        cell.classList.add("has-brief");
      }} else if (!c.muted) {{
        cell.classList.add("no-brief");
      }}
      if (iso === selectedDate) cell.classList.add("selected");

      // Day number
      const num = document.createElement("div");
      num.className = "cal-day-num";
      num.textContent = c.d;
      cell.appendChild(num);

      // Badge dots
      if (cellBriefs.length > 0 && !c.muted) {{
        const badges = document.createElement("div");
        badges.className = "cal-badges";
        // Maintain stable order: us-premarket, us-wrap, apac
        const order = ["us-premarket", "us-wrap", "apac"];
        const kinds = cellBriefs.map(b => b.kind);
        order.forEach(k => {{
          if (kinds.includes(k)) {{
            const dot = document.createElement("span");
            dot.className = `cal-dot ${{k}}`;
            dot.dataset.kind = k;
            if (currentFilter !== "all" && currentFilter !== k) dot.classList.add("hidden-by-filter");
            badges.appendChild(dot);
          }}
        }});
        cell.appendChild(badges);

        cell.addEventListener("click", () => selectDay(iso));
      }}

      grid.appendChild(cell);
    }});
  }}

  function selectDay(iso) {{
    selectedDate = (selectedDate === iso) ? null : iso;
    // re-render to update .selected class
    renderCalendar();
    renderExpansion();
  }}

  function renderExpansion() {{
    const expand = document.getElementById("cal-expand");
    if (!selectedDate) {{
      expand.innerHTML = '<div class="cal-expand-empty">Click any highlighted day to see its briefs.</div>';
      return;
    }}
    let dayBriefs = briefsByDate[selectedDate] || [];
    if (currentFilter !== "all") {{
      dayBriefs = dayBriefs.filter(b => b.kind === currentFilter);
    }}

    const d = new Date(selectedDate + "T00:00:00");
    const dow = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"][d.getDay()];
    const month = MONTH_NAMES[d.getMonth()];
    const isToday = selectedDate === TODAY;

    let html = `<div class="cal-expand-date">${{dow}}, ${{month}} ${{d.getDate()}}, ${{d.getFullYear()}}`;
    if (isToday) html += ` <span class="today-badge">TODAY</span>`;
    html += `</div>`;

    if (dayBriefs.length === 0) {{
      html += `<div class="cal-expand-empty">No briefs match the current filter for this day.</div>`;
    }} else {{
      // sort so US Pre-Market → US Overnight → APAC (chronologically through trading day)
      const order = {{ "us-premarket": 0, "us-wrap": 1, "apac": 2 }};
      dayBriefs.sort((a, b) => (order[a.kind] || 9) - (order[b.kind] || 9));
      dayBriefs.forEach(b => {{
        const head = b.headline ? escapeHtml(b.headline) : escapeHtml(b.label);
        html += `
          <a href="./${{escapeHtml(b.filename)}}" class="brief-card ${{b.css_class}}">
            <div class="brief-card-emoji">${{b.emoji}}</div>
            <div class="brief-card-meta">
              <div class="brief-card-label">${{escapeHtml(b.label)}}</div>
              <div class="brief-card-headline">${{head}}</div>
              <div class="brief-card-filename">${{escapeHtml(b.filename)}}</div>
            </div>
            <div class="brief-card-arrow">→</div>
          </a>`;
      }});
    }}

    expand.innerHTML = html;
  }}

  function escapeHtml(s) {{
    return String(s).replace(/[&<>"']/g, c => ({{ "&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;" }})[c]);
  }}

  // Month navigation
  document.getElementById("cal-prev").addEventListener("click", () => {{
    viewMonth--;
    if (viewMonth < 1) {{ viewMonth = 12; viewYear--; }}
    renderCalendar();
  }});
  document.getElementById("cal-next").addEventListener("click", () => {{
    viewMonth++;
    if (viewMonth > 12) {{ viewMonth = 1; viewYear++; }}
    renderCalendar();
  }});
  document.getElementById("cal-today").addEventListener("click", () => {{
    const t = new Date(TODAY + "T00:00:00");
    viewYear = t.getFullYear();
    viewMonth = t.getMonth() + 1;
    selectedDate = TODAY in briefsByDate ? TODAY : null;
    renderCalendar();
    renderExpansion();
  }});

  // Filter buttons
  document.querySelectorAll(".filter-btn").forEach(btn => {{
    btn.addEventListener("click", () => {{
      currentFilter = btn.dataset.filter;
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderCalendar();
      renderExpansion();
    }});
  }});

  // Initial render — auto-select latest brief date so the page is useful immediately
  if (BRIEFS.length > 0) {{
    selectedDate = BRIEFS[0].date;
  }}
  renderCalendar();
  renderExpansion();
</script>

</body>
</html>"""


def main():
    briefs = collect_briefs()
    index_html = render_index(briefs)
    out = REPO_PATH / "index.html"
    out.write_text(index_html, encoding="utf-8")
    print(f"Wrote {out} with {len(briefs)} brief(s)")


if __name__ == "__main__":
    main()
