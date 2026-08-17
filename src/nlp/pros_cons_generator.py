import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import os
import sqlite3

import numpy as np
import pandas as pd

def calculate_confidence(val, threshold, max_val=None, higher_is_better=True):

    if pd.isna(val):
        return 0

    if higher_is_better:
        if val <= threshold:
            return 0
        if max_val is None:
            max_val = threshold * 2 if threshold > 0 else 100
        score = 65 + 35 * ((val - threshold) / max(0.01, (max_val - threshold)))
    else:
        if val >= threshold:
            return 0

        min_val = max_val if max_val is not None else 0
        score = 65 + 35 * ((threshold - val) / max(0.01, (threshold - min_val)))

    return min(100, max(0, int(score)))

def generate_pros_and_cons():

    from src import config
    db_path = config.DB_PATH

    conn = sqlite3.connect(db_path)

    companies = pd.read_sql_query(
        "SELECT company_id, company_name FROM companies", conn
    )
    fr = pd.read_sql_query(
        "SELECT * FROM financial_ratios ORDER BY company_id, year", conn
    )
    pl = pd.read_sql_query(
        "SELECT * FROM profitandloss ORDER BY company_id, year", conn
    )
    bs = pd.read_sql_query("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
    mc = pd.read_sql_query("SELECT * FROM market_cap ORDER BY company_id, year", conn)
    sec = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    max_year = fr["year"].max()

    fr_latest = fr[fr["year"] == max_year].set_index("company_id")
    pl_latest = pl[pl["year"] == max_year].set_index("company_id")
    bs_latest = bs[bs["year"] == max_year].set_index("company_id")
    mc_latest = mc[mc["year"] == max_year].set_index("company_id")
    sec_idx = sec.set_index("company_id")

    results = []

    def add_insight(company, type_, rule_id, text, conf):

        if conf > 60:
            results.append(
                {
                    "company_id": company,
                    "type": type_,
                    "rule_id": rule_id,
                    "text": text,
                    "confidence_pct": conf,
                }
            )

    fr_grouped = fr.groupby("company_id")
    pl_grouped = pl.groupby("company_id")

    for comp in companies["company_id"]:
        comp_fr = (
            fr_grouped.get_group(comp) if comp in fr_grouped.groups else pd.DataFrame()
        )
        comp_pl = (
            pl_grouped.get_group(comp) if comp in pl_grouped.groups else pd.DataFrame()
        )

        if len(comp_fr) >= 3:
            roe_last3 = comp_fr.tail(3)["return_on_equity_pct"]
            if (roe_last3 > 20).all():
                avg_roe = roe_last3.mean()
                conf = calculate_confidence(
                    avg_roe, 20, max_val=40, higher_is_better=True
                )
                add_insight(
                    comp,
                    "pro",
                    "P1",
                    "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                    conf,
                )

        if len(comp_fr) >= 5:
            fcf_last5 = comp_fr.tail(5)["free_cash_flow_cr"]
            if (fcf_last5 > 0).all():
                avg_fcf = fcf_last5.mean()

                conf = min(100, 70 + int(min(30, avg_fcf / 1000)))
                add_insight(
                    comp,
                    "pro",
                    "P2",
                    "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                    conf,
                )

        latest_fr = (
            fr_latest.loc[comp] if comp in fr_latest.index else pd.Series(dtype=float)
        )

        de = latest_fr.get("debt_to_equity", np.nan)
        if pd.notna(de) and de <= 0.05:
            conf = 95 if de == 0 else 80
            add_insight(
                comp,
                "pro",
                "P3",
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                conf,
            )

        rev_cagr = latest_fr.get("revenue_cagr_5yr", np.nan)
        if pd.notna(rev_cagr) and rev_cagr > 15:
            conf = calculate_confidence(rev_cagr, 15, max_val=30, higher_is_better=True)
            add_insight(
                comp,
                "pro",
                "P4",
                "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                conf,
            )

        opm = latest_fr.get("operating_profit_margin_pct", np.nan)
        if pd.notna(opm) and opm > 25:
            conf = calculate_confidence(opm, 25, max_val=50, higher_is_better=True)
            add_insight(
                comp,
                "pro",
                "P5",
                "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                conf,
            )

        pat_cagr = latest_fr.get("pat_cagr_5yr", np.nan)
        if pd.notna(pat_cagr) and pat_cagr > 20:
            conf = calculate_confidence(pat_cagr, 20, max_val=40, higher_is_better=True)
            add_insight(
                comp,
                "pro",
                "P6",
                "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                conf,
            )

        icr = latest_fr.get("interest_coverage", np.nan)
        if (pd.notna(icr) and icr > 10) or (pd.notna(de) and de == 0):
            conf = (
                95
                if (pd.notna(de) and de == 0)
                else calculate_confidence(icr, 10, max_val=30, higher_is_better=True)
            )
            add_insight(
                comp,
                "pro",
                "P7",
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                conf,
            )

        div_y = (
            mc_latest.loc[comp, "dividend_yield_pct"]
            if comp in mc_latest.index
            else np.nan
        )
        fcf = latest_fr.get("free_cash_flow_cr", np.nan)
        if pd.notna(div_y) and div_y > 2 and pd.notna(fcf) and fcf > 0:
            conf = calculate_confidence(div_y, 2, max_val=5, higher_is_better=True)
            add_insight(
                comp,
                "pro",
                "P8",
                "Consistent dividend yield above 2% backed by positive free cash flow",
                conf,
            )

        eps_cagr = latest_fr.get("eps_cagr_5yr", np.nan)
        if pd.notna(eps_cagr) and eps_cagr > 15:
            conf = calculate_confidence(eps_cagr, 15, max_val=30, higher_is_better=True)
            add_insight(
                comp,
                "pro",
                "P9",
                "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                conf,
            )

        if len(comp_fr) >= 4:
            roes = comp_fr.tail(4)["return_on_equity_pct"].tolist()
            if len(roes) == 4 and roes[3] > roes[2] > roes[1] > roes[0]:
                conf = min(100, 70 + int((roes[3] - roes[0]) * 2))
                add_insight(
                    comp,
                    "pro",
                    "P10",
                    "Return on equity improving for 3 consecutive years shows strengthening business quality",
                    conf,
                )

        if (
            pd.notna(rev_cagr)
            and pd.notna(pat_cagr)
            and pat_cagr > rev_cagr
            and rev_cagr > 0
        ):
            conf = calculate_confidence(
                pat_cagr - rev_cagr, 0, max_val=15, higher_is_better=True
            )
            add_insight(
                comp,
                "pro",
                "P11",
                "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                conf,
            )

        if len(comp_fr) >= 2:
            comp_bs = bs[bs["company_id"] == comp].sort_values("year")
            if len(comp_bs) >= 2:
                assets_curr = comp_bs.iloc[-1]["total_assets"]
                assets_prev = comp_bs.iloc[-2]["total_assets"]
                debt_curr = comp_fr.iloc[-1]["total_debt_cr"]
                debt_prev = comp_fr.iloc[-2]["total_debt_cr"]
                if (
                    pd.notna(assets_curr)
                    and pd.notna(assets_prev)
                    and pd.notna(debt_curr)
                    and pd.notna(debt_prev)
                ):
                    if assets_curr > assets_prev and debt_curr < debt_prev:
                        asset_growth = (assets_curr / assets_prev) - 1
                        debt_decline = 1 - (debt_curr / max(0.1, debt_prev))
                        conf = min(
                            100, int(70 + (asset_growth * 100) + (debt_decline * 50))
                        )
                        add_insight(
                            comp,
                            "pro",
                            "P12",
                            "Growing asset base funded by internal accruals reflects self-sustaining growth",
                            conf,
                        )

        sector = (
            sec_idx.loc[comp, "broad_sector"] if comp in sec_idx.index else "Unknown"
        )

        if sector != "Financials" and pd.notna(de) and de > 2.0:
            conf = calculate_confidence(
                de, 2.0, max_val=5.0, higher_is_better=True
            )  
            add_insight(
                comp,
                "con",
                "C1",
                f"Debt-to-equity ratio of {de:.1f}x is elevated for a non-financial company and warrants monitoring",
                conf,
            )

        if len(comp_fr) >= 3:
            fcf_last3 = comp_fr.tail(3)["free_cash_flow_cr"]
            if (fcf_last3 < 0).all():
                avg_fcf = abs(fcf_last3.mean())
                conf = min(100, 70 + int(avg_fcf / 1000))
                add_insight(
                    comp,
                    "con",
                    "C2",
                    "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                    conf,
                )

        if len(comp_fr) >= 4:
            opms = comp_fr.tail(4)["operating_profit_margin_pct"].tolist()
            if len(opms) == 4 and opms[3] < opms[2] < opms[1] < opms[0]:
                conf = min(100, 70 + int((opms[0] - opms[3]) * 2))
                add_insight(
                    comp,
                    "con",
                    "C3",
                    "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                    conf,
                )

        latest_pl = (
            pl_latest.loc[comp] if comp in pl_latest.index else pd.Series(dtype=float)
        )
        net_profit = latest_pl.get("net_profit", np.nan)
        if pd.notna(net_profit) and net_profit < 0:
            conf = min(100, 75 + int(abs(net_profit) / 500))
            add_insight(
                comp,
                "con",
                "C4",
                "Company reported a net loss in the most recent financial year",
                conf,
            )

        if len(comp_pl) >= 3:
            revs = comp_pl.tail(3)["sales"].tolist()
            if len(revs) == 3 and revs[2] < revs[1] < revs[0]:
                conf = min(100, 70 + int(100 * (1 - revs[2] / revs[0])))
                add_insight(
                    comp,
                    "con",
                    "C5",
                    "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                    conf,
                )

        if pd.notna(icr) and icr < 1.5:
            conf = calculate_confidence(icr, 1.5, max_val=0, higher_is_better=False)
            add_insight(
                comp,
                "con",
                "C6",
                "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                conf,
            )

        div_payout = latest_fr.get("dividend_payout_ratio_pct", np.nan)
        if pd.notna(div_payout) and div_payout > 100:
            conf = calculate_confidence(
                div_payout, 100, max_val=200, higher_is_better=True
            )
            add_insight(
                comp,
                "con",
                "C7",
                "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                conf,
            )

        if len(comp_fr) >= 4:
            des = comp_fr.tail(4)["debt_to_equity"].tolist()
            if (
                len(des) == 4
                and pd.notna(des).all()
                and des[3] > des[2] > des[1] > des[0]
            ):
                conf = min(100, 70 + int((des[3] - des[0]) * 10))
                add_insight(
                    comp,
                    "con",
                    "C8",
                    "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                    conf,
                )

        if len(comp_fr) >= 4:
            eps_l = comp_fr.tail(4)["earnings_per_share"].tolist()
            if (
                len(eps_l) == 4
                and pd.notna(eps_l).all()
                and eps_l[3] < eps_l[2] < eps_l[1] < eps_l[0]
            ):
                conf = min(100, 75 + int(eps_l[0] - eps_l[3]))
                add_insight(
                    comp,
                    "con",
                    "C9",
                    "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                    conf,
                )

        roce = latest_fr.get("roce", np.nan)
        if pd.notna(roce) and roce < 10:
            conf = calculate_confidence(roce, 10, max_val=0, higher_is_better=False)
            add_insight(
                comp,
                "con",
                "C10",
                "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                conf,
            )

        net_debt = latest_fr.get("net_debt_cr", np.nan)
        op_profit = latest_pl.get("operating_profit", np.nan)
        other_inc = latest_pl.get("other_income", np.nan)

        if pd.notna(net_debt) and pd.notna(op_profit):
            ebitda = op_profit + (other_inc if pd.notna(other_inc) else 0)
            if ebitda > 0 and net_debt > 3 * ebitda:
                ratio = net_debt / ebitda
                conf = calculate_confidence(
                    ratio, 3.0, max_val=8.0, higher_is_better=True
                )
                add_insight(
                    comp,
                    "con",
                    "C11",
                    "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                    conf,
                )

        if pd.notna(rev_cagr) and rev_cagr < 5:
            conf = calculate_confidence(
                rev_cagr, 5, max_val=-10, higher_is_better=False
            )
            add_insight(
                comp,
                "con",
                "C12",
                "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                conf,
            )

    output_df = pd.DataFrame(results)

    if output_df.empty:
        print("No insights generated.")
        return

    all_comps = set(companies["company_id"])
    for comp in all_comps:
        comp_insights = output_df[output_df["company_id"] == comp]
        has_pro = any(comp_insights["type"] == "pro")
        has_con = any(comp_insights["type"] == "con")

        if not has_pro:
            add_insight(
                comp,
                "pro",
                "P_FALLBACK",
                "Company has maintained stability in competitive market conditions",
                65,
            )
        if not has_con:
            add_insight(
                comp,
                "con",
                "C_FALLBACK",
                "Macro-economic headwinds may pose challenges to near-term growth",
                65,
            )

    output_df = pd.DataFrame(results)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    out_path = config.OUTPUT_DIR / "pros_cons_generated.csv"

    output_df = output_df.sort_values(
        by=["company_id", "type", "confidence_pct"], ascending=[True, False, False]
    )
    output_df.to_csv(out_path, index=False)

    print(
        f"Generated {len(output_df)} pros and cons across {output_df['company_id'].nunique()} companies."
    )
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    generate_pros_and_cons()