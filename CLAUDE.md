# Instructions for Claude Code

This repository is the **external comms handbook** of the Learning Community (Comunidade de Aprendizagem: Bosque Escola Avelãs + Planeta Alecrim) and the Descalças cooperative, in Marvão, Portugal. The team edits Markdown pages; GitHub Actions turns them into a website on GitHub Pages: https://beathumanheart.github.io/comms/

The people who ask you for changes are members of the comms team, not developers. Explain what you changed in plain words, without file paths unless they ask.

## Layout

```
guidelines.md          the rules, one page — keep it short
channels.md            list of media: one row per channel
architecture/          the agreed model, in English (README.md) and Portuguese (pt.md), plus the two PDFs
seasons/2026-27/       names, owners, next steps, announcement for this season
calendar/              one page per month: calendar/YYYY-MM.md
funded-projects/       CES and Enraizar no Interior: obligations and the evidence log
how-to/                short instructions for the team
site/                  the website machinery (build.py, config.json, template, CSS, fonts)
site/slides/           source of the architecture PDFs (en.json, pt.json, make_slides.py)
.github/workflows/     publishes the site on every push to main
```

`README.md` (front page on GitHub) and this file are not published as pages. Every other `.md` file is.

## Rules that always apply

1. **No names in the model.** `architecture/`, `guidelines.md`, `channels.md` and `how-to/` talk about roles ("Descalças comms", "Learning Community comms"). People's names go only in `seasons/<season>/`.
2. **The repository and the site are public.** Never add passwords, children's names or photos, private phone numbers, home addresses or anything about a child. First names of adult team members are fine.
3. **Do not invent facts.** Dates, prices, sign-up links, names, numbers of participants, funding amounts: if the team has not given them, write `?`. The site shows a lone `?` in a table cell as "to decide".
4. **Media stays in Google Drive.** Do not add photos, logos or screenshots to the repository; link to Drive instead. The PDFs in `architecture/` are the only exception.
5. **Keep it brief.** The team asked for guidelines that are clear and short. Plain words, short sentences, sentence case. No marketing tone.
6. **Funded projects.** Anything about CES (European Solidarity Corps) or Enraizar no Interior must say the funding is acknowledged with the right logo and sentence. The wording lives in `funded-projects/ces.md` and `funded-projects/enraizar-no-interior.md`; do not change it unless asked, and say the agreement decides.
7. **Open questions** go in the table in `seasons/<season>/next-steps.md` (Known / To verify / Owner / Date). Do not quietly resolve them.

## Writing pages

- The first line `# Title` is the page title. Nothing above it except the language marker (below).
- Link between pages with relative links to the `.md` file: `[the rules](../guidelines.md)`. Link labels are plain words, never file names. The build turns them into `.html` links.
- Headings get the same anchors as on GitHub, so `guidelines.md#3-sync-first--the-one-rule` works on both.
- Tables: cells that are exactly `idea`, `material in`, `ready`, `published`, `to do` or `done` show as status labels; `CES` and `ENR` show as funding tags; `—` means "not applicable".
- Checklists: `- [ ] text`.
- Simple diagrams (no images needed), one box per line, parts separated by `|`:

  ````
  ```flow
  Verify | actual agreement
  Prepare | wording · logos
  ```
  ````

  ```` ```roles ```` draws three coloured boxes (blue Descalças, green Learning Community, clay Planeta Alecrim), in that order.

## Languages

- English is the main language of the handbook. Portuguese is **European Portuguese** (Portugal): *equipa, registo, fotografia, facto, ecrã, partilhar*, not Brazilian forms.
- A Portuguese page starts with the line `<!-- lang: pt-PT -->` before its title; the site then prints its own words (date, "Editar esta página") in Portuguese.
- **Bilingual pairs — change both sides together:**
  - `architecture/README.md` ↔ `architecture/pt.md` ↔ `site/slides/en.json` ↔ `site/slides/pt.json` (the same model in four places: two pages, two PDFs)
  - `seasons/<season>/announcement.md`: an `## English` section and a `## Português` section that must say the same thing
- When the team gives you text in one language, keep their wording and translate it faithfully; do not "improve" their English or Portuguese unless asked.

## The calendar

- One file per month: `calendar/YYYY-MM.md`, linked from `calendar/README.md`.
- The posts table sits under a heading that is exactly `## Posts`, with exactly these columns, in this order:

  ```
  | Date | Channel | Pillar | Purpose | What | Material from | Fund | Status |
  ```

  - **Date**: `Tue 10 Nov` (weekday, day, month; the year comes from the file name). A row whose date has no number (for example "After the training") is allowed but does not appear on the home page.
  - **Pillar**: Life · Learning · People · Community · Opportunities
  - **Purpose**: Connect · Events · Volunteers · Funding · Families
  - **Fund**: `CES`, `ENR` or `—`
  - **Status**: `idea` → `material in` → `ready` → `published`
- The home page shows the next four posts from these tables, counted from the day the reader opens it.
- Rhythm: Tuesday and Friday. Move a post off Portuguese public holidays (1 Nov, 1 Dec, 8 Dec, 25 Dec, 1 Jan, and others) to the next working day. One post a week during school holidays.
- At least one CES post (with `CES` in Fund) and one Enraizar post (`ENR`) each month.
- Posts about money (donations, prices, fundraising) need the Descalças comms owner's check — say so in the row.
- A second table, `## Comms work this month`, holds tasks that are not posts.
- Plan two months ahead: in the last week of a month, add the month after next.

## Season change

The current season is set in `site/config.json` (`"season"`). Follow `how-to/start-a-new-season.md`: copy the season folder, change names, update `"season"`, fix links that mention the old season.

## Build and check

```bash
pip install -r site/requirements.txt
python site/build.py          # writes _site/ ; open _site/index.html to look
```

The build ends with "All links between pages work." — if it prints `WARNING:` lines, fix the links before committing. Do not commit `_site/` (it is in `.gitignore`).

## The architecture PDFs

The PDFs are made from `site/slides/en.json` and `site/slides/pt.json`:

```bash
pip install playwright && python -m playwright install chromium
python site/slides/make_slides.py        # both; or: make_slides.py pt
```

Change the words in the JSON files (one entry per slide), regenerate, look at the result (for example `pdftoppm -png`), and commit the PDFs. Keep text short enough to fit its box. Fonts are in `site/slides/fonts/`.

## "Last updated … by …"

Each page shows the date and author of its last commit. The name is the git author name; `site/config.json` → `names` maps an account name to the name shown (for example `"beathumanheart": "Eugenia"`). When you commit for someone, use their git identity — never your own name as the author.

## Publishing

- Pushing to `main` publishes the site within about a minute (workflow "Publish the site").
- Commit messages: short and plain, in English, saying what changed for the reader ("Calendar: posting starts 10 November").
- Do not push unless the person asks you to. Show them what changed first.

## Do not change without being asked

- `site/build.py`, `site/template.html`, `site/assets/`, `.github/workflows/` — the machinery.
- The funding wording and logos rules.
- `guidelines.md` section 3 (the sync rule) — it is agreed by the team.
