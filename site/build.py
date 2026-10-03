#!/usr/bin/env python3
"""Build the comms handbook website from the Markdown pages.

    python site/build.py        ->  writes the website into _site/

Every .md page in the repository becomes a web page. For each page the
script asks git who changed it last and when, and prints that under the
title ("Last updated 3 October 2026 by Name").

Settings live in site/config.json. The look lives in site/assets/site.css
and site/template.html. Editors of the handbook never need to touch this
folder: they edit the .md pages and the site rebuilds itself.
"""

import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "_site"
SKIP_DIRS = {"site", "_site", ".git", ".github", "node_modules"}

CFG = json.loads((SITE / "config.json").read_text(encoding="utf-8"))
SEASON = CFG["season"]
TZ = ZoneInfo(CFG.get("timezone", "UTC"))
REPO = os.environ.get("GITHUB_REPOSITORY") or CFG.get("repository", "")
BRANCH = os.environ.get("GITHUB_REF_NAME") or CFG.get("branch", "main")
TEMPLATE = (SITE / "template.html").read_text(encoding="utf-8")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

STATUS_CHIPS = {
    "idea": "idea", "material in": "material", "ready": "ready",
    "published": "published", "to do": "todo", "done": "done",
}
FUND_TAGS = {
    "CES": "European Solidarity Corps: EU emblem and funding sentence are mandatory",
    "ENR": "Enraizar no Interior: co-financing logos and funding sentence are mandatory",
}


# ---------------------------------------------------------------- helpers

def esc(text):
    return html.escape(str(text), quote=True)


def season(path):
    return path.replace("{season}", SEASON)


def out_rel(src_rel):
    """guidelines.md -> guidelines.html ; calendar/README.md -> calendar/index.html"""
    p = Path(src_rel)
    if p.name.lower() == "readme.md":
        return (p.parent / "index.html").as_posix()
    return p.with_suffix(".html").as_posix()


def root_prefix(page_out):
    return "../" * (len(Path(page_out).parts) - 1)


def fmt_date(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def git(*args):
    try:
        res = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                             text=True, encoding="utf-8", check=True)
        return res.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def friendly(name):
    return CFG.get("names", {}).get(name, name)


def stamp_for(src_rel=None):
    """Who changed this page last, and when. Falls back to the file date when
    there is no git history yet (for example a preview on your own computer)."""
    args = ["log", "-1", "--format=%an%x1f%aI"]
    if src_rel:
        args += ["--", src_rel]
    line = git(*args)
    if line and "\x1f" in line:
        name, iso = line.split("\x1f", 1)
        when = dt.datetime.fromisoformat(iso).astimezone(TZ)
        return {"name": friendly(name), "when": when}
    if src_rel:
        when = dt.datetime.fromtimestamp((ROOT / src_rel).stat().st_mtime, TZ)
    else:
        when = dt.datetime.now(TZ)
    return {"name": CFG.get("fallback_name", "the team"), "when": when}


def stamp_html(stamp, history_url="", lead="Last updated"):
    d = stamp["when"].date()
    out = (f'{lead} <time datetime="{d.isoformat()}">{fmt_date(d)}</time> '
           f'by <b>{esc(stamp["name"])}</b>')
    if history_url:
        out += f' <a class="history" href="{esc(history_url)}">See all changes</a>'
    return out


def gh_slug(value, separator="-"):
    """Heading anchors the same way GitHub makes them, so links work in both places."""
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return value.replace(" ", "-")


# ------------------------------------------------- markdown -> html pieces

def custom_blocks(text):
    """```flow and ```roles blocks: one line per box, parts separated by |"""

    def flow(match):
        items = []
        for line in match.group(1).strip().splitlines():
            parts = [esc(p.strip()) for p in line.split("|")]
            note = f"<span>{parts[1]}</span>" if len(parts) > 1 else ""
            items.append(f"<li><b>{parts[0]}</b>{note}</li>")
        return '\n\n<ol class="flow">' + "".join(items) + "</ol>\n\n"

    def roles(match):
        items = []
        for i, line in enumerate(match.group(1).strip().splitlines(), 1):
            parts = [esc(p.strip()) for p in line.split("|")] + ["", ""]
            items.append(f'<li class="role role-{i}"><b>{parts[0]}</b>'
                         f"<span>{parts[1]}</span><small>{parts[2]}</small></li>")
        return '\n\n<ul class="roles">' + "".join(items) + "</ul>\n\n"

    text = re.sub(r"^```flow\n(.*?)^```\s*$", flow, text, flags=re.S | re.M)
    text = re.sub(r"^```roles\n(.*?)^```\s*$", roles, text, flags=re.S | re.M)
    return text


def autolink(text):
    """A bare https://… address becomes a link, as it does on GitHub."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and "http" in line:
            parts = line.split("`")
            for i in range(0, len(parts), 2):               # skip `inline code`
                parts[i] = re.sub(r'(?<![(<"\[])(https?://[^\s|)>\]]+[^\s|)>\].,;:!?])',
                                  r"<\1>", parts[i])
            line = "`".join(parts)
        out.append(line)
    return "\n".join(out)


def rewrite_links(body, page_src):
    """Links between .md pages become links between .html pages."""
    page_dir = Path(page_src).parent

    def fix(match):
        href = match.group(1)
        if re.match(r"^(https?:|mailto:|tel:|#)", href):
            return match.group(0)
        path, _, anchor = href.partition("#")
        if path.lower().endswith(".md"):
            target = os.path.normpath((page_dir / path).as_posix())
            if target.lower() == "readme.md":          # the repository front page
                new = os.path.relpath("index.html", page_dir.as_posix() or ".")
            else:
                new = os.path.relpath(out_rel(target), page_dir.as_posix() or ".")
            path = Path(new).as_posix()
        elif path.endswith("/"):
            path += "index.html"
        return f'href="{path}{"#" + anchor if anchor else ""}"'

    return re.sub(r'href="([^"]+)"', fix, body)


def polish_tables(body):
    """Wrap tables so they can scroll, label each cell for the phone layout,
    and turn status words into chips."""

    def cell(content, label):
        plain = re.sub(r"<[^>]+>", "", content).strip()
        key = plain.lower()
        if key in STATUS_CHIPS:
            content = f'<span class="chip chip-{STATUS_CHIPS[key]}">{plain}</span>'
        elif plain in FUND_TAGS:
            content = f'<abbr class="fund" title="{esc(FUND_TAGS[plain])}">{plain}</abbr>'
        elif plain == "?":
            content = '<span class="open" title="Still to be decided">to decide</span>'
        elif plain in ("—", "-", ""):
            content = '<span class="none">—</span>' if plain else ""
        label_attr = f' data-label="{esc(label)}"' if label else ""
        return f"<td{label_attr}>{content}</td>"

    def table(match):
        t = match.group(0)
        heads = [re.sub(r"<[^>]+>", "", h).strip()
                 for h in re.findall(r"<th[^>]*>(.*?)</th>", t, flags=re.S)]
        classes = []
        if not any(heads):
            classes.append("plain")
        if len(heads) >= 4:
            classes.append("stack")

        def row(m):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", m.group(1), flags=re.S)
            if not any(re.sub(r"<[^>]+>", "", c).strip() for c in cells):
                return ""                                   # drop empty spacer rows
            out = "".join(cell(c, heads[i] if i < len(heads) else "")
                          for i, c in enumerate(cells))
            return f"<tr>{out}</tr>"

        head, sep, rest = t.partition("<tbody>")
        rest = re.sub(r"<tr>(.*?)</tr>", row, rest, flags=re.S)
        t = head + sep + rest
        cls = f' class="{" ".join(classes)}"' if classes else ""
        t = t.replace("<table>", f"<table{cls}>", 1)
        return f'<div class="table-wrap" tabindex="0">{t}</div>'

    return re.sub(r"<table>.*?</table>", table, body, flags=re.S)


def polish_tasks(body):
    """- [ ] lines become real checkboxes (for ticking while you work; not saved)."""
    body = re.sub(r"<li>\s*(?:<p>)?\[ \]\s*(.*?)(?:</p>)?\s*</li>",
                  r'<li class="task"><label><input type="checkbox"> <span>\1</span></label></li>',
                  body, flags=re.S)
    return re.sub(r"<ul>\s*(<li class=\"task\">)", r'<ul class="tasks">\1', body)


def render(text, page_src):
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
        extension_configs={"toc": {"slugify": gh_slug}},
        output_format="html",
    )
    body = md.convert(custom_blocks(autolink(text)))
    body = rewrite_links(body, page_src)
    body = polish_tables(body)
    body = polish_tasks(body)
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a class="ext" href="\1" rel="noopener"', body)
    toc = [t for t in md.toc_tokens if t["level"] == 2] if md.toc_tokens else []
    # If the page has no level-2 tokens at top level, look one level down (below the h1).
    if not toc and md.toc_tokens:
        toc = [c for t in md.toc_tokens for c in t.get("children", []) if c["level"] == 2]
    return body, toc


# ------------------------------------------------------------- the pages

def find_pages():
    pages = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or rel.as_posix().lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^# +(.+?)\s*$", text, flags=re.M)
        title = m.group(1).strip() if m else rel.stem.replace("-", " ").title()
        if m:
            text = text[:m.start()] + text[m.end():]
        pages.append({"src": rel.as_posix(), "out": out_rel(rel.as_posix()),
                      "title": title, "text": text,
                      "stamp": stamp_for(rel.as_posix())})
    return pages


def nav_html(pages, current_src, prefix):
    nav_targets = {season(n["page"]) for n in CFG["nav"]}
    shown_folders = set()
    items = []
    for entry in CFG["nav"]:
        target = season(entry["page"])
        href = prefix + (out_rel(target) if target else "index.html")
        folder = Path(target).parent.as_posix() if target else "."
        current = current_src == target
        # Pages that sit in the same folder but have no nav entry of their own
        children = [] if folder == "." else [
            p for p in pages
            if Path(p["src"]).parent.as_posix() == folder
            and p["src"] not in nav_targets
            and not p["src"].lower().endswith("readme.md")]
        within = current or any(c["src"] == current_src for c in children)
        sub = ""
        if within and children and folder not in shown_folders:
            shown_folders.add(folder)
            links = ""
            for c in children:
                cur = ' aria-current="page"' if c["src"] == current_src else ""
                links += f'<li><a href="{prefix}{c["out"]}"{cur}>{esc(short_title(c["title"]))}</a></li>'
            sub = f"<ul>{links}</ul>"
        attr = ' aria-current="page"' if current else (' class="in"' if sub else "")
        items.append(f'<li><a href="{href}"{attr}>{esc(entry["label"])}</a>{sub}</li>')
    return "<ul>" + "".join(items) + "</ul>"


def short_title(title):
    return re.split(r" — | - ", title)[0]


def page_shell(*, title_tag, prefix, nav, main, site_stamp):
    robots = ('<meta name="robots" content="noindex, nofollow">'
              if CFG.get("hide_from_search_engines") else "")
    repo_link = (f' Built from <a href="https://github.com/{esc(REPO)}">the pages on GitHub</a>.'
                 if REPO else "")
    values = {
        "title_tag": esc(title_tag), "root": prefix, "robots": robots, "nav": nav,
        "main": main, "site_name": esc(CFG["site_name"]),
        "site_tagline": esc(CFG.get("site_tagline", "")),
        "site_stamp": stamp_html(site_stamp, lead="Site last updated") + "." + repo_link,
    }
    page = TEMPLATE
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", value)
    return page


def notice_html():
    return f'<p class="notice">{esc(CFG["notice"])}</p>' if CFG.get("notice") else ""


def build_page(page, pages, site_stamp):
    prefix = root_prefix(page["out"])
    body, toc = render(page["text"], page["src"])
    if REPO:
        edit_url = f"https://github.com/{REPO}/edit/{BRANCH}/{page['src']}"
        history_url = f"https://github.com/{REPO}/commits/{BRANCH}/{page['src']}"
    else:
        edit_url = prefix + "how-to/edit-a-page.html"
        history_url = ""
    toc_block = ""
    if len(toc) >= 3:
        links = "".join(f'<li><a href="#{t["id"]}">{t["name"]}</a></li>' for t in toc)
        toc_block = (f'<nav class="toc" aria-label="On this page"><details open>'
                     f"<summary>On this page</summary><ol>{links}</ol></details></nav>")
    main = f"""
{notice_html()}
<header class="page-head">
  <h1>{esc(page["title"])}</h1>
  <div class="meta">
    <p class="stamp">{stamp_html(page["stamp"], history_url)}</p>
    <a class="edit" href="{esc(edit_url)}">Edit this page</a>
  </div>
</header>
{toc_block}
<div class="prose">
{body}
</div>"""
    return page_shell(title_tag=f'{short_title(page["title"])} · {CFG["site_name"]}',
                      prefix=prefix, nav=nav_html(pages, page["src"], prefix),
                      main=main, site_stamp=site_stamp)


def calendar_posts(pages):
    """Read the 'Posts' table of every calendar/YYYY-MM.md page."""
    posts = []
    for page in pages:
        m = re.fullmatch(r"calendar/(\d{4})-(\d{2})\.md", page["src"])
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        section = re.split(r"^## +Posts\s*$", page["text"], flags=re.M)
        if len(section) < 2:
            continue
        rows = [l for l in section[1].split("\n## ")[0].splitlines() if l.strip().startswith("|")]
        if len(rows) < 3:
            continue
        heads = [h.strip().lower() for h in rows[0].strip().strip("|").split("|")]
        for line in rows[2:]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            row = dict(zip(heads, cells))
            day = re.search(r"\d{1,2}", row.get("date", ""))
            if not day:
                continue
            try:
                date = dt.date(year, month, int(day.group(0)))
            except ValueError:
                continue
            what = markdown.markdown(row.get("what", ""))
            what = re.sub(r"^<p>|</p>$", "", what.strip())
            posts.append({"date": date, "what": what, "channel": row.get("channel", ""),
                          "status": row.get("status", ""), "fund": row.get("fund", ""),
                          "page": page["out"]})
    return sorted(posts, key=lambda p: p["date"])


def build_home(pages, site_stamp):
    home = CFG["home"]
    signs = "".join(
        f'<li><a class="sign" href="{out_rel(season(s["page"]))}">'
        f'<b>{esc(s["label"])}</b><span>{esc(s["note"])}</span></a></li>'
        for s in home["signs"])

    today = dt.datetime.now(TZ).date()
    posts = calendar_posts(pages)
    shown = 0
    items = []
    for p in posts:
        upcoming = p["date"] >= today
        hidden = "" if (upcoming and shown < 4) else " hidden"
        shown += 1 if (upcoming and shown < 4) else 0
        key = p["status"].lower()
        chip = (f'<span class="chip chip-{STATUS_CHIPS[key]}">{esc(p["status"])}</span>'
                if key in STATUS_CHIPS else "")
        fund = (f'<abbr class="fund" title="{esc(FUND_TAGS[p["fund"]])}">{esc(p["fund"])}</abbr>'
                if p["fund"] in FUND_TAGS else "")
        weekday = p["date"].strftime("%a")
        items.append(
            f'<li data-date="{p["date"].isoformat()}"{hidden}>'
            f'<time datetime="{p["date"].isoformat()}"><b>{p["date"].day}</b> '
            f'{MONTHS[p["date"].month - 1][:3]}<small>{weekday}</small></time>'
            f'<div><a href="{p["page"]}">{p["what"]}</a>'
            f'<p>{esc(p["channel"])} {fund} {chip}</p></div></li>')
    empty_hidden = " hidden" if shown else ""
    coming = f"""
<section class="coming" aria-labelledby="coming-title">
  <h2 id="coming-title">Coming up</h2>
  <ol class="agenda" id="agenda">{"".join(items)}</ol>
  <p class="empty" id="agenda-empty"{empty_hidden}>Nothing is planned ahead.
    <a href="how-to/add-a-post-to-the-calendar.html">Add a post to the calendar</a>.</p>
  <p><a href="calendar/index.html">Open the full calendar</a></p>
</section>"""

    recent = sorted(pages, key=lambda p: p["stamp"]["when"], reverse=True)[:5]
    recent_items = "".join(
        f'<li><a href="{p["out"]}">{esc(short_title(p["title"]))}</a>'
        f'<span><time datetime="{p["stamp"]["when"].date().isoformat()}">'
        f'{fmt_date(p["stamp"]["when"].date())}</time> by <b>{esc(p["stamp"]["name"])}</b></span></li>'
        for p in recent)

    main = f"""
{notice_html()}
<header class="page-head home-head">
  <h1>{esc(home["title"])}</h1>
  <p class="lead">{esc(home["intro"])}</p>
</header>
<section aria-labelledby="signs-title">
  <h2 id="signs-title">{esc(home["signs_title"])}</h2>
  <ul class="signs">{signs}</ul>
</section>
<div class="home-cols">
{coming}
<section class="recent" aria-labelledby="recent-title">
  <h2 id="recent-title">Last changes</h2>
  <ul class="changes">{recent_items}</ul>
</section>
</div>"""
    return page_shell(title_tag=CFG["site_name"], prefix="",
                      nav=nav_html(pages, "", ""), main=main, site_stamp=site_stamp)


def build_404(pages, site_stamp):
    name = REPO.split("/")[-1] if REPO else ""
    base = "/" if (not name or name.endswith(".github.io") or CFG.get("custom_domain")) else f"/{name}/"
    main = f"""
<header class="page-head">
  <h1>This page does not exist</h1>
  <p class="lead">It may have been renamed or moved. Start again from the
  <a href="{base}index.html">home page</a>.</p>
</header>"""
    return page_shell(title_tag=f'Page not found · {CFG["site_name"]}', prefix=base,
                      nav=nav_html(pages, "404", base), main=main, site_stamp=site_stamp)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    pages = find_pages()
    site_stamp = stamp_for()

    for page in pages:
        target = OUT / page["out"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_page(page, pages, site_stamp), encoding="utf-8")
    (OUT / "index.html").write_text(build_home(pages, site_stamp), encoding="utf-8")
    (OUT / "404.html").write_text(build_404(pages, site_stamp), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    shutil.copytree(SITE / "assets", OUT / "assets")
    # Other files that pages link to (PDFs, images) are copied as they are.
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if (path.is_file() and rel.parts[0] not in SKIP_DIRS and len(rel.parts) > 1
                and path.suffix.lower() not in (".md",) and not rel.parts[0].startswith(".")):
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

    print(f"Built {len(pages) + 1} pages into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
