# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "Data" / "\uc11c\uc6b8\uc2dc \uc0c1\uad8c\ubd84\uc11d\uc11c\ube44\uc2a4(\ucd94\uc815\ub9e4\ucd9c-\uc0c1\uad8c)_2025\ub144.csv"
OUT = BASE / "output" / "sales_2025_analysis.txt"


def main():
    df = pd.read_csv(DATA, encoding="cp949")
    lines = []

    def w(s=""):
        lines.append(s)

    quarter_col = df.columns[0]
    district_col = df.columns[4]
    service_col = df.columns[6]
    sales_col = df.columns[7]
    cnt_col = df.columns[8]
    weekday_col = df.columns[9]
    weekend_col = df.columns[10]
    day_cols = list(df.columns[11:18])
    time_cols = list(df.columns[18:24])
    male_col, female_col = df.columns[24], df.columns[25]
    age20, age30 = df.columns[27], df.columns[28]
    age_cols = list(df.columns[26:32])

    df["sales_2030"] = df[age20] + df[age30]
    df["ratio_2030"] = np.where(df[sales_col] > 0, df["sales_2030"] / df[sales_col], np.nan)
    df["ratio_weekend"] = np.where(
        (df[weekday_col] + df[weekend_col]) > 0,
        df[weekend_col] / (df[weekday_col] + df[weekend_col]),
        np.nan,
    )
    df["avg_ticket"] = np.where(df[cnt_col] > 0, df[sales_col] / df[cnt_col], np.nan)

    w("=" * 60)
    w("Seoul commercial district estimated sales 2025 - analysis")
    w("=" * 60)
    w(f"\n[1] Overview")
    w(f"  rows: {len(df):,}  cols: {len(df.columns)}")
    w(f"  districts: {df.iloc[:, 3].nunique():,}")
    w(f"  services: {df.iloc[:, 5].nunique():,}")
    w(f"  quarters: {sorted(df[quarter_col].unique().tolist())}")

    w(f"\n[2] Total scale")
    w(f"  total sales: {df[sales_col].sum():,.0f}")
    w(f"  total count: {df[cnt_col].sum():,.0f}")
    w(f"  avg ticket (per record): {df['avg_ticket'].mean():,.0f}")

    total_2030 = df["sales_2030"].sum()
    total_all = df[sales_col].sum()
    w(f"\n[3] 2030 (20s+30s) share")
    w(f"  2030 sales: {total_2030:,.0f} ({100*total_2030/total_all:.1f}% of total)")
    w(f"  mean 2030 ratio per record: {df['ratio_2030'].mean()*100:.1f}%")
    w(f"  median 2030 ratio: {df['ratio_2030'].median()*100:.1f}%")

    by_svc = df.groupby(service_col).agg(
        total_sales=(sales_col, "sum"),
        sales_2030=("sales_2030", "sum"),
    )
    by_svc["ratio_2030"] = by_svc["sales_2030"] / by_svc["total_sales"]

    w(f"\n[4] Top 10 industries by 2030 share (excl bottom 30% by sales)")
    top_svc = by_svc[by_svc["total_sales"] >= by_svc["total_sales"].quantile(0.3)].nlargest(10, "ratio_2030")
    for name, row in top_svc.iterrows():
        w(f"    - {name}: 2030 {row['ratio_2030']*100:.1f}%, sales {row['total_sales']/1e8:.1f}eok")

    w(f"\n[5] Top 10 industries by total sales")
    for name, row in by_svc.nlargest(10, "total_sales").iterrows():
        w(f"    - {name}: {row['total_sales']/1e8:.1f}eok, 2030 {row['ratio_2030']*100:.1f}%")

    by_dist = df.groupby(district_col).agg(
        total_sales=(sales_col, "sum"),
        sales_2030=("sales_2030", "sum"),
    )
    by_dist["ratio_2030"] = by_dist["sales_2030"] / by_dist["total_sales"]

    w(f"\n[6] Top 10 districts by 2030 share (sales >= 500M KRW)")
    filt = by_dist[by_dist["total_sales"] >= 5e8]
    for name, row in filt.nlargest(10, "ratio_2030").iterrows():
        w(f"    - {name}: 2030 {row['ratio_2030']*100:.1f}%, sales {row['total_sales']/1e8:.1f}eok")

    w(f"\n[7] Top 10 districts by total sales")
    for name, row in by_dist.nlargest(10, "total_sales").iterrows():
        w(f"    - {name}: {row['total_sales']/1e8:.1f}eok, 2030 {row['ratio_2030']*100:.1f}%")

    wd, we = df[weekday_col].sum(), df[weekend_col].sum()
    w(f"\n[8] Weekday vs weekend")
    w(f"  weekday: {100*wd/(wd+we):.1f}%  weekend: {100*we/(wd+we):.1f}%")
    day_sum = df[day_cols].sum()
    for d, v in day_sum.items():
        w(f"    {d}: {100*v/day_sum.sum():.1f}%")

    w(f"\n[9] Time slots")
    tsum = df[time_cols].sum()
    for t, v in tsum.items():
        w(f"    {t}: {100*v/tsum.sum():.1f}%")

    m, f = df[male_col].sum(), df[female_col].sum()
    w(f"\n[10] Gender: male {100*m/(m+f):.1f}% female {100*f/(m+f):.1f}%")

    w(f"\n[11] Age bands")
    asum = df[age_cols].sum()
    labels = ["10s", "20s", "30s", "40s", "50s", "60s+"]
    for lab, v in zip(labels, asum):
        w(f"    {lab}: {100*v/asum.sum():.1f}%")

    w(f"\n[12] By quarter")
    for q, v in df.groupby(quarter_col)[sales_col].sum().items():
        w(f"    {q}: {v/1e8:.1f}eok")

    dist_we = df.groupby(district_col).agg(
        weekday=(weekday_col, "sum"), weekend=(weekend_col, "sum"), total=(sales_col, "sum")
    )
    dist_we["ratio_we"] = dist_we["weekend"] / (dist_we["weekday"] + dist_we["weekend"])
    dist_we = dist_we[dist_we["total"] >= 5e8]
    w(f"\n[13] Weekend-heavy vs weekday-heavy districts (sales>=500M)")
    w("  TOP weekend:")
    for name, row in dist_we.nlargest(5, "ratio_we").iterrows():
        w(f"    - {name}: weekend {row['ratio_we']*100:.1f}%")
    w("  LOW weekend (weekday-type):")
    for name, row in dist_we.nsmallest(5, "ratio_we").iterrows():
        w(f"    - {name}: weekend {row['ratio_we']*100:.1f}%")

    coffee = df[df[service_col].str.contains("\ucee4\ud53c|\uc74c\ub8cc", na=False, regex=True)]
    if len(coffee) > 0:
        c_by = coffee.groupby(district_col).agg(
            total=(sales_col, "sum"), r2030=("ratio_2030", "mean"), rwe=("ratio_weekend", "mean")
        )
        c_by = c_by[c_by["total"] >= 1e8]
        w(f"\n[14] Coffee/beverage (records {len(coffee):,})")
        w("  Top sales districts:")
        for name, row in c_by.nlargest(5, "total").iterrows():
            w(f"    - {name}: {row['total']/1e8:.1f}eok, 2030 avg {row['r2030']*100:.1f}%, weekend {row['rwe']*100:.1f}%")
        w("  Top 2030 share districts (sales>=100M):")
        for name, row in c_by.nlargest(5, "r2030").iterrows():
            w(f"    - {name}: 2030 {row['r2030']*100:.1f}%, sales {row['total']/1e8:.1f}eok")

    hi = df[(df[sales_col] >= 3e7) & (df["ratio_2030"] >= 0.55)].nlargest(8, "ratio_2030")
    w(f"\n[15] High 2030 combos (sales>=30M, 2030>=55%)")
    for _, r in hi.iterrows():
        w(
            f"    - {r[district_col]} / {r[service_col]} / {r[quarter_col]}: "
            f"sales {r[sales_col]/1e6:.0f}M, 2030 {r['ratio_2030']*100:.0f}%, weekend {r['ratio_weekend']*100:.0f}%"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("OK", OUT)


if __name__ == "__main__":
    main()
