import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Force output to this script's directory
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
print("WRITING FILES TO:", OUTPUT_DIR)
# -----------------------------
# CONFIG
# -----------------------------
np.random.seed(42)

WEEKS = 104                  # 2 fiscal years
START_DATE = datetime(2024, 1, 1)
N_SKUS = 600

CATEGORIES = [
    "Men's Denim","Women's Denim","Aerie Intimates","Graphic Tees","Tops & Blouses",
    "Outerwear","Activewear","Accessories","Loungewear","Seasonal Capsule"
]

PARTNERS = pd.DataFrame([
    {"Partner":"Macy's","Tier":"Tier 1","Service_Target":0.92,"Priority":1,"Demand_Mult":1.00,"Vol":0.18,"Breadth":0.70},
    {"Partner":"Nordstrom","Tier":"Tier 1","Service_Target":0.94,"Priority":2,"Demand_Mult":0.70,"Vol":0.16,"Breadth":0.55},
    {"Partner":"Amazon","Tier":"Tier 1","Service_Target":0.90,"Priority":3,"Demand_Mult":1.40,"Vol":0.22,"Breadth":0.45},
    {"Partner":"Zappos","Tier":"Tier 2","Service_Target":0.88,"Priority":4,"Demand_Mult":0.45,"Vol":0.20,"Breadth":0.35},
    {"Partner":"NuOrder_Direct","Tier":"Direct","Service_Target":0.95,"Priority":0,"Demand_Mult":0.55,"Vol":0.12,"Breadth":0.60},
]).sort_values("Priority")

CATEGORY_BASE_UNITS = {
    "Men's Denim":18,"Women's Denim":20,"Aerie Intimates":26,"Graphic Tees":22,"Tops & Blouses":16,
    "Outerwear":10,"Activewear":14,"Accessories":12,"Loungewear":15,"Seasonal Capsule":9
}

CATEGORY_PRICING = {
    "Men's Denim":(49.95,79.95,0.48),
    "Women's Denim":(39.95,69.95,0.46),
    "Aerie Intimates":(14.95,34.95,0.42),
    "Graphic Tees":(12.95,29.95,0.40),
    "Tops & Blouses":(19.95,49.95,0.44),
    "Outerwear":(59.95,129.95,0.52),
    "Activewear":(24.95,69.95,0.45),
    "Accessories":(9.95,39.95,0.38),
    "Loungewear":(19.95,59.95,0.43),
    "Seasonal Capsule":(29.95,99.95,0.50),
}

def season_for_week(fw):  # 1..52
    if 1 <= fw <= 13: return "Spring"
    if 14 <= fw <= 26: return "Summer"
    if 27 <= fw <= 39: return "Fall"
    return "Holiday"

def seasonal_mult(category, season):
    if category == "Outerwear":
        return {"Spring":0.75,"Summer":0.55,"Fall":1.15,"Holiday":1.45}[season]
    if category in ["Men's Denim","Women's Denim"]:
        return {"Spring":1.00,"Summer":0.95,"Fall":1.05,"Holiday":1.10}[season]
    if category == "Aerie Intimates":
        return {"Spring":1.00,"Summer":1.05,"Fall":0.98,"Holiday":1.08}[season]
    if category == "Graphic Tees":
        return {"Spring":1.05,"Summer":1.10,"Fall":0.95,"Holiday":1.00}[season]
    if category == "Seasonal Capsule":
        return {"Spring":1.10,"Summer":1.05,"Fall":1.05,"Holiday":1.20}[season]
    return {"Spring":1.02,"Summer":1.00,"Fall":1.03,"Holiday":1.06}[season]

def clamp(x, lo, hi): return max(lo, min(hi, x))

# -----------------------------
# 1) DIM_DATE (weekly)
# -----------------------------
dim_date = pd.DataFrame({
    "Week_Index": np.arange(1, WEEKS+1),
})
dim_date["Week_Start_Date"] = dim_date["Week_Index"].apply(lambda i: (START_DATE + timedelta(days=7*(i-1))).date().isoformat())
dim_date["Fiscal_Year"] = 2024 + ((dim_date["Week_Index"]-1) // 52)
dim_date["Fiscal_Week"] = ((dim_date["Week_Index"]-1) % 52) + 1
dim_date["Season"] = dim_date["Fiscal_Week"].apply(season_for_week)
dim_date["Fiscal_Month"] = np.ceil(dim_date["Fiscal_Week"]/4.33).astype(int).clip(1,12)

# -----------------------------
# 2) DIM_PRODUCT (assortment)
# -----------------------------
styles = [f"STY{str(i).zfill(4)}" for i in range(1, int(N_SKUS/3)+1)]
cat_probs = np.array([0.12,0.12,0.10,0.10,0.10,0.08,0.10,0.08,0.10,0.10])

cats = np.random.choice(CATEGORIES, size=N_SKUS, p=cat_probs)
msrp = []
cost = []
tgm = []
launch = []
end = []
color = np.random.choice(["Black","White","Blue","Navy","Gray","Red","Green","Pink","Tan"], size=N_SKUS)
size = np.random.choice(["XS","S","M","L","XL","XXL"], size=N_SKUS, p=[0.10,0.18,0.24,0.24,0.16,0.08])
style = np.random.choice(styles, size=N_SKUS)

for c in cats:
    lo, hi, ratio = CATEGORY_PRICING[c]
    p = float(np.round(np.random.uniform(lo, hi), 2))
    uc = float(np.round(p * np.random.uniform(ratio-0.05, ratio+0.05), 2))
    msrp.append(p); cost.append(uc); tgm.append(float(np.round(1 - (uc/p), 3)))

    life = np.random.randint(10, 22) if c == "Seasonal Capsule" else np.random.randint(24, 62)
    lw = np.random.randint(1, WEEKS - life + 1)
    launch.append(lw); end.append(lw + life - 1)

dim_product = pd.DataFrame({
    "SKU": [f"SKU{str(i+1).zfill(5)}" for i in range(N_SKUS)],
    "Style": style,
    "Category": cats,
    "Color": color,
    "Size": size,
    "MSRP": msrp,
    "Unit_Cost": cost,
    "Target_GM_Pct": tgm,
    "Launch_Week_Index": launch,
    "End_Week_Index": end
})

# -----------------------------
# 3) ASSORTMENT MAP (partner carries SKU)
# -----------------------------
# Not every partner carries every SKU; breadth differs by partner.
assort_rows = []
for _, p in PARTNERS.iterrows():
    carry = np.random.rand(N_SKUS) < p["Breadth"]
    assort_rows.append(pd.DataFrame({"Partner": p["Partner"], "SKU": dim_product["SKU"], "Carried_Flag": carry.astype(int)}))
assortment_map = pd.concat(assort_rows, ignore_index=True)
assortment_map = assortment_map[assortment_map["Carried_Flag"] == 1].drop(columns=["Carried_Flag"])

# -----------------------------
# 4) FACT_PLAN (weekly plan by partner/SKU)
# -----------------------------
# Build plan at week-partner-category then distribute to carried SKUs in that category (keeps it realistic + manageable)
prod_cat = dim_product[["SKU","Category","MSRP","Unit_Cost","Launch_Week_Index","End_Week_Index"]].copy()
sku_weights = prod_cat.groupby("Category")["SKU"].transform(lambda s: np.random.dirichlet(np.ones(len(s))))
prod_cat["SKU_Weight_In_Category"] = sku_weights

# Precompute carried SKUs with category
carry = assortment_map.merge(prod_cat[["SKU","Category","SKU_Weight_In_Category","Launch_Week_Index","End_Week_Index","MSRP","Unit_Cost"]], on="SKU", how="left")

plan_rows = []
for _, p in PARTNERS.iterrows():
    partner = p["Partner"]
    dm = p["Demand_Mult"]
    vol = p["Vol"]

    for wk in range(1, WEEKS+1):
        season = dim_date.loc[dim_date["Week_Index"]==wk, "Season"].iloc[0]
        active = carry[
            (carry["Partner"] == partner) &
            (carry["Launch_Week_Index"] <= wk) &
            (carry["End_Week_Index"] >= wk)
        ]
        if active.empty:
            continue

        # category totals this week (volume plan)
        cat_totals = []
        for cat in CATEGORIES:
            base = CATEGORY_BASE_UNITS[cat] * seasonal_mult(cat, season) * dm
            units_cat = int(np.round(base * np.random.uniform(1-vol, 1+vol) * 20))  # scale to meaningful weekly volume
            units_cat = int(clamp(units_cat, 0, 5000))
            cat_totals.append((cat, units_cat))
        cat_totals = pd.DataFrame(cat_totals, columns=["Category","Planned_Units_Category"])

        active2 = active.merge(cat_totals, on="Category", how="left")
        # distribute category units to SKUs by weight
        active2["Planned_Units"] = np.round(active2["Planned_Units_Category"] * active2["SKU_Weight_In_Category"]).astype(int)
        active2 = active2[active2["Planned_Units"] > 0]

        if active2.empty:
            continue

        # Keep a reasonable row count: sample if too large
        if len(active2) > 2500:
            active2 = active2.sample(2500, random_state=SEED)

        active2["Week_Index"] = wk
        active2["Partner"] = partner
        active2["Planned_Revenue"] = np.round(active2["Planned_Units"] * active2["MSRP"], 2)
        active2["Planned_GM_Dollars"] = np.round(active2["Planned_Units"] * (active2["MSRP"] - active2["Unit_Cost"]), 2)

        plan_rows.append(active2[["Week_Index","Partner","SKU","Category","Planned_Units","Planned_Revenue","Planned_GM_Dollars"]])

fact_plan = pd.concat(plan_rows, ignore_index=True)

# -----------------------------
# 5) INVENTORY + ALLOCATION + ACTUALS
# -----------------------------
# Starting inventory per SKU: ~6 weeks of total planned demand early in life
sku_plan_week = fact_plan.groupby(["SKU","Week_Index"])["Planned_Units"].sum().reset_index()
prod_lookup = dim_product.set_index("SKU").to_dict(orient="index")

sku_inventory = {}
for sku in dim_product["SKU"]:
    prod = prod_lookup[sku]
    lw = prod["Launch_Week_Index"]
    ew = prod["End_Week_Index"]
    window_end = min(lw + 6, ew)
    window = sku_plan_week[(sku_plan_week["SKU"]==sku) & (sku_plan_week["Week_Index"].between(lw, window_end))]
    init = window["Planned_Units"].sum() if len(window) else np.random.randint(200, 700)
    sku_inventory[sku] = int(np.round(init * np.random.uniform(0.8, 1.2)))

def receipts(prod, wk, planned_total):
    lw, ew = prod["Launch_Week_Index"], prod["End_Week_Index"]
    life_pos = (wk - lw) / max(1, (ew - lw))
    taper = clamp(1.0 - 0.7*life_pos, 0.15, 1.10)
    r = int(np.round(planned_total * np.random.uniform(0.35, 0.85) * taper))
    return int(clamp(r, 0, 5000))

actual_rows = []
partners_meta = PARTNERS.set_index("Partner").to_dict(orient="index")

for wk in range(1, WEEKS+1):
    week_plan = fact_plan[fact_plan["Week_Index"] == wk].copy()
    if week_plan.empty:
        continue

    totals_by_sku = week_plan.groupby("SKU")["Planned_Units"].sum().to_dict()

    # add receipts
    for sku, t in totals_by_sku.items():
        prod = prod_lookup[sku]
        if prod["Launch_Week_Index"] <= wk <= prod["End_Week_Index"]:
            sku_inventory[sku] += receipts(prod, wk, t)

    # allocate per SKU by partner priority
    for sku, sku_lines in week_plan.groupby("SKU"):
        prod = prod_lookup[sku]
        on_hand = int(sku_inventory.get(sku, 0))

        sku_lines = sku_lines.copy()
        sku_lines["Priority"] = sku_lines["Partner"].map(lambda x: partners_meta[x]["Priority"])
        sku_lines = sku_lines.sort_values("Priority")

        # Allocate to meet higher priority first (simple + defensible)
        for _, row in sku_lines.iterrows():
            partner = row["Partner"]
            planned = int(row["Planned_Units"])

            allocated = min(on_hand, planned)
            backorder = planned - allocated
            on_hand -= allocated

            # Forecast vs actual + markdown dynamics
            forecast = int(np.round(planned * np.random.uniform(0.85, 1.15)))
            demand_shock = np.random.uniform(0.85, 1.10)
            actual_units = int(np.round(min(allocated, allocated * demand_shock)))

            life_pos = (wk - prod["Launch_Week_Index"]) / max(1, (prod["End_Week_Index"] - prod["Launch_Week_Index"]))
            base_md = 0.02 + 0.18 * clamp(life_pos, 0, 1)
            over_alloc = max(0, allocated - actual_units)
            md_bump = 0.01 * (over_alloc / max(1, allocated))
            markdown_rate = float(clamp(base_md + md_bump + np.random.uniform(-0.01, 0.02), 0.0, 0.55))

            realized_price = float(np.round(prod["MSRP"] * (1 - markdown_rate), 2))
            revenue = float(np.round(actual_units * realized_price, 2))
            gm = float(np.round(actual_units * (realized_price - prod["Unit_Cost"]), 2))

            fill_rate = allocated / planned if planned else 1.0
            fc_acc = 1 - (abs(actual_units - forecast) / max(1, forecast))

            actual_rows.append({
                "Week_Index": wk,
                "Partner": partner,
                "SKU": sku,
                "Category": prod["Category"],
                "Planned_Units": planned,
                "Forecast_Units": forecast,
                "On_Hand_Before_Allocation": int(sku_inventory[sku]),
                "Allocated_Units": allocated,
                "Backorder_Units": backorder,
                "Actual_Units": actual_units,
                "Markdown_Rate": round(markdown_rate, 3),
                "Realized_Unit_Price": realized_price,
                "Actual_Revenue": revenue,
                "Actual_GM_Dollars": gm,
                "Fill_Rate": round(fill_rate, 3),
                "Forecast_Accuracy": round(clamp(fc_acc, -1, 1), 3),
            })

        sku_inventory[sku] = on_hand

fact_actual = pd.DataFrame(actual_rows)

# -----------------------------
# 6) FACT_BUDGET (explicit budget planning by month/partner/category)
# -----------------------------
# Budget is based on plan with slight top-down adjustments (what planners actually do)
plan_w_date = fact_plan.merge(dim_date[["Week_Index","Fiscal_Year","Fiscal_Month"]], on="Week_Index", how="left")
budget = plan_w_date.groupby(["Fiscal_Year","Fiscal_Month","Partner","Category"], as_index=False).agg(
    Budget_Units=("Planned_Units","sum"),
    Budget_Revenue=("Planned_Revenue","sum"),
    Budget_GM_Dollars=("Planned_GM_Dollars","sum")
)

# Introduce realistic budget revision noise (e.g., leadership adjustments)
adj = np.random.uniform(0.97, 1.05, size=len(budget))
budget["Budget_Revenue"] = np.round(budget["Budget_Revenue"] * adj, 2)
budget["Budget_GM_Dollars"] = np.round(budget["Budget_GM_Dollars"] * np.random.uniform(0.96, 1.04, size=len(budget)), 2)

# -----------------------------
# 7) WEEKLY_KPIs (Excel-ready)
# -----------------------------
actual_w_date = fact_actual.merge(dim_date[["Week_Index","Fiscal_Year","Fiscal_Month","Season"]], on="Week_Index", how="left")
weekly_kpis = actual_w_date.groupby(["Fiscal_Year","Week_Index","Season","Partner","Category"], as_index=False).agg(
    Planned_Units=("Planned_Units","sum"),
    Allocated_Units=("Allocated_Units","sum"),
    Backorder_Units=("Backorder_Units","sum"),
    Actual_Units=("Actual_Units","sum"),
    Actual_Revenue=("Actual_Revenue","sum"),
    Actual_GM_Dollars=("Actual_GM_Dollars","sum"),
    Avg_Fill_Rate=("Fill_Rate","mean"),
    Avg_Forecast_Accuracy=("Forecast_Accuracy","mean"),
    Avg_Markdown_Rate=("Markdown_Rate","mean"),
)

weekly_kpis["Actual_GM_Pct"] = np.round(weekly_kpis["Actual_GM_Dollars"] / weekly_kpis["Actual_Revenue"].replace(0, np.nan), 3)

# -----------------------------
# EXPORT CSVs (Excel/Tableau friendly)
# -----------------------------
dim_date.to_csv(os.path.join(OUTPUT_DIR, "dim_date.csv"), index=False)
PARTNERS.rename(columns={"Service_Target":"Service_Level_Target"}).to_csv(os.path.join(OUTPUT_DIR, "dim_partner.csv"), index=False)
dim_product.to_csv(os.path.join(OUTPUT_DIR, "dim_product.csv"), index=False)
assortment_map.to_csv(os.path.join(OUTPUT_DIR, "assortment_map.csv"), index=False)
fact_plan.to_csv(os.path.join(OUTPUT_DIR, "fact_plan.csv"), index=False)
fact_actual.to_csv(os.path.join(OUTPUT_DIR, "fact_actual_allocation.csv"), index=False)
budget.to_csv(os.path.join(OUTPUT_DIR, "fact_budget.csv"), index=False)
weekly_kpis.to_csv(os.path.join(OUTPUT_DIR, "weekly_kpis.csv"), index=False)

print("✅ V2 Export complete: dim_date, dim_partner, dim_product, assortment_map, fact_plan, fact_actual_allocation, fact_budget, weekly_kpis")