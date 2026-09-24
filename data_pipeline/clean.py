import re
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent      # the data_pipeline folder itself

# Project-defined fixed conversion rate (stated in README, no API lookup needed)
GBP_TO_INR = 105.50

# Maps the scraped word form of the rating to its integer value
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def clean_price(value):
    """'£51.77' -> 51.77 ; returns None if it can't be parsed.

    Strips every character that is not a digit or a dot, so it survives any
    stray currency symbol or encoding artefact, not just a clean '£'.
    """
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except (ValueError, TypeError):
        return None


def clean_rating(value):
    """'Three' -> 3 ; returns None if the word isn't recognised."""
    return RATING_MAP.get(str(value).strip())


def clean_stock(value):
    """'In stock (22 available)' -> True ; anything else -> False."""
    return "in stock" in str(value).lower()


def main():
    df = pd.read_csv(HERE / "books_raw.csv")
    print(f"Loaded {len(df)} raw rows")

    # --- Part 2: type conversion ---
    df["price_gbp"] = df["price"].apply(clean_price)
    df["rating"] = df["star_rating"].apply(clean_rating)
    df["in_stock"] = df["availability"].apply(clean_stock)

    # --- Part 2: handle rows that failed to parse ---
    # Numeric fields get MEDIAN IMPUTATION (keeps the row; the median resists
    # outliers better than the mean). Justified in the README.
    n_bad_price = df["price_gbp"].isna().sum()
    n_bad_rating = df["rating"].isna().sum()

    if n_bad_price:
        df["price_gbp"] = df["price_gbp"].fillna(df["price_gbp"].median())
    if n_bad_rating:
        df["rating"] = df["rating"].fillna(df["rating"].median())

    df["rating"] = df["rating"].astype(int)   # lock to int 1-5 after imputing

    print(f"Imputed {n_bad_price} bad prices, {n_bad_rating} bad ratings")

    # --- Part 3: fixed-rate currency conversion ---
    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR).round(2)

    # Keep only the columns the database schema needs
    out = df[["title", "category", "price_gbp", "price_inr", "rating", "in_stock"]]

    print("\n--- dtypes (proof of correct typing) ---")
    print(out.dtypes)
    print("\n--- first 5 rows ---")
    print(out.head())

    out_path = HERE / "books_clean.csv"
    out.to_csv(out_path, index=False)
    print(f"\nSaved {len(out)} clean rows -> {out_path}")


if __name__ == "__main__":
    main()