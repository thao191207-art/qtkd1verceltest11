import openpyxl
import pandas as pd

wb = openpyxl.load_workbook(r'C:\Users\ADMIIN\Downloads\Dashboard_Ban_hang.xlsx', data_only=True)
ws_pt = wb['Phân tích']

cached_kpis = {}
for r in list(ws_pt.iter_rows(values_only=True))[4:20]:
    if r[0] and r[1] is not None:
        cached_kpis[r[0]] = r[1]

print('Cached KPIs from Phân tích sheet:')
for k, v in cached_kpis.items():
    print(f'  {k}: {v}')

# Calculate from Dữ liệu
df = pd.read_excel(r'C:\Users\ADMIIN\Downloads\Dashboard_Ban_hang.xlsx', sheet_name='Dữ liệu')
print('\nCalculated from Dữ liệu sheet:')
total_net_sales = df['Net_Sales_VND'].sum() / 1e6
total_profit = df['Profit_VND'].sum() / 1e6
margin = df['Profit_VND'].sum() / df['Net_Sales_VND'].sum()
order_count = len(df)
return_count = (df['Returned'] == 'Có').sum()
return_rate = return_count / order_count
avg_sat = df['Customer_Satisfaction'].mean()

print(f'  Tổng doanh thu thuần (tr): {total_net_sales:.3f} vs {cached_kpis.get("Tổng doanh thu thuần (tr)")}')
print(f'  Tổng lợi nhuận (tr): {total_profit:.3f} vs {cached_kpis.get("Tổng lợi nhuận (tr)")}')
print(f'  Biên lợi nhuận: {margin:.6f} vs {cached_kpis.get("Biên lợi nhuận")}')
print(f'  Tổng số đơn: {order_count} vs {cached_kpis.get("Tổng số đơn")}')
print(f'  Số đơn bị hoàn: {return_count} vs {cached_kpis.get("Số đơn bị hoàn")}')
print(f'  Tỷ lệ hoàn: {return_rate:.6f} vs {cached_kpis.get("Tỷ lệ hoàn")}')
print(f'  Hài lòng TB (1–5): {avg_sat:.4f} vs {cached_kpis.get("Hài lòng TB (1–5)")}')
