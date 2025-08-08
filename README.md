# OpenAlex Scholar Dashboard (static)

Simple, free dashboard that shows author-level metrics (papers, citations, per-year series, h-index) using the OpenAlex API. Auto-refreshes daily with GitHub Actions. Host on GitHub Pages or Netlify.

## Quick start

1. **Use this repo as a template** (or clone & push to your GitHub).
2. Edit `authors.csv` with your authors. If you don’t have OpenAlex IDs, leave blank.
3. In your repo, go to **Settings → Pages** and serve the `/site` folder (GitHub Pages) **or** deploy `/site` to Netlify.
4. Optional: add a repository secret `OPENALEX_MAILTO` with your email (recommended by OpenAlex).
5. The workflow runs daily and updates `site/data/authors.json`. You can also run it manually via **Actions → Refresh OpenAlex data → Run workflow**.

## Local build (optional)
```bash
python -m venv .venv && source .venv/bin/activate
pip install requests
python scripts/build.py
# then open site/index.html in a browser
```

## Notes
- OpenAlex is generous but rate-limited. Keep author lists reasonable.
- h-index is computed from up to 2000 works for speed; set a higher cap if needed.
- For stricter matching, put precise institution names in `authors.csv`.
- If you truly need Google Scholar data, consider the Python `scholarly` package — but scraping may break and is against Scholar’s ToS. OpenAlex is the stable option.
