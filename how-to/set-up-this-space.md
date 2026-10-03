# Set up this space on GitHub

Done once, by one person. About 20 minutes.

## 1. Create it

1. Create a free GitHub account (or use an existing one). Better: create a free **organisation** for the Learning Community, so the space does not belong to one person's account.
2. **New repository** → name it for example `comms` → choose **Public** → Create.
3. **Add file → Upload files** → drag in everything from the starter folder, including the folders `site` and `.github` → Commit. If `.github` does not show up on your computer, turn on "show hidden files" first.

## 2. Turn on the website

1. In the repository: **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Open the **Actions** tab. A run called *Publish the site* starts by itself; when it turns green, the address of the website is shown in **Settings → Pages**. It looks like `https://your-account.github.io/comms/`.

From now on every saved change republishes the website by itself, in about a minute.

## 3. The website is public

On GitHub's free plan the website and the repository can be read by anyone who has the address. The website asks search engines not to list it, but that is a request, not a lock.

So before publishing, decide as a team:

- Are first names on the "Who to ask" page fine?
- Should the links to shared Drive folders and documents stay? (People without access still cannot open them.)
- Is anything in "Next steps" or the evidence log too internal?

Never put here: passwords, children's names or photos, private phone numbers or addresses.

## 4. Invite people

**Settings → Collaborators** (or **People** in an organisation) → invite by email or username → role **Write**. Everyone who edits needs their own free account. Give at least two people the **Admin** role.

## 5. The settings file

`site/config.json` holds the few settings of the website:

| Setting | What it does |
|---|---|
| `site_name`, `site_tagline` | The name at the top of the menu |
| `season` | Which folder in `seasons/` the menu points to |
| `notice` | The line at the top of every page. Empty it (`""`) when the draft is agreed |
| `names` | The name to show for a GitHub account, for example `"mariasilva82": "Maria"` |
| `hide_from_search_engines` | `true` asks search engines not to list the site |
| `nav`, `home` | The menu entries and the signposts on the home page |

The look of the website is in `site/assets/site.css`. Nobody needs to open the `site` folder to edit pages.

## What does not belong here

Photos, videos, logo files and screenshots — they stay in Drive.
