import pandas as pd

df = pd.read_csv("data/superstore.csv", encoding="latin-1")

df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")

print("Shape:", df.shape)
print("\nMissing values per column:")
print(df.isna().sum())
print("\nDuplicate rows:", df.duplicated().sum())

df["Year"] = df["Order Date"].dt.year
df["Month"] = df["Order Date"].dt.month
df["Profit Margin %"] = df["Profit"] / df["Sales"] * 100

print("\nDate range:", df["Order Date"].min().date(), "to", df["Order Date"].max().date())
print("Years in data:", sorted(df["Year"].unique()))
print("\nLoss-making rows:", (df["Profit"] < 0).sum())


import sqlite3

df.columns = [
    c.lower().replace(" ", "_").replace("-", "_").replace("%", "pct")
    for c in df.columns
]

conn = sqlite3.connect("superstore.db")
df.to_sql("orders", conn, if_exists="replace", index=False)

q_region = """
SELECT region,
       ROUND(SUM(sales), 0) AS total_sales,
       ROUND(SUM(profit), 0) AS total_profit,
       ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM orders
GROUP BY region
ORDER BY total_sales DESC;
"""

q_subcat = """
SELECT category, sub_category,
       ROUND(SUM(sales), 0) AS total_sales,
       ROUND(SUM(profit), 0) AS total_profit,
       ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM orders
GROUP BY category, sub_category
ORDER BY margin_pct ASC;
"""

q_year = """
SELECT year,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(sales), 0) AS total_sales,
       ROUND(SUM(profit), 0) AS total_profit
FROM orders
GROUP BY year
ORDER BY year;
"""

print("\nBy region:")
print(pd.read_sql_query(q_region, conn))
print("\nBy sub-category (worst margin first):")
print(pd.read_sql_query(q_subcat, conn))
print("\nBy year:")
print(pd.read_sql_query(q_year, conn))


q_band = """
SELECT CASE WHEN discount = 0 THEN '0%'
            WHEN discount <= 0.2 THEN '1-20%'
            WHEN discount <= 0.4 THEN '21-40%'
            ELSE 'Over 40%' END AS discount_band,
       COUNT(*) AS order_lines,
       ROUND(SUM(sales), 0) AS total_sales,
       ROUND(SUM(profit), 0) AS total_profit,
       ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM orders
GROUP BY discount_band
ORDER BY MIN(discount);
"""

q_disc_sub = """
SELECT sub_category,
       ROUND(AVG(discount) * 100, 1) AS avg_discount_pct,
       ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM orders
GROUP BY sub_category
ORDER BY margin_pct ASC;
"""

q_disc_region = """
SELECT region,
       ROUND(AVG(discount) * 100, 1) AS avg_discount_pct,
       ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM orders
GROUP BY region
ORDER BY margin_pct ASC;
"""

print("\nMargin by discount band:")
print(pd.read_sql_query(q_band, conn))
print("\nDiscount vs margin by sub-category:")
print(pd.read_sql_query(q_disc_sub, conn))
print("\nDiscount vs margin by region:")
print(pd.read_sql_query(q_disc_region, conn))


q_within = """
SELECT sub_category,
       ROUND(SUM(CASE WHEN discount <= 0.2 THEN profit ELSE 0 END) * 100.0
             / SUM(CASE WHEN discount <= 0.2 THEN sales ELSE 0 END), 1) AS margin_low_disc,
       ROUND(SUM(CASE WHEN discount > 0.2 THEN profit ELSE 0 END) * 100.0
             / SUM(CASE WHEN discount > 0.2 THEN sales ELSE 0 END), 1) AS margin_high_disc,
       SUM(CASE WHEN discount > 0.2 THEN 1 ELSE 0 END) AS high_disc_lines
FROM orders
GROUP BY sub_category
ORDER BY margin_low_disc ASC;
"""

print("\nMargin at low vs high discount, within each sub-category:")
print(pd.read_sql_query(q_within, conn))



df["discount_band"] = pd.cut(
    df["discount"],
    bins=[-0.01, 0, 0.2, 0.4, 1.0],
    labels=["0%", "1-20%", "21-40%", "Over 40%"],
)
df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()

df.to_csv("orders_clean.csv", index=False)
print("\nSaved orders_clean.csv:", df.shape)
conn.close()




conn = sqlite3.connect("superstore.db")

q_season = """
SELECT month,
       ROUND(SUM(sales), 0) AS total_sales,
       ROUND(SUM(sales) * 100.0 / (SELECT SUM(sales) FROM orders), 1) AS share_pct
FROM orders
GROUP BY month
ORDER BY month;
"""

print("\nSales by calendar month, all four years combined:")
print(pd.read_sql_query(q_season, conn))
conn.close()