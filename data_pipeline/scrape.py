import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from pathlib import Path

BASE = "http://books.toscrape.com/"
HERE = Path(__file__).resolve().parent      # the data_pipeline folder itself


def get_soup(url):
    """Fetch one page and return it as a searchable BeautifulSoup tree."""
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"          # avoids the "Â£" price-encoding glitch
    return BeautifulSoup(resp.text, "html.parser")


def discover_categories():
    """Read the homepage sidebar -> list of (name, url) for every category."""
    soup = get_soup(BASE)
    links = soup.select("div.side_categories ul li ul li a")  # skips top-level "Books"
    return [(a.get_text(strip=True), urljoin(BASE, a["href"])) for a in links]


def scrape_category(name, url):
    """Scrape every book across all paginated pages of one category."""
    rows = []
    while url:
        soup = get_soup(url)
        for art in soup.select("article.product_pod"):
            rows.append({
                "title":        art.h3.a["title"],
                "price":        art.select_one("p.price_color").get_text(strip=True),
                "star_rating":  art.select_one("p.star-rating")["class"][1],  # e.g. "Three"
                "availability": art.select_one("p.instock.availability").get_text(strip=True),
                "category":     name,
            })
        nxt = soup.select_one("li.next a")       # follow "next" if this category paginates
        url = urljoin(url, nxt["href"]) if nxt else None
    return rows


def main():
    all_rows, used = [], 0
    for name, url in discover_categories():
        print(f"Scraping category: {name}")
        all_rows.extend(scrape_category(name, url))
        used += 1
        if len(all_rows) >= 60 and used >= 3:    # meets the >=60 books / >=3 categories rule
            break

    df = pd.DataFrame(all_rows)
    print(f"\nScraped {len(df)} books across {df['category'].nunique()} categories")

    out_path = HERE / "books_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()