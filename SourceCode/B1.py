from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time
from io import StringIO
from tqdm import tqdm

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # chạy ẩn trình duyệt
    return webdriver.Chrome(service=Service(), options=options)

def get_soup(driver, url):
    driver.get(url)
    time.sleep(2)
    return BeautifulSoup(driver.page_source, "html.parser")

def extract_table(soup, table_id):
    table = soup.find("table", {"id": table_id})
    if table:
        df = pd.read_html(StringIO(str(table)), header=1)[0]
        if df.columns[0] == "Rk":
            df = df.iloc[:, 1:]
        return df
    return None

def fetch_team_data(driver, team_name, url, table_ids):
    soup = get_soup(driver, url)
    tables = {}
    for tid in table_ids:
        df = extract_table(soup, tid)
        if df is not None:
            df["Squad"] = team_name
        tables[tid] = df
    return tables

def fetch_all_teams_data(driver, team_urls, table_ids):
    aggregated = {tid: [] for tid in table_ids}
    print("Đang thu thập dữ liệu từ các đội:")
    for team, url in tqdm(team_urls.items()):
        team_data = fetch_team_data(driver, team, url, table_ids)
        for tid, df in team_data.items():
            if df is not None:
                aggregated[tid].append(df)
    return {tid: pd.concat(frames, ignore_index=True) if frames else None for tid, frames in aggregated.items()}

def merge_tables(base_df, data_dict, keys):
    for tid, df in data_dict.items():
        if tid != "stats_standard_9" and df is not None:
            df = df[df["Player"] != "Player"]
            df = df.rename(columns=lambda col: col if col in keys else f"{tid}_{col}")
            base_df = pd.merge(base_df, df, on=keys, how="left")
    return base_df

def clean_and_filter_data(df, min_minutes=90):
    df = df.fillna("N/a")
    df["Nation"] = df["Nation"].astype(str).apply(lambda x: x.split()[-1])
    df["Min"] = pd.to_numeric(df["Min"], errors="coerce")
    df = df[df["Min"] > min_minutes]
    df = df.sort_values("Player")
    return df

def main():
    team_urls = {
        "Arsenal": "https://fbref.com/en/squads/18bb7c10/Arsenal-Stats",
        "Aston Villa": "https://fbref.com/en/squads/d9a146ce/Aston-Villa-Stats",
        "AFC Bournemouth": "https://fbref.com/en/squads/cc2d82a3/AFC-Bournemouth-Stats",
        "Brentford": "https://fbref.com/en/squads/042d22d0/Brentford-Stats",
        "Brighton & Hove Albion": "https://fbref.com/en/squads/3acff17b/Brighton-&-Hove-Albion-Stats",
        "Chelsea": "https://fbref.com/en/squads/cd3b4a0a/Chelsea-Stats",
        "Crystal Palace": "https://fbref.com/en/squads/4186b788/Crystal-Palace-Stats",
        "Everton": "https://fbref.com/en/squads/4c1fa01b/Everton-Stats",
        "Fulham": "https://fbref.com/en/squads/44c8e1e6/Fulham-Stats",
        "Ipswich Town": "https://fbref.com/en/squads/1f389f6b/Ipswich-Town-Stats",
        "Leicester City": "https://fbref.com/en/squads/d2d3fce0/Leicester-City-Stats",
        "Liverpool": "https://fbref.com/en/squads/822bd0ba/Liverpool-Stats",
        "Manchester City": "https://fbref.com/en/squads/d8eec475/Manchester-City-Stats",
        "Manchester United": "https://fbref.com/en/squads/19538871/Manchester-United-Stats",
        "Newcastle United": "https://fbref.com/en/squads/26213b52/Newcastle-United-Stats",
        "Nottingham Forest": "https://fbref.com/en/squads/976d8421/Nottingham-Forest-Stats",
        "Southampton": "https://fbref.com/en/squads/f227ad98/Southampton-Stats",
        "Tottenham Hotspur": "https://fbref.com/en/squads/2b0a0bde/Tottenham-Hotspur-Stats",
        "West Ham United": "https://fbref.com/en/squads/9d1c2f97/West-Ham-United-Stats",
        "Wolverhampton Wanderers": "https://fbref.com/en/squads/573237c2/Wolverhampton-Wanderers-Stats"
    }

    table_ids = [
        "stats_standard_9", "stats_keeper_9", "stats_keeper_adv_9", "stats_shooting_9",
        "stats_passing_9", "stats_passing_types_9", "stats_possession_9",
        "stats_defense_9", "stats_misc_9", "stats_gca_9"
    ]

    columns_to_keep = [
        "Player", "Nation", "Squad", "Pos", "Age", "MP", "Starts", "Min", "Gls", "Ast", "CrdY", "CrdR",
        "xG", "xAG", "PrgC", "PrgP", "PrgR", "Gls.1", "Ast.1", "xG.1", "xAG.1",
        "stats_keeper_9_GA90", "stats_keeper_9_Save%", "stats_keeper_9_CS%", "stats_keeper_9_Save%.1",
        "stats_shooting_9_SoT%", "stats_shooting_9_SoT/90", "stats_shooting_9_G/Sh", "stats_shooting_9_Dist",
        "stats_passing_9_Cmp", "stats_passing_9_Cmp%", "stats_passing_9_TotDist", 
        "stats_passing_9_Cmp%.1", "stats_passing_9_Cmp%.2", "stats_passing_9_Cmp%.3", 
        "stats_passing_9_KP", "stats_passing_9_1/3", "stats_passing_9_PPA", "stats_passing_9_CrsPA", "stats_passing_9_PrgP",
        "stats_gca_9_SCA", "stats_gca_9_SCA90", "stats_gca_9_GCA", "stats_gca_9_GCA90",
        "stats_defense_9_Tkl", "stats_defense_9_TklW", "stats_defense_9_Att", "stats_defense_9_Lost",
        "stats_defense_9_Blocks", "stats_defense_9_Sh", "stats_defense_9_Pass", "stats_defense_9_Int",
        "stats_possession_9_Touches", "stats_possession_9_Def Pen", "stats_possession_9_Def 3rd",
        "stats_possession_9_Mid 3rd", "stats_possession_9_Att 3rd", "stats_possession_9_Att Pen",
        "stats_possession_9_Att", "stats_possession_9_Succ%", "stats_possession_9_Tkld%",
        "stats_possession_9_Carries", "stats_possession_9_PrgDist", "stats_possession_9_PrgC", 
        "stats_possession_9_1/3", "stats_possession_9_CPA", "stats_possession_9_Mis", 
        "stats_possession_9_Dis", "stats_possession_9_Rec", "stats_possession_9_PrgR",
        "stats_misc_9_Fls", "stats_misc_9_Fld", "stats_misc_9_Off", "stats_misc_9_Crs", 
        "stats_misc_9_Recov", "stats_misc_9_Won", "stats_misc_9_Lost", "stats_misc_9_Won%"
    ]

    key_columns = ["Player", "Nation", "Squad", "Pos"]

    driver = init_driver()
    try:
        raw_data = fetch_all_teams_data(driver, team_urls, table_ids)
        base_df = raw_data["stats_standard_9"]
        if base_df is None:
            print("Không có bảng chính (stats_standard_9). Dừng chương trình.")
            return
        merged_df = merge_tables(base_df, raw_data, key_columns)
    finally:
        driver.quit()

    final_df = merged_df[[col for col in columns_to_keep if col in merged_df.columns]]
    final_df = clean_and_filter_data(final_df)

    final_df.to_csv("results.csv", index=False)
    print("Hoàn tất. Dữ liệu đã lưu vào 'results.csv'.")

if __name__ == "__main__":
    main()