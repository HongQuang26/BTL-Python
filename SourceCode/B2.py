import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# ----------------- 1. Đọc file CSV -----------------
df = pd.read_csv("results.csv")

# Các cột định danh:
id_cols = ["Player", "Squad", "Nation", "Pos"]

print("Kích thước dữ liệu ban đầu:", df.shape)
print("Các cột:", df.columns.tolist())

# ----------------- 2. Xác định các cột số -----------------
# Chuyển các cột (ngoại trừ id_cols) về kiểu số nếu có thể, và xác định danh sách cột số
numeric_cols = []
for col in df.columns:
    if col in id_cols:
        continue
    df[col] = pd.to_numeric(df[col], errors="coerce")
    if pd.api.types.is_numeric_dtype(df[col]):
        numeric_cols.append(col)

print("\nCác cột số được phân tích:", numeric_cols)

# ----------------- 3. Tính Top 3 (cao nhất và thấp nhất) -----------------
top3_lines = []  # Lưu chuỗi kết quả cho file top_3.txt

for col in numeric_cols:
    top3_lines.append(f"--- Statistic: {col} ---\n")
    # Loại bỏ các giá trị NaN của cột
    df_valid = df.dropna(subset=[col])
    
    # Sắp xếp theo cột, lấy top 3 cao nhất và thấp nhất
    df_sorted_desc = df_valid.sort_values(by=col, ascending=False)
    df_sorted_asc = df_valid.sort_values(by=col, ascending=True)
    
    # Top 3 cao nhất:
    top_high = df_sorted_desc.head(3)
    top3_lines.append("Top 3 Highest:\n")
    for idx, row in top_high.iterrows():
        top3_lines.append(f"{row['Player']} ({row['Squad']}): {row[col]}\n")
        
    # Top 3 thấp nhất:
    top_low = df_sorted_asc.head(3)
    top3_lines.append("Top 3 Lowest:\n")
    for idx, row in top_low.iterrows():
        top3_lines.append(f"{row['Player']} ({row['Squad']}): {row[col]}\n")
    
    top3_lines.append("\n")

# Ghi kết quả Top 3 vào file top_3.txt
with open("top_3.txt", "w", encoding="utf-8") as f:
    f.writelines(top3_lines)

print("Ghi kết quả Top 3 vào file top_3.txt")

# ----------------- 4. Tính thống kê mô tả (Median, Mean, Std) -----------------
def compute_stats(sub_df, cols):
    stats = {}
    for col in cols:
        if sub_df[col].dropna().empty:
            median_val = np.nan
            mean_val = np.nan
            std_val = np.nan
        else:
            median_val = np.nanmedian(sub_df[col].values)
            mean_val = np.nanmean(sub_df[col].values)
            std_val = np.nanstd(sub_df[col].values)
        stats[f"Median_{col}"] = median_val
        stats[f"Mean_{col}"] = mean_val
        stats[f"Std_{col}"] = std_val
    return stats

# Thống kê toàn giải
stats_overall = compute_stats(df, numeric_cols)
stats_all = {"Team": "all"}
stats_all.update(stats_overall)

# Thống kê theo từng đội
teams = df["Squad"].unique()
stats_rows = [stats_all]

for team in teams:
    sub_df = df[df["Squad"] == team]
    team_stats = compute_stats(sub_df, numeric_cols)
    row = {"Team": team}
    row.update(team_stats)
    stats_rows.append(row)

df_stats = pd.DataFrame(stats_rows)
df_stats.to_csv("results2.csv", index=False)
print("Ghi thống kê mô tả vào file results2.csv")

# ----------------- 5. Vẽ biểu đồ Histogram -----------------
# Tạo folder lưu file hình (nếu chưa có)
os.makedirs("histograms", exist_ok=True)

# Hàm chuyển đổi tên cột thành tên file an toàn (loại bỏ ký tự không hợp lệ)
def safe_filename(s):
    # Thay thế mọi ký tự không phải chữ số, chữ cái, dấu gạch dưới hoặc dấu gạch ngang thành dấu gạch dưới
    return re.sub(r"[^\w\-]", "_", s)

for col in numeric_cols:
    # a) Histogram cho toàn giải
    plt.figure(figsize=(8, 6))
    plt.hist(df[col].dropna(), bins=20, color='skyblue', edgecolor='black', alpha=0.8)
    plt.title(f"Distribution of {col} for all players")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.tight_layout()
    filename = safe_filename(f"hist_all_{col}.png")
    plt.savefig(os.path.join("histograms", filename))
    plt.close()
    
    # b) Histogram theo từng đội
    for team in teams:
        team_df = df[df["Squad"] == team]
        if team_df[col].dropna().empty:
            continue
        plt.figure(figsize=(8, 6))
        plt.hist(team_df[col].dropna(), bins=10, color='lightgreen', edgecolor='black', alpha=0.8)
        plt.title(f"Distribution of {col} for {team}")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.tight_layout()
        safe_team = safe_filename(team)
        filename = safe_filename(f"hist_{safe_team}_{col}.png")
        plt.savefig(os.path.join("histograms", filename))
        plt.close()

print("Đã lưu các histogram vào folder 'histograms'.")

# ----------------- 6. Xác định cầu thủ có chỉ số cao nhất -----------------
print("\n----- Cầu thủ có chỉ số cao nhất cho mỗi chỉ số -----")
best_players_lines = []

for col in numeric_cols:
    valid_df = df.dropna(subset=[col])
    if valid_df.empty:
        continue
    idxmax = valid_df[col].idxmax()
    best_player = valid_df.loc[idxmax, "Player"]
    best_team = valid_df.loc[idxmax, "Squad"]
    best_val = valid_df.loc[idxmax, col]
    line = f"For {col}, highest is {best_player} ({best_team}), value = {best_val}"
    best_players_lines.append(line)
    print(line)

with open("best_players.txt", "w", encoding="utf-8") as f:
    f.writelines("\n".join(best_players_lines))

print("\nHoàn thành việc phân tích thống kê và ghi các file kết quả.")
