"""
Tiny static-site builder for the GitHub Pages project report (docs/index.html).

Each project's scripts/build_site.py creates Plotly figures and tables from the
real pipeline outputs and passes them here. Charts stay interactive (zoom,
hover) because Plotly.js runs in the browser; no Python server is needed.
"""

from datetime import date
from html import escape

import plotly.graph_objects as go

PLOTLY_JS = "assets/plotly.min.js"  # bundled copy, so the page works without a CDN


def fig_html(fig: go.Figure, height: int = 420) -> str:
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=height, margin=dict(l=10, r=10, t=50, b=10), font=dict(family="Inter, sans-serif"))
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False, "responsive": True})


def table_html(df, max_rows: int = 50) -> str:
    return df.head(max_rows).to_html(index=False, classes="tbl", border=0, escape=True)


def page(*, title: str, tagline: str, accent: str, repo: str, kpis: list[tuple[str, str]],
         sections: list[tuple[str, str, str]], note: str = "", run_cmds: list[str] | None = None) -> str:
    """sections: (heading, description, inner_html)"""
    kpi_html = "".join(f'<div class="kpi"><div class="v">{escape(v)}</div><div class="l">{escape(l)}</div></div>'
                       for l, v in kpis)
    nav = "".join(f'<a href="#s{i}">{escape(h)}</a>' for i, (h, _, _) in enumerate(sections))
    body = "".join(f'<section id="s{i}"><h2>{escape(h)}</h2><p class="d">{escape(d)}</p>{inner}</section>'
                   for i, (h, d, inner) in enumerate(sections))
    cmds = "".join(f"<code>{escape(c)}</code>" for c in (run_cmds or []))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(tagline)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<script src="{PLOTLY_JS}"></script>
<style>
:root{{--a:{accent};--bg:#0B1120;--card:#111a2e;--line:#1f2a44;--t:#e2e8f0;--m:#94a3b8}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--t);font-family:Inter,system-ui,sans-serif;line-height:1.55}}
header{{padding:56px 24px 36px;background:radial-gradient(circle at 80% 0,color-mix(in srgb,var(--a) 35%,transparent),transparent 55%),linear-gradient(160deg,#0f172a,#0b1120);border-bottom:1px solid var(--line)}}
.wrap{{max-width:1180px;margin:0 auto}} .tag{{color:var(--a);font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:13px}}
h1{{font-size:clamp(30px,5vw,52px);margin:.2em 0 .25em;letter-spacing:-.02em}} .sub{{color:#cbd5e1;font-size:18px;max-width:820px}}
.btns{{margin-top:22px;display:flex;gap:10px;flex-wrap:wrap}} .btns a{{padding:10px 18px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px}}
.p{{background:var(--a);color:#0b1120}} .s{{border:1px solid var(--line);color:var(--t)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:30px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}} .kpi .v{{font-size:26px;font-weight:800;color:var(--a)}} .kpi .l{{color:var(--m);font-size:13px}}
nav{{position:sticky;top:0;background:rgba(11,17,32,.92);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);z-index:5}}
nav .wrap{{display:flex;gap:18px;overflow-x:auto;padding:12px 24px}} nav a{{color:var(--m);text-decoration:none;font-size:14px;white-space:nowrap}} nav a:hover{{color:var(--a)}}
main .wrap{{padding:10px 24px 60px}} section{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;margin-top:22px}}
h2{{margin:0 0 4px;font-size:22px}} .d{{color:var(--m);margin:0 0 12px}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px}} .grid2>div{{min-width:0;overflow:hidden}}
.tbl{{width:100%;border-collapse:collapse;font-size:13px}} .tbl th{{text-align:left;color:var(--m);border-bottom:1px solid var(--line);padding:8px}} .tbl td{{border-bottom:1px solid var(--line);padding:8px}}
.scroll{{overflow-x:auto}} .note{{background:#422006;color:#fde68a;border-radius:10px;padding:10px 14px;margin-top:18px;font-size:14px}}
.list li{{margin:6px 0}} code{{display:block;background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:6px 0;color:#a5f3fc;font-size:13px}}
footer{{color:var(--m);text-align:center;font-size:13px;padding:30px}}
@media(max-width:520px){{.grid2{{grid-template-columns:1fr}}}}
</style></head><body>
<header><div class="wrap"><div class="tag">Python Project · Live Report</div><h1>{escape(title)}</h1><div class="sub">{escape(tagline)}</div>
<div class="btns"><a class="p" href="https://github.com/rohitsingh83/{repo}">View source on GitHub</a><a class="s" href="https://github.com/rohitsingh83/{repo}#how-to-run">Run it locally</a></div>
<div class="kpis">{kpi_html}</div>{f'<div class="note">{escape(note)}</div>' if note else ''}</div></header>
<nav><div class="wrap">{nav}</div></nav>
<main><div class="wrap">{body}
<section><h2>Run the full app</h2><p class="d">This page is a static snapshot. The complete project (CLI, Streamlit dashboard, tests) runs locally:</p>{cmds}</section>
</div></main>
<script>window.addEventListener("load",()=>document.querySelectorAll(".js-plotly-plot").forEach(p=>Plotly.Plots.resize(p)));</script>
<footer>Built by Rohit Singh · generated {date.today():%d %b %Y} by <code style="display:inline;padding:2px 6px">scripts/build_site.py</code> · <a style="color:var(--a)" href="https://github.com/rohitsingh83/{repo}">github.com/rohitsingh83/{repo}</a></footer>
</body></html>"""
