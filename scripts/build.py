#!/usr/bin/env python3
import csv, json, os, sys, time
from datetime import datetime
from urllib.parse import urlencode
import requests

MAILTO = os.getenv("OPENALEX_MAILTO", "YOUR_EMAIL@example.com")
BASE = "https://api.openalex.org"
HEADERS = {"User-Agent": f"openalex-dashboard (+{MAILTO})"}

# --- Helpers ---

def get(url, params=None):
    params = params or {}
    if MAILTO:
        params.setdefault("mailto", MAILTO)
    for attempt in range(4):
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        # polite backoff
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()


def resolve_author_id(name: str, institution: str | None) -> str | None:
    params = {"search": name, "per-page": 5}
    if institution:
        params["filter"] = f"last_known_institution.display_name.search:{institution}"
    data = get(f"{BASE}/authors", params)
    results = data.get("results", [])
    return results[0]["id"] if results else None


def author_core(author_id: str):
    return get(f"{BASE}/authors/{author_id}")


def author_h_index(author_id: str, max_works: int = 2000) -> int | None:
    # Compute h-index from works’ cited_by_count using pagination.
    citations = []
    cursor = "*"
    fetched = 0
    while cursor and fetched < max_works:
        params = {
            "filter": f"author.id:{author_id}",
            "select": "cited_by_count",
            "per-page": 200,
            "cursor": cursor,
        }
        data = get(f"{BASE}/works", params)
        works = data.get("results", [])
        citations.extend([w.get("cited_by_count", 0) for w in works])
        fetched += len(works)
        cursor = data.get("meta", {}).get("next_cursor")
        if not works:
            break
    if not citations:
        return None
    citations.sort(reverse=True)
    h = 0
    for i, c in enumerate(citations, start=1):
        if c >= i:
            h = i
        else:
            break
    return h


def extract_year_series(counts_by_year):
    # OpenAlex returns list of {year, works_count, cited_by_count}
    series = sorted(counts_by_year or [], key=lambda x: x.get("year", 0))
    years = [x["year"] for x in series]
    papers = [x.get("works_count", 0) for x in series]
    cites = [x.get("cited_by_count", 0) for x in series]
    return years, papers, cites


def main():
    out = {"generated_at": datetime.utcnow().isoformat() + "Z", "authors": []}

    with open("authors.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        name = (row.get("author_name") or "").strip()
        institution = (row.get("institution") or "").strip()
        author_id = (row.get("openalex_id") or "").strip()

        if not author_id:
            author_id = resolve_author_id(name, institution)
            if not author_id:
                print(f"WARN: Could not resolve author for '{name}' ({institution})", file=sys.stderr)
                continue

        core = author_core(author_id)
        display_name = core.get("display_name", name)
        works_count = core.get("works_count", 0)
        cited_by_count = core.get("cited_by_count", 0)
        counts_by_year = core.get("counts_by_year", [])
        years, papers_by_year, cites_by_year = extract_year_series(counts_by_year)

        try:
            h_idx = author_h_index(author_id)
        except Exception:
            h_idx = None

        out["authors"].append({
            "name": display_name,
            "openalex_id": author_id,
            "institution": core.get("last_known_institution", {}).get("display_name"),
            "works_count": works_count,
            "cited_by_count": cited_by_count,
            "h_index": h_idx,
            "years": years,
            "papers_by_year": papers_by_year,
            "cites_by_year": cites_by_year,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })

    os.makedirs("site/data", exist_ok=True)
    with open("site/data/authors.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("Wrote site/data/authors.json with", len(out["authors"]), "authors")


if __name__ == "__main__":
    main()
