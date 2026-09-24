# Module 1 — Data Pipeline

An ETL pipeline that scrapes catalog data from books.toscrape.com, cleans and
type-converts it, converts prices to INR, loads it into a normalized SQLite
database, and queries it with both SQL and pandas.

## Pipeline stages

| Stage | Script | What it does |
|---|---|---|
| Extract | `scrape.py` | Scrapes 69 books across 3 categories → `books_raw.csv` |
| Transform | `clean.py` | Types the fields, converts GBP→INR → `books_clean.csv` |
| Load + Query | `database.py` | Builds the 2-table schema, loads data, runs 6 SQL queries → `books.db` |
| Verify | `analysis.py` | Reads results via `pd.read_sql`, reproduces the JOIN via `pd.merge` |

## Setup and run

```bash
# from the repository root
python -m venv venv
venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt

python data_pipeline/scrape.py
python data_pipeline/clean.py
python data_pipeline/database.py
python data_pipeline/analysis.py
```

Scripts resolve their own paths, so they run correctly from any directory.

## Currency conversion

`price_inr` is computed with the project-defined fixed baseline rate:

**1 GBP = 105.50 INR**

This is an artificial project constant, not a market rate. No API call or
network access is involved.

## Dataset

- **69 books** across **3 categories**: Travel (11), Mystery (32), Historical Fiction (26)
- Categories are discovered dynamically from the site's sidebar rather than hardcoded.
- Scraping stops once ≥60 books across ≥3 categories have been collected.

## Cleaning decisions

| Field | Raw form | Cleaned form | Method |
|---|---|---|---|
| `price` | `£51.77` | `price_gbp` (float) | Strips every non-digit/non-dot character with a regex, so it survives any stray symbol or encoding artifact, not just a clean `£`. Returns `None` on failure rather than raising. |
| `star_rating` | `Three` | `rating` (int 1–5) | A dictionary mapping the five word forms to integers; `.get()` returns `None` for anything unexpected instead of throwing. |
| `availability` | `In stock (22 available)` | `in_stock` (bool) | Checks whether `"in stock"` appears in the lowercased text. Exact equality would fail because the site appends a varying count. |

**Parse-failure strategy:** median imputation over dropping rows — the dataset is
small (69 books) so dropping loses real information, and the median resists outlier
prices better than the mean. Note that 0 rows actually failed to parse on this run,
so the safety net never fired.

## Database schema

```
categories                          books
----------                          -----
category_id    INTEGER PK    <───┐   book_id      INTEGER PK
category_name  TEXT UNIQUE       └── category_id  INTEGER FK
                                     title        TEXT
                                     price_gbp    REAL
                                     price_inr    REAL
                                     rating       INTEGER
                                     in_stock     INTEGER (SQLite has no BOOLEAN)
```

**Why two tables:** the category name is stored once in `categories` instead of
repeating across all 69 book rows; `books` references it by ID. This removes
duplication and prevents values drifting apart (`"Travel"` vs `"travel"`).

`database.py` drops and recreates both tables on each run, so it regenerates
`books.db` from scratch and is safely re-runnable.

## SQL queries and output

```
======================================================================
Q1 — SELECT / WHERE: books rated 4 or above
----------------------------------------------------------------------
SELECT title, rating, price_gbp
        FROM books
        WHERE rating >= 4
----------------------------------------------------------------------
                                                                   title  rating  price_gbp
        Full Moon over Noah's Ark: An Odyssey to Mount Ararat and Beyond       4      49.43
                                        A Year in Provence (Provence #1)       4      56.88
                                      1,000 Places to See Before You Die       5      26.08
                                                           Sharp Objects       4      47.82
                                                     The Past Never Ends       4      56.50
                         The Murder of Roger Ackroyd (Hercule Poirot #4)       4      44.10
                                  A Time of Torment (Charlie Parker #14)       5      48.35
                   Murder at the 42nd Street Library (Raymond Ambler #1)       4      54.36
       What Happened on Beale Street (Secrets of the South Mysteries #2)       5      25.37
The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)       5      52.30
                        Delivering the Truth (Quaker Midwife Mystery #1)       4      20.89
                     The Mysterious Affair at Styles (Hercule Poirot #1)       4      24.80
                                       The Silkworm (Cormoran Strike #2)       5      23.05
  The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)       4      57.70
                                                       The Girl You Lost       5      12.29
                                 A Flight of Arrows (The Pathfinders #2)       5      55.53
                                                            Mrs. Houdini       5      30.25
                                               The Marriage of Opposites       4      28.08
                                                       A Paris Apartment       4      39.01
                         World Without End (The Pillars of the Earth #2)       4      32.97
                                                   The Passion of Dolssa       5      28.32
                                                  Voyager (Outlander #3)       5      21.07
                                                            The Red Tent       5      35.66
                                                  Between Shades of Gray       5      20.79
                                                     While You Were Mine       5      41.32
                                                   Lost Among the Living       4      27.70
                       A Spy's Devotion (The Regency Spies of London #1)       5      16.97

======================================================================
Q2 — ORDER BY + LIMIT: 10 most expensive books
----------------------------------------------------------------------
SELECT title, price_gbp, price_inr
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10
----------------------------------------------------------------------
                                                                 title  price_gbp  price_inr
                                         Boar Island (Anna Pigeon #19)      59.48    6275.14
The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)      57.70    6087.35
                                      A Year in Provence (Provence #1)      56.88    6000.84
                                                   The Past Never Ends      56.50    5960.75
                                      The Last Painting of Sara de Vos      55.55    5860.52
                               A Flight of Arrows (The Pathfinders #2)      55.53    5858.42
                 Murder at the 42nd Street Library (Raymond Ambler #1)      54.36    5734.98
                                        The Last Mile (Amos Decker #2)      54.21    5719.16
                                   1st to Die (Women's Murder Club #1)      53.98    5694.89
                                                    Tipping the Velvet      53.74    5669.57

======================================================================
Q3 — DISTINCT: every rating value present
----------------------------------------------------------------------
SELECT DISTINCT rating
        FROM books
        ORDER BY rating
----------------------------------------------------------------------
 rating
      1
      2
      3
      4
      5

======================================================================
Q4 — BETWEEN + IN: mid-priced books in chosen ratings
----------------------------------------------------------------------
SELECT title, price_gbp, rating
        FROM books
        WHERE price_gbp BETWEEN 20 AND 40
          AND rating IN (3, 4, 5)
        ORDER BY price_gbp
----------------------------------------------------------------------
                                                                    title  price_gbp  rating
                                     Blood Defense (Samantha Brinkman #1)      20.30       3
                                                   Between Shades of Gray      20.79       5
                         Delivering the Truth (Quaker Midwife Mystery #1)      20.89       4
                                                   Voyager (Outlander #3)      21.07       5
                                        The Silkworm (Cormoran Strike #2)      23.05       5
                      The Mysterious Affair at Styles (Hercule Poirot #1)      24.80       4
        What Happened on Beale Street (Secrets of the South Mysteries #2)      25.37       5
                                       Extreme Prey (Lucas Davenport #26)      25.40       3
                                                                 Starlark      25.83       3
                                       1,000 Places to See Before You Die      26.08       5
                                         Poisonous (Max Revere Novels #3)      26.80       3
                                                    Lost Among the Living      27.70       4
                                                The Marriage of Opposites      28.08       4
                                                    The Passion of Dolssa      28.32       5
Forever and Forever: The Courtship of Henry Longfellow and Fanny Appleton      29.69       3
                                                             Mrs. Houdini      30.25       5
                          World Without End (The Pillars of the Earth #2)      32.97       4
                                                        The Secret Healer      34.56       3
                                                              Most Wanted      35.28       3
                                                             The Red Tent      35.66       5
                                                     Under the Tuscan Sun      37.33       3
                                Neither Here nor There: Travels in Europe      38.95       3
                                                        A Paris Apartment      39.01       4

======================================================================
Q5 — JOIN: top 5 highest-rated books with their category
----------------------------------------------------------------------
SELECT b.title, b.rating, b.price_inr, c.category_name
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        ORDER BY b.rating DESC, b.price_inr DESC
        LIMIT 5
----------------------------------------------------------------------
                                                                   title  rating  price_inr      category_name
                                 A Flight of Arrows (The Pathfinders #2)       5    5858.42 Historical Fiction
The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)       5    5517.65            Mystery
                                  A Time of Torment (Charlie Parker #14)       5    5100.92            Mystery
                                                     While You Were Mine       5    4359.26 Historical Fiction
                                                            The Red Tent       5    3762.13 Historical Fiction

======================================================================
Q6 — JOIN + GROUP BY: book count and average price per category
----------------------------------------------------------------------
SELECT c.category_name,
               COUNT(b.book_id)       AS book_count,
               ROUND(AVG(b.price_inr), 2) AS avg_price_inr
        FROM categories c
        JOIN books b ON c.category_id = b.category_id
        GROUP BY c.category_name
        ORDER BY book_count DESC
----------------------------------------------------------------------
     category_name  book_count  avg_price_inr
           Mystery          32        3346.36
Historical Fiction          26        3549.47
            Travel          11        4198.32
```

## SQL JOIN vs pandas merge

```
======================================================================
pd.read_sql #1 — 10 most expensive books
======================================================================
                                                                 title  price_gbp  price_inr
                                         Boar Island (Anna Pigeon #19)      59.48    6275.14
The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)      57.70    6087.35
                                      A Year in Provence (Provence #1)      56.88    6000.84
                                                   The Past Never Ends      56.50    5960.75
                                      The Last Painting of Sara de Vos      55.55    5860.52
                               A Flight of Arrows (The Pathfinders #2)      55.53    5858.42
                 Murder at the 42nd Street Library (Raymond Ambler #1)      54.36    5734.98
                                        The Last Mile (Amos Decker #2)      54.21    5719.16
                                   1st to Die (Women's Murder Club #1)      53.98    5694.89
                                                    Tipping the Velvet      53.74    5669.57

type: DataFrame, shape: (10, 3)

======================================================================
pd.read_sql #2 — distinct ratings
======================================================================
 rating
      1
      2
      3
      4
      5

type: DataFrame, shape: (5, 1)

======================================================================
SQL JOIN result (pd.read_sql)
======================================================================
     category_name  book_count  avg_price_inr
           Mystery          32        3346.36
Historical Fiction          26        3549.47
            Travel          11        4198.32

======================================================================
pandas merge result (pd.merge, no SQL)
======================================================================
     category_name  book_count  avg_price_inr
           Mystery          32        3346.36
Historical Fiction          26        3549.47
            Travel          11        4198.32

======================================================================
Do the two approaches match?  ->  True
======================================================================
```

The identical results confirm that a SQL `JOIN` and `pd.merge` are the same
operation expressed in two languages, and serve as a cross-check that the
foreign-key relationship loaded correctly — a mismatch would have indicated
rows lost or mis-linked during the load.

In practice the choice is about *where* computation should happen: push the work
to the database when the data is large, remote, or shared by many consumers,
and pull it into pandas when it fits in memory or needs Python-side logic that
SQL expresses poorly.