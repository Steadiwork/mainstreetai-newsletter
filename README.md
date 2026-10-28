# Main Street AI Brief: newsletter email code

Code that turns each published issue of [Main Street AI Brief](https://mainstreetaibrief.com/) into an email in [Buttondown](https://buttondown.com/). The website itself lives in [`Steadiwork/mainstreetai-brief`](https://github.com/Steadiwork/mainstreetai-brief).

## Files

| File | What it does |
|---|---|
| `buttondown_post.py` | Posts one issue to Buttondown. Run once per normal issue day. |
| `bd_brand.py` | `brand(body_html)`: wraps the issue's email HTML in the brand header and inline styles. Pure string function, no network. |
| `tests/test_brand.py` | Offline tests for `bd_brand.py` (`python3 -m unittest`). |
| `CONTRIBUTING.md` | How to change this repo. Read it before opening a PR. |

## Where the email HTML comes from

The email body is **not** built in this repo. It is the `feed2(i)` function in the site generator's `build.py` (not published), which writes each issue's email-safe HTML into the `<description>` of the matching `<item>` in `feed.xml` (live at https://mainstreetaibrief.com/feed.xml). `buttondown_post.py` reads that item, so the feed is the contract:

- `<title>` becomes the email subject
- `<description>` (HTML) becomes the body, passed through `brand()`
- `<pubDate>` must be today (America/New_York) or the script refuses to post

`feed2` depends on many generator internals (issue JSON, link helpers, UTM tags), so it stays in `build.py` and was not copied here. Branding and styling of the email are done here, in `bd_brand.py`.

## How the daily job runs it

After the day's issue is published to the website and the live pages return 200, the job runs:

```
cd <generator folder> && python3 buttondown_post.py <issue-slug>
```

The scripts are deployed into the generator folder (where `public-prod/feed.xml`, `config.json` and `sabbath_gate.py` live). `SITE` defaults to the script's own folder; set `MSAIB_SITE` to override it.

Exit codes: `0` done, `3` Sabbath skip, `4` already exists (silent, fine), `5` abort (report), `6` not eligible (report). `--dry-run` goes through every check and only skips the POST, but it still reads from the Buttondown API, so it needs the key.

### Safety checks, in order

1. **Sabbath gate**: runs `sabbath_gate.py` (Friday 60 minutes before sundown until Saturday sundown, America/New_York); exit 3 means skip.
2. **Mode switch** (below).
3. **Local duplicate check**: `buttondown_state.json` already has the slug, so exit 4.
4. **Freshness**: the feed item must be dated today, so an old issue is never re-sent.
5. **Template guard**: Buttondown renders Django templates, so the script aborts (exit 5) if the subject or body contains `{{`, `{%` or `{#`.
6. **Live check**: `https://mainstreetaibrief.com/issues/<slug>.html` must return 200.
7. **Remote duplicate check**: lists all emails (paginated) and stops (exit 4) if any non-deleted email has the same slug or subject.
8. **Send-mode preconditions**: in `send` mode only, aborts unless the newsletter Footer (mailing address) is non-empty and the sending domain status is `valid`.
9. **Create**: always creates the email as a `draft` first (`slug` = issue slug, `canonical_url` = the issue page, `archival_mode: disabled`). Only in `send` mode does it then PATCH `about_to_send`.

One attempt only: it never retries a failed POST or PATCH.

## Draft / send mode switch

A one-line file `buttondown_mode.txt` next to the script holds `draft` or `send`.

- `draft` (default, also used when the file is missing): the issue lands in Buttondown as a draft for the owner to review. Nothing is emailed.
- `send`: the issue is queued to all subscribers.

The file is **not committed** (see `.gitignore`); it is a per-deployment switch that only the owner changes. Anything other than `draft` or `send` aborts with exit 5. `buttondown_state.json` (slug to email id) is also local and ignored.

## Branding

Free Buttondown plans have no custom CSS or templates, so everything is inline HTML in `bd_brand.py`:

- Navy `#14213D`, orange `#FF6B1A`, peach `#FFF1E6`, border `#E2DED5`
- Header: full-width navy band with the logo https://mainstreetaibrief.com/assets/header-lockup@2x.png (white on transparent, so it needs the navy band) and an orange rule beneath
- Bold orange links; headings with an orange left bar; blockquotes (copy-paste prompts) as peach boxes; navy table headers
- Light-only colour-scheme hints, so dark-mode clients recolour less

## Buttondown settings in use

Configured in the Buttondown dashboard or API, not by this repo:

- Email template: `classic` (the `modern` template adds its own title block above the logo)
- Link colour: orange
- From: `Main Street AI Brief <brief@mail.mainstreetaibrief.com>` (sending domain `mail.mainstreetaibrief.com`)
- Reply-To: `hello@mainstreetaibrief.com`
- Mailing address: in the newsletter Footer setting, never in the email body
- "Powered by Buttondown" stays (removing it needs a paid plan)

## Secrets

`BUTTONDOWN_API_KEY` must come from the process environment. The script never prints, logs or writes it. Do not commit keys, `.env` files, subscriber lists or exports, or the state and mode files.

## Local checks

```
python3 -m py_compile buttondown_post.py bd_brand.py
python3 -m unittest discover -s tests
```
