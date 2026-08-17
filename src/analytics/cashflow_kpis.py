import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src import config
import os
import re

import numpy as np
import pandas as pd

def extract_year(y):

    match = re.search(r"\d{2,4}", str(y))
    if match:
        val = match.group()
        if len(val) == 2:
            return 2000 + int(val)
        return int(val)
    return None

def calc_fcf(operating_activity, investing_activity):

    if pd.isna(operating_activity) or pd.isna(investing_activity):
        return None
    return operating_activity + investing_activity

def calc_capex_intensity(investing_activity, sales):

    if pd.isna(investing_activity) or pd.isna(sales) or sales == 0:
        return None
    return (abs(investing_activity) / sales) * 100

def calc_fcf_conversion(fcf, net_profit):

    if pd.isna(fcf) or pd.isna(net_profit) or net_profit == 0:
        return None
    return (fcf / net_profit) * 100

def classify_capital_allocation(cfo, inv_act, cff, capex_intensity):

    if pd.isna(cfo) or pd.isna(cff) or pd.isna(inv_act) or pd.isna(capex_intensity):
        return "Unknown"

    if cfo < 0 and inv_act < 0 and cff < 0:
        return "Pre-Revenue"
    if cfo < 0 and inv_act > 0 and cff > 0:
        return "Distress Signal"
    if cfo < 0 and inv_act < 0 and cff > 0:
        return "Growth Funded by Debt"

    if cfo > 0 and inv_act < 0 and cff < 0:
        if capex_intensity > 1.0:
            return "Shareholder Returns"
        return "Reinvestor"
    if cfo > 0 and inv_act > 0 and cff > 0:
        return "Cash Accumulator"
    if cfo > 0 and inv_act > 0 and cff < 0:
        return "Liquidating Assets"

    return "Mixed"

def main():

    try:
        cf = pd.read_excel(config.DATA_DIR / "cashflow.xlsx", header=1)
        pl = pd.read_excel(config.DATA_DIR / "profitandloss.xlsx", header=1)
        bs = pd.read_excel(config.DATA_DIR / "balancesheet.xlsx", header=1)

    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    cf["year_val"] = cf["year"].apply(extract_year)
    pl["year_val"] = pl["year"].apply(extract_year)
    bs["year_val"] = bs["year"].apply(extract_year)

    df = cf.merge(pl, on=["company_id", "year_val"], suffixes=("", "_pl"), how="outer")
    df = df.merge(bs, on=["company_id", "year_val"], suffixes=("", "_bs"), how="outer")

    df = df.sort_values(["company_id", "year_val"]).reset_index(drop=True)

    results = []
    distress_alerts = []

    for company_id, group in df.groupby("company_id"):
        group = group.dropna(subset=["year_val"]).sort_values("year_val")
        if len(group) == 0:
            continue

        latest_year_data = group.iloc[-1]

        last_5_years = group.tail(5)
        cfo = last_5_years["operating_activity"]
        pat = last_5_years["net_profit"]

        ratios = []
        for c, p in zip(cfo, pat):
            if pd.notna(c) and pd.notna(p) and p != 0:
                ratios.append(c / p)

        cfo_quality_score = np.mean(ratios) if ratios else np.nan

        cfo_quality_label = "Unknown"
        if pd.notna(cfo_quality_score):
            if cfo_quality_score > 1.0:
                cfo_quality_label = "High Quality"
            elif cfo_quality_score >= 0.5:
                cfo_quality_label = "Moderate"
            else:
                cfo_quality_label = "Accrual Risk"

        inv_act = latest_year_data["investing_activity"]
        sales = latest_year_data["sales"]
        capex_intensity_pct = np.nan
        if pd.notna(inv_act) and pd.notna(sales) and sales > 0:
            capex_intensity_pct = (abs(inv_act) / sales) * 100

        capex_label = "Unknown"
        if pd.notna(capex_intensity_pct):
            if capex_intensity_pct > 8:
                capex_label = "Capital Intensive"
            elif capex_intensity_pct >= 3:
                capex_label = "Moderate"
            else:
                capex_label = "Asset Light"

        latest_cfo = latest_year_data.get("operating_activity", np.nan)
        latest_cff = latest_year_data.get("financing_activity", np.nan)
        latest_pat = latest_year_data.get("net_profit", np.nan)

        distress_flag = False
        if pd.notna(latest_cfo) and pd.notna(latest_cff):
            if latest_cfo < 0 and latest_cff > 0:
                distress_flag = True

        deleveraging_flag = False
        if len(group) >= 2:
            prev_year_data = group.iloc[-2]
            latest_borrow = latest_year_data.get("borrowings", np.nan)
            prev_borrow = prev_year_data.get("borrowings", np.nan)
            if (
                pd.notna(latest_cff)
                and pd.notna(latest_borrow)
                and pd.notna(prev_borrow)
            ):
                if latest_cff < 0 and latest_borrow < prev_borrow:
                    deleveraging_flag = True

        group["fcf"] = group["operating_activity"] + group["investing_activity"]
        latest_fcf = group["fcf"].iloc[-1] if not group["fcf"].isna().all() else np.nan

        fcf_cagr_5yr = np.nan
        if len(group) >= 5:
            first_fcf = group["fcf"].iloc[-5]
            if (
                pd.notna(latest_fcf)
                and pd.notna(first_fcf)
                and first_fcf > 0
                and latest_fcf > 0
            ):
                fcf_cagr_5yr = ((latest_fcf / first_fcf) ** (1 / 4)) - 1

        fcf_conversion_pct = np.nan
        if pd.notna(latest_fcf) and pd.notna(latest_pat) and latest_pat != 0:
            fcf_conversion_pct = (latest_fcf / latest_pat) * 100

        if deleveraging_flag:
            cap_alloc = "Debt Reduction"
        elif pd.notna(capex_intensity_pct) and capex_intensity_pct > 8:
            cap_alloc = "Growth Reinvestment"
        elif pd.notna(capex_intensity_pct):
            cap_alloc = "Asset Light Operations"
        else:
            cap_alloc = "Unknown"

        results.append(
            {
                "company_id": company_id,
                "sector": "Unknown",
                "cfo_quality_score": cfo_quality_score,
                "cfo_quality_label": cfo_quality_label,
                "capex_intensity_pct": capex_intensity_pct,
                "capex_label": capex_label,
                "fcf_cagr_5yr": fcf_cagr_5yr,
                "fcf_conversion_pct": fcf_conversion_pct,
                "distress_flag": distress_flag,
                "deleveraging_flag": deleveraging_flag,
                "capital_allocation_label": cap_alloc,
            }
        )

        if distress_flag:
            distress_alerts.append(
                {
                    "company_id": company_id,
                    "CFO value": latest_cfo,
                    "CFF value": latest_cff,
                    "latest net profit": latest_pat,
                }
            )

    res_df = pd.DataFrame(results)
    alerts_df = pd.DataFrame(distress_alerts)

    os.makedirs("output", exist_ok=True)
    res_df.to_excel(config.OUTPUT_DIR / "cashflow_intelligence.xlsx", index=False)
    alerts_df.to_csv(config.OUTPUT_DIR / "distress_alerts.csv", index=False)
    print("Cash flow intelligence data successfully generated.")

if __name__ == "__main__":
    main()