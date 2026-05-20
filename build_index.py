"""
build_index.py — regenerates index.html for the market-briefs GitHub Pages site.

Region-based layout: 🇺🇸 US Markets + 🌏 APAC Markets sections, each with
chronological brief cards (newest first). Top tabs filter between All / US / APAC.

Scans the repo for brief HTML files matching:
  - US-Brief-YYYY-MM-DD.html       (US overnight wrap)
  - US-PreMarket-YYYY-MM-DD.html   (US pre-market brief)
  - APAC-Brief-YYYY-MM-DD.html     (APAC afternoon wrap)

Usage: python3 build_index.py <repo_path>
"""
import sys
import re
import os
from datetime import datetime, date, timedelta
from pathlib import Path
import html

REPO_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/market-briefs"))

# Each pattern maps to: (regex, label, css_class, region, region_label)
BRIEF_PATTERNS = {
    "us-wrap":      (re.compile(r"^US-Brief-(\d{4})-(\d{2})-(\d{2})\.html$"),     "US Overnight Wrap",  "us-wrap",      "us",   "🇺🇸 US Markets"),
    "us-premarket": (re.compile(r"^US-PreMarket-(\d{4})-(\d{2})-(\d{2})\.html$"), "US Pre-Market",       "us-premarket", "us",   "🇺🇸 US Markets"),
    "apac":         (re.compile(r"^APAC-Brief-(\d{4})-(\d{2})-(\d{2})\.html$"),   "APAC Wrap",            "apac",         "apac", "🌏 APAC Markets"),
}


def extract_headline(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(80000)
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
        for kind, (pattern, label, css_class, region, region_label) in BRIEF_PATTERNS.items():
            m = pattern.match(fp.name)
            if m:
                d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                headline = extract_headline(fp)
                briefs.append({
                    "date": d, "kind": kind, "label": label, "css_class": css_class,
                    "region": region, "region_label": region_label,
                    "filename": fp.name, "headline": headline,
                })
                break
    briefs.sort(key=lambda b: (b["date"], b["kind"]), reverse=True)
    return briefs


def render_brief_card(b):
    headline = html.escape(b["headline"]) if b["headline"] else html.escape(b["label"])
    day_name = b["date"].strftime("%a")
    return f'''
        <a href="./{html.escape(b["filename"])}" class="brief-row {b["css_class"]}" data-region="{b["region"]}" data-kind="{b["css_class"]}">
          <div class="brief-date">
            <div class="bd-dow">{day_name}</div>
            <div class="bd-dom">{b["date"].day}</div>
            <div class="bd-mon">{b["date"].strftime("%b").upper()}</div>
          </div>
          <div class="brief-meta">
            <div class="brief-label">{html.escape(b["label"])}</div>
            <div class="brief-headline">{headline}</div>
            <div class="brief-filename">{html.escape(b["filename"])}</div>
          </div>
          <div class="brief-arrow">→</div>
        </a>'''


def render_region_section(region_key, region_label, region_briefs):
    if not region_briefs:
        empty = f'<div class="region-empty">No {html.escape(region_label)} briefs yet.</div>'
        cards_html = empty
    else:
        cards_html = "\n".join(render_brief_card(b) for b in region_briefs)

    return f'''
    <section class="region-section" data-region="{region_key}">
      <div class="region-header">
        <div class="region-label">{html.escape(region_label)}</div>
        <div class="region-count">{len(region_briefs)} brief{"" if len(region_briefs) == 1 else "s"}</div>
      </div>
      <div class="region-cards">
        {cards_html}
      </div>
    </section>'''


def render_index(briefs):
    if briefs:
        latest = briefs[0]["date"]
    else:
        latest = date.today()

    us_briefs = [b for b in briefs if b["region"] == "us"]
    apac_briefs = [b for b in briefs if b["region"] == "apac"]

    us_section = render_region_section("us", "🇺🇸 US Markets", us_briefs)
    apac_section = render_region_section("apac", "🌏 APAC Markets", apac_briefs)

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
  .wrap {{ max-width: 920px; margin: 0 auto; }}

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
    background: linear-gradient(90deg, #3b82f6 0%, #b91c1c 100%);
  }}
  header.hero .eyebrow {{ font-size: 10.5px; color: #3b82f6; text-transform: uppercase; letter-spacing: 1.4px; font-weight: 700; margin-bottom: 4px; }}
  header.hero h1 {{ margin: 0 0 4px 0; font-size: 22px; letter-spacing: -0.4px; font-weight: 800; }}
  header.hero .sub {{ color: #64748b; font-size: 12.5px; }}

  /* REGION TAB BAR (segmented control style) */
  .region-tabs {{
    display: flex;
    background: #ffffff;
    border-radius: 12px;
    padding: 5px;
    border: 1px solid #e2e8f0;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    gap: 4px;
  }}
  .region-tab {{
    flex: 1;
    background: transparent;
    border: none;
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
    letter-spacing: 0.2px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }}
  .region-tab:hover {{ background: #f1f5f9; color: #0f172a; }}
  .region-tab.active {{
    background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
    color: #ffffff;
    box-shadow: 0 1px 3px rgba(59,130,246,0.35);
  }}
  .region-tab.us.active {{
    background: linear-gradient(180deg, #1d4ed8 0%, #1e3a8a 100%);
    box-shadow: 0 1px 3px rgba(29,78,216,0.4);
  }}
  .region-tab.apac.active {{
    background: linear-gradient(180deg, #b91c1c 0%, #7f1d1d 100%);
    box-shadow: 0 1px 3px rgba(185,28,28,0.4);
  }}
  .region-tab-count {{
    font-size: 10.5px;
    background: rgba(255,255,255,0.18);
    color: inherit;
    padding: 1px 7px;
    border-radius: 10px;
    font-weight: 700;
    margin-left: 2px;
  }}
  .region-tab:not(.active) .region-tab-count {{
    background: #f1f5f9;
    color: #94a3b8;
  }}

  /* REGION SECTION */
  .region-section {{
    margin-bottom: 18px;
  }}
  .region-section.hidden {{ display: none; }}
  .region-header {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 0 4px 10px;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 12px;
  }}
  .region-label {{
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.2px;
  }}
  .region-count {{
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }}
  .region-cards {{ display: flex; flex-direction: column; gap: 8px; }}
  .region-empty {{
    background: #fff;
    border-radius: 10px;
    border: 1px dashed #cbd5e1;
    padding: 22px 16px;
    text-align: center;
    color: #94a3b8;
    font-size: 13px;
    font-style: italic;
  }}

  /* BRIEF CARD */
  .brief-row {{
    display: flex;
    align-items: stretch;
    gap: 14px;
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #94a3b8;
    padding: 12px 14px;
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
  .brief-label {{ font-size: 10.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: #475569; }}
  .brief-row.us-wrap .brief-label {{ color: #1d4ed8; }}
  .brief-row.us-premarket .brief-label {{ color: #047857; }}
  .brief-row.apac .brief-label {{ color: #b91c1c; }}
  .brief-headline {{ font-size: 14px; font-weight: 700; color: #0f172a; line-height: 1.35; }}
  .brief-filename {{ font-size: 10.5px; color: #94a3b8; font-family: ui-monospace, monospace; }}
  .brief-arrow {{ color: #cbd5e1; font-size: 18px; align-self: center; font-weight: 600; }}
  .brief-row:hover .brief-arrow {{ color: #3b82f6; }}

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
    header.hero h1 {{ font-size: 19px; }}
    header.hero .sub {{ font-size: 11.5px; }}
    .region-tab {{ font-size: 12px; padding: 9px 8px; gap: 4px; }}
    .region-tab-count {{ font-size: 10px; padding: 1px 6px; }}
    .region-label {{ font-size: 15px; }}
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
    <h1>Market Overview</h1>
    <div class="sub">US Overnight Wrap (8am China) · US Pre-Market (8pm China) · APAC Wrap (4pm China)</div>
  </header>

  <div class="region-tabs">
    <button class="region-tab active" data-region="all">All <span class="region-tab-count">{len(briefs)}</span></button>
    <button class="region-tab us" data-region="us">🇺🇸 US <span class="region-tab-count">{len(us_briefs)}</span></button>
    <button class="region-tab apac" data-region="apac">🌏 APAC <span class="region-tab-count">{len(apac_briefs)}</span></button>
  </div>

  {us_section}
  {apac_section}

  <footer class="foot">
    <span class="badge">Last updated {latest.strftime("%b %d, %Y")}</span>
    Built by Carson · Auto-published Mon-Fri · No investment advice<br>
    Data: WebSearch-verified · CNBC, Trading Economics, Reuters, Bloomberg, FRED
  </footer>

</div>

<script>
  document.querySelectorAll(".region-tab").forEach(btn => {{
    btn.addEventListener("click", () => {{
      const region = btn.dataset.region;
      document.querySelectorAll(".region-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".region-section").forEach(sec => {{
        if (region === "all" || sec.dataset.region === region) {{
          sec.classList.remove("hidden");
        }} else {{
          sec.classList.add("hidden");
        }}
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
