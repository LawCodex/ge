# Georgia — legislation as Markdown (LawCodex)

Legislation of Georgia (საქართველო) as Markdown, one file per act: the Constitution, the codes,
organic laws and all other laws in force, in their latest consolidated version as published by
the **Legislative Herald of Georgia** (matsne.gov.ge), plus the English translations published
there. Part of [LawCodex](https://github.com/LawCodex).

Retrieved: **2026-10-12**.

## Coverage

| Directory | Contents | ka | en |
|---|---|---:|---:|
| `<lang>/konstitucia/` | Constitution of Georgia (1995, consolidated to 29 Jun 2020); constitutional law on the Adjara Autonomous Republic; the 1921 Constitution (kept "active" by matsne as a historical act) | 3 | 3 |
| `<lang>/kodeksebi/` | codes: civil, civil procedure, criminal, criminal procedure, administrative offences, general administrative, administrative procedure, tax, budget, customs, labour, local self-government, electoral, juvenile justice, rights of the child, spatial planning & construction, environmental assessment, waste, forest, maritime, air, railway, defence, penitentiary, product safety, food safety | 26 | 26 |
| `<lang>/organuli-kanonebi/` | organic laws (not codes) | 25 | 17 |
| `<lang>/kanonebi/<year>/` | laws of Georgia / of the Republic of Georgia, and a few laws of the Georgian SSR still in force, by year of adoption | 415 | 252 |
| `<lang>/avtonomiuri-respublikebi/` | constitution, laws and rules of procedure of the Autonomous Republics of Adjara and Abkhazia | 29 | 1 |
| `<lang>/sxva/` | other acts matsne classifies as legislative acts in force: Rules of Procedure of the Parliament, Soviet-era decrees of the Supreme Soviet Presidium / State Council | 9 | 0 |
| **Total** | | **507** | **299** |

- Selection: matsne advanced search, document group "კანონი" (legislative acts), type "main
  (consolidated) documents only", status "in force" → 507 acts. Amending laws are not "main"
  documents, so they are excluded; their content is in the consolidated texts.
- `ka/` is the authoritative Georgian text. `en/` holds the English translations matsne offers
  for 299 of these acts; they are **not legally binding** and may follow an older consolidated
  version (see `last_amended` in each file). Directory names under `en/` mirror `ka/`.
- File names: `<matsne document id>-<romanised Georgian title>.md` (Georgian national
  romanisation). Front matter: `identifier` (document number), `matsne_id`,
  `registration_code`, `document_type`, `issuer`, `date` (adoption), `last_amended` (date of the
  consolidated publication shown), `publication` (official source), `source`.
- Structure: books / parts / sections (კარი) / chapters (თავი) / sub-chapters become `##`…
  headings, articles (მუხლი) the deepest heading. The italic lines after provisions are matsne's
  amendment notes (the amending act and its publication). Tables are kept as HTML.

## Not covered

- Secondary legislation: decrees and resolutions of the Government (≈6,200 in force),
  presidential decrees (≈3,600), ministerial orders, local self-government acts; also
  international treaties, Constitutional Court decisions, Parliament resolutions. Not collected:
  matsne's robots.txt requires a 10-second crawl delay, which makes tens of thousands of
  documents impractical.
- Translations into Abkhaz, Ossetian, Azerbaijani and Armenian that matsne attaches to a few
  acts (e.g. the Constitution) as files.
- Earlier consolidated versions, amending laws, repealed acts.

## Source

- **Legislative Herald of Georgia** (LEPL "საქართველოს საკანონმდებლო მაცნე"), Ministry of
  Justice — https://matsne.gov.ge, the official publication of Georgian normative acts.
  Pages used: `/ka/document/search?…` (lists) and `/ka|en/document/view/<id>` (latest
  consolidated version).
- Politeness: robots.txt `Crawl-delay: 10` obeyed (one request every ≥ 10 s), User-Agent
  `LawCodex/1.0 (+https://github.com/LawCodex)`. One request was answered with a transient
  "Access Denied" page and was retried successfully.
- Copyright: the Law of Georgia on Copyright and Related Rights (art. 8) excludes official
  documents (laws, decrees, regulations and other normative acts) and their official
  translations from copyright protection.

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt
python3 scripts/ge_fetch.py     # ~2.5 h because of the crawl delay; cached in ../_raw/ge/
python3 scripts/ge_convert.py
```
