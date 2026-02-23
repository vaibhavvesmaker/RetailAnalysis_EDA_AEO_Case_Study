# Revenue at Risk: Retail Fulfillment & Allocation Analysis (AEO Case Study)

## 📌 Project Overview

This project quantifies the financial impact of fulfillment constraints (backorders) and inventory allocation gaps across a multi-year retail dataset. Designed to mirror the **AEO "New Order" B2B platform** workflow, the analysis provides a "Hindsight" view of performance across wholesale partners like Macy’s, Nordstrom, and Amazon.

The core objective is to move from operational metrics (units) to financial outcomes (estimated lost revenue) to support **Assortment and Volume Planning** decisions.

## 📊 Key Retail Metrics Defined

* 
**Fill Rate:** Measures service level performance—how much demand was actually met with allocated stock.


* 
**Lost Revenue (Estimated):** A financial translation of backorder units multiplied by unit price to quantify "Revenue at Risk".


* 
**Hindsight Variance:** Year-over-year (FY24 vs FY25) comparison to identify if fulfillment trends are improving or deteriorating.


* 
**Gross Margin % (GM%):** Evaluates the profitability of fulfilled units per category.



## 🛠️ Technical Stack

* 
**Python:** Used for data engineering, synthetic dataset generation, and multi-year data cleaning.


* 
**Excel (Power Pivot & DAX):** Built the "Connected Planning" engine to reconcile 10,000+ transaction rows into standardized business rules.


* 
**SQL:** Leveraged for relational modeling and data validation to ensure metric integrity.


* 
**Power BI:** Created executive-level dashboards for drill-down analysis into partner and category performance.



## 📂 Repository Structure

* `data/`: Contains the raw and processed CSV datasets.
* 
`notebooks/`: Python scripts used for the initial data engine and KPI calculations.


* 
`dashboard/`: The final Excel/Power BI files containing the visual Hindsight Analysis.


* 
`documentation/`: Detailed business rules and metric definitions used in the model.



## 💡 Strategic Insights

1. 
**Revenue Exposure:** Identified **$1.88M in total lost revenue** due to allocation gaps.


2. 
**Service Levels:** Discovered a **55.87% Fill Rate**, indicating significant inventory constraints in the Denim and Outerwear categories.


3. 
**Partner Prioritization:** Benchmarked B2B partners, revealing that while revenue is high for certain channels, fulfillment inefficiency is eroding margin potential.



## 🚀 How to Use This Project

1. Review the `Executive_Briefing.pdf` for the high-level business case.
2. Explore the `AEO_Retail_Dashboard.xlsx` to interact with the Power Pivot models.
3. Examine the `data_pipeline.py` to see the logic behind the volume planning simulations.



---

**Author:** Vaibhav Vesmaker 

**Contact:** [vaibhavvesmaker@gmail.com](mailto:vaibhavvesmaker@gmail.com) 

**Links:** [LinkedIn](https://www.google.com/search?q=https://linkedin.com/in/vaibhav) | [GitHub](https://github.com/vaibhav) 
