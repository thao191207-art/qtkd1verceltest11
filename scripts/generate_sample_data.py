import pandas as pd
import numpy as np
from pathlib import Path

# Create directory
Path("data").mkdir(exist_ok=True)

np.random.seed(42)

records = []
regions = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Cần Thơ", "Hải Phòng"]
products = ["Hoa Hồng Đỏ Ecuador", "Hoa Lan Hồ Điệp Trắng", "Hoa Cúc Mẫu Đơn Vàng", "Hoa Tulip Hà Lan", "Hoa Hướng Dương Đà Lạt", "Hoa Cẩm Tú Cầu Xanh"]
customers = [
    "Tập Đoàn Khách Sạn Á Đông", "Resort Biển Vàng", "Công Ty Sự Kiện Hoàng Gia",
    "Nhà Hàng Sen Tây Hồ", "Công ty CP Hoa Tươi Việt", "Chuỗi Cafe Xanh",
    "Khách Lẻ Trần Văn Hưng", "Khách Lẻ Lê Thị Mai", "Khách Lẻ Nguyễn Văn Nam"
]

dates = pd.date_range(start="2026-01-01", end="2026-06-30", freq="D")

for i in range(1, 351):
    region = np.random.choice(regions, p=[0.35, 0.30, 0.15, 0.10, 0.10])
    prod = np.random.choice(products)
    
    # Pareto concentration: first 2 customers get higher volume
    cust = np.random.choice(customers, p=[0.25, 0.20, 0.15, 0.10, 0.10, 0.08, 0.04, 0.04, 0.04])
    date = np.random.choice(dates)

    qty = int(np.random.randint(5, 120))
    if prod == "Hoa Lan Hồ Điệp Trắng":
        unit_price = 450000.0
        unit_cost = 280000.0
    elif prod == "Hoa Hồng Đỏ Ecuador":
        unit_price = 350000.0
        unit_cost = 210000.0
    elif prod == "Hoa Tulip Hà Lan":
        unit_price = 280000.0
        unit_cost = 190000.0
    elif prod == "Hoa Cúc Mẫu Đơn Vàng":
        unit_price = 180000.0
        unit_cost = 110000.0
    elif prod == "Hoa Cẩm Tú Cầu Xanh":
        unit_price = 150000.0
        unit_cost = 95000.0
    else:
        unit_price = 90000.0
        unit_cost = 55000.0

    revenue = round(qty * unit_price, 2)
    cost = round(qty * unit_cost, 2)
    profit = round(revenue - cost, 2)

    # Imperfections for cleaning testing
    # whitespace
    region_val = f"  {region}  " if i % 15 == 0 else region
    # missing note
    note = "Giao gấp buổi sáng" if i % 4 == 0 else (None if i % 3 == 0 else "Giao tiêu chuẩn")

    records.append({
        "Ma_Don": f"DH-{10000 + i}",
        "Ngay_Dat": pd.to_datetime(date).strftime("%Y-%m-%d"),
        "Khu_Vuc": region_val,
        "Khach_Hang": cust,
        "SanPham": prod,
        "So_Luong": qty,
        "Don_Gia": unit_price,
        "Doanh_Thu": revenue,
        "Chi_Phi": cost,
        "Loi_Nhuan": profit,
        "Ghi_Chu": note
    })

# Add 4 duplicate rows to test duplicate detection
records.append(records[5].copy())
records.append(records[12].copy())
records.append(records[20].copy())
records.append(records[35].copy())

df = pd.DataFrame(records)

excel_path = "data/sample_flower_business.xlsx"
df.to_excel(excel_path, index=False, sheet_name="Doanh_Thu_2026")
print(f"Created {excel_path} with {len(df)} rows and {len(df.columns)} columns.")

csv_path = "data/sample_flower_business.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"Created {csv_path}.")
