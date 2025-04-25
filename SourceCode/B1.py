from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
from io import StringIO

driver = webdriver.Chrome()

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

# Danh sách các id bảng cần lấy
table_ids = [
    "stats_standard_9",
    "stats_keeper_9",
    "stats_keeper_adv_9",
    "stats_shooting_9",
    "stats_passing_9",
    "stats_passing_types_9",
    "stats_possession_9",
    "stats_defense_9",
    "stats_misc_9",
    "stats_gca_9"
]

# Tạo dictionary lưu trữ các bảng của từng loại (mỗi key sẽ chứa danh sách DataFrame từ các đội)
aggregated_tables = { tid: [] for tid in table_ids }

# Duyệt qua từng đội và thu thập dữ liệu các bảng
for team, url in team_urls.items():
    driver.get(url)
    time.sleep(3)  # Chờ trang tải hoàn toàn
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    for tid in table_ids:
        table = soup.find("table", {"id": tid})
        if table:
            # Chuyển bảng HTML sang DataFrame (header=1 để bỏ qua hàng tiêu đề phụ thừa)
            df = pd.read_html(StringIO(str(table)), header=1)[0]
            # Xóa cột đầu tiên nếu nó là cột thừa (ví dụ: cột đánh số thứ tự - "Rk")
            if df.columns[0] == "Rk":
                df.drop(df.columns[0], axis=1, inplace=True)
            # Thêm cột Squad để lưu tên đội
            df["Squad"] = team
            aggregated_tables[tid].append(df)
        else:
            print(f"Không tìm thấy bảng {tid} trên trang của đội {team}")

# Gộp các DataFrame của cùng loại bảng lại với nhau
for tid in aggregated_tables:
    if aggregated_tables[tid]:
        aggregated_tables[tid] = pd.concat(aggregated_tables[tid], ignore_index=True)
    else:
        aggregated_tables[tid] = None

driver.quit()

df_merged = aggregated_tables["stats_standard_9"]

# Các cột chung để merge
common_keys = ["Player", "Nation", "Squad", "Pos"]

# Với mỗi bảng còn lại, chuẩn hóa dữ liệu và merge với df_merged
for tid in table_ids:
    if tid != "stats_standard_9" and aggregated_tables[tid] is not None:
        df_temp = aggregated_tables[tid]
        # Loại bỏ các dòng tiêu đề lặp lại nếu có
        df_temp = df_temp[df_temp["Player"] != "Player"]
        # Đổi tên các cột (trừ các cột chung) để tránh trùng lặp
        df_temp = df_temp.rename(columns=lambda x: x if x in common_keys else f"{tid}_{x}")
        # Merge bảng với bảng chính
        df_merged = pd.merge(df_merged, df_temp, on=common_keys, how="left")

# ---------------- Xử lý dữ liệu theo yêu cầu ban đầu ----------------
# Danh sách 78 cột cần giữ lại (cập nhật lại theo tên cột sau khi đã merge)
columns_to_keep = [ 
    "Player", "Nation", "Squad", "Pos", "Age",            
    "MP", "Starts", "Min",
    "Gls", "Ast", "CrdY", "CrdR",
    "xG", "xAG",
    "PrgC", "PrgP", "PrgR",
    "Gls.1", "Ast.1", "xG.1", "xAG.1",
    "stats_keeper_9_GA90", "stats_keeper_9_Save%", "stats_keeper_9_CS%", 
    "stats_keeper_9_Save%.1",
    "stats_shooting_9_SoT%", "stats_shooting_9_SoT/90", "stats_shooting_9_G/Sh", "stats_shooting_9_Dist",
    "stats_passing_9_Cmp", "stats_passing_9_Cmp%", "stats_passing_9_TotDist", 
    "stats_passing_9_Cmp%.1", 
    "stats_passing_9_Cmp%.2", 
    "stats_passing_9_Cmp%.3", 
    "stats_passing_9_KP", "stats_passing_9_1/3", "stats_passing_9_PPA", "stats_passing_9_CrsPA", "stats_passing_9_PrgP",
    "stats_gca_9_SCA", "stats_gca_9_SCA90",
    "stats_gca_9_GCA", "stats_gca_9_GCA90",
    "stats_defense_9_Tkl", "stats_defense_9_TklW",
    "stats_defense_9_Att", "stats_defense_9_Lost",
    "stats_defense_9_Blocks", "stats_defense_9_Sh", "stats_defense_9_Pass", "stats_defense_9_Int",
    "stats_possession_9_Touches", "stats_possession_9_Def Pen", "stats_possession_9_Def 3rd", "stats_possession_9_Mid 3rd", 
    "stats_possession_9_Att 3rd", "stats_possession_9_Att Pen",
    "stats_possession_9_Att", "stats_possession_9_Succ%", "stats_possession_9_Tkld%",
    "stats_possession_9_Carries", "stats_possession_9_PrgDist", "stats_possession_9_PrgC", "stats_possession_9_1/3", 
    "stats_possession_9_CPA", "stats_possession_9_Mis", "stats_possession_9_Dis",
    "stats_possession_9_Rec", "stats_possession_9_PrgR",
    "stats_misc_9_Fls", "stats_misc_9_Fld", "stats_misc_9_Off", "stats_misc_9_Crs", "stats_misc_9_Recov",
    "stats_misc_9_Won", "stats_misc_9_Lost", "stats_misc_9_Won%",
]

# Lọc giữ lại các cột theo danh sách (nếu có cột nào không xuất hiện trong dữ liệu thì bỏ qua)
df_final = df_merged[[col for col in columns_to_keep if col in df_merged.columns]]

# Xử lý giá trị thiếu
df_final = df_final.fillna("N/a")

# Xử lý tên quốc gia: giả sử thông tin Nation là phần cuối của chuỗi
df_final["Nation"] = df_final["Nation"].str.split().str[-1]

# Chuyển đổi cột "Min" sang kiểu số
df_final["Min"] = pd.to_numeric(df_final["Min"], errors="coerce")

# Lọc các cầu thủ thi đấu trên 90 phút
df_final = df_final[df_final["Min"] > 90]

# Sắp xếp theo tên cầu thủ
df_final = df_final.sort_values(by="Player")
print(df_final.shape)

# Xuất dữ liệu ra file CSV 
df_final.to_csv("results.csv", index=False)

