"""
build_index.py — regenerates index.html for the market-briefs GitHub Pages site.

Scans the repo for brief HTML files matching:
  - US-Brief-YYYY-MM-DD.html       (US overnight wrap)
  - US-PreMarket-YYYY-MM-DD.html   (US pre-market brief)
  - APAC-Brief-YYYY-MM-DD.html     (APAC afternoon wrap)

Extracts title/headline from each file's <h1> tag where possible,
sorts newest-first, groups by week, and renders a clean landing page.

Usage: python3 build_index.py <repo_path>
"""
import sys
import re
import os
from datetime import datetime, date, timedelta
from pathlib import Path
import html

REPO_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/market-briefs"))

BRIEF_PATTERNS = {
    "us-wrap":      (re.compile(r"^US-Brief-(\d{4})-(\d{2})-(\d{2})\.html$"),     "🇺🇸 US Overnight Wrap",  "us-wrap"),
    "us-premarket": (re.compile(r"^US-PreMarket-(\d{4})-(\d{2})-(\d{2})\.html$"), "🇺🇸 US Pre-Market",       "us-premarket"),
    "apac":         (re.compile(r"^APAC-Brief-(\d{4})-(\d{2})-(\d{2})\.html$"),   "🌏 APAC Wrap",            "apac"),
}

def extract_headline(filepath: Path) -> str:
    """Try to pull the <h1> text from the file. Falls back to '' if not found."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(8000)  # only need the head
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.DOTALL | re.IGNORECASE)
        if not m:
            return ""
        inner = m.group(1)
        # strip tags + collapse whitespace + drop emoji-only prefixes
        inner = re.sub(r"<[^>]+>", "", inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        # Strip leading flag emoji + common prefixes
        inner = re.sub(r"^(🇺🇸|🌏|🇨🇳|🇪🇺)\s*", "", inner)
        # Strip date suffix like "— Mon May 18, 2026"
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
                    "date": d, "kind": kind, "label": label, "css_class": css_class,
                    "filename": fp.name, "headline": headline,
                })
                break
    briefs.sort(key=lambda b: (b["date"], b["kind"]), reverse=True)
    return briefs

def week_label(d: date) -> str:
    # Monday-anchored week
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    if monday.month == sunday.month:
        return f"Week of {monday.strftime('%b')} {monday.day}–{sunday.day}, {monday.year}"
    return f"Week of {monday.strftime('%b %d')} – {sunday.strftime('%b %d')}, {monday.year}"

def render_index(briefs):
    if briefs:
        latest = briefs[0]["date"]
    else:
        latest = date.today()

    # Group by week
    weeks = {}
    for b in briefs:
        wk = week_label(b["date"])
        weeks.setdefault(wk, []).append(b)

    rows_html = []
    for wk, items in weeks.items():
        rows_html.append(f'<div class="week-header">{html.escape(wk)}</div>')
        for b in items:
            day_name = b["date"].strftime("%a")
            day_short = b["date"].strftime("%b %d")
            headline = html.escape(b["headline"]) if b["headline"] else ""
            rows_html.append(f'''
        <a href="./{html.escape(b["filename"])}" class="brief-row {b["css_class"]}" data-kind="{b["css_class"]}">
          <div class="brief-date">
            <div class="bd-dow">{day_name}</div>
            <div class="bd-dom">{b["date"].day}</div>
            <div class="bd-mon">{b["date"].strftime("%b").upper()}</div>
          </div>
          <div class="brief-meta">
            <div class="brief-label">{b["label"]}</div>
            <div class="brief-headline">{headline}</div>
            <div class="brief-filename">{html.escape(b["filename"])}</div>
          </div>
          <div class="brief-arrow">→</div>
        </a>''')

    rows_section = "\n".join(rows_html) if rows_html else '<div class="empty">No briefs yet — first one lands tomorrow morning (8am China time).</div>'

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
  header.hero {{
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    color: #0f172a;
    padding: 32px 28px 24px;
    border-radius: 14px;
    border-left: 6px solid #3b82f6;
    border-top: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 18px;
    box-shadow: 0 2px 6px rgba(15,23,42,0.05);
    position: relative;
    overflow: hidden;
  }}
  header.hero::after {{
    content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #f59e0b 100%);
  }}
  header.hero .eyebrow {{ font-size: 11px; color: #3b82f6; text-transform: uppercase; letter-spacing: 1.4px; font-weight: 700; margin-bottom: 6px; }}
  header.hero h1 {{ margin: 0 0 8px 0; font-size: 28px; letter-spacing: -0.5px; font-weight: 800; }}
  header.hero .sub {{ color: #475569; font-size: 14px; margin-bottom: 14px; max-width: 620px; }}
  header.hero .tags .tag {{
    display: inline-block;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
    padding: 4px 11px;
    border-radius: 12px;
    font-size: 10.5px;
    font-weight: 700;
    margin-right: 6px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .filter-bar {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;
    background: #ffffff;
    padding: 12px 14px;
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
  }}
  .filter-btn:hover {{ background: #e2e8f0; color: #0f172a; }}
  .filter-btn.active {{ background: #3b82f6; color: #fff; border-color: #3b82f6; box-shadow: 0 1px 3px rgba(59,130,246,0.3); }}
  .filter-btn.us-wrap.active      {{ background: #1d4ed8; border-color: #1d4ed8; }}
  .filter-btn.us-premarket.active {{ background: #047857; border-color: #047857; }}
  .filter-btn.apac.active         {{ background: #b91c1c; border-color: #b91c1c; }}
  .week-header {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #64748b;
    font-weight: 700;
    margin: 18px 0 8px;
    padding: 0 4px;
  }}
  .brief-row {{
    display: flex;
    align-items: stretch;
    gap: 14px;
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
  .brief-row:hover {{ transform: translateY(-1px); box-shadow: 0 4px 10px rgba(15,23,42,0.08); }}
  .brief-row.us-wrap {{ border-left-color: #1d4ed8; }}
  .brief-row.us-premarket {{ border-left-color: #047857; }}
  .brief-row.apac {{ border-left-color: #b91c1c; }}
  .brief-date {{
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #fff;
    border-radius: 8px;
    padding: 6px 4px 5px;
    min-width: 54px;
    text-align: center;
    flex-shrink: 0;
  }}
  .brief-row.us-wrap .brief-date {{ background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%); }}
  .brief-row.us-premarket .brief-date {{ background: linear-gradient(135deg, #064e3b 0%, #047857 100%); }}
  .brief-row.apac .brief-date {{ background: linear-gradient(135deg, #7f1d1d 0%, #b91c1c 100%); }}
  .bd-dow {{ font-size: 9px; font-weight: 700; letter-spacing: 1px; color: rgba(255,255,255,0.7); text-transform: uppercase; }}
  .bd-dom {{ font-size: 20px; font-weight: 800; line-height: 1.1; margin: 2px 0 1px; letter-spacing: -0.5px; }}
  .bd-mon {{ font-size: 8.5px; color: rgba(255,255,255,0.6); letter-spacing: 0.9px; font-weight: 600; }}
  .brief-meta {{ flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 3px; }}
  .brief-label {{ font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.4px; }}
  .brief-headline {{ font-size: 14px; font-weight: 700; color: #0f172a; line-height: 1.35; }}
  .brief-filename {{ font-size: 10.5px; color: #94a3b8; font-family: ui-monospace, monospace; }}
  .brief-arrow {{ color: #cbd5e1; font-size: 18px; align-self: center; font-weight: 600; }}
  .brief-row:hover .brief-arrow {{ color: #3b82f6; }}
  .empty {{
    background: #fff;
    border-radius: 10px;
    border: 1px dashed #cbd5e1;
    padding: 32px 18px;
    text-align: center;
    color: #64748b;
    font-size: 14px;
  }}
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

  @media (max-width: 640px) {{
    body {{ padding: 12px; font-size: 14px; }}
    header.hero {{ padding: 22px 18px 18px; }}
    header.hero h1 {{ font-size: 22px; }}
    header.hero .sub {{ font-size: 13px; }}
    .filter-btn {{ font-size: 11px; padding: 6px 11px; }}
    .brief-row {{ padding: 10px 12px; gap: 10px; }}
    .brief-date {{ min-width: 48px; padding: 5px 3px 4px; }}
    .bd-dom {{ font-size: 18px; }}
    .brief-headline {{ font-size: 13px; }}
    .brief-filename {{ font-size: 10px; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <div class="eyebrow">Daily Market Briefs · Mon-Fri</div>
    <h1>Carson's Market Briefs</h1>
    <div class="sub">Cross-asset overnight wraps, pre-market positioning, and APAC session recaps — interview-prep edition for Sales &amp; Trading (Rates/FX/EM), Investment Banking (DCM/M&amp;A), and Equity Research (Semis + AI focus).</div>
    <div class="tags">
      <span class="tag">Rates/Macro</span>
      <span class="tag">FX/EM</span>
      <span class="tag">DCM/M&amp;A</span>
      <span class="tag">Equity Research</span>
    </div>
  </header>

  <div class="filter-bar">
    <button class="filter-btn active" data-filter="all">All Briefs</button>
    <button class="filter-btn us-wrap" data-filter="us-wrap">🇺🇸 US Overnight</button>
    <button class="filter-btn us-premarket" data-filter="us-premarket">🇺🇸 US Pre-Market</button>
    <button class="filter-btn apac" data-filter="apac">🌏 APAC Wrap</button>
  </div>

  <div class="brief-list" id="brief-list">
    {rows_section}
  </div>

  <footer class="foot">
    <span class="badge">Last updated {latest.strftime("%b %d, %Y")}</span>
    Built by Carson · Auto-published Mon-Fri · No investment advice<br>
    Sources: BLS, FRED, US Treasury, Bloomberg, CNBC, Reuters, Yahoo Finance, EIA · Estimates labeled where data not publicly confirmable
  </footer>

</div>

<script>
  document.querySelectorAll(".filter-btn").forEach(btn => {{
    btn.addEventListener("click", () => {{
      const filter = btn.dataset.filter;
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".brief-row").forEach(row => {{
        if (filter === "all" || row.dataset.kind === filter) {{
          row.style.display = "";
        }} else {{
          row.style.display = "none";
        }}
      }});
      // Hide week headers that have no visible briefs
      document.querySelectorAll(".week-header").forEach(wh => {{
        let next = wh.nextElementSibling;
        let hasVisible = false;
        while (next && next.classList.contains("brief-row")) {{
          if (next.style.display !== "none") {{ hasVisible = true; break; }}
          next = next.nextElementSibling;
        }}
        wh.style.display = hasVisible ? "" : "none";
      }});
    }});
  }});
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
