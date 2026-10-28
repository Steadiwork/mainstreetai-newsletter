# Contributing

- Change this repo only through a pull request. Nothing merges until the owner says "make it live".
- **No new sending code paths without the owner's explicit OK.** Today the only code that touches subscribers is the single path in `buttondown_post.py`: create a draft, and queue it only when `buttondown_mode.txt` says `send`. Do not add test sends, `send-draft`, `publish`, scheduling, subscriber imports or edits, or settings, billing or DNS calls.
- Keep draft the default. Keep every safety check in the README list (Sabbath gate, freshness, template guard, live check, duplicate checks).
- Never commit secrets, API keys, `.env` files, subscriber data, or the local state and mode files. The key is read from `BUTTONDOWN_API_KEY` in the environment only, and must never be printed or logged.
- Changes to `bd_brand.py` must keep it a pure string transform and keep `python3 -m unittest discover -s tests` passing. Branding changes should include before/after screenshots rendered from a sample body.
- Run `python3 -m py_compile buttondown_post.py bd_brand.py` before opening the PR.
- The deployed copies are pulled from `main` only after a merge. Do not rely on unmerged branches.
