import pandas as pd
from backend.data_engine.reporter import generate_insights_and_report, export_report_excel, export_report_pdf

df = pd.read_excel(r'C:\Users\ADMIIN\Downloads\Dashboard_Ban_hang.xlsx', sheet_name='Dữ liệu')
rep = generate_insights_and_report(df)

print("KPIs count:", len(rep["kpis"]))
for k in rep["kpis"]:
    print(f"  {k['label']}: {k['value']} ({k['numeric_value']})")

print("\nChart cards count:", len(rep["chart_cards"]))
for idx, c in enumerate(rep["chart_cards"], 1):
    print(f"  {idx}. [{c['section']}] {c['title']} -> {c['analysis']['severity']} (Impact: {c['analysis']['profit_impact']:,.0f})")

print("\nProblem list count:", len(rep["problem_list"]))
print("Top 3 problems:")
for p in rep["problem_list"][:3]:
    print(f"  [{p['severity']}] {p['title']} - Tác động: {p['business_impact']}")
    print(f"    Vấn đề: {p['problem'][:80]}...")
    print(f"    Đề xuất: {p['action'][:80]}...")

# Test Excel export
excel_buf = export_report_excel(df, rep)
print("\nExcel export bytes:", len(excel_buf.getvalue()))

# Test PDF export
pdf_buf = export_report_pdf(df, rep)
print("PDF export bytes:", len(pdf_buf.getvalue()))
print("ALL TESTS PASSED SUCCESSFULLY!")
