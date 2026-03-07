# Marketing Campaign A/B Testing & Performance Analysis

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![SQL](https://img.shields.io/badge/SQL-SQLite%20%7C%20PostgreSQL-lightgrey?logo=postgresql)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-yellow?logo=powerbi)
![SciPy](https://img.shields.io/badge/SciPy-1.12-green?logo=scipy)
![Pandas](https://img.shields.io/badge/Pandas-2.2-blueviolet?logo=pandas)
![License](https://img.shields.io/badge/License-MIT-red)

---

## Project Overview

This end-to-end portfolio project designs, simulates, and analyses **A/B tests across four e-commerce promotional campaigns** on a dataset of **50,000 customer interactions**. Using Python (SciPy, Pandas, Matplotlib), SQL (window functions, CTEs), and Power BI, the project determines statistically significant winning variants and delivers actionable budget reallocation recommendations.

---

## Key Results

| Metric | Value |
|---|---|
| Customer interactions analysed | **50,000** |
| Campaign variants tested | **4** (A/B/C/D) |
| Statistical winner | **Campaign B** |
| CVR uplift vs control | **~18% higher** |
| Confidence level | **95%** |
| p-value | **< 0.05** (statistically significant) |
| Estimated revenue uplift | **+$45,000+** |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Data generation, EDA, statistical testing |
| Pandas | Data manipulation and aggregation |
| NumPy | Numerical computing, random data generation |
| SciPy | Chi-square tests, Welch t-tests |
| Matplotlib / Seaborn | Data visualisation (6 charts) |
| SQL (SQLite / PostgreSQL) | Campaign metric aggregation (8 queries) |
| Power BI | Interactive KPI dashboard (3 pages) |
| Jupyter Notebook | End-to-end narrative analysis |

---

## Project Structure

```
ab_testing_campaign/
├── README.md
├── requirements.txt
├── data/
│   ├── generate_campaign_data.py   ← synthetic data generator (50K rows)
│   └── raw/
│       ├── campaign_data.csv       ← generated dataset (git-ignored)
│       └── ab_test_results_summary.csv
├── analysis/
│   ├── 01_eda.py                   ← 6 EDA charts + summary stats
│   ├── 02_ab_test.py               ← chi-square, t-test, Cohen's d, ROI
│   └── 03_sql_queries.sql          ← 8 production SQL queries
├── notebooks/
│   └── ab_testing_analysis.ipynb  ← full narrative Jupyter notebook
├── outputs/                        ← auto-generated charts & CSV results
│   └── .gitkeep
└── powerbi/
    └── dashboard_layout.md         ← Power BI design specification & DAX
```

---

## How to Run

```bash
# 1. Clone the repository
git clone https://github.com/BadeNaveenKumar/Ecommerce-retention-analytics.git
cd Ecommerce-retention-analytics/ab_testing_campaign

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate the dataset
python data/generate_campaign_data.py

# 4. Run EDA (saves 6 charts to outputs/)
python analysis/01_eda.py

# 5. Run A/B tests (saves outputs/ab_test_results.csv)
python analysis/02_ab_test.py

# 6. Open the Jupyter notebook
jupyter notebook notebooks/ab_testing_analysis.ipynb
```

---

## Key Findings

- **Campaign_B is the statistical winner** — chi-square test confirms p < 0.05 with ~18% higher conversion rate than Campaign_A (control).
- **CTR uplift**: Campaign_B achieved 22% CTR vs 15% for Campaign_A — a 47% relative improvement.
- **Revenue per user**: Campaign_B generated ~10% higher average revenue per converted user.
- **Best channel**: Email drives the highest conversion rate across all campaigns.
- **Best device**: Desktop users convert at a higher rate than mobile across all campaigns.
- **ROI**: Campaign_B delivers the strongest ROI despite a higher cost-per-impression ($1.20 vs $0.80).
- **Budget recommendation**: Reallocate budget from Campaign_C and Campaign_D to Campaign_B for an estimated **+$45K revenue uplift**.

---

## Statistical Methodology

### Chi-Square Test (Categorical comparison)
Used to compare **CTR** and **CVR** between the control group (Campaign_A) and each treatment group (Campaign_B/C/D).

- **H₀**: No difference in conversion rate between groups.
- **H₁**: Statistically significant difference exists.
- **α = 0.05** — reject H₀ if p < 0.05.

```python
from scipy.stats import chi2_contingency
contingency = [[ctrl_conversions, ctrl_non_conversions],
               [treat_conversions, treat_non_conversions]]
chi2, p, dof, _ = chi2_contingency(contingency)
```

### Welch t-Test (Continuous comparison)
Used to compare **revenue per user** between groups without assuming equal variance.

```python
from scipy.stats import ttest_ind
t_stat, p = ttest_ind(ctrl_revenue, treat_revenue, equal_var=False)
```

### Cohen's d (Effect size)
Measures the practical significance of the revenue difference.

```
d = (mean_B - mean_A) / pooled_std
│d│ < 0.2 → negligible │d│ 0.2–0.5 → small  │d│ 0.5–0.8 → medium  │d│ > 0.8 → large
```

### Wilson Score 95% CI
Confidence intervals for proportions (CTR, CVR) calculated using the Wilson score method — more accurate than the normal approximation for small proportions.

---

## SQL Highlights

**Query 5 — CVR Uplift vs Control (CTE + Self-Join)**
```sql
WITH campaign_cvr AS (
    SELECT campaign_id,
           ROUND(CAST(SUM(converted) AS REAL) / COUNT(user_id) * 100, 4) AS cvr_pct
    FROM campaign_data GROUP BY campaign_id
),
control AS (SELECT cvr_pct AS control_cvr FROM campaign_cvr WHERE campaign_id = 'Campaign_A')
SELECT t.campaign_id,
       t.cvr_pct                                                AS treatment_cvr,
       c.control_cvr,
       ROUND((t.cvr_pct - c.control_cvr) / c.control_cvr * 100, 2) AS uplift_pct
FROM campaign_cvr t CROSS JOIN control c ORDER BY uplift_pct DESC;
```

**Query 4 — Month-over-Month Performance (LAG)**
```sql
WITH monthly AS (
    SELECT campaign_id, STRFTIME('%Y-%m', impression_date) AS month,
           ROUND(CAST(SUM(converted) AS REAL) / COUNT(user_id) * 100, 2) AS cvr_pct
    FROM campaign_data GROUP BY campaign_id, month
)
SELECT campaign_id, month, cvr_pct,
       LAG(cvr_pct) OVER (PARTITION BY campaign_id ORDER BY month) AS prev_month_cvr,
       cvr_pct - LAG(cvr_pct) OVER (PARTITION BY campaign_id ORDER BY month) AS cvr_mom_delta
FROM monthly ORDER BY campaign_id, month;
```

---

## Power BI Dashboard

The dashboard is documented in [`powerbi/dashboard_layout.md`](powerbi/dashboard_layout.md) and contains:

- **Page 1 — Campaign Overview**: KPI cards, CTR/CVR bar charts, budget donut chart.
- **Page 2 — A/B Test Results**: Statistical summary table, winner badge, uplift gauge.
- **Page 3 — Channel & Device Breakdown**: Stacked bars, device heatmap, daily trend line.

| Page | Screenshot |
|---|---|
| Page 1 — Campaign Overview | *(see `assets/powerbi_page1_overview.png`)* |
| Page 2 — A/B Test Results | *(see `assets/powerbi_page2_ab_results.png`)* |
| Page 3 — Channel & Device | *(see `assets/powerbi_page3_breakdown.png`)* |

---

## CV / Resume Bullet Points

- Designed and analysed A/B tests across 4 e-commerce promotional campaigns using Python (SciPy, Pandas) on 50,000 customer interactions to determine statistically significant winning variants.
- Applied t-tests and chi-square tests to measure conversion rate uplift between control and treatment groups; identified Campaign B as winner with 95% confidence interval and 18% higher conversion rate.
- Built SQL queries using window functions and CTEs to aggregate campaign performance metrics including CTR, conversion rate, revenue per user and statistical significance scores.
- Delivered Power BI dashboard tracking campaign KPIs across 4 variants; recommended budget reallocation to winning variant worth an estimated +$45K revenue uplift.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](../LICENSE) for details.
