#!/usr/bin/env python3
"""Make the communication-architecture slides as PDF, in English and Portuguese.

    pip install playwright && python -m playwright install chromium
    python site/slides/make_slides.py            # both languages
    python site/slides/make_slides.py pt         # one language

The words live in en.json and pt.json (one entry per slide). Change the words
there, run this script, and commit the new PDFs in architecture/.
The same content is also on the website: architecture/README.md (English)
and architecture/pt.md (Portuguese) — keep all four in step.
"""

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
W, H = 1280, 800  # 960 x 600 pt, the size of the original slides

CSS = """
@font-face { font-family: "Instrument Sans"; font-weight: 400; src: url("fonts/instrument-sans-latin-400-normal.woff2"); unicode-range: U+0000-00FF,U+2000-206F,U+2190-21FF; }
@font-face { font-family: "Instrument Sans"; font-weight: 400; src: url("fonts/instrument-sans-latin-ext-400-normal.woff2"); unicode-range: U+0100-02FF; }
@font-face { font-family: "Instrument Sans"; font-weight: 700; src: url("fonts/instrument-sans-latin-700-normal.woff2"); unicode-range: U+0000-00FF,U+2000-206F,U+2190-21FF; }
@font-face { font-family: "Instrument Sans"; font-weight: 700; src: url("fonts/instrument-sans-latin-ext-700-normal.woff2"); unicode-range: U+0100-02FF; }
@font-face { font-family: "Instrument Serif"; src: url("fonts/instrument-serif-latin-400-normal.woff2"); unicode-range: U+0000-00FF,U+2000-206F; }
@font-face { font-family: "Instrument Serif"; src: url("fonts/instrument-serif-latin-ext-400-normal.woff2"); unicode-range: U+0100-02FF; }
@font-face { font-family: "DM Mono"; src: url("fonts/dm-mono-latin-400-normal.woff2"); unicode-range: U+0000-00FF,U+2000-206F; }
@font-face { font-family: "DM Mono"; src: url("fonts/dm-mono-latin-ext-400-normal.woff2"); unicode-range: U+0100-02FF; }

:root { --paper:#fcfcfa; --ink:#1b3a32; --muted:#6e7c76; --rule:#c8d0cb; --pale:#f2f6f4;
  --green:#17604a; --greenwash:#e2f0e9; --blue:#275a72; --bluewash:#e5f0f6; --clay:#b0532f; --claywash:#fbeae1; }
@page { size: 1280px 800px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--paper); color: var(--ink); font-family: "Instrument Sans", sans-serif; }
.slide { position: relative; width: 1280px; height: 800px; overflow: hidden; background: var(--paper); page-break-after: always; }
.mono { font-family: "DM Mono", monospace; letter-spacing: .04em; }
.head { position: absolute; left: 64px; right: 64px; top: 38px; height: 31px; border-bottom: 1px solid var(--rule);
  display: flex; justify-content: space-between; font-size: 12.5px; color: var(--muted); }
.head span.sep { margin: 0 22px; }
.eyebrow { position: absolute; left: 64px; top: 94px; font-size: 13.5px; color: var(--clay); }
.title { position: absolute; left: 64px; right: 64px; top: 116px; font: 400 55px/1.05 "Instrument Serif", serif; letter-spacing: -.01em; color: var(--ink); }
.sub { position: absolute; left: 64px; right: 64px; top: 186px; font-size: 17px; color: var(--muted); }
.foot { position: absolute; left: 64px; right: 64px; top: 741px; padding-top: 18px; border-top: 1px solid var(--rule);
  display: flex; justify-content: space-between; font-size: 11.5px; color: var(--muted); }
.foot span.dot { margin: 0 16px; }
.abs { position: absolute; }

/* venn */
.caption { position: absolute; left: 0; right: 0; top: 706px; text-align: center; font-size: 17px; }
.vlabel { position: absolute; top: 672px; font-size: 13px; transform: translateX(-50%); white-space: nowrap; }

/* boxes */
.box { position: absolute; border: 1.5px solid; border-radius: 6px; padding: 26px 24px; }
.box h3 { font-size: 22px; font-weight: 700; line-height: 1.1; }
.box .bsub { font-size: 15px; margin-top: 8px; padding-bottom: 14px; border-bottom: 1px solid; }
.box .bsub.serif { font: 400 15.5px "Instrument Serif", serif; }
.box p { font-size: 15.5px; margin-top: 15px; line-height: 1.25; }
.green { border-color: var(--green); background: var(--greenwash); } .green h3, .green .bsub { color: var(--green); border-color: var(--green); }
.blue { border-color: var(--blue); background: var(--bluewash); } .blue h3, .blue .bsub { color: var(--blue); border-color: var(--blue); }
.clay { border-color: var(--clay); background: var(--claywash); } .clay h3, .clay .bsub { color: var(--clay); border-color: var(--clay); }
.shared { position: absolute; left: 64px; top: 260px; width: 764px; height: 94px; border: 1.5px solid var(--rule); border-radius: 6px;
  background: var(--pale); text-align: center; padding-top: 22px; }
.shared b { font-size: 17.5px; } .shared div { font-size: 15px; color: var(--muted); margin-top: 10px; }
.note { position: absolute; left: 64px; font-size: 17px; color: var(--muted); }

/* cards */
.card { position: absolute; top: 284px; width: 214px; height: 306px; padding: 22px 20px; }
.card .n { font-size: 12.5px; }
.card h3 { position: absolute; left: 20px; right: 20px; top: 124px; font-size: 21px; font-weight: 700; padding-bottom: 14px; border-bottom: 1px solid; }
.card p { position: absolute; left: 20px; right: 16px; top: 180px; font-size: 15px; line-height: 1.3; }
.card.g { background: var(--greenwash); border-bottom: 6px solid var(--green); } .card.g h3 { border-color: var(--green); }
.card.b { background: var(--bluewash); border-bottom: 6px solid var(--blue); } .card.b h3 { border-color: var(--blue); }
.label { position: absolute; left: 64px; font-size: 13.5px; color: var(--clay); }
.chain { position: absolute; left: 64px; right: 64px; top: 676px; display: flex; align-items: center; }
.chain b { font-size: 21px; white-space: nowrap; }
.chain svg { flex: 1; margin: 0 28px; height: 12px; max-width: 110px; }

/* steps */
.step { position: absolute; border: 1px solid #bfd0c7; border-radius: 4px; padding: 20px 20px; }
.step .n { font-size: 12.5px; color: var(--clay); }
.step h3 { font-size: 21px; font-weight: 700; line-height: 1.15; margin-top: 36px; }
.step p { font-size: 15px; color: var(--muted); margin-top: 12px; line-height: 1.3; }
.arrow { position: absolute; width: 22px; height: 12px; }
.rulebar { position: absolute; left: 64px; right: 64px; height: 1px; background: var(--rule); }
.bignote { position: absolute; left: 64px; right: 64px; font-size: 19px; }

/* band */
.band { position: absolute; left: 64px; right: 64px; top: 272px; height: 86px; border: 1.5px solid var(--blue); border-radius: 6px;
  background: var(--bluewash); display: flex; align-items: center; padding: 0 24px; }
.band b { font-size: 23px; color: var(--blue); width: 292px; }
.band span { font-size: 14px; color: var(--blue); }
.band span.dot { margin: 0 18px; }

/* timeline */
.tl-line { position: absolute; left: 106px; right: 108px; top: 419px; height: 2px; background: var(--green); }
.tl-dot { position: absolute; top: 414px; width: 12px; height: 12px; border-radius: 50%; background: var(--green); transform: translateX(-50%); }
.tl-top { position: absolute; top: 371px; font-size: 13.5px; color: var(--blue); transform: translateX(-50%); white-space: nowrap; }
.tl-bot { position: absolute; top: 449px; font-size: 15.5px; transform: translateX(-50%); white-space: nowrap; text-align: center; }
.handoff { position: absolute; left: 64px; right: 64px; top: 562px; height: 100px; background: var(--pale); padding: 24px 24px; }
.handoff .mono { font-size: 13.5px; color: var(--clay); }
.handoff p { font-size: 18px; margin-top: 12px; }

/* list */
.row { position: absolute; left: 64px; right: 64px; height: 76px; border-bottom: 1px solid var(--rule); display: flex; align-items: center; }
.row .n { width: 79px; font-size: 12.5px; color: var(--clay); }
.row b { width: 274px; font-size: 21px; color: var(--green); }
.row span { font-size: 17.5px; }
.out { position: absolute; left: 64px; right: 64px; top: 676px; display: flex; align-items: center; }
.out .mono { width: 353px; font-size: 13.5px; color: var(--clay); }
.out b { font-size: 18px; white-space: pre; }
"""


def e(text):
    return html.escape(str(text))


def rich(text):
    """**bold** inside a line."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(text))


def arrow(width=22, colour="#275a72"):
    return (f'<svg viewBox="0 0 {width} 12" width="{width}" height="12" preserveAspectRatio="none">'
            f'<line x1="0" y1="6" x2="{width - 1}" y2="6" stroke="{colour}" stroke-width="1.4"/>'
            f'<polyline points="{width - 7},1 {width - 1},6 {width - 7},11" fill="none" stroke="{colour}" stroke-width="1.4"/></svg>')


def with_arrows(text):
    """The fonts have no → sign, so draw it."""
    parts = [e(p.strip()) for p in text.split("→")]
    return f' <span style="display:inline-block;margin:0 10px;vertical-align:1px">{arrow(18, "#1b3a32")}</span> '.join(parts)


def frame(text, number, total, body, s):
    return f"""<section class="slide">
  <div class="head mono"><span>{e(text["header"][0])}<span class="sep">/</span>{e(text["header"][1])}</span><span>{number:02d} / {total:02d}</span></div>
  <div class="eyebrow mono">{e(s["eyebrow"])}</div>
  <h1 class="title">{e(s["title"])}</h1>
  <p class="sub">{e(s["sub"])}</p>
  {body}
  <div class="foot mono"><span>{'<span class="dot">·</span>'.join(e(w) for w in text["footer_left"])}</span><span>{e(text["footer_right"])}</span></div>
</section>"""


def venn(s):
    def lines(names, x, y0, size, family, weight, colour, step):
        out = ""
        for i, n in enumerate(names):
            out += (f'<text x="{x}" y="{y0 + i * step}" text-anchor="middle" font-size="{size}" '
                    f'font-family="{family}" font-weight="{weight}" fill="{colour}">{e(n)}</text>')
        return out

    left, centre, right = s["left"], s["centre"], s["right"]
    cy = 452
    svg = f"""<svg class="abs venn" style="left:0;top:0" width="1280" height="800" viewBox="0 0 1280 800">
  <circle cx="391" cy="{cy}" r="202" fill="#e5f0f6" stroke="#275a72" stroke-width="2.2"/>
  <circle cx="667" cy="{cy}" r="221" fill="#e2f0e9" stroke="#17604a" stroke-width="2.6"/>
  <circle cx="949" cy="{cy}" r="154" fill="#fbeae1" stroke="#b0532f" stroke-width="2.2"/>
  {lines(left["name"], 308, cy - 14 - (len(left["name"]) - 1) * 14, 25, "Instrument Sans", 700, "#275a72", 29)}
  {lines([left["kind"]], 308, cy + 16 + (len(left["name"]) - 1) * 14, 16, "Instrument Sans", 400, "#275a72", 0)}
  {lines(centre["name"], 667, cy - 58, 33, "Instrument Serif", 400, "#17604a", 37)}
  {lines([centre["kind"]], 667, cy + 26, 15.5, "Instrument Sans", 400, "#17604a", 0)}
  {lines(right["name"], 1016, cy - 30, 23, "Instrument Sans", 700, "#b0532f", 28)}
  {lines([right["kind"]], 1016, cy + 28, 15, "Instrument Sans", 400, "#b0532f", 0)}
  <line x1="530" y1="{cy + 86}" x2="530" y2="662" stroke="#275a72" stroke-width="1.2"/><circle cx="530" cy="{cy + 86}" r="4.5" fill="#275a72"/>
  <line x1="837" y1="{cy + 86}" x2="837" y2="662" stroke="#b0532f" stroke-width="1.2"/><circle cx="837" cy="{cy + 86}" r="4.5" fill="#b0532f"/>
</svg>"""
    return (svg
            + f'<div class="vlabel mono" style="left:530px;color:var(--blue)">{e(s["left_label"])}</div>'
            + f'<div class="vlabel mono" style="left:837px;color:var(--clay)">{e(s["right_label"])}</div>'
            + f'<p class="caption">{e(s["caption"])}</p>')


def channels(s):
    out = (f'<div class="shared"><b>{e(s["shared"]["title"])}</b><div>{e(s["shared"]["note"])}</div></div>'
           '<svg class="abs" style="left:0;top:0" width="1280" height="420"><g stroke="#c8d0cb" stroke-width="1.5" fill="none">'
           '<line x1="446" y1="355" x2="446" y2="382"/><line x1="247" y1="382" x2="642" y2="382"/>'
           '<line x1="247" y1="382" x2="247" y2="409"/><line x1="642" y1="382" x2="642" y2="409"/></g></svg>')
    lefts = [(64, 366), (462, 366), (868, 348)]
    for (x, w), b in zip(lefts, s["boxes"]):
        serif = " serif" if b.get("sub_serif") else ""
        body = "".join(f"<p>{rich(l)}</p>" for l in b["lines"])
        out += (f'<div class="box {b["colour"]}" style="left:{x}px;top:409px;width:{w}px;height:250px">'
                f'<h3>{e(b["title"])}</h3><div class="bsub{serif}">{e(b["sub"])}</div>{body}</div>')
    return out + f'<p class="note" style="top:690px">{e(s["note"])}</p>'


def pillars(s):
    out = ""
    for i, (name, q) in enumerate(s["cards"]):
        cls = "g" if i % 2 == 0 else "b"
        out += (f'<div class="card {cls}" style="left:{64 + i * 234}px"><div class="n mono">{i + 1:02d}</div>'
                f"<h3>{e(name)}</h3><p>{e(q)}</p></div>")
    out += f'<div class="label mono" style="top:631px">{e(s["chain_label"])}</div><div class="chain">'
    for i, word in enumerate(s["chain"]):
        if i:
            out += arrow(110, "#6e7c76")
        out += f"<b>{e(word)}</b>"
    return out + "</div>"


def step_row(steps, top, height, colours):
    n = len(steps)
    gap = 24
    width = (1152 - gap * (n - 1)) / n
    out = ""
    for i, (name, note) in enumerate(steps):
        x = 64 + i * (width + gap)
        out += (f'<div class="step" style="left:{x:.0f}px;top:{top}px;width:{width:.0f}px;height:{height}px;background:{colours[i]}">'
                f'<div class="n mono">{i + 1:02d}</div><h3>{e(name)}</h3><p>{e(note)}</p></div>')
        if i < n - 1:
            out += f'<div class="arrow" style="left:{x + width:.0f}px;top:{top + height / 2 - 6:.0f}px">{arrow(gap)}</div>'
    return out


def steps(s):
    colours = ["var(--greenwash)", "var(--greenwash)", "var(--bluewash)", "var(--bluewash)"]
    return (step_row(s["steps"], 308, 194, colours)
            + '<div class="rulebar" style="top:567px"></div>'
            + f'<div class="label mono" style="top:608px">{e(s["note_label"])}</div>'
            + f'<p class="bignote" style="top:640px">{e(s["note"])}</p>')


def funded(s):
    items = '<span class="dot">·</span>'.join(f"<span>{e(i)}</span>" for i in s["band_items"])
    return (f'<div class="band"><b>{e(s["band_title"])}</b><span class="mono" style="display:flex">{items}</span></div>'
            + step_row(s["steps"], 413, 162, ["var(--pale)"] * 5)
            + f'<div class="label mono" style="top:625px">{e(s["note_label"])}</div>'
            + f'<p class="bignote" style="top:657px">{e(s["note"])}</p>')


def timeline(s):
    pts = s["points"]
    x0, x1 = 106, 1172
    out = '<div class="tl-line"></div>'
    for i, (when, what) in enumerate(pts):
        x = x0 + (x1 - x0) * i / (len(pts) - 1)
        out += (f'<div class="tl-dot" style="left:{x:.0f}px"></div>'
                f'<div class="tl-top mono" style="left:{x:.0f}px">{e(when)}</div>'
                f'<div class="tl-bot" style="left:{x:.0f}px">{e(what)}</div>')
    return out + (f'<div class="handoff"><div class="mono">{e(s["note_label"])}</div>'
                  f'<p>{with_arrows(s["note"])}</p></div>')


def listing(s):
    out = ""
    for i, (word, what) in enumerate(s["rows"]):
        out += (f'<div class="row" style="top:{272 + i * 76}px"><span class="n mono">{i + 1:02d}</span>'
                f"<b>{e(word)}</b><span>{e(what)}</span></div>")
    return out + (f'<div class="out"><span class="mono">{e(s["out_label"])}</span>'
                  f'<b>{e(s["out"])}</b></div>')


KINDS = {"venn": venn, "channels": channels, "pillars": pillars, "steps": steps,
         "funded": funded, "timeline": timeline, "list": listing}


def page(text):
    slides = text["slides"]
    body = "\n".join(frame(text, i + 1, len(slides), KINDS[s["kind"]](s), s) for i, s in enumerate(slides))
    return (f'<!doctype html><html lang="{e(text["lang"])}"><head><meta charset="utf-8">'
            f'<title>{e(text["document_title"])}</title><style>{CSS}</style></head><body>{body}</body></html>')


def main(langs):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in langs:
            text = json.loads((HERE / f"{lang}.json").read_text(encoding="utf-8"))
            html_file = HERE / f"_preview-{lang}.html"
            html_file.write_text(page(text), encoding="utf-8")
            tab = browser.new_page(viewport={"width": W, "height": H})
            tab.goto(html_file.as_uri())
            tab.evaluate("document.fonts.ready")
            out = ROOT / text["output"]
            tab.pdf(path=str(out), width=f"{W}px", height=f"{H}px", print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            tab.close()
            html_file.unlink()
            print("wrote", out.relative_to(ROOT))
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:] or ["en", "pt"])
