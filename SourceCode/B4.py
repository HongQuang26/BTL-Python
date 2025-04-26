import csv
import re
import time
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import fuzz, process
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def load_and_filter(path: Path, min_minutes: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df.loc[df["Min"] > min_minutes].copy()


def fetch_player_rows(page_num: int, driver) -> list:
    base = "https://www.footballtransfers.com/us/values/players/most-valuable-soccer-players/playing-in-uk-premier-league"
    url = base if page_num == 1 else f"{base}/{page_num}"
    driver.get(url)
    time.sleep(2)  # đợi JS render
    soup = BeautifulSoup(driver.page_source, "html.parser")
    body = soup.select_one("tbody#player-table-body")
    if not body:
        return []
    return body.select("tr")


def parse_row(tr) -> tuple:
    cells = [td.get_text(strip=True) for td in tr.select("td")]
    # cell[2] là Player có span
    name_el = tr.select_one("td:nth-of-type(3) span")
    cells[2] = name_el.text.strip() if name_el else cells[2]
    return tuple(cells)


def scrape_all(pages: int, driver_path: Path) -> pd.DataFrame:
    service = Service(str(driver_path))
    driver = webdriver.Chrome(service=service)
    records = []
    for p in range(1, pages + 1):
        rows = fetch_player_rows(p, driver)
        print(f"--- Page {p}: found {len(rows)} players")
        for r in rows:
            records.append(parse_row(r))
    driver.quit()

    cols = ["Skill", "Rank", "Player", "Age", "Club", "MarketValue","Nation"]
    return pd.DataFrame(records, columns=cols)


def normalize_name(n: str) -> str:
    n = n.strip()
    # loại lặp chuỗi: e.g. "CaicedoCaicedo"
    m = re.match(r"^(.+?)\1$", n)
    if m:
        return m.group(1)
    parts = n.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else n


def attach_clean_names(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df["clean_name"] = df[col].apply(normalize_name)
    return df


def fuzzy_market_value(targets: list, lookup: dict, name: str, threshold=85):
    match, score, _ = process.extractOne(name, targets, scorer=fuzz.token_sort_ratio)
    return lookup[match] if score >= threshold else "N/A"


def merge_values(play_df: pd.DataFrame, val_df: pd.DataFrame) -> pd.DataFrame:
    play_df = attach_clean_names(play_df, "Player")
    val_df = attach_clean_names(val_df, "Player")
    lookup = dict(zip(val_df["clean_name"], val_df["MarketValue"]))
    names = list(lookup.keys())
    play_df["MarketValue"] = play_df["clean_name"].apply(
        lambda x: fuzzy_market_value(names, lookup, x)
    )
    return play_df.drop(columns="clean_name")


def save_output(df: pd.DataFrame, out_path: Path):
    df.insert(0, "stt", range(1, len(df) + 1))
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✨ Saved to {out_path}")


if __name__ == "__main__":
    input_csv = Path(r"D:\Bai_Tap_Lon\results.csv")
    output_csv = Path(r"D:\Bai_Tap_Lon\transfer_player.csv")
    chrome_driver = Path(r"C:\Users\hieu2\.wdm\drivers\chromedriver\win64\134.0.6998.165\chromedriver-win32\chromedriver.exe")

    # 1. load & filter
    players = load_and_filter(input_csv, min_minutes=900)

    # 2. crawl giá trị
    values = scrape_all(pages=22, driver_path=chrome_driver)

    # 3. ghép fuzzy
    combined = merge_values(players, values)[["Player","Nation","Min", "MarketValue"]]

    # 4. xuất file
    save_output(combined, output_csv)
