# Power BI Dashboard Design — A/B Testing Campaign Analysis

> **File:** `powerbi/dashboard_layout.md`  
> **Purpose:** Design specification for the campaign A/B testing Power BI report.  
> **Data source:** `data/raw/campaign_data.csv` imported as table `campaign_data`.

---

## Report Overview

| Property | Value |
|---|---|
| Report name | Campaign A/B Testing Performance Dashboard |
| Pages | 3 |
| Primary audience | Marketing leadership / CMO |
| Refresh cadence | Daily |
| Row count | 50,000 impressions |

---

## Page 1 — Campaign Overview

### KPI Cards (top row)
| Card | Measure | Format |
|---|---|---|
| Total Users | `COUNT(campaign_data[user_id])` | Whole number |
| Overall CTR | `CTR %` | Percentage, 1 dp |
| Overall CVR | `CVR %` | Percentage, 2 dp |
| Total Revenue | `SUM(campaign_data[revenue])` | Currency $, 0 dp |
| Total Cost | `SUM(campaign_data[marketing_cost])` | Currency $, 0 dp |
| Overall ROI | `ROI %` | Percentage, 1 dp |

### Visuals
1. **Bar Chart — CTR by Campaign**
   - X-axis: `campaign_id`
   - Y-axis: `CTR %`
   - Sort: descending by CTR
   - Data labels: on
   - Color: conditional — Campaign_B in orange, others in blue

2. **Bar Chart — Conversion Rate by Campaign**
   - X-axis: `campaign_id`
   - Y-axis: `CVR %`
   - Campaign_B highlighted in gold (#FFD700)
   - Reference line at Campaign_A CVR (dashed, labelled "Control Baseline")
   - Data labels: on

3. **Donut Chart — Budget Allocation by Campaign**
   - Legend: `campaign_id`
   - Values: `SUM(campaign_data[marketing_cost])`
   - Detail labels: percentage + campaign name

### Slicers
- Date range slicer on `impression_date`
- `channel` multi-select slicer
- `device` multi-select slicer

---

## Page 2 — A/B Test Results

### Visuals
1. **Table — Campaign Statistical Summary**

   | Column | Source |
   |---|---|
   | Campaign | `campaign_id` |
   | Impressions | `COUNT(user_id)` |
   | CTR (%) | `CTR %` |
   | CVR (%) | `CVR %` |
   | Revenue / User ($) | `Revenue per User` |
   | p-value | Static value from analysis (manual or parameter table) |
   | Significant? | Conditional column: p < 0.05 → "✅ Yes", else "❌ No" |

   - Conditional formatting on CVR column: green gradient for highest values.

2. **Clustered Bar Chart — Campaign_A vs Campaign_B CVR with CI Bands**
   - Show Campaign_A and Campaign_B CVR as clustered bars
   - Add error bars for 95% confidence interval (via a supporting CI measure table)
   - X-axis: Campaign
   - Y-axis: CVR %

3. **Card — Winner Badge**
   - Text: `"🏆 Campaign_B wins at 95% confidence"`
   - Background: gold (#FFD700), font: bold 16pt, dark text

4. **Gauge — Conversion Rate Uplift**
   - Value: `Uplift vs Control` measure (see DAX below)
   - Min: 0 %
   - Max: 30 %
   - Target: 18 %
   - Needle colour: green

---

## Page 3 — Channel & Device Breakdown

### Visuals
1. **Stacked Bar Chart — Conversions by Channel per Campaign**
   - X-axis: `campaign_id`
   - Y-axis: `SUM(campaign_data[converted])`
   - Legend: `channel`

2. **Matrix — Device × Campaign Conversion Rate Heatmap**
   - Rows: `device`
   - Columns: `campaign_id`
   - Values: `CVR %`
   - Conditional formatting: red-yellow-green colour scale

3. **Line Chart — Daily Conversion Trend by Campaign**
   - X-axis: `impression_date` (day)
   - Y-axis: `CVR %`
   - Series: `campaign_id`
   - Include a 7-day moving average trend line

---

## DAX Measures

```dax
-- Click-Through Rate
CTR % =
DIVIDE(
    SUM(campaign_data[clicked]),
    COUNT(campaign_data[user_id]),
    0
)

-- Conversion Rate (of impressions)
CVR % =
DIVIDE(
    SUM(campaign_data[converted]),
    COUNT(campaign_data[user_id]),
    0
)

-- Revenue per User
Revenue per User =
DIVIDE(
    SUM(campaign_data[revenue]),
    COUNT(campaign_data[user_id]),
    0
)

-- Return on Investment
ROI % =
DIVIDE(
    SUM(campaign_data[revenue]) - SUM(campaign_data[marketing_cost]),
    SUM(campaign_data[marketing_cost]),
    0
)

-- Uplift vs Control (Campaign_A baseline)
Uplift vs Control =
VAR ControlCVR =
    CALCULATE(
        DIVIDE(SUM(campaign_data[converted]), COUNT(campaign_data[user_id]), 0),
        campaign_data[campaign_id] = "Campaign_A"
    )
VAR TreatmentCVR =
    DIVIDE(SUM(campaign_data[converted]), COUNT(campaign_data[user_id]), 0)
RETURN
    DIVIDE(TreatmentCVR - ControlCVR, ControlCVR, 0) * 100

-- 7-day Moving Average CVR
CVR 7D MA =
AVERAGEX(
    DATESINPERIOD(campaign_data[impression_date], LASTDATE(campaign_data[impression_date]), -7, DAY),
    [CVR %]
)

-- Total Revenue (formatted)
Total Revenue $ =
FORMAT(SUM(campaign_data[revenue]), "$#,##0")

-- Campaign Winner Flag
Is Winner =
IF(SELECTEDVALUE(campaign_data[campaign_id]) = "Campaign_B", "🏆 Winner", "")
```

---

## Data Model Notes

- Import `campaign_data.csv` directly into Power BI Desktop.
- Set `impression_date` column to **Date** data type.
- Mark `impression_date` as a Date table for time intelligence functions.
- For p-values and confidence interval bands, create a separate **parameter table**
  loaded from `outputs/ab_test_results.csv` and join on `campaign_id`.

---

## Publishing & Sharing

1. Publish to Power BI Service workspace: `Marketing Analytics`.
2. Set scheduled refresh to **daily at 06:00 UTC**.
3. Share dashboard with `marketing-leadership@company.com` group.
4. Export PDF snapshot to `outputs/` after each refresh.

---

## Screenshot Placeholders

> Replace the placeholders below with actual screenshots once the report is built.

| Page | Placeholder |
|---|---|
| Page 1 — Campaign Overview | `../assets/powerbi_page1_overview.png` |
| Page 2 — A/B Test Results | `../assets/powerbi_page2_ab_results.png` |
| Page 3 — Channel & Device | `../assets/powerbi_page3_breakdown.png` |
