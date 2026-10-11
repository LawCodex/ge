#!/usr/bin/env python3
"""Download all laws in force from the Legislative Herald of Georgia (matsne.gov.ge).

Lists the "main (consolidated)" documents of group "კანონი" (laws: constitution, codes,
organic laws, laws, ...) with status "active", then downloads the latest consolidated
Georgian text of each and, when matsne offers one, the official English translation.

Obeys robots.txt Crawl-delay: 10 (one request every 10 s). Raw HTML is cached in
../_raw/ge/ (relative to the repo root), so re-runs only fetch what is missing.
"""
import json, os, re, sys, time, requests
from bs4 import BeautifulSoup

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://matsne.gov.ge"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "ge")
DELAY = 10.0
S = requests.Session()
S.headers["User-Agent"] = UA
_last = [0.0]


def get(url):
    for attempt in range(5):
        wait = _last[0] + DELAY - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = S.get(url, timeout=180)
            if r.status_code == 200:
                return r.text
            print("HTTP", r.status_code, url, file=sys.stderr)
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            print("ERR", e, url, file=sys.stderr)
        time.sleep(30 * (attempt + 1))
    return None


def list_laws():
    path = os.path.join(RAW, "index.json")
    if os.path.exists(path):
        return json.load(open(path))
    items, page = [], 1
    while True:
        url = (f"{BASE}/ka/document/search?type=main&group=1000003&status=active&limit=100"
               f"&sort=signingDate_asc&page={page}")
        html = get(url)
        soup = BeautifulSoup(html, "lxml")
        found = soup.select("div.document-search-result-item")
        for it in found:
            a = it.select_one(".panel-heading a")
            did = int(re.search(r"/view/(\d+)", a["href"]).group(1))
            smalls = [x.get_text(" ", strip=True) for x in it.select(".panel-body small")]
            smalls = [x for x in smalls if x != "●"]
            items.append(dict(id=did, title=re.sub(r"\s+", " ", a.get_text(" ", strip=True)),
                              meta=smalls,
                              en=bool(it.select_one('a[href*="impose=translateEn"]'))))
        total = int(re.search(r"სულ მოიძებნა: (\d+)", html).group(1))
        print(f"page {page}: {len(items)}/{total}", flush=True)
        if not found or len(items) >= total:
            break
        page += 1
    json.dump(items, open(path, "w"), ensure_ascii=False, indent=1)
    return items


def main():
    os.makedirs(os.path.join(RAW, "ka"), exist_ok=True)
    os.makedirs(os.path.join(RAW, "en"), exist_ok=True)
    items = list_laws()
    jobs = [("ka", it["id"]) for it in items] + [("en", it["id"]) for it in items if it["en"]]
    for n, (lang, did) in enumerate(jobs):
        path = os.path.join(RAW, lang, f"{did}.html")
        if os.path.exists(path):
            continue
        html = get(f"{BASE}/{lang}/document/view/{did}")
        if html:
            open(path, "w", encoding="utf-8").write(html)
        print(n + 1, len(jobs), lang, did, len(html or ""), flush=True)


if __name__ == "__main__":
    main()
