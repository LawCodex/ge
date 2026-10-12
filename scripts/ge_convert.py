#!/usr/bin/env python3
"""Convert matsne.gov.ge HTML (cached by ge_fetch.py in ../_raw/ge/) to Markdown."""
import datetime, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "ge")
SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
KA2LAT = dict(zip("აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ",
                  ["a", "b", "g", "d", "e", "v", "z", "t", "i", "k", "l", "m", "n", "o", "p", "zh", "r", "s", "t",
                   "u", "p", "k", "gh", "q", "sh", "ch", "ts", "dz", "ts", "ch", "kh", "j", "h"]))

# heading kinds, from the top of the hierarchy down
KINDS = {
    "ka": [("book", r"წიგნი\b"), ("part", r"([IVXLC]+\.\s*)?(ზოგადი|განსაკუთრებული|კერძო)\s+ნაწილი|ნაწილი\s+[IVXLC\d]"),
           ("section", r"კარი\b"), ("chapter", r"თავი\b"), ("subchapter", r"ქვეთავი\b"),
           ("article", r"მუხლი\s*\d")],
    "en": [("book", r"Book\b"), ("part", r"(General|Special)\s+Part|Part\s+[IVXLC\d]+\b|Part\s+(One|Two|Three|Four|Five)\b"),
           ("section", r"Section\b"), ("chapter", r"Chapter\b"), ("subchapter", r"Sub-?chapter\b"),
           ("article", r"Article\s*\d")],
}


def translit(s):
    s = "".join(KA2LAT.get(ch, ch) for ch in s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def slug(title, n=70):
    s = translit(title)
    if len(s) > n:
        s = s[:n].rsplit("-", 1)[0]
    return s or "untitled"


def text_of(el):
    """Inline text with <sup> rendered as superscript digits and <i>/<b> dropped."""
    out = []
    for d in el.descendants:
        if isinstance(d, NavigableString):
            if d.parent.name in ("script", "style"):
                continue
            t = str(d)
            if d.parent.name == "sup" and re.fullmatch(r"\s*\d+\s*", t):
                t = t.strip().translate(SUP)
            out.append(t)
        elif isinstance(d, Tag) and d.name == "br":
            out.append("\n")
    t = "".join(out).replace("\xa0", " ")
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = "\n".join(x.strip() for x in t.split("\n"))
    return re.sub(r"\n{2,}", "\n", t).strip()


def esc(t):
    # avoid accidental Markdown structures at line start
    t = re.sub(r"^(#+|>|[-+*] )", lambda m: "\\" + m.group(0), t)
    return t


def table_html(tb):
    rows = []
    for tr in tb.find_all("tr"):
        cells = []
        for td in tr.find_all(["td", "th"]):
            attrs = "".join(f' {a}="{td[a]}"' for a in ("colspan", "rowspan") if td.get(a) and td.get(a) != "1")
            cells.append(f"<{td.name}{attrs}>{text_of(td).replace(chr(10), '<br>')}</{td.name}>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def kind_of(text, lang):
    for k, rx in KINDS[lang]:
        if re.match(rx, text):
            return k
    return None


def blocks(root):
    """Yield top-level text blocks (p/div/headings/tables) in document order."""
    for el in root.children:
        if not isinstance(el, Tag):
            continue
        if el.name == "table":
            yield el
        elif el.name in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            yield el
        elif el.name in ("div", "ol", "ul", "span", "center", "font", "section", "blockquote"):
            inner = [c for c in el.children if isinstance(c, Tag) and c.name in ("p", "div", "table", "ol", "ul", "h1",
                                                                                     "h2", "h3", "h4", "h5", "h6", "li")]
            if inner:
                yield from blocks(el)
            else:
                yield el
        elif el.name == "style":
            continue
        else:
            yield el


def is_italic(el):
    t = el.get_text(" ", strip=True)
    if not t:
        return False
    it = " ".join(i.get_text(" ", strip=True) for i in el.find_all(["i", "em"]))
    return len(it) >= 0.9 * len(t)


def is_bold(el):
    t = el.get_text("", strip=True)
    if not t:
        return False
    b = "".join(i.get_text("", strip=True) for i in el.find_all(["b", "strong"]))
    return len(b) >= 0.9 * len(t)


def unwrap_new_format(maindoc, soup):
    """Newer matsne documents lay out every structural unit as tables with ids like
    'DOCUMENT:1;PART:1;CHAPTER:2;ARTICLE:5;_Title' / '..._Content'. Turn titles into
    structural paragraphs and unwrap the content/container tables."""
    for tb in list(maindoc.find_all("table", id=re.compile(r"^DOCUMENT:"))):
        tid = tb.get("id", "")
        if tid.endswith("_Title"):
            for blk in tb.find_all(["div", "center", "p"]):
                blk.insert_after(NavigableString("\n"))
            txt = ". ".join(x for x in text_of(tb).split("\n") if x.strip())
            txt = re.sub(r"\.\s*\.", ".", txt)
            p = soup.new_tag("p")
            a = soup.new_tag("a", attrs={"class": "oldStyleDocumentPart"})
            a.string = txt
            p.append(a)
            tb.replace_with(p)
        else:
            for td in tb.find_all("td"):
                if td.find_parent("table") is tb:
                    div = soup.new_tag("div")
                    for c in list(td.contents):
                        div.append(c.extract())
                    td.replace_with(div)
            for tag in tb.find_all(["tr", "tbody"]):
                if tag.find_parent("table") is tb:
                    tag.unwrap()
            tb.name = "div"
            tb.attrs = {}


def convert_body(maindoc, lang, title):
    items = []  # (kind or None, text) ; kind 'table', 'note', 'para', or heading kind
    for el in blocks(maindoc):
        if el.name == "table":
            items.append(("table", table_html(el)))
            continue
        if el.find("a", attrs={"name": "DOCUMENT"}) and not el.find("a", class_="oldStyleDocumentPart"):
            continue
        t = text_of(el)
        if not t:
            continue
        structural = el.find("a", class_="oldStyleDocumentPart") is not None
        cls = " ".join(el.get("class") or [])
        k = kind_of(t, lang) if (structural or lang == "en" and is_bold(el) or "xml" in cls and (
                "tavi" in cls or "muxli" in cls or "kari" in cls)) else None
        if k is None and structural:
            k = "other"
        if k:
            items.append((k, t.replace("\n", " ")))
        elif "satauri" in cls and items and items[-1][0] in ("book", "part", "section", "chapter", "subchapter") \
                and not re.search(r"[.–-]\s*\S", items[-1][1][6:]):
            items[-1] = (items[-1][0], items[-1][1] + ". " + t.replace("\n", " "))
        elif is_italic(el):
            items.append(("note", t))
        else:
            items.append(("para", t))
    # drop a leading heading that only repeats the title
    while items and items[0][0] in ("other",) + tuple(k for k, _ in KINDS[lang]) and \
            re.sub(r"\W", "", items[0][1]).lower() == re.sub(r"\W", "", title).lower():
        items.pop(0)
    # "კარი პირველი" / "Chapter I" followed by its name as a separate structural line: merge
    merged = []
    for k, t in items:
        if k == "other" and merged and merged[-1][0] in ("book", "part", "section", "chapter", "subchapter") \
                and len(merged[-1][1].split()) <= 3 and not re.search(r"[.:–—-]", merged[-1][1]):
            merged[-1] = (merged[-1][0], merged[-1][1] + ". " + t)
        else:
            merged.append((k, t))
    items = merged
    # structural lines before the first real heading (title page) become bold paragraphs
    for n, (k, t) in enumerate(items):
        if k == "other":
            items[n] = ("bold", t)
        elif k != "note":
            break
    order = [k for k, _ in KINDS[lang] if k != "article"]
    present = [k for k in order if any(i[0] == k for i in items)]
    level = {k: 2 + n for n, k in enumerate(present)}
    art_level = min(6, 2 + len(present))
    other_level = level.get("chapter", 2)
    out = []
    for k, t in items:
        if k == "para":
            out.append(esc(t).replace("\n", "  \n"))
        elif k == "note":
            out.append("*" + t.replace("\n", " ").replace("*", "\\*") + "*")
        elif k == "table":
            out.append(t)
        elif k == "bold":
            out.append("**" + t.replace("*", "\\*") + "**")
        else:
            lv = art_level if k == "article" else level.get(k, other_level)
            out.append("#" * min(lv, 6) + " " + t)
    return "\n\n".join(out) + "\n"


def meta_table(soup):
    m = {}
    tb = soup.select_one(".document-header table")
    if tb:
        for tr in tb.select("tbody tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                m[tds[0].get_text(strip=True)] = tds[1].get_text(" ", strip=True)
    sel = soup.select_one("#publication-switcher option[selected]")
    m["_publication"] = sel.get_text(strip=True) if sel else None
    m["_publication_id"] = sel.get("value") if sel else None
    return m


def dmy(s):
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def category(item):
    t, typ = item["title"], item["meta"][0] if item["meta"] else ""
    if ("კონსტიტუცია" in typ and "ავტონომიური" not in typ) or re.match(r"საქართველოს კონსტიტუცია\s*$", t):
        return "konstitucia", "constitution"
    if "ავტონომიური" in typ:
        return "avtonomiuri-respublikebi", "act"
    if re.search(r"კოდექსი\s*$", t) and not t.startswith("„"):
        return "kodeksebi", "code"
    if "ორგანული" in typ:
        return "organuli-kanonebi", "organic_law"
    if "კანონი" in typ:
        return "kanonebi", "act"
    if "რეგლამენტი" in typ:
        return "sxva", "regulation"
    return "sxva", "decree"


def yaml_str(s):
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    today = datetime.date.today().isoformat()
    items = json.load(open(os.path.join(RAW, "index.json")))
    counts = {}
    for it in items:
        for lang in ("ka", "en"):
            p = os.path.join(RAW, lang, f"{it['id']}.html")
            if not os.path.exists(p):
                continue
            soup = BeautifulSoup(open(p, encoding="utf-8").read(), "lxml")
            md = soup.select_one("#maindoc")
            if md is None:
                print("no maindoc", p, file=sys.stderr)
                continue
            for x in md.find_all(["style", "script"]):
                x.decompose()
            unwrap_new_format(md, soup)
            meta = meta_table(soup)
            name = soup.select_one('#maindoc a[name="DOCUMENT"]')
            title = it["title"] if lang == "ka" else (name.get_text(" ", strip=True) if name else it["title"])
            title = re.sub(r"\s+", " ", title).strip()
            cat, typ = category(it)
            date = dmy(meta.get("მიღების თარიღი") or meta.get("Date of issuing"))
            year = (date or "0000")[:4]
            fn = f"{it['id']}-{slug(it['title'])}.md"
            rel = os.path.join(lang, cat, year, fn) if cat in ("kanonebi",) else os.path.join(lang, cat, fn)
            body = convert_body(md, lang, title)
            num = meta.get("დოკუმენტის ნომერი") or meta.get("Document number") or ""
            fm = ["---", f"title: {yaml_str(title)}", f"identifier: {yaml_str(num)}",
                  f"matsne_id: {it['id']}",
                  f"registration_code: {yaml_str(meta.get('სარეგისტრაციო კოდი') or meta.get('Registration code'))}",
                  f"type: {typ}",
                  f"document_type: {yaml_str(meta.get('დოკუმენტის ტიპი') or meta.get('Document type') or it['meta'][0])}",
                  f"issuer: {yaml_str(meta.get('დოკუმენტის მიმღები') or meta.get('Document issuer'))}",
                  "jurisdiction: ge", f"language: {lang}"]
            if date:
                fm.append(f"date: {date}")
            if dmy(meta.get("_publication")):
                fm.append(f"last_amended: {dmy(meta['_publication'])}  # consolidated publication shown")
            fm += [f"publication: {yaml_str(meta.get('გამოქვეყნების წყარო, თარიღი') or meta.get('Source and date of publishing'))}",
                   "status: in_force",
                   f"source: \"https://matsne.gov.ge/{lang}/document/view/{it['id']}\""]
            if lang == "en":
                fm.append("translation: true  # English translation published by matsne.gov.ge; the Georgian text is authoritative")
            fm += [f"retrieved: {today}", "---", "", f"# {title}", "", ""]
            out = os.path.join(REPO, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write("\n".join(fm) + body)
            counts[(lang, cat)] = counts.get((lang, cat), 0) + 1
    for k, v in sorted(counts.items()):
        print(k, v)


if __name__ == "__main__":
    main()
