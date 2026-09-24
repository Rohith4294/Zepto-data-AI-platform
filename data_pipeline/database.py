import sqlite3
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "books.db"


# ---------------------------------------------------------------- Part 4: schema
def create_schema(conn):
    """Build the normalized two-table schema from scratch.

    categories holds each category ONCE (no repeated text across 69 rows);
    books points at it via a foreign key. That is what makes this normalized.
    """
    cur = conn.cursor()

    # Drop first so the script is re-runnable and always rebuilds cleanly
    cur.execute("DROP TABLE IF EXISTS books")
    cur.execute("DROP TABLE IF EXISTS categories")

    cur.execute("""
        CREATE TABLE categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE books (
            book_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            price_gbp   REAL    NOT NULL,
            price_inr   REAL    NOT NULL,
            rating      INTEGER NOT NULL,
            in_stock    INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    conn.commit()
    print("Schema created: categories + books (PK/FK)")


# ------------------------------------------------------------------ Part 5: load
def load_data(conn, df):
    """Insert categories first, then books carrying the matching category_id."""
    cur = conn.cursor()

    # 1. Each unique category becomes one row -> {name: category_id}
    for name in sorted(df["category"].unique()):
        cur.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))

    cur.execute("SELECT category_id, category_name FROM categories")
    cat_ids = {name: cid for cid, name in cur.fetchall()}

    # 2. Books reference the category by id, not by repeating its name
    rows = [
        (r.title, r.price_gbp, r.price_inr, int(r.rating),
         int(r.in_stock), cat_ids[r.category])
        for r in df.itertuples(index=False)
    ]
    cur.executemany("""
        INSERT INTO books (title, price_gbp, price_inr, rating, in_stock, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    print(f"Loaded {len(cat_ids)} categories and {len(rows)} books")


# --------------------------------------------------------------- Part 5: queries
QUERIES = {
    "Q1 — SELECT / WHERE: books rated 4 or above": """
        SELECT title, rating, price_gbp
        FROM books
        WHERE rating >= 4
    """,

    "Q2 — ORDER BY + LIMIT: 10 most expensive books": """
        SELECT title, price_gbp, price_inr
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10
    """,

    "Q3 — DISTINCT: every rating value present": """
        SELECT DISTINCT rating
        FROM books
        ORDER BY rating
    """,

    "Q4 — BETWEEN + IN: mid-priced books in chosen ratings": """
        SELECT title, price_gbp, rating
        FROM books
        WHERE price_gbp BETWEEN 20 AND 40
          AND rating IN (3, 4, 5)
        ORDER BY price_gbp
    """,

    "Q5 — JOIN: top 5 highest-rated books with their category": """
        SELECT b.title, b.rating, b.price_inr, c.category_name
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        ORDER BY b.rating DESC, b.price_inr DESC
        LIMIT 5
    """,

    "Q6 — JOIN + GROUP BY: book count and average price per category": """
        SELECT c.category_name,
               COUNT(b.book_id)       AS book_count,
               ROUND(AVG(b.price_inr), 2) AS avg_price_inr
        FROM categories c
        JOIN books b ON c.category_id = b.category_id
        GROUP BY c.category_name
        ORDER BY book_count DESC
    """,
}


def run_queries(conn):
    """Execute every query and print it alongside its result."""
    for label, sql in QUERIES.items():
        print("\n" + "=" * 70)
        print(label)
        print("-" * 70)
        print(sql.strip())
        print("-" * 70)
        print(pd.read_sql(sql, conn).to_string(index=False))


def main():
    df = pd.read_csv(HERE / "books_clean.csv")
    print(f"Read {len(df)} clean rows")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")   # SQLite needs FKs switched on explicitly

    create_schema(conn)
    load_data(conn, df)
    run_queries(conn)

    conn.close()
    print(f"\nDatabase saved -> {DB_PATH}")


if __name__ == "__main__":
    main()