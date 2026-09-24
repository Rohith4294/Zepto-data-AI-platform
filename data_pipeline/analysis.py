import sqlite3
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "books.db"

pd.set_option("display.width", 200)


def read_sql_results(conn):
    """Part 6a: read two of the earlier SQL query results back into DataFrames."""

    q2 = """
        SELECT title, price_gbp, price_inr
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10
    """
    df_q2 = pd.read_sql(q2, conn)
    print("=" * 70)
    print("pd.read_sql #1 — 10 most expensive books")
    print("=" * 70)
    print(df_q2.to_string(index=False))
    print(f"\ntype: {type(df_q2).__name__}, shape: {df_q2.shape}")

    q3 = """
        SELECT DISTINCT rating
        FROM books
        ORDER BY rating
    """
    df_q3 = pd.read_sql(q3, conn)
    print("\n" + "=" * 70)
    print("pd.read_sql #2 — distinct ratings")
    print("=" * 70)
    print(df_q3.to_string(index=False))
    print(f"\ntype: {type(df_q3).__name__}, shape: {df_q3.shape}")


def compare_join_vs_merge(conn):
    """Part 6b: reproduce the SQL JOIN with pd.merge and prove they match."""

    sql_join = """
        SELECT c.category_name,
               COUNT(b.book_id)           AS book_count,
               ROUND(AVG(b.price_inr), 2) AS avg_price_inr
        FROM categories c
        JOIN books b ON c.category_id = b.category_id
        GROUP BY c.category_name
        ORDER BY book_count DESC
    """
    sql_result = pd.read_sql(sql_join, conn)

    books = pd.read_sql("SELECT * FROM books", conn)
    categories = pd.read_sql("SELECT * FROM categories", conn)

    merged = pd.merge(
        categories,          # left table
        books,               # right table
        on="category_id",    # the shared key — same column the SQL JOIN used
        how="inner",         # inner join, matching SQL's plain JOIN
    )

    merge_result = (
        merged.groupby("category_name")
              .agg(book_count=("book_id", "count"),
                   avg_price_inr=("price_inr", "mean"))
              .round(2)
              .reset_index()
              .sort_values("book_count", ascending=False)
              .reset_index(drop=True)
    )

    print("\n" + "=" * 70)
    print("SQL JOIN result (pd.read_sql)")
    print("=" * 70)
    print(sql_result.to_string(index=False))

    print("\n" + "=" * 70)
    print("pandas merge result (pd.merge, no SQL)")
    print("=" * 70)
    print(merge_result.to_string(index=False))

    identical = sql_result.equals(merge_result)
    print("\n" + "=" * 70)
    print(f"Do the two approaches match?  ->  {identical}")
    print("=" * 70)

    if not identical:
        print("\nDifferences:")
        print(sql_result.compare(merge_result))


def main():
    conn = sqlite3.connect(DB_PATH)
    read_sql_results(conn)
    compare_join_vs_merge(conn)
    conn.close()


if __name__ == "__main__":
    main()