import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer

# Đọc dữ liệu
df = pd.read_csv("results.csv")

# Lọc các cột số
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# Xử lý NaN: loại bỏ cột toàn NaN
data = df[numeric_cols].dropna(axis=1, how="all")

# Impute NaN bằng giá trị trung bình
imputer = SimpleImputer(strategy="mean")
data_imputed_np = imputer.fit_transform(data)

# Lấy tên cột đã được giữ lại (bỏ cột bị toàn NaN)
valid_cols = data.columns[imputer.statistics_ != None]
data_imputed = pd.DataFrame(data_imputed_np, columns=valid_cols)

# Chuẩn hóa dữ liệu
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data_imputed)

# Elbow method để xác định số lượng cụm tối ưu
inertia = []
K_range = range(1, 11)
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(data_scaled)
    inertia.append(kmeans.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(K_range, inertia, marker='o')
plt.title("Elbow Method - Xác định số cụm tối ưu")
plt.xlabel("Số cụm (k)")
plt.ylabel("Inertia")
plt.grid(True)
plt.savefig("elbow_method.png")
plt.show()

# Chọn số cụm (ví dụ: 3 cụm sau khi nhìn biểu đồ)
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(data_scaled)

# Thêm kết quả phân cụm vào dataframe
df["Cluster"] = clusters

# PCA giảm chiều xuống 2D để trực quan hóa
pca = PCA(n_components=2)
pca_result = pca.fit_transform(data_scaled)

df["PCA1"] = pca_result[:, 0]
df["PCA2"] = pca_result[:, 1]

# Vẽ biểu đồ phân cụm 2D
plt.figure(figsize=(10, 7))
sns.scatterplot(data=df, x="PCA1", y="PCA2", hue="Cluster", palette="Set2", s=100)
plt.title("Phân cụm cầu thủ bằng KMeans và PCA")
plt.xlabel("Thành phần chính 1 (PCA1)")
plt.ylabel("Thành phần chính 2 (PCA2)")
plt.legend(title="Cụm")
plt.grid(True)
plt.savefig("player_clusters.png")
plt.show()
