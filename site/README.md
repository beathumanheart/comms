# The website machinery

You do not need anything in this folder to edit the handbook. Pages are the `.md` files outside it.

| File | What it is |
|---|---|
| `config.json` | Settings: site name, current season, menu, home page signposts, display names |
| `build.py` | Turns every `.md` page into a web page and adds "Last updated … by …" from the change history |
| `template.html` | The frame around every page (menu, footer) |
| `assets/site.css` | Colours, type, layout |
| `assets/site.js` | Small conveniences: next posts on the home page, Copy buttons |
| `assets/fonts/` | Atkinson Hyperlegible Next and Instrument Serif, served from the site itself (SIL Open Font License) |

## Preview on your own computer

```
pip install -r site/requirements.txt
python site/build.py
```

Then open `_site/index.html` in a browser.

## How "Last updated … by …" works

For every page the build asks git for the last change to that file: the date and the author's name. On GitHub the author's name is the name in the person's GitHub profile. `names` in `config.json` can replace an account name with a friendlier one. Without change history (a fresh preview), the file's date and `fallback_name` are used.

## Diagrams

Two simple blocks are drawn as diagrams. One box per line, parts separated by `|`:

````
```flow
Activity | school · project · event
Capture | photos · facts · context
```

```roles
Descalças | cooperative | terrain · funding · partnerships
Learning Community | Bosque Escola + Planeta Alecrim | education · families · learning
Planeta Alecrim | association | Beirã Station
```
````

## Tables

Cells that contain exactly `idea`, `material in`, `ready`, `published`, `to do` or `done` are drawn as status labels. `CES` and `ENR` are drawn as funding tags. A lone `?` is shown as "to decide".
